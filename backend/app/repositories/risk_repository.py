from sqlalchemy.orm import Session
from app.models.risk import Risk

def get_risk_by_external_id(db: Session, ext_id: str):
    return db.query(Risk).filter(Risk.external_id == ext_id).first()

def create_risk(db: Session, risk: Risk):
    db.add(risk)
    db.commit()
    db.refresh(risk)
    return risk

def get_all_risks(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Risk).offset(skip).limit(limit).all()

def get_risks_by_country(db: Session, country_code: str):
    return db.query(Risk).filter(Risk.country_code == country_code).all()

def delete_all_risks(db: Session):
    db.query(Risk).delete()
    db.commit()
