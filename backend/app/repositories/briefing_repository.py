from sqlalchemy.orm import Session
from app.models.briefing import Briefing

def get_briefing_by_external_id(db: Session, ext_id: str):
    return db.query(Briefing).filter(Briefing.external_id == ext_id).first()

def create_briefing(db: Session, briefing: Briefing):
    db.add(briefing)
    db.commit()
    db.refresh(briefing)
    return briefing

def get_all_briefings(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Briefing).offset(skip).limit(limit).all()

def delete_all_briefings(db: Session):
    db.query(Briefing).delete()
    db.commit()
