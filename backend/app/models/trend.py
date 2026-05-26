from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Date
from sqlalchemy.sql import func
from app.db.session import Base

class Trend(Base):
    __tablename__ = "trends"

    id = Column(Integer, primary_key=True, index=True)
    
    external_id = Column(String(255), unique=True, index=True)
    
    title = Column(String(500), nullable=False)
    description = Column(Text)
    
    category = Column(String(100), index=True)  # e.g., renewable_energy, net_zero, diversity
    esg_category = Column(String(10), index=True)  # E, S, G
    
    trend_type = Column(String(50))  # emerging, accelerating, declining
    momentum = Column(Float)  # 변화 정도 (-1~1)
    
    keywords = Column(Text)
    related_countries = Column(Text)  # 콤마 분리
    
    source = Column(String(100))
    published_at = Column(Date)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
