from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.esg_stat import ESGStat

router = APIRouter()

@router.get("/list")
def list_risks(skip: int = Query(0), limit: int = Query(100), db: Session = Depends(get_db)):
    risks = db.query(ESGStat).filter(ESGStat.risk_type.isnot(None)).offset(skip).limit(limit).all()
    return {
        "total": len(risks),
        "items": risks,
        "skip": skip,
        "limit": limit
    }

@router.get("/{risk_id}")
def get_risk(risk_id: int, db: Session = Depends(get_db)):
    risk = db.query(ESGStat).filter(ESGStat.id == risk_id, ESGStat.risk_type.isnot(None)).first()
    if not risk:
        return {"status": "failed", "message": "리스크를 찾을 수 없습니다"}
    return risk

@router.get("/country/{country_code}")
def get_country_risks(country_code: str, db: Session = Depends(get_db)):
    risks = db.query(ESGStat).filter(ESGStat.country_code == country_code, ESGStat.risk_type.isnot(None)).all()
    return {
        "country_code": country_code,
        "total": len(risks),
        "items": risks
    }

@router.get("/category/{risk_category}")
def get_risks_by_category(risk_category: str, db: Session = Depends(get_db)):
    risks = db.query(ESGStat).filter(ESGStat.category == risk_category, ESGStat.risk_type.isnot(None)).all()
    return {
        "category": risk_category,
        "total": len(risks),
        "items": risks
    }

@router.get("/level/critical")
def get_critical_risks(db: Session = Depends(get_db)):
    risks = db.query(ESGStat).filter(ESGStat.risk_type.isnot(None), ESGStat.value >= 70).all()
    return {
        "level": "critical",
        "total": len(risks),
        "items": risks
    }

@router.delete("/clear")
def clear_all_risks(db: Session = Depends(get_db)):
    try:
        db.query(ESGStat).filter(ESGStat.risk_type.isnot(None)).delete()
        db.commit()
        return {"status": "성공", "message": "모든 리스크 데이터가 삭제되었습니다"}
    except Exception as e:
        db.rollback()
        return {"status": "실패", "message": str(e)}