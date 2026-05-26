from pydantic import BaseModel
from typing import Optional

class CountryCreate(BaseModel):
    country_code: str
    country_name: str
    region: Optional[str] = None
    esg_score: Optional[float] = None
    e_score: Optional[float] = None
    s_score: Optional[float] = None
    g_score: Optional[float] = None
    risk_level: Optional[str] = None

class CountryResponse(CountryCreate):
    id: int
    class Config:
        from_attributes = True
