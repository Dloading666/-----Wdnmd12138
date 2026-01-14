from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class AnalysisReport(Base):
    __tablename__ = "analysis_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, comment="关联用户ID")
    report_date = Column(DateTime, nullable=False)
    title = Column(String(500))
    summary = Column(Text)
    content = Column(Text)
    analysis_type = Column(String(100))  # 日报、深度分析、舆情分析等
    news_ids = Column(JSON)  # 关联的新闻ID列表
    statistics = Column(JSON)  # 统计数据
    sentiment_analysis = Column(JSON)  # 情感分析结果
    created_at = Column(DateTime, server_default=func.now())
    
    # 关联关系
    user = relationship("User", backref="analysis_reports")
