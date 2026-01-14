from pydantic import BaseModel, EmailStr, field_validator, ConfigDict
from typing import Optional
from datetime import datetime

class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str
    
    @field_validator('password')
    @classmethod
    def validate_password_length(cls, v: str) -> str:
        """验证密码长度（bcrypt限制72字节）"""
        password_bytes = v.encode('utf-8')
        if len(password_bytes) > 72:
            raise ValueError("密码过长，请使用不超过72个字符的密码")
        return v

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    is_active: bool
    created_at: Optional[datetime] = None
    
    model_config = ConfigDict(
        from_attributes=True,
        # 排除敏感字段
        exclude={'hashed_password', 'preferences'}
    )

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str
    
    @field_validator('new_password')
    @classmethod
    def validate_password_length(cls, v: str) -> str:
        """验证新密码长度（bcrypt限制72字节）"""
        password_bytes = v.encode('utf-8')
        if len(password_bytes) > 72:
            raise ValueError("密码过长，请使用不超过72个字符的密码")
        if len(v) < 6:
            raise ValueError("密码至少需要6个字符")
        return v
