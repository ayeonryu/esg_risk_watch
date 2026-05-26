from pydantic import BaseModel
from datetime import date
from typing import Optional

class BriefingCreate(BaseModel):
    external_id: str
    title: str
    content: Optional[str] = None
    category: Optional[str] = None
    source: Optional[str] = None
    country: Optional[str] = None
    published_at: Optional[date] = None
    summary: Optional[str] = None
    esg_score: Optional[int] = None

class BriefingResponse(BriefingCreate):
    id: int
    class Config:
        from_attributes = True
