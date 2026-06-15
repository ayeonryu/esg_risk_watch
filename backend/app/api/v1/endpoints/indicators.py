from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.esg_stat import ESGStat
from app import scheduler

router = APIRouter()

@router.post("/sync/freedom")
def sync_freedom_indicator():
    synced_rows = scheduler.sync_freedom_score()
    return {"status": "success", "synced_rows": synced_rows}


@router.post("/sync/all")
def sync_all_indicators():
    return scheduler.run_indicator_syncs()


@router.get("/sync/status")
def indicator_sync_status():
    return scheduler.get_indicator_sync_status()

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


def _clamp_score(value: float) -> float:
    return round(max(0, min(100, value)), 1)


def _indicator_score(risk_type: str, latest, previous, higher_is_risk: bool) -> tuple[float, float | None]:
    if risk_type == "freedom_governance_risk":
        score = _clamp_score(latest.value)
        previous_score = _clamp_score(previous.value) if previous else None
        return score, previous_score

    if not previous or previous.value in (None, 0):
        return 70.0, None

    change = latest.value - previous.value
    change_pct = (change / abs(previous.value)) * 100
    risk_delta = change_pct if higher_is_risk else -change_pct
    score = _clamp_score(85 - (risk_delta * 5))
    previous_score = 85.0
    return score, previous_score


def _date_range_years(
    start_date: date | None,
    end_date: date | None,
) -> tuple[int | None, int | None]:
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="start_date must be on or before end_date",
        )
    return (
        start_date.year if start_date else None,
        end_date.year if end_date else None,
    )


def _indicator_query(
    country: str,
    db: Session,
    start_year: int | None = None,
    end_year: int | None = None,
):
    query = (
        db.query(ESGStat)
        .filter(ESGStat.country_code == country)
        .filter(ESGStat.risk_type.in_(INDICATOR_META.keys()))
        .filter(ESGStat.value.isnot(None))
    )
    if start_year is not None:
        query = query.filter(ESGStat.year >= start_year)
    if end_year is not None:
        query = query.filter(ESGStat.year <= end_year)
    return query


def _latest_rows_by_type(
    country: str,
    db: Session,
    start_year: int | None = None,
    end_year: int | None = None,
):
    rows = (
        _indicator_query(country, db, start_year, end_year)
        .order_by(ESGStat.risk_type.asc(), ESGStat.year.desc(), ESGStat.id.desc())
        .all()
    )

    rows_by_type = {}
    seen_years_by_type = {}
    for row in rows:
        if row.risk_type == "energy_consumption_risk" and row.value == 0:
            continue

        seen_years = seen_years_by_type.setdefault(row.risk_type, set())
        if row.year in seen_years:
            continue

        seen_years.add(row.year)
        rows_by_type.setdefault(row.risk_type, []).append(row)
    return rows_by_type


def _rows_by_type_and_year(
    country: str,
    db: Session,
    start_year: int | None = None,
    end_year: int | None = None,
):
    rows = (
        _indicator_query(country, db, start_year, end_year)
        .order_by(ESGStat.risk_type.asc(), ESGStat.year.desc(), ESGStat.id.desc())
        .all()
    )

    rows_by_type = {}
    seen_years_by_type = {}
    for row in rows:
        if row.risk_type == "energy_consumption_risk" and row.value == 0:
            continue

        seen_years = seen_years_by_type.setdefault(row.risk_type, set())
        if row.year in seen_years:
            continue

        seen_years.add(row.year)
        rows_by_type.setdefault(row.risk_type, {})[row.year] = row
    return rows_by_type


def _previous_year_row(rows_by_year: dict, year: int):
    previous_years = [candidate for candidate in rows_by_year if candidate < year]
    if not previous_years:
        return None
    return rows_by_year[max(previous_years)]


def _category_scores_for_year(rows_by_type: dict, year: int):
    category_scores = {"E": [], "S": [], "G": []}

    for risk_type, meta in INDICATOR_META.items():
        rows_by_year = rows_by_type.get(risk_type, {})
        current = rows_by_year.get(year)
        if not current:
            continue

        previous = _previous_year_row(rows_by_year, year)
        score, _ = _indicator_score(
            risk_type,
            current,
            previous,
            meta["higher_is_risk"],
        )
        category_scores[meta["category"]].append(score)

    return {
        category: _clamp_score(sum(values) / len(values))
        for category, values in category_scores.items()
        if values
    }


def _complete_score_years(
    rows_by_type: dict,
    start_year: int | None = None,
    end_year: int | None = None,
):
    years = sorted(
        {
            year
            for rows_by_year in rows_by_type.values()
            for year in rows_by_year
            if (start_year is None or year >= start_year)
            and (end_year is None or year <= end_year)
        }
    )
    return [
        year
        for year in years
        if all(category in _category_scores_for_year(rows_by_type, year) for category in ("E", "S", "G"))
    ]


@router.get("/scores")
def indicator_scores(
    country: str = Query(..., min_length=2),
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
):
    start_year, end_year = _date_range_years(start_date, end_date)
    has_date_filter = start_date is not None or end_date is not None
    target_year = None
    previous_year = None

    if has_date_filter:
        rows_by_type = _rows_by_type_and_year(country, db)
        available_years = _complete_score_years(rows_by_type, end_year=end_year)

        target_year = available_years[-1] if available_years else None
        previous_year = target_year - 1 if target_year is not None else None

        scores = (
            _category_scores_for_year(rows_by_type, target_year)
            if target_year is not None
            else {}
        )
        previous_scores = (
            _category_scores_for_year(rows_by_type, previous_year)
            if previous_year is not None
            else {}
        )
    else:
        rows_by_type = _latest_rows_by_type(country, db)
        category_scores = {"E": [], "S": [], "G": []}
        previous_category_scores = {"E": [], "S": [], "G": []}

        for risk_type, meta in INDICATOR_META.items():
            stats = rows_by_type.get(risk_type, [])
            if not stats:
                continue

            latest = stats[0]
            previous = stats[1] if len(stats) > 1 else None
            score, previous_score = _indicator_score(
                risk_type,
                latest,
                previous,
                meta["higher_is_risk"],
            )
            category = meta["category"]
            category_scores[category].append(score)
            if previous_score is not None:
                previous_category_scores[category].append(previous_score)

        scores = {
            category: _clamp_score(sum(values) / len(values))
            for category, values in category_scores.items()
            if values
        }
        previous_scores = {
            category: _clamp_score(sum(values) / len(values))
            for category, values in previous_category_scores.items()
            if values
        }
    score_changes = {
        category: round(scores[category] - previous_scores[category], 1)
        for category in scores
        if category in previous_scores
    }

    overall = (
        _clamp_score(sum(scores.values()) / len(scores))
        if scores
        else None
    )
    previous_overall = (
        _clamp_score(sum(previous_scores.values()) / len(previous_scores))
        if previous_scores
        else None
    )
    overall_change = (
        round(overall - previous_overall, 1)
        if overall is not None and previous_overall is not None
        else None
    )

    return {
        "country": country,
        "year": target_year,
        "previous_year": previous_year,
        "total": len(scores),
        "scores": scores,
        "previous_scores": previous_scores,
        "score_changes": score_changes,
        "overall": overall,
        "previous_overall": previous_overall,
        "overall_change": overall_change,
    }


@router.get("/score-trend")
def score_trend(
    country: str = Query(..., min_length=2),
    limit: int = Query(6, ge=2, le=20),
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
):
    _, end_year = _date_range_years(start_date, end_date)
    rows_by_type = _rows_by_type_and_year(country, db)
    years = _complete_score_years(rows_by_type, end_year=end_year)

    target_year = years[-1] if years else None
    items = []
    for year in years:
        scores = _category_scores_for_year(rows_by_type, year)
        if not all(category in scores for category in ("E", "S", "G")):
            continue

        overall = _clamp_score(sum(scores.values()) / len(scores))
        items.append({
            "year": year,
            "overall": overall,
            "scores": scores,
        })

    limited_items = items[-limit:]
    return {
        "country": country,
        "year": target_year,
        "total": len(limited_items),
        "items": limited_items,
    }


@router.get("/summary")
def indicator_summary(
    country: str = Query(..., min_length=2),
    limit: int = Query(4, ge=1, le=10),
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
):
    start_year, end_year = _date_range_years(start_date, end_date)
    rows_by_type = _latest_rows_by_type(country, db, start_year, end_year)

    items = []
    for risk_type, meta in INDICATOR_META.items():
        stats = rows_by_type.get(risk_type, [])
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
