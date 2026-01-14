from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response, StreamingResponse
from urllib.parse import quote
from sqlalchemy.orm import Session
from app.database import get_db
from app.agents.news_analyzer import NewsAnalyzerAgent
from app.models.news import NewsArticle
from app.models.report import AnalysisReport
from app.models.user import User
from app.schemas.report import AnalysisReportResponse
from app.auth import get_current_active_user
from datetime import datetime
from typing import List
import json
import asyncio

router = APIRouter(prefix="/api/report", tags=["report"])

@router.get("/list", response_model=List[AnalysisReportResponse])
async def get_report_list(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取当前用户的报告列表（数据隔离：只返回当前用户的报告）"""
    # 核心隔离：只查询当前用户的报告
    reports = db.query(AnalysisReport).filter(
        AnalysisReport.user_id == current_user.id
    ).order_by(AnalysisReport.created_at.desc()).offset(skip).limit(limit).all()
    return reports

async def analyze_news_stream(db: Session, current_user: User):
    """流式分析新闻并推送进度"""
    progress_queue = asyncio.Queue()
    
    async def progress_callback(progress: int, message: str):
        """进度回调函数，将进度放入队列"""
        await progress_queue.put({'progress': progress, 'message': message, 'status': 'loading'})
    
    async def analysis_task():
        """执行分析任务的协程"""
        try:
            # 获取今日未分析的新闻（只查询当前用户的新闻）
            await progress_queue.put({'progress': 10, 'message': '正在获取新闻数据...', 'status': 'loading'})
            
            today_news = db.query(NewsArticle).filter(
                NewsArticle.user_id == current_user.id,  # 核心隔离：只查询当前用户的新闻
                NewsArticle.processed == 0
            ).all()
            
            if not today_news:
                await progress_queue.put({'progress': 0, 'message': '没有需要分析的新闻', 'status': 'error', 'error': '没有需要分析的新闻'})
                return None
            
            # 转换为字典格式
            news_list = [
                {
                    "title": news.title,
                    "content": news.content,
                    "source": news.source,
                    "category": news.category,
                    "id": news.id,
                    "metadata": news.article_metadata or {}
                }
                for news in today_news
            ]
            
            await progress_queue.put({'progress': 20, 'message': f'已获取 {len(news_list)} 条新闻，开始分析...', 'status': 'loading'})
            
            # 使用分析Agent，传入进度回调
            analyzer = NewsAnalyzerAgent()
            analysis_result = await analyzer.analyze_news(news_list, "daily", progress_callback=progress_callback)
            
            await progress_queue.put({'progress': 80, 'message': '分析完成，正在保存报告...', 'status': 'loading'})
            
            # 保存分析报告（绑定当前用户ID）
            report = AnalysisReport(
                user_id=current_user.id,  # 核心隔离：写入时绑定用户ID
                report_date=datetime.now(),
                title=f"今日体育新闻分析报告 - {datetime.now().strftime('%Y-%m-%d')}",
                summary=analysis_result.get('summary', ''),
                content=analysis_result.get('content', ''),
                analysis_type="daily",
                news_ids=[news['id'] for news in news_list],
                statistics=analysis_result.get('statistics', {}),
                sentiment_analysis=analysis_result.get('sentiment_analysis', {})
            )
            
            db.add(report)
            
            # 标记新闻为已处理
            for news in today_news:
                news.processed = 1
            
            db.commit()
            db.refresh(report)
            
            await progress_queue.put({'progress': 100, 'message': '报告生成完成！', 'status': 'success', 'report': {'id': report.id, 'title': report.title}})
            return report
            
        except HTTPException as e:
            await progress_queue.put({'progress': 0, 'message': e.detail, 'status': 'error', 'error': e.detail})
            return None
        except Exception as e:
            db.rollback()
            import traceback
            error_detail = traceback.format_exc()
            error_msg = str(e)
            
            # 检查是否是API额度问题
            if "AllocationQuota" in error_msg or "free tier" in error_msg.lower() or "quota" in error_msg.lower():
                error_msg = "API免费额度已用完。请在DashScope管理控制台关闭'仅使用免费额度'模式，或充值后继续使用。"
            elif "403" in error_msg or "401" in error_msg:
                error_msg = "API认证失败，请检查API密钥是否正确。"
            elif "timeout" in error_msg.lower():
                error_msg = "请求超时，请稍后重试。"
            
            print(f"分析失败: {error_msg}")
            print(f"错误详情: {error_detail}")
            await progress_queue.put({'progress': 0, 'message': error_msg, 'status': 'error', 'error': error_msg})
            return None
        finally:
            # 发送结束标记
            await progress_queue.put(None)
    
    # 启动分析任务
    task = asyncio.create_task(analysis_task())
    
    # 发送初始进度
    yield f"data: {json.dumps({'progress': 0, 'message': '开始分析...', 'status': 'start'})}\n\n"
    await asyncio.sleep(0.05)  # 短暂延迟，确保客户端能接收到
    
    # 从队列中读取进度并推送
    while True:
        try:
            # 等待进度更新，设置超时避免阻塞
            try:
                progress_data = await asyncio.wait_for(progress_queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                # 超时后检查任务是否完成
                if task.done():
                    # 任务完成，尝试获取剩余的数据
                    try:
                        while True:
                            progress_data = progress_queue.get_nowait()
                            if progress_data is None:
                                break
                            yield f"data: {json.dumps(progress_data)}\n\n"
                            await asyncio.sleep(0.05)
                    except asyncio.QueueEmpty:
                        pass
                    break
                continue
            
            if progress_data is None:
                # 收到结束标记
                break
            
            yield f"data: {json.dumps(progress_data)}\n\n"
            await asyncio.sleep(0.05)  # 短暂延迟，确保客户端能接收到
            
        except Exception as e:
            print(f"推送进度时出错: {str(e)}")
            # 检查任务是否完成
            if task.done():
                break
            continue
    
    # 等待任务完成（确保没有异常）
    try:
        await task
    except Exception as e:
        print(f"分析任务异常: {str(e)}")


@router.post("/analyze")
async def analyze_news(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """分析今日体育新闻并生成报告（支持进度推送）"""
    return StreamingResponse(
        analyze_news_stream(db, current_user),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@router.get("/{report_id}", response_model=AnalysisReportResponse)
async def get_report_detail(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取报告详情（数据隔离：只能查看自己的报告）"""
    # 核心隔离：只允许查看当前用户的报告
    report = db.query(AnalysisReport).filter(
        AnalysisReport.id == report_id,
        AnalysisReport.user_id == current_user.id  # 强制用户隔离
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在或无权限访问")
    return report

@router.get("/{report_id}/download-md")
async def download_report_markdown(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """下载报告Markdown文件（数据隔离：只能下载自己的报告）"""
    # 核心隔离：只允许下载当前用户的报告
    report = db.query(AnalysisReport).filter(
        AnalysisReport.id == report_id,
        AnalysisReport.user_id == current_user.id  # 强制用户隔离
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在或无权限访问")

    md_content = report.content or report.summary or ""
    if not md_content.strip():
        md_content = f"# {report.title or '分析报告'}\n\n（报告内容为空）\n"

    safe_title = (report.title or f"report-{report_id}").replace("/", "-").replace("\\", "-").strip()
    filename = f"{safe_title}.md"
    quoted = quote(filename)

    return Response(
        content=md_content,
        media_type="text/markdown; charset=utf-8",
        headers={
            # RFC 5987 for UTF-8 filenames
            "Content-Disposition": f"attachment; filename*=UTF-8''{quoted}"
        },
    )

@router.delete("/{report_id}")
async def delete_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """删除分析报告（数据隔离：只能删除自己的报告）"""
    # 核心隔离：只允许删除当前用户的报告
    report = db.query(AnalysisReport).filter(
        AnalysisReport.id == report_id,
        AnalysisReport.user_id == current_user.id  # 强制用户隔离
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在或无权限访问")
    
    try:
        db.delete(report)
        db.commit()
        return {"message": "报告删除成功", "id": report_id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除报告失败: {str(e)}")
