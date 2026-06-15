from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Date
from sqlalchemy.sql import func
from app.db.session import Base

class Risk(Base):
    __tablename__ = "risks"

    id = Column(Integer, primary_key=True, index=True)
    
    external_id = Column(String(255), unique=True, index=True)
    
    country_code = Column(String(20), index=True)
    country_name = Column(String(100), index=True)
    
    risk_type = Column(String(100), index=True)  # environmental, social, governance, geopolitical 등
    risk_category = Column(String(100), index=True)  # climate_change, labor_dispute, corruption 등
    
    risk_level = Column(String(20), index=True)  # low, medium, high, critical
    risk_score = Column(Float)  # 0~100
    
    description = Column(Text)
    impact = Column(Text)
    mitigation = Column(Text)
    
    source = Column(String(100))
    date_identified = Column(Date)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
