from sqlalchemy.orm import Session
from app.models.trend import Trend
from app.repositories import trend_repository

def create_trend_from_dict(db: Session, trend_data: dict):
    """API 응답을 Trend 객체로 변환 후 저장"""
    external_id = trend_data.get("external_id") or trend_data.get("id")
    
    if trend_repository.get_trend_by_external_id(db, str(external_id)):
        return None
    
    trend = Trend(
        external_id=str(external_id),
        title=trend_data.get("title", "No Title"),
        description=trend_data.get("description"),
        category=trend_data.get("category"),
        esg_category=trend_data.get("esg_category", "E"),
        trend_type=trend_data.get("trend_type", "emerging"),
        momentum=trend_data.get("momentum"),
        keywords=trend_data.get("keywords"),
        related_countries=trend_data.get("related_countries"),
        source=trend_data.get("source"),
        published_at=trend_data.get("published_at")
    )
    
    return trend_repository.create_trend(db, trend)

def get_all_trends(db: Session, skip: int = 0, limit: int = 100):
    return trend_repository.get_all_trends(db, skip, limit)

def get_trends_by_category(db: Session, category: str):
    return trend_repository.get_trends_by_category(db, category)

def clear_all_trends(db: Session):
    trend_repository.delete_all_trends(db)
