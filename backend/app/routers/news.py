from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.agents.news_collector import NewsCollectorAgent
from app.tools.hupu_scraper import scrape_hupu_news
from app.models.news import NewsArticle
from app.models.user import User
from app.schemas.news import NewsArticleResponse
from app.auth import get_current_active_user
from datetime import datetime

router = APIRouter(prefix="/api/news", tags=["news"])

@router.post("/generate-daily", response_model=List[NewsArticleResponse])
async def generate_daily_news(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """生成今日体育新闻日报（5条）- 从虎扑网站采集"""
    try:
        # 从虎扑网站采集新闻
        news_list = scrape_hupu_news(category="nba", limit=5)
        
        # 如果虎扑采集失败或数量不足，使用Agent作为备用方案
        if len(news_list) < 5:
            collector = NewsCollectorAgent()
            news_sources = [
                {"name": "虎扑NBA", "url": "https://www.hupu.com/nba"},
                {"name": "虎扑足球", "url": "https://www.hupu.com/soccer"}
            ]
            agent_news = await collector.collect_news(news_sources)
            # 合并结果，去重
            seen_titles = {item.get('title', '') for item in news_list}
            for news in agent_news:
                if news.get('title') and news.get('title') not in seen_titles:
                    news_list.append(news)
                    seen_titles.add(news.get('title'))
        
        # 保存到数据库（只保存5条，绑定当前用户ID）
        saved_articles = []
        for news in news_list[:5]:
            # 处理发布时间
            publish_time = news.get('publish_time')
            if isinstance(publish_time, str):
                try:
                    publish_time = datetime.fromisoformat(publish_time.replace('Z', '+00:00'))
                except:
                    publish_time = datetime.now()
            elif not isinstance(publish_time, datetime):
                publish_time = datetime.now()
            
            article = NewsArticle(
                user_id=current_user.id,  # 核心隔离：写入时绑定用户ID
                title=news.get('title', ''),
                content=news.get('content', '')[:5000] if news.get('content') else '',  # 限制内容长度
                source=news.get('source', '虎扑'),
                source_url=news.get('url', ''),
                category=news.get('category', '体育'),
                article_metadata=news.get('metadata', {}),
                publish_time=publish_time
            )
            db.add(article)
            saved_articles.append(article)
        
        db.commit()
        
        # 刷新以获取ID
        for article in saved_articles:
            db.refresh(article)
        
        return saved_articles
    except Exception as e:
        db.rollback()
        import traceback
        error_detail = traceback.format_exc()
        print(f"生成日报失败: {str(e)}")
        print(f"错误详情: {error_detail}")
        raise HTTPException(status_code=500, detail=f"生成日报失败: {str(e)}")

@router.get("/list", response_model=List[NewsArticleResponse])
async def get_news_list(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取当前用户的新闻列表（数据隔离：只返回当前用户的新闻）"""
    # 核心隔离：只查询当前用户的新闻
    news = db.query(NewsArticle)\
        .filter(NewsArticle.user_id == current_user.id)\
        .order_by(NewsArticle.collected_at.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()
    return news

@router.get("/{news_id}", response_model=NewsArticleResponse)
async def get_news_detail(
    news_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取新闻详情（数据隔离：只能查看自己的新闻）"""
    # 核心隔离：只允许查看当前用户的新闻
    news = db.query(NewsArticle).filter(
        NewsArticle.id == news_id,
        NewsArticle.user_id == current_user.id  # 强制用户隔离
    ).first()
    if not news:
        raise HTTPException(status_code=404, detail="新闻不存在或无权限访问")
    return news

@router.delete("/{news_id}")
async def delete_news(
    news_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """删除新闻（数据隔离：只能删除自己的新闻）"""
    # 核心隔离：只允许删除当前用户的新闻
    news = db.query(NewsArticle).filter(
        NewsArticle.id == news_id,
        NewsArticle.user_id == current_user.id  # 强制用户隔离
    ).first()
    if not news:
        raise HTTPException(status_code=404, detail="新闻不存在或无权限访问")
    
    try:
        db.delete(news)
        db.commit()
        return {"message": "新闻删除成功", "id": news_id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除新闻失败: {str(e)}")
