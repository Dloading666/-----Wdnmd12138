import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 数据库配置
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = ""  # 从环境变量读取，不要硬编码
    MYSQL_DATABASE: str = "sports_analysis"
    
    # LLM配置
    # 注意：LangChain会自动在base_url后添加/chat/completions
    # 所以base_url应该是: https://dashscope.aliyuncs.com/compatible-mode/v1
    # 最终请求URL会是: https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions
    LLM_API_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    LLM_API_KEY: str = ""  # 从环境变量读取，不要硬编码
    LLM_MODEL: str = "qwen3-max"
    
    # 应用配置
    SECRET_KEY: str = ""  # 从环境变量读取，不要硬编码
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
