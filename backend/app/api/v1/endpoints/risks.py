from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
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


@router.get("/list")
def list_risks(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(ESGStat).filter(ESGStat.risk_type.isnot(None))
    rows = (
        _apply_year_range(query, start_date, end_date)
        .order_by(ESGStat.year.desc(), ESGStat.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return {"total": len(rows), "items": [_serialize_stat(row) for row in rows], "skip": skip, "limit": limit}


@router.get("/country/{country_code}")
def get_country_risks(
    country_code: str,
    limit: int = Query(20, ge=1, le=500),
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(ESGStat).filter(
        ESGStat.country_code == country_code,
        ESGStat.risk_type.isnot(None),
    )
    rows = (
        _apply_year_range(query, start_date, end_date)
        .order_by(ESGStat.year.desc(), ESGStat.id.desc())
        .limit(limit)
        .all()
    )
    return {"country_code": country_code, "total": len(rows), "items": [_serialize_stat(row) for row in rows]}


@router.get("/category/{risk_category}")
def get_risks_by_category(
    risk_category: str,
    limit: int = Query(100, ge=1, le=500),
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(ESGStat).filter(
        ESGStat.category == risk_category,
        ESGStat.risk_type.isnot(None),
    )
    rows = (
        _apply_year_range(query, start_date, end_date)
        .order_by(ESGStat.year.desc(), ESGStat.id.desc())
        .limit(limit)
        .all()
    )
    return {"category": risk_category, "total": len(rows), "items": [_serialize_stat(row) for row in rows]}


@router.get("/level/critical")
def get_critical_risks(
    limit: int = Query(100, ge=1, le=500),
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(ESGStat).filter(ESGStat.risk_type.isnot(None), ESGStat.value >= 70)
    rows = (
        _apply_year_range(query, start_date, end_date)
        .order_by(ESGStat.year.desc(), ESGStat.id.desc())
        .limit(limit)
        .all()
    )
    return {"level": "critical", "total": len(rows), "items": [_serialize_stat(row) for row in rows]}


@router.get("/{risk_id}")
def get_risk(risk_id: int, db: Session = Depends(get_db)):
    row = db.query(ESGStat).filter(ESGStat.id == risk_id, ESGStat.risk_type.isnot(None)).first()
    if not row:
        return {"status": "failed", "message": "risk not found"}
    return _serialize_stat(row)


@router.delete("/clear")
def clear_all_risks(db: Session = Depends(get_db)):
    try:
        db.query(ESGStat).filter(ESGStat.risk_type.isnot(None)).delete()
        db.commit()
        return {"status": "success", "message": "risk data deleted"}
    except Exception as e:
        db.rollback()
        return {"status": "failed", "message": str(e)}
