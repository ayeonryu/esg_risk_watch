from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.country import Country
from app.services import country_service
from app.schemas.country import CountryResponse

router = APIRouter()

@router.get("/list")
def list_countries(skip: int = Query(0), limit: int = Query(100), db: Session = Depends(get_db)):
    """모든 국가 조회"""
    countries = country_service.get_all_countries(db, skip, limit)
    return {
        "total": len(countries),
        "items": countries,
        "skip": skip,
        "limit": limit
    }

@router.get("/{country_code}")
def get_country(country_code: str, db: Session = Depends(get_db)):
    """특정 국가 조회"""
    country = country_service.get_country_by_code(db, country_code)
    if not country:
        return {"status": "failed", "message": "국가를 찾을 수 없습니다"}
    return country

@router.get("/esg/ranking")
def get_esg_ranking(skip: int = Query(0), limit: int = Query(20), db: Session = Depends(get_db)):
    """ESG 점수 높은 순으로 국가 순위 조회"""
    countries = db.query(Country).order_by(Country.esg_score.desc()).offset(skip).limit(limit).all()
    return {
        "total": len(countries),
        "items": countries,
        "skip": skip,
        "limit": limit
    }

@router.get("/risk/high-risk")
def get_high_risk_countries(db: Session = Depends(get_db)):
    """리스크 높은 국가 목록"""
    countries = db.query(Country).filter(Country.risk_level.in_(["high", "critical"])).all()
    return {
        "total": len(countries),
        "items": countries
    }

@router.delete("/clear")
def clear_all_countries(db: Session = Depends(get_db)):
    """모든 국가 데이터 삭제"""
    try:
        country_service.clear_all_countries(db)
        return {"status": "성공", "message": "모든 국가 데이터가 삭제되었습니다"}
    except Exception as e:
        return {"status": "실패", "message": str(e)}
