from sqlalchemy import Column, Integer, String, Text, DateTime, Date
from sqlalchemy.sql import func
from app.db.session import Base

class Briefing(Base):
    __tablename__ = "briefings"

    id = Column(Integer, primary_key=True, index=True)
    
    external_id = Column(String(255), unique=True, index=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=True)
    
    category = Column(String(100), index=True)  # 주제별 분류
    source = Column(String(100), index=True)    # 출처
    country = Column(String(50), index=True)
    
    published_at = Column(Date, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    summary = Column(Text, nullable=True)  # 요약본
    esg_score = Column(Integer)
