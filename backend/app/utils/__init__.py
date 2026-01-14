"""
工具函数模块
"""
from .llm_config import (
    call_llm_native,
    acall_llm_native,
    NativeDashScopeLLM
)

__all__ = [
    'call_llm_native',
    'acall_llm_native',
    'NativeDashScopeLLM'
]
