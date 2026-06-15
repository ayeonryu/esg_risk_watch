from sqlalchemy import Column, Integer, String, Text, DateTime, Date
from sqlalchemy.sql import func
from app.db.session import Base

class News(Base):
    __tablename__ = "news"

    id = Column(Integer, primary_key=True, index=True)
    
    # 중복 방지용 ID (URL이나 nttSn을 넣으세요. 길이는 255가 안전합니다)
    external_id = Column(String(255), unique=True, index=True) 
    
    # 출처 구분 (ESG, CHINA, REPORT, BIGDATA 등)
    category = Column(String(50), index=True) 
    
    title = Column(String(500), nullable=False)        
    content = Column(Text, nullable=True)            
    
    # 빅데이터 API에서 새로 발견한 꿀정보들!
    keywords = Column(Text, nullable=True)             # "키워드", "특성추출" 저장
    media = Column(String(100), index=True)            # "언론사", "무역관(kbc)" 저장
    
    country = Column(String(50), index=True)           
    region = Column(String(50), index=True)            
    published_at = Column(Date, index=True)            
    
    # 데이터가 언제 들어왔는지 기록 (나중에 정렬할 때 꼭 필요해요)
    created_at = Column(DateTime(timezone=True), server_default=func.now()) 
    
    # 나중에 분석 팀이 채워넣을 곳
    esg_score = Column(Integer)