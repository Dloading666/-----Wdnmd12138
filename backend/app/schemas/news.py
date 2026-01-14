from pydantic import BaseModel, Field
from typing import Optional, Dict
from datetime import datetime

class NewsArticleBase(BaseModel):
    title: str
    content: str
    source: Optional[str] = None
    source_url: Optional[str] = None
    category: Optional[str] = None
    metadata: Optional[Dict] = Field(None, alias="article_metadata")  # 映射数据库字段article_metadata

class NewsArticleCreate(NewsArticleBase):
    pass

class NewsArticleResponse(NewsArticleBase):
    id: int
    collected_at: datetime
    processed: int
    
    class Config:
        from_attributes = True
        populate_by_name = True  # 允许使用字段名或别名