from fastapi import APIRouter, Depends, BackgroundTasks, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.briefing import Briefing
from app.services import briefing_service
from app.schemas.briefing import BriefingResponse

router = APIRouter()

@router.post("/sync/all")
def sync_all_briefings(background_tasks: BackgroundTasks):
    """모든 보고서 동기화 시작 (백그라운드)"""
    background_tasks.add_task(lambda: None)  # TODO: 실제 동기화 로직 연결
    return {"status": "처리 중", "message": "보고서 동기화 시작"}

@router.get("/list")
def list_briefings(skip: int = Query(0), limit: int = Query(100), db: Session = Depends(get_db)):
    """모든 보고서 조회"""
    briefings = briefing_service.get_all_briefings(db, skip, limit)
    return {
        "total": len(briefings),
        "items": briefings,
        "skip": skip,
        "limit": limit
    }

@router.get("/{briefing_id}")
def get_briefing(briefing_id: int, db: Session = Depends(get_db)):
    """특정 보고서 조회"""
    briefing = db.query(Briefing).filter(Briefing.id == briefing_id).first()
    if not briefing:
        return {"status": "failed", "message": "보고서를 찾을 수 없습니다"}
    return briefing

@router.delete("/clear")
def clear_all_briefings(db: Session = Depends(get_db)):
    """모든 보고서 삭제"""
    try:
        briefing_service.clear_all_briefings(db)
        return {"status": "성공", "message": "모든 보고서가 삭제되었습니다"}
    except Exception as e:
        return {"status": "실패", "message": str(e)}
