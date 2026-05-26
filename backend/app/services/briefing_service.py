from sqlalchemy.orm import Session
from app.models.briefing import Briefing
from app.repositories import briefing_repository

def create_briefing_from_dict(db: Session, briefing_data: dict):
    """API 응답을 Briefing 객체로 변환 후 저장"""
    external_id = briefing_data.get("external_id") or briefing_data.get("id")
    
    if briefing_repository.get_briefing_by_external_id(db, str(external_id)):
        return None
    
    briefing = Briefing(
        external_id=str(external_id),
        title=briefing_data.get("title", "No Title"),
        content=briefing_data.get("content") or briefing_data.get("description"),
        category=briefing_data.get("category"),
        source=briefing_data.get("source"),
        country=briefing_data.get("country"),
        published_at=briefing_data.get("published_at"),
        summary=briefing_data.get("summary")
    )
    
    return briefing_repository.create_briefing(db, briefing)

def get_all_briefings(db: Session, skip: int = 0, limit: int = 100):
    return briefing_repository.get_all_briefings(db, skip, limit)

def clear_all_briefings(db: Session):
    briefing_repository.delete_all_briefings(db)
