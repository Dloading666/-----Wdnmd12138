from sqlalchemy import Column, Integer, String, DateTime, JSON, Boolean
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(200), unique=True, index=True)
    hashed_password = Column(String(255), nullable=False)  # 存储哈希后的密码
    is_active = Column(Boolean, default=True)  # 用户是否激活
    preferences = Column(JSON)  # 用户偏好（关注的球队、运动类型等）
    created_at = Column(DateTime, server_default=func.now())
