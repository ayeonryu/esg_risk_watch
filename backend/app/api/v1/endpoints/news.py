from fastapi import APIRouter, Depends, BackgroundTasks, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.news import News
from app.models.esg_stat import ESGStat
from app import scheduler

router = APIRouter()

def _serialize_news(row: News):
    return {
        "id": row.id,
        "external_id": row.external_id,
        "category": row.category,
        "title": row.title,
        "content": row.content,
        "keywords": row.keywords,
        "media": row.media,
        "country": row.country,
        "region": row.region,
        "published_at": row.published_at.isoformat() if row.published_at else None,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "esg_score": row.esg_score,
    }


@router.get("/")
def list_news(
    country: str | None = Query(None),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(News)
    if country:
        query = query.filter(News.country == country)

    rows = (
        query.order_by(News.published_at.desc(), News.created_at.desc(), News.id.desc())
        .limit(min(limit * 20, 500))
        .all()
    )

    unique_rows = []
    seen = set()
    for row in rows:
        key = row.external_id or f"{row.title}|{row.published_at}|{row.media}"
        if key in seen:
            continue
        seen.add(key)
        unique_rows.append(row)
        if len(unique_rows) >= limit:
            break

    return [_serialize_news(row) for row in unique_rows]


@router.post("/sync/all")
def sync_everything(background_tasks: BackgroundTasks):
    background_tasks.add_task(scheduler.run_all_syncs)
    return {"status": "처리 중", "message": "전체 동기화 시작"}

@router.post("/sync/countries")
def sync_news_countries():
    updated = scheduler.backfill_news_countries()
    return {"status": "success", "updated": updated}

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
