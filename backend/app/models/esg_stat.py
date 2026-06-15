from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from app.db.session import Base

class ESGStat(Base):
    __tablename__ = "esg_stats"

    id = Column(Integer, primary_key=True, index=True)
    
    # 구분 정보
    category = Column(String(10), index=True)       # E, S, G 구분
    risk_type = Column(String(100), index=True)    # greenhouse_gas_emissions 등
    
    # 국가 정보
    country = Column(String(100), index=True)      # Korea, China 등
    country_code = Column(String(20), index=True) # KOR 등
    
    # 지표 정보
    indicator = Column(String(255))                # Annual Greenhouse Gas Emissions 등
    indicator_code = Column(String(100))           # Annual_Emissions_GreenhouseGas 등
    
    # 수치 정보
    year = Column(Integer, index=True)             # 2015, 2024 등
    value = Column(Float, nullable=True)           # 752008481.85... (실수형)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())