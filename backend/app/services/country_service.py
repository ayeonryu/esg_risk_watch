from sqlalchemy.orm import Session
from app.models.country import Country
from app.repositories import country_repository

def create_or_update_country_from_dict(db: Session, country_data: dict):
    """API 응답을 Country 객체로 변환 후 저장/업데이트"""
    country_code = country_data.get("country_code")
    if not country_code:
        return None
    
    country = Country(
        country_code=country_code,
        country_name=country_data.get("country_name", ""),
        region=country_data.get("region"),
        esg_score=country_data.get("esg_score"),
        e_score=country_data.get("e_score"),
        s_score=country_data.get("s_score"),
        g_score=country_data.get("g_score"),
        risk_level=country_data.get("risk_level")
    )
    
    return country_repository.create_or_update_country(db, country)

def get_all_countries(db: Session, skip: int = 0, limit: int = 100):
    return country_repository.get_all_countries(db, skip, limit)

def get_country_by_code(db: Session, country_code: str):
    return country_repository.get_country_by_code(db, country_code)

def clear_all_countries(db: Session):
    country_repository.delete_all_countries(db)
