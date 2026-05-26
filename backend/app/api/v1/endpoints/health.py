from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from datetime import datetime

router = APIRouter()

@router.get("/")
def health_check(db: Session = Depends(get_db)):
    """API 헬스 체크"""
    try:
        # DB 연결 확인
        db.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    return {
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "database": db_status,
        "version": "1.0.0"
    }

@router.get("/info")
def info():
    """API 정보"""
    return {
        "name": "ESG Risk Watch API",
        "version": "1.0.0",
        "endpoints": {
            "news": "/api/v1/news",
            "briefings": "/api/v1/briefings",
            "countries": "/api/v1/countries",
            "risks": "/api/v1/risks",
            "trends": "/api/v1/trends",
            "health": "/api/v1/health"
        }
    }
