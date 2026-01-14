from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class NewsArticle(Base):
    __tablename__ = "news_articles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, comment="关联用户ID")
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    source = Column(String(200))
    source_url = Column(String(1000))
    category = Column(String(100))  # 足球、篮球、网球等
    publish_time = Column(DateTime)
    collected_at = Column(DateTime, server_default=func.now())
    article_metadata = Column(JSON)  # 存储额外信息（球员、球队等）- 重命名避免与SQLAlchemy保留字冲突
    processed = Column(Integer, default=0)  # 0:未处理, 1:已处理
    
    # 关联关系
    user = relationship("User", backref="news_articles")
