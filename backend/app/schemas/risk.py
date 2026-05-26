from pydantic import BaseModel
from datetime import date
from typing import Optional

class RiskCreate(BaseModel):
    external_id: str
    country_code: str
    country_name: str
    risk_type: str
    risk_category: str
    risk_level: str
    risk_score: float
    description: Optional[str] = None
    impact: Optional[str] = None
    mitigation: Optional[str] = None
    source: Optional[str] = None
    date_identified: Optional[date] = None

class RiskResponse(RiskCreate):
    id: int
    class Config:
        from_attributes = True
