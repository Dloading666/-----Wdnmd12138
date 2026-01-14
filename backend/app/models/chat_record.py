"""
聊天记录模型
存储用户与AI助手的对话记录
"""
from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class ChatRecord(Base):
    __tablename__ = "chat_records"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, comment="关联用户ID")
    message = Column(Text, nullable=False, comment="用户消息")
    response = Column(Text, nullable=False, comment="AI回复")
    created_at = Column(DateTime, server_default=func.now(), index=True, comment="创建时间")
    
    # 关联关系
    user = relationship("User", backref="chat_records")
