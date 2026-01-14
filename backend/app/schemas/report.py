from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime

class AnalysisReportResponse(BaseModel):
    id: int
    report_date: datetime
    title: Optional[str]
    summary: Optional[str]
    content: Optional[str]
    analysis_type: Optional[str]
    news_ids: Optional[List[int]]
    statistics: Optional[Dict]
    sentiment_analysis: Optional[Dict]
    created_at: datetime
    
    class Config:
        from_attributes = True
