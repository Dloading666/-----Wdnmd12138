from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.news import NewsArticle
from app.models.report import AnalysisReport
from app.models.user import User
from app.auth import get_current_active_user

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

@router.get("/stats")
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取仪表板统计数据（数据隔离：只统计当前用户的数据）"""
    # 今日新闻数量（只统计当前用户）
    today_news_count = db.query(NewsArticle).filter(
        NewsArticle.user_id == current_user.id,  # 核心隔离
        func.date(NewsArticle.collected_at) == func.curdate()
    ).count()
    
    # 总新闻数量（只统计当前用户）
    total_news_count = db.query(NewsArticle).filter(
        NewsArticle.user_id == current_user.id  # 核心隔离
    ).count()
    
    # 今日报告数量（只统计当前用户）
    today_reports_count = db.query(AnalysisReport).filter(
        AnalysisReport.user_id == current_user.id,  # 核心隔离
        func.date(AnalysisReport.created_at) == func.curdate()
    ).count()
    
    # 总报告数量（只统计当前用户）
    total_reports_count = db.query(AnalysisReport).filter(
        AnalysisReport.user_id == current_user.id  # 核心隔离
    ).count()
    
    return {
        "today_news_count": today_news_count,
        "total_news_count": total_news_count,
        "today_reports_count": today_reports_count,
        "total_reports_count": total_reports_count
    }
