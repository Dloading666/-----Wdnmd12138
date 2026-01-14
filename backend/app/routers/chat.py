from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.agents.chat_agent import ChatAgent
from app.schemas.chat import ChatRequest, ChatResponse
from app.auth import get_current_active_user

router = APIRouter(prefix="/api/chat", tags=["chat"])

@router.post("/message", response_model=ChatResponse)
async def chat_message(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """处理用户对话（数据隔离：每个用户独立的聊天记录）"""
    try:
        # 核心隔离：初始化ChatAgent时传入当前用户ID和数据库会话
        chat_agent = ChatAgent(user_id=current_user.id, db=db)
        
        # 可选：加载用户的历史聊天记录（最近10条）
        # chat_agent.load_history_from_db(limit=10)
        
        # 使用当前登录用户的偏好
        user_preferences = current_user.preferences if current_user.preferences else None
        
        response = await chat_agent.chat(request.message, user_preferences)
        
        return ChatResponse(response=response)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return ChatResponse(response=f"抱歉，处理您的请求时出现了错误：{str(e)}。请稍后重试。")
