from sqlalchemy import Column, Integer, String, Text, DateTime, Date, Index
from sqlalchemy.sql import func
from app.db.session import Base

class News(Base):
    __tablename__ = "news"
    __table_args__ = (
        Index("idx_news_country_published_id", "country", "published_at", "id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String(255), unique=True, index=True) 
    category = Column(String(50), index=True) 
    title = Column(String(500), nullable=False)        
    content = Column(Text, nullable=True)            
    
    # [추가] 원본 뉴스 주소 저장용 컬럼
    url = Column(String(500), nullable=True) 
    
    keywords = Column(Text, nullable=True)            
    media = Column(String(100), index=True)           
    country = Column(String(50), index=True)          
    region = Column(String(50), index=True)           
    published_at = Column(Date, index=True)           
    created_at = Column(DateTime(timezone=True), server_default=func.now()) 
    esg_score = Column(Integer)
