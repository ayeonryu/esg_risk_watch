from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.risk import Risk
from app.services import risk_service

router = APIRouter()

@router.get("/list")
def list_risks(skip: int = Query(0), limit: int = Query(100), db: Session = Depends(get_db)):
    """모든 리스크 조회"""
    risks = risk_service.get_all_risks(db, skip, limit)
    return {
        "total": len(risks),
        "items": risks,
        "skip": skip,
        "limit": limit
    }

@router.get("/{risk_id}")
def get_risk(risk_id: int, db: Session = Depends(get_db)):
    """특정 리스크 조회"""
    risk = db.query(Risk).filter(Risk.id == risk_id).first()
    if not risk:
        return {"status": "failed", "message": "리스크를 찾을 수 없습니다"}
    return risk

@router.get("/country/{country_code}")
def get_country_risks(country_code: str, db: Session = Depends(get_db)):
    """특정 국가의 리스크 조회"""
    risks = risk_service.get_risks_by_country(db, country_code)
    return {
        "country_code": country_code,
        "total": len(risks),
        "items": risks
    }

@router.get("/category/{risk_category}")
def get_risks_by_category(risk_category: str, db: Session = Depends(get_db)):
    """특정 카테고리의 리스크 조회"""
    risks = db.query(Risk).filter(Risk.risk_category == risk_category).all()
    return {
        "category": risk_category,
        "total": len(risks),
        "items": risks
    }

@router.get("/level/critical")
def get_critical_risks(db: Session = Depends(get_db)):
    """심각(critical) 리스크 조회"""
    risks = db.query(Risk).filter(Risk.risk_level == "critical").all()
    return {
        "level": "critical",
        "total": len(risks),
        "items": risks
    }

@router.delete("/clear")
def clear_all_risks(db: Session = Depends(get_db)):
    """모든 리스크 데이터 삭제"""
    try:
        risk_service.clear_all_risks(db)
        return {"status": "성공", "message": "모든 리스크 데이터가 삭제되었습니다"}
    except Exception as e:
        return {"status": "실패", "message": str(e)}
