from sqlalchemy.orm import Session
from app.models.risk import Risk
from app.repositories import risk_repository

def create_risk_from_dict(db: Session, risk_data: dict):
    external_id = risk_data.get("external_id") or risk_data.get("id")
    
    if risk_repository.get_risk_by_external_id(db, str(external_id)):
        return None
    
    country_code = risk_data.get("country_code")
    if country_code in ["DE", "Germany", "독일"]:
        country_code = "DEU"
        
    risk = Risk(
        external_id=str(external_id),
        country_code=country_code,
        country_name=risk_data.get("country_name"),
        risk_type=risk_data.get("risk_type"),
        risk_category=risk_data.get("risk_category"),
        risk_level=risk_data.get("risk_level", "medium"),
        risk_score=risk_data.get("risk_score", 50.0),
        description=risk_data.get("description"),
        impact=risk_data.get("impact"),
        mitigation=risk_data.get("mitigation"),
        source=risk_data.get("source"),
        date_identified=risk_data.get("date_identified")
    )
    
    return risk_repository.create_risk(db, risk)

def get_all_risks(db: Session, skip: int = 0, limit: int = 100):
    return risk_repository.get_all_risks(db, skip, limit)

def get_risks_by_country(db: Session, country_code: str):
    if country_code in ["DE", "Germany", "독일"]:
        country_code = "DEU"
    return risk_repository.get_risks_by_country(db, country_code)

def clear_all_risks(db: Session):
    risk_repository.delete_all_risks(db)