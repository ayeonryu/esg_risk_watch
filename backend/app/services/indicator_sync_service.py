import csv
import io
from io import StringIO
import zipfile

import requests
from sqlalchemy.orm import Session

from app.models.esg_stat import ESGStat

TARGET_COUNTRIES = {
    "KOR": "South Korea",
    "USA": "United States",
    "CHN": "China",
}

WORLDBANK_INDICATORS = [
    {
        "indicator_code": "EG.USE.PCAP.KG.OE",
        "category": "E",
        "risk_type": "energy_consumption_risk",
    },
    {
        "indicator_code": "SL.UEM.TOTL.ZS",
        "category": "S",
        "risk_type": "unemployment_risk",
    },
    {
        "indicator_code": "SP.DYN.LE00.IN",
        "category": "S",
        "risk_type": "life_expectancy_risk",
    },
]

FREEDOM_SCORE_URLS = [
    "https://raw.githubusercontent.com/datasets/freedom-in-the-world/main/data/freedom-house-scores.csv",
    "https://raw.githubusercontent.com/datasets/freedom-in-the-world/master/data/freedom-house-scores.csv",
]


def _upsert_stat(
    db: Session,
    *,
    category: str,
    risk_type: str,
    country: str,
    country_code: str,
    indicator: str,
    indicator_code: str,
    year: int,
    value: float,
) -> bool:
    row = (
        db.query(ESGStat)
        .filter(
            ESGStat.country_code == country_code,
            ESGStat.risk_type == risk_type,
            ESGStat.indicator_code == indicator_code,
            ESGStat.year == year,
        )
        .first()
    )

    if row:
        row.category = category
        row.country = country
        row.indicator = indicator
        row.value = value
        return False

    db.add(
        ESGStat(
            category=category,
            risk_type=risk_type,
            country=country,
            country_code=country_code,
            indicator=indicator,
            indicator_code=indicator_code,
            year=year,
            value=value,
        )
    )
    return True


def sync_target_worldbank_indicators(db: Session, years_back: int = 6) -> int:
    added = 0

    for config in WORLDBANK_INDICATORS:
        url = (
            "https://api.worldbank.org/v2/en/indicator/"
            f"{config['indicator_code']}?downloadformat=csv"
        )
        response = requests.get(url, timeout=60)
        response.raise_for_status()

        with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
            csv_name = next(
                name
                for name in archive.namelist()
                if name.startswith("API_") and name.endswith(".csv")
            )
            text = archive.read(csv_name).decode("utf-8-sig")

        lines = text.splitlines()
        header_index = next(
            index for index, line in enumerate(lines) if line.startswith('"Country Name"')
        )
        reader = csv.DictReader(lines[header_index:])

        for row in reader:
            country_code = row.get("Country Code")
            country_name = TARGET_COUNTRIES.get(country_code)
            if not country_name:
                continue

            year_values = []
            for year, value in row.items():
                if not year.isdigit() or not value:
                    continue
                year_values.append((int(year), float(value)))

            for year, value in sorted(year_values, reverse=True)[:years_back]:
                inserted = _upsert_stat(
                    db,
                    category=config["category"],
                    risk_type=config["risk_type"],
                    country=country_name,
                    country_code=country_code,
                    indicator=row.get("Indicator Name", ""),
                    indicator_code=config["indicator_code"],
                    year=year,
                    value=value,
                )
                added += 1 if inserted else 0

    db.commit()
    return added


def sync_target_freedom_scores(db: Session) -> int:
    last_error = None
    response = None

    for url in FREEDOM_SCORE_URLS:
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                break
            last_error = RuntimeError(f"{url} returned {response.status_code}")
        except requests.RequestException as exc:
            last_error = exc

    if response is None or response.status_code != 200:
        raise RuntimeError(f"Freedom House source unavailable: {last_error}")

    country_codes_by_name = {name: code for code, name in TARGET_COUNTRIES.items()}
    added = 0
    reader = csv.DictReader(StringIO(response.text))
    for row in reader:
        country = row.get("Country/Territory")
        country_code = country_codes_by_name.get(country)
        if not country_code:
            continue

        score = row.get("Total Score and Status", "").split()
        if not score:
            continue

        inserted = _upsert_stat(
            db,
            category="G",
            risk_type="freedom_governance_risk",
            country=country,
            country_code=country_code,
            indicator="Freedom House score",
            indicator_code="freedom-score-fh",
            year=int(row.get("Edition")),
            value=float(score[0]),
        )
        added += 1 if inserted else 0

    db.commit()
    return added


def sync_target_indicators(db: Session) -> dict:
    result = {"worldbank_added": 0, "freedom_added": 0, "errors": []}

    try:
        result["worldbank_added"] = sync_target_worldbank_indicators(db)
    except Exception as exc:
        db.rollback()
        result["errors"].append(f"worldbank: {exc}")

    try:
        result["freedom_added"] = sync_target_freedom_scores(db)
    except Exception as exc:
        db.rollback()
        result["errors"].append(f"freedom: {exc}")

    return result
