from sqlalchemy.orm import Session
from app.models.trend import Trend

def get_trend_by_external_id(db: Session, ext_id: str):
    return db.query(Trend).filter(Trend.external_id == ext_id).first()

def create_trend(db: Session, trend: Trend):
    db.add(trend)
    db.commit()
    db.refresh(trend)
    return trend

def get_all_trends(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Trend).offset(skip).limit(limit).all()

def get_trends_by_category(db: Session, category: str):
    return db.query(Trend).filter(Trend.category == category).all()

def delete_all_trends(db: Session):
    db.query(Trend).delete()
    db.commit()
