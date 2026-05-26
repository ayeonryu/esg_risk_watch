from sqlalchemy.orm import Session
from app.models.country import Country

def get_country_by_code(db: Session, country_code: str):
    return db.query(Country).filter(Country.country_code == country_code).first()

def create_or_update_country(db: Session, country: Country):
    existing = get_country_by_code(db, country.country_code)
    if existing:
        for key, value in country.__dict__.items():
            if not key.startswith('_'):
                setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return existing
    db.add(country)
    db.commit()
    db.refresh(country)
    return country

def get_all_countries(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Country).offset(skip).limit(limit).all()

def delete_all_countries(db: Session):
    db.query(Country).delete()
    db.commit()
