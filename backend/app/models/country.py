from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from app.db.session import Base

class Country(Base):
    __tablename__ = "countries"

    id = Column(Integer, primary_key=True, index=True)
    
    country_code = Column(String(20), unique=True, index=True)
    country_name = Column(String(100), index=True)
    
    region = Column(String(50))
    
    # ESG 통합 점수 (가중치 적용 가능)
    esg_score = Column(Float, nullable=True)
    e_score = Column(Float, nullable=True)  # Environmental
    s_score = Column(Float, nullable=True)  # Social
    g_score = Column(Float, nullable=True)  # Governance
    
    risk_level = Column(String(20))  # low, medium, high, critical
    
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
