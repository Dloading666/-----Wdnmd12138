"""
LLM配置工具函数
确保base_url配置正确，避免路径重复问题
提供原生SDK调用封装，支持enable_search参数
"""
from typing import List, Dict, Optional, Union
from app.config import settings

try:
    from dashscope import Generation
    DASHSCOPE_AVAILABLE = True
except ImportError:
    DASHSCOPE_AVAILABLE = False
    print("⚠️ dashscope未安装，请运行: pip install dashscope")

# LangChain消息类型和Runnable基类
try:
    from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
    from langchain_core.runnables import Runnable
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    BaseMessage = None
    SystemMessage = None
    HumanMessage = None
    AIMessage = None
    Runnable = object  # 如果LangChain不可用，使用object作为基类


def convert_langchain_messages_to_dashscope(messages: List[BaseMessage]) -> List[Dict[str, str]]:
    """
    将LangChain消息格式转换为DashScope消息格式
    
    Args:
        messages: LangChain消息列表（SystemMessage, HumanMessage, AIMessage等）
    
    Returns:
        DashScope格式的消息列表 [{'role': 'system', 'content': '...'}, ...]
    """
    dashscope_messages = []
    
    for msg in messages:
        if isinstance(msg, SystemMessage):
            dashscope_messages.append({
                'role': 'system',
                'content': msg.content
            })
        elif isinstance(msg, HumanMessage):
            dashscope_messages.append({
                'role': 'user',
                'content': msg.content
            })
        elif isinstance(msg, AIMessage):
            dashscope_messages.append({
                'role': 'assistant',
                'content': msg.content
            })
        else:
            # 其他类型消息，尝试获取content
            content = getattr(msg, 'content', str(msg))
            dashscope_messages.append({
                'role': 'user',
                'content': content
            })
    
    return dashscope_messages


def convert_dict_messages_to_dashscope(messages: List[Dict]) -> List[Dict[str, str]]:
    """
    将字典格式的消息转换为DashScope消息格式
    
    Args:
        messages: 字典消息列表，格式如 [{'role': 'system', 'content': '...'}, ...]
    
    Returns:
        DashScope格式的消息列表
    """
    dashscope_messages = []
    
    for msg in messages:
        if isinstance(msg, dict):
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            dashscope_messages.append({
                'role': role,
                'content': content
            })
        else:
            # 如果不是字典，尝试转换为字符串
            dashscope_messages.append({
                'role': 'user',
                'content': str(msg)
            })
    
    return dashscope_messages


class LLMResponse:
    """封装LLM响应，保持与LangChain兼容的接口"""
    def __init__(self, content: str):
        self.content = content


def call_llm_native(
    messages: Union[List[BaseMessage], List[Dict]],
    temperature: float = 0.7,
    enable_search: bool = True
) -> LLMResponse:
    """
    使用原生DashScope SDK同步调用LLM
    
    Args:
        messages: LangChain消息列表或字典消息列表
        temperature: 温度参数，控制随机性
        enable_search: 是否启用联网搜索功能
    
    Returns:
        LLMResponse对象，包含content属性（与LangChain兼容）
    """
    if not DASHSCOPE_AVAILABLE:
        raise ImportError("dashscope未安装，请运行: pip install dashscope")
    
    # 转换消息格式
    if messages and isinstance(messages[0], dict):
        dashscope_messages = convert_dict_messages_to_dashscope(messages)
    elif LANGCHAIN_AVAILABLE and messages and isinstance(messages[0], BaseMessage):
        dashscope_messages = convert_langchain_messages_to_dashscope(messages)
    else:
        # 尝试自动转换
        try:
            dashscope_messages = convert_langchain_messages_to_dashscope(messages)
        except:
            dashscope_messages = convert_dict_messages_to_dashscope(messages)
    
    # 调用DashScope API
    response = Generation.call(
        api_key=settings.LLM_API_KEY,
        model=settings.LLM_MODEL,
        messages=dashscope_messages,
        temperature=temperature,
        enable_search=enable_search,
        result_format="message"
    )
    
    # 处理响应
    if response.status_code == 200:
        content = response.output.choices[0].message.content
        return LLMResponse(content=content)
    else:
        error_msg = f"DashScope API调用失败: HTTP {response.status_code}, 错误码: {response.code}, 错误信息: {response.message}"
        print(f"✗ {error_msg}")
        raise Exception(error_msg)


async def acall_llm_native(
    messages: Union[List[BaseMessage], List[Dict]],
    temperature: float = 0.7,
    enable_search: bool = True
) -> LLMResponse:
    """
    使用原生DashScope SDK异步调用LLM
    
    Args:
        messages: LangChain消息列表或字典消息列表
        temperature: 温度参数，控制随机性
        enable_search: 是否启用联网搜索功能
    
    Returns:
        LLMResponse对象，包含content属性（与LangChain兼容）
    """
    import asyncio
    
    # DashScope SDK本身是同步的，使用asyncio在线程池中执行
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None,
        lambda: call_llm_native(messages, temperature, enable_search)
    )
    return response


class NativeDashScopeLLM(Runnable):
    """
    兼容LangChain ChatOpenAI接口的原生SDK包装类
    保留LangChain Agent的对话管理和上下文处理逻辑
    内部使用原生DashScope SDK调用（带enable_search=True）
    继承Runnable基类，使其能被LangChain识别为Runnable对象
    """
    def __init__(
        self,
        model: str = None,
        temperature: float = 0.7,
        enable_search: bool = True,
        **kwargs
    ):
        """
        初始化原生SDK LLM包装类
        
        Args:
            model: 模型名称（如果为None，使用settings中的配置）
            temperature: 温度参数
            enable_search: 是否启用联网搜索
            **kwargs: 其他参数（兼容LangChain接口）
        """
        # 调用父类初始化（如果Runnable有__init__方法）
        try:
            super().__init__(**kwargs)
        except TypeError:
            # 如果父类不接受这些参数，忽略错误
            pass
        
        self.model = model or settings.LLM_MODEL
        self.temperature = temperature
        self.enable_search = enable_search
        self.kwargs = kwargs
        
        # 兼容LangChain的属性
        self.client = None  # 占位符，某些Agent可能需要
        self.bound_tools = None  # 绑定的工具列表
        
    def bind(self, tools=None, **kwargs):
        """
        绑定工具到LLM（兼容LangChain接口）
        
        Args:
            tools: 工具列表
            **kwargs: 其他绑定参数
        
        Returns:
            新的NativeDashScopeLLM实例，带有绑定的工具
        """
        # 创建新实例，保留原有配置
        bound_llm = NativeDashScopeLLM(
            model=self.model,
            temperature=self.temperature,
            enable_search=self.enable_search,
            **self.kwargs
        )
        # 绑定工具
        bound_llm.bound_tools = tools
        # 更新其他绑定参数
        for key, value in kwargs.items():
            setattr(bound_llm, key, value)
        return bound_llm
    
    def bind_tools(self, tools, **kwargs):
        """
        绑定工具到LLM（LangChain标准方法）
        
        Args:
            tools: 工具列表
            **kwargs: 其他参数
        
        Returns:
            绑定了工具的LLM实例
        """
        return self.bind(tools=tools, **kwargs)
        
    async def ainvoke(self, messages, **kwargs):
        """
        异步调用LLM（兼容LangChain接口）
        
        Args:
            messages: LangChain消息列表
            **kwargs: 其他参数
        
        Returns:
            AIMessage对象（兼容LangChain）
        """
        # 合并kwargs中的temperature和enable_search
        temp = kwargs.get('temperature', self.temperature)
        search = kwargs.get('enable_search', self.enable_search)
        
        # 调用原生SDK
        response = await acall_llm_native(
            messages=messages,
            temperature=temp,
            enable_search=search
        )
        
        # 返回兼容LangChain的AIMessage对象
        if LANGCHAIN_AVAILABLE:
            return AIMessage(content=response.content)
        else:
            # 如果LangChain不可用，返回简单的响应对象
            class SimpleAIMessage:
                def __init__(self, content):
                    self.content = content
            return SimpleAIMessage(content=response.content)
    
    def invoke(self, messages, **kwargs):
        """
        同步调用LLM（兼容LangChain接口）
        
        Args:
            messages: LangChain消息列表
            **kwargs: 其他参数
        
        Returns:
            AIMessage对象（兼容LangChain）
        """
        # 合并kwargs中的temperature和enable_search
        temp = kwargs.get('temperature', self.temperature)
        search = kwargs.get('enable_search', self.enable_search)
        
        # 调用原生SDK
        response = call_llm_native(
            messages=messages,
            temperature=temp,
            enable_search=search
        )
        
        # 返回兼容LangChain的AIMessage对象
        if LANGCHAIN_AVAILABLE:
            return AIMessage(content=response.content)
        else:
            # 如果LangChain不可用，返回简单的响应对象
            class SimpleAIMessage:
                def __init__(self, content):
                    self.content = content
            return SimpleAIMessage(content=response.content)
