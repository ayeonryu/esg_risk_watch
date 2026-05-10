from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.news import News
from app.models.esg_stat import ESGStat
from app import scheduler

router = APIRouter()

@router.post("/sync/all")
def sync_everything(background_tasks: BackgroundTasks):
    background_tasks.add_task(scheduler.run_all_syncs)
    return {"status": "처리 중", "message": "전체 동기화 시작"}

@router.delete("/clear")
def clear_all_data(db: Session = Depends(get_db)):
    try:
        db.query(News).delete()
        db.query(ESGStat).delete()
        db.commit()
        print("알림: 데이터베이스 초기화 완료")
        return {"status": "성공", "message": "데이터 삭제 완료"}
    except Exception as e:
        db.rollback()
        return {"status": "실패", "message": str(e)}