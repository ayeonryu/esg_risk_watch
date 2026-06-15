from datetime import date

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.esg_stat import ESGStat

router = APIRouter()


def _apply_year_range(query, start_date: date | None, end_date: date | None):
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="start_date must be on or before end_date",
        )
    if start_date:
        query = query.filter(ESGStat.year >= start_date.year)
    if end_date:
        query = query.filter(ESGStat.year <= end_date.year)
    return query


def _serialize_stat(row: ESGStat):
    return {
        "id": row.id,
        "category": row.category,
        "risk_type": row.risk_type,
        "country": row.country,
        "country_code": row.country_code,
        "indicator": row.indicator,
        "indicator_code": row.indicator_code,
        "year": row.year,
        "value": row.value,
    }


@router.post("/sync/all")
def sync_all_trends(background_tasks: BackgroundTasks):
    background_tasks.add_task(lambda: None)
    return {"status": "processing", "message": "trend sync started"}


@router.get("/list")
def list_trends(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
):
    rows = (
        _apply_year_range(db.query(ESGStat), start_date, end_date)
        .order_by(ESGStat.year.desc(), ESGStat.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return {"total": len(rows), "items": [_serialize_stat(row) for row in rows], "skip": skip, "limit": limit}


@router.get("/country/{country_code}")
def get_trends_by_country(
    country_code: str,
    limit: int = Query(20, ge=1, le=500),
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(ESGStat).filter(ESGStat.country_code == country_code)
    rows = (
        _apply_year_range(query, start_date, end_date)
        .order_by(ESGStat.year.desc(), ESGStat.id.desc())
        .limit(limit)
        .all()
    )
    return {"country_code": country_code, "total": len(rows), "items": [_serialize_stat(row) for row in rows]}


@router.get("/category/{category}")
def get_trends_by_category(
    category: str,
    limit: int = Query(100, ge=1, le=500),
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(ESGStat).filter(ESGStat.category == category)
    rows = (
        _apply_year_range(query, start_date, end_date)
        .order_by(ESGStat.year.desc(), ESGStat.id.desc())
        .limit(limit)
        .all()
    )
    return {"category": category, "total": len(rows), "items": [_serialize_stat(row) for row in rows]}


@router.get("/esg/{esg_category}")
def get_trends_by_esg(
    esg_category: str,
    limit: int = Query(100, ge=1, le=500),
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
):
    if esg_category not in ["E", "S", "G"]:
        return {"status": "failed", "message": "choose one of E, S, G"}
    query = db.query(ESGStat).filter(ESGStat.category == esg_category)
    rows = (
        _apply_year_range(query, start_date, end_date)
        .order_by(ESGStat.year.desc(), ESGStat.id.desc())
        .limit(limit)
        .all()
    )
    return {"esg_category": esg_category, "total": len(rows), "items": [_serialize_stat(row) for row in rows]}


@router.get("/emerging")
def get_emerging_trends(
    limit: int = Query(100, ge=1, le=500),
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(ESGStat)
    if not start_date and not end_date:
        query = query.filter(ESGStat.year == 2026)
    rows = (
        _apply_year_range(query, start_date, end_date)
        .order_by(ESGStat.year.desc(), ESGStat.id.desc())
        .limit(limit)
        .all()
    )
    return {"trend_type": "emerging", "total": len(rows), "items": [_serialize_stat(row) for row in rows]}


@router.delete("/clear")
def clear_all_trends(db: Session = Depends(get_db)):
    try:
        db.query(ESGStat).delete()
        db.commit()
        return {"status": "success", "message": "trend data deleted"}
    except Exception as e:
        db.rollback()
        return {"status": "failed", "message": str(e)}
