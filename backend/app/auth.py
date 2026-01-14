from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db
from app.models.user import User

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    try:
        import bcrypt
        # 尝试使用bcrypt直接验证
        password_bytes = plain_password.encode('utf-8')
        if len(password_bytes) > 72:
            # 截断密码以匹配bcrypt限制
            truncated = password_bytes[:72]
            while truncated and (truncated[-1] & 0xC0) == 0x80:
                truncated = truncated[:-1]
            password_bytes = truncated
        
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except (ImportError, ValueError):
        # 如果bcrypt不可用或验证失败，回退到passlib
        return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    # bcrypt限制：密码不能超过72字节
    # 将密码编码为UTF-8字节，如果超过72字节则截断
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        # 截断到72字节，但要确保不会在UTF-8字符中间截断
        # 简单方法：截断到72字节，然后尝试解码，如果失败则继续截断
        truncated = password_bytes[:72]
        # 尝试找到最后一个完整的UTF-8字符边界
        while truncated and (truncated[-1] & 0xC0) == 0x80:
            truncated = truncated[:-1]
        password_bytes = truncated
        password = password_bytes.decode('utf-8', errors='ignore')
    else:
        password_bytes = password_bytes
    
    # 直接使用bcrypt，避免passlib的版本兼容问题
    try:
        import bcrypt
        # 生成salt并哈希密码
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')
    except ImportError:
        # 如果bcrypt不可用，回退到passlib
        return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建JWT访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[dict]:
    """验证JWT令牌"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """获取当前登录用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = verify_token(token)
    if payload is None:
        raise credentials_exception
    
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )
    
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """获取当前活跃用户"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )
    return current_user
