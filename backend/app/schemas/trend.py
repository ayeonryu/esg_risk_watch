from pydantic import BaseModel
from datetime import date
from typing import Optional

class TrendCreate(BaseModel):
    external_id: str
    title: str
    description: Optional[str] = None
    category: str
    esg_category: str
    trend_type: str
    momentum: Optional[float] = None
    keywords: Optional[str] = None
    related_countries: Optional[str] = None
    source: Optional[str] = None
    published_at: Optional[date] = None

class TrendResponse(TrendCreate):
    id: int
    class Config:
        from_attributes = True
