from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.db.session import SessionLocal
from app.models.news import News
from app.models.esg_stat import ESGStat
import requests
import csv
from io import StringIO
from datetime import datetime, date
import hashlib
import json

SERVICE_KEY = "43b016f2295f780a65665aa1587a7f80e7f3be918cfacf883a66488069cd075c"
DC_API_KEY = "3bRAYyaN6gBdO7esp4GkyRlzYETJcXXuGkiAM6fRPf77hOvs"

BIGDATA_URLS = [
    "https://api.odcloud.kr/api/15097922/v1/uddi:97ce0eff-7786-4ace-ac15-aec8d947112a",
    "https://api.odcloud.kr/api/15097922/v1/uddi:27150cfe-98f8-4608-9036-d68907d18fad",
    "https://api.odcloud.kr/api/15097922/v1/uddi:36367d6b-9588-4245-819f-b1f0ba836185",
    "https://api.odcloud.kr/api/15097922/v1/uddi:729fb13d-78df-47c1-bc75-e8ee986fbd67",
]

BIGDATA_YEAR_MIN = 2021
BIGDATA_YEAR_MAX = 2024
BIGDATA_BATCH_SIZE = 100


def _parse_bigdata_date(value):
    if value is None:
        return None
    if isinstance(value, date):
        return value

    text = str(value).strip()
    if not text:
        return None

    for candidate in (text, text[:10]):
        for fmt in ("%Y-%m-%d", "%Y.%m.%d", "%Y/%m/%d", "%Y%m%d"):
            try:
                return datetime.strptime(candidate, fmt).date()
            except ValueError:
                continue
    return None


def _is_bigdata_year_allowed(value):
    parsed_date = _parse_bigdata_date(value)
    if not parsed_date:
        return False
    return BIGDATA_YEAR_MIN <= parsed_date.year <= BIGDATA_YEAR_MAX


def _extract_bigdata_items(payload):
    if not isinstance(payload, dict):
        return []

    data = payload.get("data")
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("items", "item", "data", "rows"):
            items = data.get(key)
            if isinstance(items, list):
                return items
            if isinstance(items, dict):
                return [items]

    return []


def _build_bigdata_external_id(source_name, item):
    stable_payload = {
        "source": source_name,
        "title": item.get("제목") or item.get("title") or "",
        "content": item.get("본문") or item.get("content") or "",
        "media": item.get("언론사") or item.get("media") or "",
        "date": item.get("일자") or item.get("date") or "",
        "raw_id": item.get("뉴스식별자") or item.get("id") or item.get("ID") or item.get("news_id") or "",
    }
    digest = hashlib.sha256(
        json.dumps(stable_payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    return f"{source_name}:{digest}"

def fetch_all_news(url: str, category: str, db, start_page: int = 1):
    try:
        # API 호출 및 JSON 변환
        res = requests.get(url, params={"serviceKey": SERVICE_KEY, "type": "json", "numOfRows": 1, "pageNo": start_page})
        data = res.json()
        
        # API 응답 형식 확인 (KeyError 방지)
        if "response" not in data or "body" not in data["response"]:
            print(f"[Error] {category} API 응답 형식이 올바르지 않습니다: {data}")
            return 0

        total = int(data["response"]["body"].get("totalCnt", 0))
        added = 0
        page = start_page
        
        while True:
            res = requests.get(url, params={"serviceKey": SERVICE_KEY, "type": "json", "numOfRows": 10, "pageNo": page})
            data = res.json()
            
            try:
                items = data["response"]["body"]["itemList"]["item"]
            except (KeyError, TypeError):
                break
                
            if not items:
                break
                
            if isinstance(items, dict):
                items = [items]
                
            for item in items:
                # 중복 방지를 위한 고유 ID (nttSn 또는 제목 사용)
                ext_id = str(item.get("nttSn") or item.get("nttSj"))
                
                # 이미 DB에 있는지 확인
                if db.query(News).filter(News.external_id == ext_id).first():
                    continue
                    
                db.add(News(
                    external_id=ext_id, 
                    category=category,
                    title=item.get("nttSj") or "No Title",
                    content=item.get("smmarCn") or "",
                    media=item.get("kbc") or "KOTRA",
                    published_at=item.get("regDt")
                ))
                added += 1
                
            db.commit()
            page += 1
            
            # 페이지 초과 방지
            if page > (total // 10) + 2:
                break
                
        print(f"[{category}] 동기화 완료: {added}건 신규 저장")
        return added
        
    except Exception as e:
        print(f"[Error] {category} 수집 중 예외 발생: {str(e)}")
        return 0

def sync_esg_news():
    db = SessionLocal()
    try:
        fetch_all_news("https://apis.data.go.kr/B410001/trend-news/getTrend-news", "ESG", db)
    finally:
        db.close()

def sync_china_issues():
    db = SessionLocal()
    try:
        fetch_all_news("https://apis.data.go.kr/B410001/chinaGlobalIssueMonitoring/getChinaGlobalIssueMonitoring", "CHINA", db)
    finally:
        db.close()

def sync_usa_issues():
    db = SessionLocal()
    try:
        fetch_all_news("https://apis.data.go.kr/B410001/usaGlobalIssueMonitoring/getUsaGlobalIssueMonitoring", "USA", db, start_page=2)
    finally:
        db.close()

def sync_bigdata_esg():
    db = SessionLocal()
    try:
        for idx, url in enumerate(BIGDATA_URLS, start=1):
            try:
                source_name = f"NEWS_BIGDATA_ESG_{idx}"
                existing_ids = {
                    row[0]
                    for row in db.query(News.external_id)
                    .filter(News.external_id.like(f"{source_name}:%"))
                    .all()
                }
                page = 1
                added = 0
                while True:
                    print(f"[BIGDATA] 수집 중: {url} page={page}")
                    res = requests.get(
                        url,
                        params={
                            "serviceKey": SERVICE_KEY,
                            "page": page,
                            "perPage": BIGDATA_BATCH_SIZE,
                            "returnType": "JSON",
                        },
                        timeout=30,
                    )
                    data = res.json()
                    items = _extract_bigdata_items(data)
                    if not items:
                        print(f"[BIGDATA] 데이터 없음: {url} page={page}")
                        break

                    new_rows = []
                    page_has_allowed_year = False
                    page_max_year = 0

                    for item in items:
                        if not isinstance(item, dict):
                            continue

                        published_at = _parse_bigdata_date(item.get("일자"))
                        if published_at:
                            page_has_allowed_year = True
                            page_max_year = max(page_max_year, published_at.year)

                        if not _is_bigdata_year_allowed(published_at):
                            continue
                        ext_id = _build_bigdata_external_id(source_name, item)
                        if ext_id in existing_ids:
                            continue
                        existing_ids.add(ext_id)
                        new_rows.append(News(
                            external_id=ext_id,
                            category=source_name,
                            title=item.get("제목") or "No Title",
                            content=item.get("본문") or "",
                            media=item.get("언론사") or "ODcloud",
                            published_at=published_at,
                        ))
                        added += 1

                    if new_rows:
                        db.bulk_save_objects(new_rows)
                        db.commit()

                    total = data.get("totalCount", 0)
                    if total and page * BIGDATA_BATCH_SIZE >= total:
                        break

                    if page_has_allowed_year and page_max_year < BIGDATA_YEAR_MIN:
                        break

                    page += 1

                print(f"[BIGDATA] 저장 완료: {url} ({added}건)")
            except Exception as e:
                db.rollback()
                print(f"[BIGDATA] 수집 실패: {url} / {e}")
    finally:
        db.close()

def sync_greenhouse_gas():
    db = SessionLocal()
    try:
        countries = {
            "country/KOR": "Korea", "country/USA": "United States",
            "country/CHN": "China", "country/DEU": "Germany"
        }
        url = "https://api.datacommons.org/v2/observation"
        for country_code, country_name in countries.items():
            payload = {
                "date": "",
                "variable": {"dcids": ["Annual_Emissions_GreenhouseGas"]},
                "entity": {"dcids": [country_code]},
                "select": ["variable", "entity", "date", "value"]
            }
            response = requests.post(url, params={"key": DC_API_KEY}, json=payload)
            data = response.json()
            facets = (data.get("byVariable", {})
                      .get("Annual_Emissions_GreenhouseGas", {})
                      .get("byEntity", {})
                      .get(country_code, {})
                      .get("orderedFacets", []))
            for facet in facets:
                for obs in facet.get("observations", []):
                    db.add(ESGStat(
                        category="E", risk_type="greenhouse_gas_emissions",
                        country=country_name, country_code=country_code,
                        indicator="Annual Greenhouse Gas Emissions",
                        indicator_code="Annual_Emissions_GreenhouseGas",
                        year=int(obs["date"][:4]) if obs.get("date") else 0,
                        value=float(obs["value"]) if obs.get("value") else 0.0
                    ))
        db.commit()
    finally:
        db.close()

def sync_worldbank(indicator: str, category: str, risk_type: str,
                   countries_str: str = "KOR,USA,CHN,DEU", start: int = 2020, end: int = 2025):
    db = SessionLocal()
    try:
        for country in countries_str.split(","):
            url = f"https://api.worldbank.org/v2/country/{country}/indicator/{indicator}"
            res = requests.get(url, params={"format": "json", "date": f"{start}:{end}", "per_page": 100})
            data = res.json()
            if len(data) > 1 and data[1]:
                for item in data[1]:
                    db.add(ESGStat(
                        category=category, risk_type=risk_type,
                        country=item["country"]["value"],
                        country_code=item["countryiso3code"],
                        indicator=item["indicator"]["value"],
                        indicator_code=indicator,
                        year=int(item["date"]) if item["date"] else 0,
                        value=float(item["value"]) if item["value"] is not None else 0.0
                    ))
        db.commit()
    finally:
        db.close()

def sync_freedom_score():
    db = SessionLocal()
    try:
        countries = {
            "South Korea": "Korea", "United States": "United States",
            "China": "China", "Germany": "Germany"
        }
        url = "https://ourworldindata.org/grapher/freedom-score-fh.csv"
        response = requests.get(url)
        reader = csv.DictReader(StringIO(response.text))
        value_column = [c for c in reader.fieldnames if c not in ["Entity", "Code", "Year"]][0]
        for row in reader:
            entity = row.get("Entity")
            year = row.get("Year")
            value = row.get(value_column)
            if entity in countries and year and int(year) >= 2020:
                db.add(ESGStat(
                    category="G", risk_type="freedom_governance_risk",
                    country=countries[entity], country_code=row.get("Code"),
                    indicator="Freedom House score",
                    indicator_code="freedom-score-fh",
                    year=int(year),
                    value=float(value) if value not in [None, ""] else 0.0
                ))
        db.commit()
    finally:
        db.close()

def run_all_syncs():
    print("[Scheduler] 전체 동기화 시작...")
    steps = [
        ("ESG news", sync_esg_news),
        ("China issues", sync_china_issues),
        ("USA issues", sync_usa_issues),
        ("Bigdata ESG", sync_bigdata_esg),
        ("Greenhouse gas", sync_greenhouse_gas),
        ("Energy use", lambda: sync_worldbank("EG.USE.PCAP.KG.OE", "E", "energy_consumption_risk")),
        ("Unemployment", lambda: sync_worldbank("SL.UEM.TOTL.ZS", "S", "unemployment_risk")),
        ("Life expectancy", lambda: sync_worldbank("SP.DYN.LE00.IN", "S", "life_expectancy_risk")),
        ("Freedom score", sync_freedom_score),
    ]

    for name, step in steps:
        try:
            print(f"[Scheduler] 시작: {name}")
            step()
            print(f"[Scheduler] 완료: {name}")
        except Exception as e:
            print(f"[Scheduler] 실패: {name} / {e}")
    print("[Scheduler] 전체 동기화 완료!")

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        run_all_syncs,
        trigger=IntervalTrigger(hours=1),
        id="sync_all_apis",
        replace_existing=True
    )
    scheduler.start()
    print("[Scheduler] 스케줄러 시작됨 (1시간 간격)")
    return scheduler
