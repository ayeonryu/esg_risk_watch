from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.db.session import Base

class News(Base):
    __tablename__ = "news"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)        # 뉴스 제목
    content = Column(Text, nullable=False)             # 뉴스 본문
    url = Column(String(500), nullable=False)          # 원문 링크
    country = Column(String(50), index=True)           # 국가 (예: USA, KOR)
    company = Column(String(100), index=True)          # 대상 기업
    esg_score = Column(Integer)                        # ESG 점수 (데이터팀 협의 필요)
    created_at = Column(DateTime(timezone=True), server_default=func.now()) # 수집 일시