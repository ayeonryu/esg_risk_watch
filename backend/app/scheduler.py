import requests
import math
import hashlib
import json
import csv
from io import StringIO
from datetime import datetime, date
from app.db.session import SessionLocal
from app.models.news import News
from app.models.esg_stat import ESGStat
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.dialects.mysql import insert as mysql_insert

SERVICE_KEY = "43b016f2295f780a65665aa1587a7f80e7f3be918cfacf883a66488069cd075c"
current_year = datetime.now().year

BIGDATA_CONFIGS = [
    {"url": "https://api.odcloud.kr/api/15097922/v1/uddi:97ce0eff-7786-4ace-ac15-aec8d947112a", "year_min": 2020, "year_max": current_year, "name": "NEWS_BIGDATA_ESG_1"},
    {"url": "https://api.odcloud.kr/api/15097922/v1/uddi:27150cfe-98f8-4608-9036-d68907d18fad", "year_min": 2020, "year_max": current_year, "name": "NEWS_BIGDATA_ESG_2"},
    {"url": "https://api.odcloud.kr/api/15097922/v1/uddi:36367d6b-9588-4245-819f-b1f0ba836185", "year_min": 2020, "year_max": current_year, "name": "NEWS_BIGDATA_ESG_3"},
    {"url": "https://api.odcloud.kr/api/15097922/v1/uddi:729fb13d-78df-47c1-bc75-e8ee986fbd67", "year_min": 2020, "year_max": current_year, "name": "NEWS_BIGDATA_ESG_4"},
]

def _parse_bigdata_date(value):
    if value is None: return None
    if isinstance(value, date): return value
    text = str(value).strip()
    if not text: return None
    for candidate in (text, text[:10]):
        for fmt in ("%Y-%m-%d", "%Y.%m.%d", "%Y/%m/%d", "%Y%m%d"):
            try: return datetime.strptime(candidate, fmt).date()
            except ValueError: continue
    return None

def fetch_all_news(url, category, db):
    import time
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        res = requests.get(url, params={"serviceKey": SERVICE_KEY, "type": "json", "numOfRows": 1, "pageNo": 1}, headers=headers, timeout=5)
        data = res.json()
        total = int(data.get("response", {}).get("body", {}).get("totalCnt", 0))
        if total == 0: return 0
        added, page, max_page = 0, 1, math.ceil(total / 10)
        while page <= max_page:
            try:
                print(f"[{category}] 현재 {page} / {max_page} 페이지 수집 중...", flush=True)
                time.sleep(0.3)
                res = requests.get(url, params={"serviceKey": SERVICE_KEY, "type": "json", "numOfRows": 10, "pageNo": page}, headers=headers, timeout=5)
                
                if res.status_code != 200:
                    page += 1
                    continue
                    
                json_data = res.json()
                response_obj = json_data.get("response") or {}
                body_obj = response_obj.get("body") or {}
                item_list_obj = body_obj.get("itemList") or {}
                
                if isinstance(item_list_obj, dict):
                    items = item_list_obj.get("item", [])
                else:
                    items = []
                    
                if not items:
                    page += 1
                    continue
                    
                if isinstance(items, dict): 
                    items = [items]
                    
                for item in items:
                    if not isinstance(item, dict): 
                        continue
                    ext_id = str(item.get("nttSn") or item.get("nttSj") or "")
                    if not ext_id: 
                        continue
                    if db.query(News).filter(News.external_id == ext_id).first(): 
                        continue
                    db.add(News(
                        external_id=ext_id, category=category,
                        title=item.get("nttSj") or "No Title", content=item.get("smmarCn") or "",
                        media=item.get("kbc") or "KOTRA", published_at=item.get("regDt")
                    ))
                    added += 1
                db.commit()
                page += 1
            except Exception as e:
                print(f"-> {page}페이지 오류 발생(무시): {e}", flush=True)
                page += 1
        return added
    except Exception as e:
        print(f"[오류] {category} API 에러: {e}", flush=True)
        return 0

def sync_bigdata_esg():
    db = SessionLocal()
    total_added = 0
    try:
        for config in BIGDATA_CONFIGS:
            source_name, page, added = config["name"], 1, 0
            while True:
                print(f"[{source_name}] 현재 {page} 페이지 분석 중...")
                res = requests.get(config["url"], params={"serviceKey": SERVICE_KEY, "page": page, "perPage": 100, "returnType": "JSON"}, timeout=30)
                data = res.json()
                items = data.get("data", [])
                if not items:
                    break

                new_rows = []
                for item in items:
                    published_at = _parse_bigdata_date(item.get("일자"))
                    if not published_at or not (config["year_min"] <= published_at.year <= config["year_max"]):
                        continue
                    digest = hashlib.sha256(json.dumps(item, sort_keys=True).encode()).hexdigest()
                    ext_id = f"{source_name}:{digest}"
                    new_rows.append({
                        "external_id": ext_id,
                        "category": source_name,
                        "title": item.get("제목") or "No Title",
                        "content": item.get("본문") or "",
                        "media": item.get("언론사") or "ODcloud",
                        "published_at": published_at,
                    })

                if new_rows:
                    stmt = mysql_insert(News).values(new_rows).prefix_with("IGNORE")
                    result = db.execute(stmt)
                    db.commit()
                    added += result.rowcount
                    total_added += result.rowcount

                total_count = data.get("totalCount", 0)
                if not total_count or page * 100 >= total_count:
                    break
                page += 1

            print(f"[{source_name}] 완료: 신규 {added}건")
        return total_added
    finally:
        db.close()

def sync_worldbank(indicator_code, category, risk_type):
    import requests
    from datetime import datetime
    db = SessionLocal()
    try:
        current_year = datetime.now().year
        url = f"https://api.worldbank.org/v2/country/all/indicator/{indicator_code}"
        res = requests.get(url, params={"format": "json", "per_page": 300, "date": f"{current_year-5}:{current_year}"}, timeout=20)
        
        if res.status_code != 200:
            return
            
        try:
            data = res.json()
        except Exception:
            return
            
        if not isinstance(data, list) or len(data) < 2: 
            return
            
        target_countries = {"KOR", "USA", "CHN"}
        for item in data[1]:
            if not isinstance(item, dict):
                continue
            val = item.get("value")
            if val is None: 
                continue
            c_code = item.get("countryiso3code")
            if c_code not in target_countries:
                continue
            db.add(ESGStat(
                category=category, risk_type=risk_type, country=item.get("country", {}).get("value"),
                country_code=c_code, indicator=item.get("indicator", {}).get("value"),
                indicator_code=indicator_code, year=int(item.get("date")), value=float(val)
            ))
        db.commit()
    except Exception as e:
        print(f"[오류] 월드뱅크 지표({indicator_code}) 수집 무시: {e}", flush=True)
    finally:
        db.close()   
        db = SessionLocal()
    try:
        url = f"https://api.worldbank.org/v2/country/all/indicator/{indicator_code}"
        res = requests.get(url, params={"format": "json", "per_page": 300, "date": f"{current_year-5}:{current_year}"}, timeout=20)
        data = res.json()
        if len(data) < 2: return
        
        target_countries = {"KOR", "USA", "CHN"}
        
        for item in data[1]:
            val = item.get("value")
            if val is None: continue
            
            c_code = item.get("countryiso3code")
            if c_code not in target_countries:
                continue
                
            db.add(ESGStat(
                category=category, risk_type=risk_type, country=item.get("country", {}).get("value"),
                country_code=c_code, indicator=item.get("indicator", {}).get("value"),
                indicator_code=indicator_code, year=int(item.get("date")), value=float(val)
            ))
        db.commit()
    finally: db.close()
def sync_freedom_score():
    db = SessionLocal()
    try:
        url = "https://raw.githubusercontent.com/datasets/freedom-in-the-world/master/data/freedom-house-scores.csv"
        res = requests.get(url, timeout=20)
        reader = csv.DictReader(StringIO(res.text))
        countries = {"South Korea": "KOR", "United States": "USA", "China": "CHN"}
        for row in reader:
            entity = row.get("Country/Territory")
            if entity in countries:
                db.add(ESGStat(
                    category="G", risk_type="freedom_governance_risk", country=entity, country_code=countries[entity],
                    indicator="Freedom House score", indicator_code="freedom-score-fh", year=int(row.get("Edition")),
                    value=float(row.get("Total Score and Status").split()[0])
                ))
        db.commit()
    finally: db.close()

def run_all_syncs():
    db = SessionLocal()
    print("전체 동기화 시작")
    print("[1/8] ESG 뉴스 수집")
    c1 = fetch_all_news("https://apis.data.go.kr/B410001/trend-news/getTrend-news", "ESG", db)
    print(f"-> 완료: 신규 {c1}건")
    print("[2/8] 중국 이슈 수집")
    c2 = fetch_all_news("https://apis.data.go.kr/B410001/chinaGlobalIssueMonitoring/getChinaGlobalIssueMonitoring", "CHINA", db)
    print(f"-> 완료: 신규 {c2}건")
    print("[3/8] 미국 이슈 수집")
    c3 = fetch_all_news("https://apis.data.go.kr/B410001/usaGlobalIssueMonitoring/getUsaGlobalIssueMonitoring", "USA", db)
    print(f"-> 완료: 신규 {c3}건")
    print("[4/8] 빅데이터 ESG 수집 (1~4)")
    c4 = sync_bigdata_esg()
    print(f"-> 완료: 신규 {c4}건")
    print("[5/8] 에너지 소비 지표 수집")
    sync_worldbank("EG.USE.PCAP.KG.OE", "E", "energy_consumption_risk")
    print("[6/8] 실업률 지표 수집")
    sync_worldbank("SL.UEM.TOTL.ZS", "S", "unemployment_risk")
    print("[7/8] 기대수명 지표 수집")
    sync_worldbank("SP.DYN.LE00.IN", "S", "life_expectancy_risk")
    print("[8/8] 자유지수 수집")
    sync_freedom_score()
    print("전체 동기화 완료")
    db.close()

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_all_syncs, trigger=IntervalTrigger(hours=1), id="sync_all", replace_existing=True)
    scheduler.start()
    return scheduler