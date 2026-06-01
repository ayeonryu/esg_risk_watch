from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import SessionLocal, get_db
from app.models.esg_stat import ESGStat
from app.services.indicator_sync_service import sync_target_indicators

router = APIRouter()

INDICATOR_META = {
    "energy_consumption_risk": {
        "label": "에너지 소비",
        "unit": "kg oil equivalent",
        "category": "E",
        "higher_is_risk": True,
    },
    "unemployment_risk": {
        "label": "실업률",
        "unit": "%",
        "category": "S",
        "higher_is_risk": True,
    },
    "life_expectancy_risk": {
        "label": "기대수명",
        "unit": "years",
        "category": "S",
        "higher_is_risk": False,
    },
    "freedom_governance_risk": {
        "label": "자유지수",
        "unit": "score",
        "category": "G",
        "higher_is_risk": False,
    },
}


def _risk_level(change_pct: float | None, higher_is_risk: bool) -> str:
    if change_pct is None:
        return "low"

    risk_delta = change_pct if higher_is_risk else -change_pct
    if risk_delta >= 5:
        return "high"
    if risk_delta >= 1:
        return "medium"
    return "low"


@router.get("/summary")
def indicator_summary(
    country: str = Query(..., min_length=2),
    limit: int = Query(4, ge=1, le=10),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(ESGStat)
        .filter(ESGStat.country_code == country)
        .filter(ESGStat.risk_type.in_(INDICATOR_META.keys()))
        .filter(ESGStat.value.isnot(None))
        .order_by(ESGStat.risk_type.asc(), ESGStat.year.desc())
        .all()
    )

    by_type = {}
    for row in rows:
        by_type.setdefault(row.risk_type, []).append(row)

    items = []
    for risk_type, meta in INDICATOR_META.items():
        stats = by_type.get(risk_type, [])
        if not stats:
            continue

        latest = stats[0]
        previous = stats[1] if len(stats) > 1 else None
        change = latest.value - previous.value if previous else None
        change_pct = (
            (change / abs(previous.value)) * 100
            if previous and previous.value not in (None, 0)
            else None
        )

        direction = "flat"
        if change is not None and change > 0:
            direction = "up"
        elif change is not None and change < 0:
            direction = "down"

        items.append(
            {
                "risk_type": risk_type,
                "label": meta["label"],
                "category": meta["category"],
                "value": latest.value,
                "unit": meta["unit"],
                "year": latest.year,
                "previous_value": previous.value if previous else None,
                "previous_year": previous.year if previous else None,
                "change": change,
                "change_pct": change_pct,
                "direction": direction,
                "risk_level": _risk_level(change_pct, meta["higher_is_risk"]),
            }
        )

    limited_items = items[:limit]
    return {
        "country": country,
        "total": len(limited_items),
        "items": limited_items,
    }


@router.post("/sync/target")
def sync_target_indicator_data(
    background_tasks: BackgroundTasks,
):
    def run_sync():
        db = SessionLocal()
        try:
            sync_target_indicators(db)
        finally:
            db.close()

    background_tasks.add_task(run_sync)
    return {
        "status": "processing",
        "message": "KOR/USA/CHN indicator sync started",
    }
