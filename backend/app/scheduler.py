from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.db.session import SessionLocal
from app.models.news import News
from app.models.esg_stat import ESGStat
import requests
import csv
from io import StringIO

SERVICE_KEY = "43b016f2295f780a65665aa1587a7f80e7f3be918cfacf883a66488069cd075c"
DC_API_KEY = "3bRAYyaN6gBdO7esp4GkyRlzYETJcXXuGkiAM6fRPf77hOvs"

BIGDATA_URLS = [
    "https://api.odcloud.kr/api/15097922/v1/uddi:97ce0eff-7786-4ace-ac15-aec8d947112a",
    "https://api.odcloud.kr/api/15097922/v1/uddi:27150cfe-98f8-4608-9036-d68907d18fad",
    "https://api.odcloud.kr/api/15097922/v1/uddi:36367d6b-9588-4245-819f-b1f0ba836185",
    "https://api.odcloud.kr/api/15097922/v1/uddi:729fb13d-78df-47c1-bc75-e8ee986fbd67",
]

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
        for url in BIGDATA_URLS:
            page = 1
            while True:
                res = requests.get(url, params={"serviceKey": SERVICE_KEY, "page": page, "perPage": 10, "returnType": "JSON"})
                data = res.json()
                items = data.get("data", [])
                if not items:
                    break
                for item in items:
                    db.add(News(
                        title=item.get("제목"),
                        content=item.get("본문"),
                        published_at=item.get("일자")
                    ))
                db.commit()
                total = data.get("totalCount", 0)
                if page * 10 >= total:
                    break
                page += 1
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
    sync_esg_news()
    sync_china_issues()
    sync_usa_issues()
    sync_bigdata_esg()
    sync_greenhouse_gas()
    sync_worldbank("EG.USE.PCAP.KG.OE", "E", "energy_consumption_risk")
    sync_worldbank("SL.UEM.TOTL.ZS", "S", "unemployment_risk")
    sync_worldbank("SP.DYN.LE00.IN", "S", "life_expectancy_risk")
    sync_freedom_score()
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