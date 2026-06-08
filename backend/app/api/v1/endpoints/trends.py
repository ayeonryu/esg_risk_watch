from fastapi import APIRouter, Depends, Query, BackgroundTasks
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.trend import Trend
from app.services import trend_service

router = APIRouter()

@router.post("/sync/all")
def sync_all_trends(background_tasks: BackgroundTasks):
    background_tasks.add_task(lambda: None)
    return {"status": "처리 중", "message": "트렌드 동기화 시작"}

@router.get("/list")
def list_trends(skip: int = Query(0), limit: int = Query(100), db: Session = Depends(get_db)):
    trends = trend_service.get_all_trends(db, skip, limit)
    return {
        "total": len(trends),
        "items": trends,
        "skip": skip,
        "limit": limit
    }

@router.get("/country/{country_code}")
def get_trends_by_country(country_code: str, db: Session = Depends(get_db)):
    trends = db.query(Trend).filter(Trend.country_code == country_code).all()
    return {
        "country_code": country_code,
        "total": len(trends),
        "items": trends
    }

@router.get("/category/{category}")
def get_trends_by_category(category: str, db: Session = Depends(get_db)):
    trends = trend_service.get_trends_by_category(db, category)
    return {
        "category": category,
        "total": len(trends),
        "items": trends
    }

@router.get("/esg/{esg_category}")
def get_trends_by_esg(esg_category: str, db: Session = Depends(get_db)):
    if esg_category not in ["E", "S", "G"]:
        return {"status": "failed", "message": "E, S, G 중 하나를 선택하세요"}
    
    trends = db.query(Trend).filter(Trend.esg_category == esg_category).all()
    return {
        "esg_category": esg_category,
        "total": len(trends),
        "items": trends
    }

@router.get("/emerging")
def get_emerging_trends(db: Session = Depends(get_db)):
    trends = db.query(Trend).filter(Trend.trend_type == "emerging").all()
    return {
        "trend_type": "emerging",
        "total": len(trends),
        "items": trends
    }

@router.delete("/clear")
def clear_all_trends(db: Session = Depends(get_db)):
    try:
        trend_service.clear_all_trends(db)
        return {"status": "성공", "message": "모든 트렌드 데이터가 삭제되었습니다"}
    except Exception as e:
        return {"status": "실패", "message": str(e)}