"""
聊天助手Agent - 使用原生DashScope SDK的enable_search功能
完全移除自定义爬取逻辑，仅依赖模型内置联网能力
支持用户数据隔离
"""
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from app.config import settings
from app.utils.llm_config import acall_llm_native
from app.models.chat_record import ChatRecord


class ChatAgent:
    def __init__(self, user_id: int, db: Session):
        """
        初始化聊天助手
        
        Args:
            user_id: 当前用户ID（用于数据隔离）
            db: 数据库会话（用于保存聊天记录）
        """
        self.user_id = user_id  # 绑定用户ID，实现数据隔离
        self.db = db
        self.chat_history: List = []
        self.temperature = 0.7
        
        # 系统提示：明确告知模型使用内置联网功能
        self.system_prompt = """你是一个专业的体育智能助手，具有内置联网搜索功能。

**你的核心能力：**
1. 回答用户关于体育的各种问题（比赛结果、球员数据、赛事信息等）
2. 支持上下文连续对话
3. **内置联网搜索功能**：系统已为你启用了联网搜索（enable_search=True），你可以自动从互联网获取最新的体育资讯

**联网功能说明：**
- 系统已启用内置联网搜索功能，你可以自动从互联网获取最新信息
- 当用户询问"今天"、"最新"、"实时"、"最近"、"比分"、"赛程"等需要实时信息的问题时，**请自动使用联网搜索功能获取最新数据**
- 联网搜索会自动从互联网获取最新的体育新闻、比赛结果、球员统计等信息
- **重要**：对于需要实时数据的问题（如今天的比赛、最新比分、球员得分等），请务必使用联网搜索获取最新信息
- 如果联网搜索获取到具体数据（得分、比分、统计数据等），请直接使用这些数据回答用户
- 如果联网搜索没有找到相关信息，请基于你的知识库回答，并说明这是历史数据

**回答要求：**
- 对于需要实时信息的问题，优先使用联网搜索获取最新数据
- 回答要准确、专业、友好
- 如果使用了联网搜索，可以在回答中说明信息来源

请友好、专业地回答用户的问题。"""
    
    async def chat(self, user_input: str, user_preferences: Optional[Dict] = None) -> str:
        """
        处理用户对话 - 仅使用原生SDK的enable_search功能
        
        Args:
            user_input: 用户输入的问题
            user_preferences: 用户偏好设置（可选）
        
        Returns:
            模型的回答
        """
        try:
            # 构建消息列表
            messages = [SystemMessage(content=self.system_prompt)]
            
            # 如果有用户偏好，添加到系统消息
            if user_preferences:
                preference_text = f"用户偏好信息：{user_preferences}"
                messages.append(SystemMessage(content=preference_text))
            
            # 添加对话历史
            messages.extend(self.chat_history)
            
            # 添加当前用户输入
            messages.append(HumanMessage(content=user_input))
            
            # 直接调用原生SDK（enable_search=True，让模型自己决定是否联网）
            response = await acall_llm_native(
                messages=messages,
                temperature=self.temperature,
                enable_search=True  # 核心：启用模型内置联网功能
            )
            response_text = response.content
            
            # 更新对话历史
            self.chat_history.append(HumanMessage(content=user_input))
            self.chat_history.append(AIMessage(content=response_text))
            
            # 限制历史长度（保留最近10轮对话）
            if len(self.chat_history) > 20:  # 10轮对话 = 20条消息
                self.chat_history = self.chat_history[-20:]
            
            # 保存聊天记录到数据库（绑定用户ID）
            try:
                chat_record = ChatRecord(
                    user_id=self.user_id,  # 核心隔离：绑定用户ID
                    message=user_input,
                    response=response_text
                )
                self.db.add(chat_record)
                self.db.commit()
            except Exception as e:
                # 如果保存失败，记录错误但不影响返回结果
                print(f"保存聊天记录失败: {str(e)}")
                self.db.rollback()
            
            return response_text
            
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            print(f"❌ 聊天处理出错: {str(e)}")
            print(f"错误详情: {error_detail}")
            return f"抱歉，处理您的请求时出现了错误：{str(e)}。请稍后重试。"
    
    def reset_history(self):
        """重置对话历史（仅重置内存中的历史，数据库记录保留）"""
        self.chat_history = []
    
    def load_history_from_db(self, limit: int = 10):
        """
        从数据库加载当前用户的聊天历史
        
        Args:
            limit: 加载的历史记录数量（默认10条）
        """
        try:
            # 核心隔离：只加载当前用户的聊天记录
            records = self.db.query(ChatRecord).filter(
                ChatRecord.user_id == self.user_id
            ).order_by(ChatRecord.created_at.desc()).limit(limit).all()
            
            # 转换为LangChain消息格式（倒序，最新的在后面）
            self.chat_history = []
            for record in reversed(records):
                self.chat_history.append(HumanMessage(content=record.message))
                self.chat_history.append(AIMessage(content=record.response))
        except Exception as e:
            print(f"加载聊天历史失败: {str(e)}")
            self.chat_history = []
