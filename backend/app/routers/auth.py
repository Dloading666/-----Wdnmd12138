from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_active_user
)
from app.schemas.auth import UserRegister, UserLogin, Token, UserResponse, ChangePasswordRequest
from datetime import timedelta
from app.config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """用户注册"""
    try:
        # 检查用户名是否已存在
        db_user = db.query(User).filter(User.username == user_data.username).first()
        if db_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )
        
        # 检查邮箱是否已存在
        db_user = db.query(User).filter(User.email == user_data.email).first()
        if db_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被注册"
            )
        
        # 验证密码长度（bcrypt限制72字节）
        password_bytes = user_data.password.encode('utf-8')
        if len(password_bytes) > 72:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="密码过长，请使用不超过72个字符的密码"
            )
        
        # 创建新用户
        hashed_password = get_password_hash(user_data.password)
        db_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            is_active=True
        )
        
        db.add(db_user)
        try:
            db.commit()
            db.refresh(db_user)
            print(f"✓ 用户注册成功: {db_user.username} (ID: {db_user.id})")
            # 确保返回的数据符合 UserResponse schema
            return UserResponse(
                id=db_user.id,
                username=db_user.username,
                email=db_user.email,
                is_active=db_user.is_active,
                created_at=db_user.created_at
            )
        except Exception as commit_error:
            db.rollback()
            print(f"✗ 数据库提交失败: {str(commit_error)}")
            import traceback
            traceback.print_exc()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"保存用户数据失败: {str(commit_error)}"
            )
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        # 回滚事务
        db.rollback()
        # 记录详细错误信息到日志
        import traceback
        error_detail = traceback.format_exc()
        import logging
        logging.error(f"注册失败错误: {str(e)}")
        logging.error(f"错误详情: {error_detail}")
        # 返回更友好的错误信息
        error_msg = str(e)
        if "hashed_password" in error_msg or "Column" in error_msg:
            error_msg = "数据库表结构不完整，请运行数据库初始化脚本"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )

@router.post("/login", response_model=Token)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """用户登录"""
    # 查找用户
    user = db.query(User).filter(User.username == user_data.username).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 验证密码
    if not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 检查用户是否激活
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )
    
    # 创建访问令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """获取当前用户信息"""
    return current_user

@router.post("/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """修改密码"""
    try:
        # 验证旧密码
        if not verify_password(password_data.old_password, current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="原密码错误"
            )
        
        # 验证新密码长度
        password_bytes = password_data.new_password.encode('utf-8')
        if len(password_bytes) > 72:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="密码过长，请使用不超过72个字符的密码"
            )
        
        if len(password_data.new_password) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="密码至少需要6个字符"
            )
        
        # 检查新旧密码是否相同
        if password_data.old_password == password_data.new_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="新密码不能与原密码相同"
            )
        
        # 更新密码
        current_user.hashed_password = get_password_hash(password_data.new_password)
        db.commit()
        db.refresh(current_user)
        
        return {"message": "密码修改成功"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"修改密码失败: {str(e)}"
        )

@router.post("/logout")
async def logout():
    """用户登出（客户端删除token即可）"""
    return {"message": "登出成功"}
