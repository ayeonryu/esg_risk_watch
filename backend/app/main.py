from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from app.db.session import engine, Base
from app.models.news import News
from app.models.esg_stat import ESGStat
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.scheduler import start_scheduler, run_all_syncs
from io import StringIO
import requests
import csv
from datetime import datetime

Base.metadata.create_all(bind=engine)

scheduler = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global scheduler
    scheduler = start_scheduler()
    run_all_syncs()  # 서버 시작 시 즉시 1회 실행
    yield
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)

@app.get("/")
def read_root():
    return {"message": "ESG Watch Server is running!"}

@app.post("/api/admin/sync-all")
def manual_sync_all():
    run_all_syncs()
    return {"message": "전체 동기화 완료"}

@app.get("/api/external/esg-news")
def get_external_esg_news(page: int = 1, size: int = 10, db: Session = Depends(get_db)):
    service_key = "43b016f2295f780a65665aa1587a7f80e7f3be918cfacf883a66488069cd075c"
    url = "https://apis.data.go.kr/B410001/trend-news/getTrend-news"
    params = {"serviceKey": service_key, "type": "json", "numOfRows": size, "pageNo": page}
    response = requests.get(url, params=params)
    data = response.json()
    try:
        items = data["response"]["body"]["itemList"]["item"]
    except (KeyError, TypeError):
        return data
    if isinstance(items, dict):
        items = [items]
    for item in items:
        ext_id = str(item.get("nttSn") or item.get("nttSj"))
        if db.query(News).filter(News.external_id == ext_id).first():
            continue
        db.add(News(external_id=ext_id, category="ESG", title=item.get("nttSj") or "No Title", content=item.get("smmarCn") or "", media=item.get("kbc") or "KOTRA", published_at=item.get("regDt")))
    db.commit()
    return data

@app.get("/api/external/esg-news/all")
def get_all_esg_news(db: Session = Depends(get_db)):
    service_key = "43b016f2295f780a65665aa1587a7f80e7f3be918cfacf883a66488069cd075c"
    url = "https://apis.data.go.kr/B410001/trend-news/getTrend-news"
    res = requests.get(url, params={"serviceKey": service_key, "type": "json", "numOfRows": 1, "pageNo": 1})
    total = int(res.json()["response"]["body"]["totalCnt"])
    added = 0
    page = 1
    while True:
        res = requests.get(url, params={"serviceKey": service_key, "type": "json", "numOfRows": 10, "pageNo": page})
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
            ext_id = str(item.get("nttSn") or item.get("nttSj"))
            if db.query(News).filter(News.external_id == ext_id).first():
                continue
            db.add(News(external_id=ext_id, category="ESG", title=item.get("nttSj") or "No Title", content=item.get("smmarCn") or "", media=item.get("kbc") or "KOTRA", published_at=item.get("regDt")))
            added += 1
        db.commit()
        page += 1
        if page > (total // 10) + 2:
            break
    return {"added": added, "total": total}

@app.get("/api/external/china-global-issues")
def get_external_china_global_issues(page: int = 1, size: int = 10, db: Session = Depends(get_db)):
    service_key = "43b016f2295f780a65665aa1587a7f80e7f3be918cfacf883a66488069cd075c"
    url = "https://apis.data.go.kr/B410001/chinaGlobalIssueMonitoring/getChinaGlobalIssueMonitoring"
    params = {"serviceKey": service_key, "type": "json", "numOfRows": size, "pageNo": page}
    response = requests.get(url, params=params)
    data = response.json()
    try:
        items = data["response"]["body"]["itemList"]["item"]
    except (KeyError, TypeError):
        return data
    if isinstance(items, dict):
        items = [items]
    for item in items:
        ext_id = str(item.get("nttSn") or item.get("nttSj"))
        if db.query(News).filter(News.external_id == ext_id).first():
            continue
        db.add(News(external_id=ext_id, category="CHINA", title=item.get("nttSj") or "No Title", content=item.get("smmarCn") or "", media=item.get("kbc") or "KOTRA", published_at=item.get("regDt")))
    db.commit()
    return data

@app.get("/api/external/china-global-issues/all")
def get_all_china_global_issues(db: Session = Depends(get_db)):
    service_key = "43b016f2295f780a65665aa1587a7f80e7f3be918cfacf883a66488069cd075c"
    url = "https://apis.data.go.kr/B410001/chinaGlobalIssueMonitoring/getChinaGlobalIssueMonitoring"
    res = requests.get(url, params={"serviceKey": service_key, "type": "json", "numOfRows": 1, "pageNo": 1})
    total = int(res.json()["response"]["body"]["totalCnt"])
    added = 0
    page = 1
    while True:
        res = requests.get(url, params={"serviceKey": service_key, "type": "json", "numOfRows": 10, "pageNo": page})
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
            ext_id = str(item.get("nttSn") or item.get("nttSj"))
            if db.query(News).filter(News.external_id == ext_id).first():
                continue
            db.add(News(external_id=ext_id, category="CHINA", title=item.get("nttSj") or "No Title", content=item.get("smmarCn") or "", media=item.get("kbc") or "KOTRA", published_at=item.get("regDt")))
            added += 1
        db.commit()
        page += 1
        if page > (total // 10) + 2:
            break
    return {"added": added, "total": total}

@app.get("/api/external/usa-global-issues")
def get_external_usa_global_issues(page: int = 1, size: int = 10, db: Session = Depends(get_db)):
    service_key = "43b016f2295f780a65665aa1587a7f80e7f3be918cfacf883a66488069cd075c"
    url = "https://apis.data.go.kr/B410001/usaGlobalIssueMonitoring/getUsaGlobalIssueMonitoring"
    params = {"serviceKey": service_key, "type": "json", "numOfRows": size, "pageNo": page}
    res = requests.get(url, params=params)
    data = res.json()
    try:
        items = data["response"]["body"]["itemList"]["item"]
    except (KeyError, TypeError):
        return data
    if isinstance(items, dict):
        items = [items]
    for item in items:
        ext_id = str(item.get("nttSn") or item.get("nttSj"))
        if db.query(News).filter(News.external_id == ext_id).first():
            continue
        db.add(News(external_id=ext_id, category="USA", title=item.get("nttSj") or "No Title", content=item.get("smmarCn") or "", media=item.get("kbc") or "KOTRA", published_at=item.get("regDt")))
    db.commit()
    return data

@app.get("/api/external/usa-global-issues/all")
def get_all_usa_global_issues(db: Session = Depends(get_db)):
    service_key = "43b016f2295f780a65665aa1587a7f80e7f3be918cfacf883a66488069cd075c"
    url = "https://apis.data.go.kr/B410001/usaGlobalIssueMonitoring/getUsaGlobalIssueMonitoring"
    res = requests.get(url, params={"serviceKey": service_key, "type": "json", "numOfRows": 1, "pageNo": 2})
    total = int(res.json()["response"]["body"]["totalCnt"])
    added = 0
    page = 2
    while True:
        res = requests.get(url, params={"serviceKey": service_key, "type": "json", "numOfRows": 10, "pageNo": page})
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
            ext_id = str(item.get("nttSn") or item.get("nttSj"))
            if db.query(News).filter(News.external_id == ext_id).first():
                continue
            db.add(News(external_id=ext_id, category="USA", title=item.get("nttSj") or "No Title", content=item.get("smmarCn") or "", media=item.get("kbc") or "KOTRA", published_at=item.get("regDt")))
            added += 1
        db.commit()
        page += 1
        if page > (total // 10) + 2:
            break
    return {"added": added, "total": total}

@app.get("/api/news")
def get_news(
    category: str = None,
    start: str = None,
    end: str = None,
    page: int = 1,
    size: int = 10,
    db: Session = Depends(get_db)
):
    query = db.query(News)
    if category:
        query = query.filter(News.category == category)
    if start:
        query = query.filter(News.published_at >= start)
    if end:
        query = query.filter(News.published_at <= end)
    total = query.count()
    items = query.order_by(News.published_at.desc()).offset((page-1)*size).limit(size).all()
    return {
        "total": total,
        "page": page,
        "size": size,
        "items": [{"id": n.id, "category": n.category, "title": n.title, "content": n.content, "media": n.media, "published_at": str(n.published_at)} for n in items]
    }

@app.get("/api/external/news-bigdata-esg-1")
def get_news_bigdata_esg_1(page: int = 1, size: int = 10, db: Session = Depends(get_db)):
    service_key = "43b016f2295f780a65665aa1587a7f80e7f3be918cfacf883a66488069cd075c"
    url = "https://api.odcloud.kr/api/15097922/v1/uddi:97ce0eff-7786-4ace-ac15-aec8d947112a"
    params = {"serviceKey": service_key, "page": page, "perPage": size, "returnType": "JSON"}
    response = requests.get(url, params=params)
    data = response.json()
    items = data.get("data", [])
    for item in items:
        db.add(News(title=item.get("제목"), content=item.get("본문"), published_at=item.get("일자")))
    db.commit()
    return data

@app.get("/api/external/news-bigdata-esg-2")
def get_news_bigdata_esg_2(page: int = 1, size: int = 10, db: Session = Depends(get_db)):
    service_key = "43b016f2295f780a65665aa1587a7f80e7f3be918cfacf883a66488069cd075c"
    url = "https://api.odcloud.kr/api/15097922/v1/uddi:27150cfe-98f8-4608-9036-d68907d18fad"
    params = {"serviceKey": service_key, "page": page, "perPage": size, "returnType": "JSON"}
    response = requests.get(url, params=params)
    data = response.json()
    items = data.get("data", [])
    for item in items:
        db.add(News(title=item.get("제목"), content=item.get("본문"), published_at=item.get("일자")))
    db.commit()
    return data

@app.get("/api/external/news-bigdata-esg-3")
def get_news_bigdata_esg_3(page: int = 1, size: int = 10, db: Session = Depends(get_db)):
    service_key = "43b016f2295f780a65665aa1587a7f80e7f3be918cfacf883a66488069cd075c"
    url = "https://api.odcloud.kr/api/15097922/v1/uddi:36367d6b-9588-4245-819f-b1f0ba836185"
    params = {"serviceKey": service_key, "page": page, "perPage": size, "returnType": "JSON"}
    response = requests.get(url, params=params)
    data = response.json()
    items = data.get("data", [])
    for item in items:
        db.add(News(title=item.get("제목"), content=item.get("본문"), published_at=item.get("일자")))
    db.commit()
    return data

@app.get("/api/external/news-bigdata-esg-4")
def get_news_bigdata_esg_4(page: int = 1, size: int = 10, db: Session = Depends(get_db)):
    service_key = "43b016f2295f780a65665aa1587a7f80e7f3be918cfacf883a66488069cd075c"
    url = "https://api.odcloud.kr/api/15097922/v1/uddi:729fb13d-78df-47c1-bc75-e8ee986fbd67"
    params = {"serviceKey": service_key, "page": page, "perPage": size, "returnType": "JSON"}
    response = requests.get(url, params=params)
    data = response.json()
    items = data.get("data", [])
    for item in items:
        db.add(News(title=item.get("제목"), content=item.get("본문"), published_at=item.get("일자")))
    db.commit()
    return data

@app.get("/api/external/datacommons/greenhouse-gas/yearly")
def get_greenhouse_gas_yearly(db: Session = Depends(get_db)):
    api_key = "3bRAYyaN6gBdO7esp4GkyRlzYETJcXXuGkiAM6fRPf77hOvs"
    countries = {"country/KOR": "Korea", "country/USA": "United States", "country/CHN": "China", "country/DEU": "Germany"}
    url = "https://api.datacommons.org/v2/observation"
    result = []
    for country_code, country_name in countries.items():
        payload = {"date": "", "variable": {"dcids": ["Annual_Emissions_GreenhouseGas"]}, "entity": {"dcids": [country_code]}, "select": ["variable", "entity", "date", "value"]}
        response = requests.post(url, params={"key": api_key}, json=payload)
        data = response.json()
        ordered_facets = data.get("byVariable", {}).get("Annual_Emissions_GreenhouseGas", {}).get("byEntity", {}).get(country_code, {}).get("orderedFacets", [])
        for facet in ordered_facets:
            for obs in facet.get("observations", []):
                record_data = {"category": "E", "risk_type": "greenhouse_gas_emissions", "country": country_name, "country_code": country_code, "indicator": "Annual Greenhouse Gas Emissions", "indicator_code": "Annual_Emissions_GreenhouseGas", "year": int(obs.get("date")[:4]) if obs.get("date") else 0, "value": float(obs.get("value")) if obs.get("value") else 0.0}
                result.append(record_data)
                db.add(ESGStat(**record_data))
    db.commit()
    return result

@app.get("/api/external/energy-use/worldbank/multi")
def get_energy_use_multi(countries: str = "KOR,USA,CHN,DEU", start: int = 2020, end: int = 2024, db: Session = Depends(get_db)):
    indicator = "EG.USE.PCAP.KG.OE"
    country_list = countries.split(",")
    result = []
    for country in country_list:
        url = f"https://api.worldbank.org/v2/country/{country}/indicator/{indicator}"
        response = requests.get(url, params={"format": "json", "date": f"{start}:{end}", "per_page": 100})
        data = response.json()
        if len(data) > 1 and data[1]:
            for item in data[1]:
                record_data = {"category": "E", "risk_type": "energy_consumption_risk", "country": item["country"]["value"], "country_code": item["countryiso3code"], "indicator": item["indicator"]["value"], "indicator_code": indicator, "year": int(item["date"]) if item["date"] else 0, "value": float(item["value"]) if item["value"] is not None else 0.0}
                result.append(record_data)
                db.add(ESGStat(**record_data))
    db.commit()
    return result

@app.get("/api/external/unemployment/worldbank/multi")
def get_worldbank_multi(countries: str = "KOR,USA,CHN,DEU", indicator: str = "SL.UEM.TOTL.ZS", start: int = 2020, end: int = 2025, db: Session = Depends(get_db)):
    country_list = countries.split(",")
    result = []
    for country in country_list:
        url = f"https://api.worldbank.org/v2/country/{country}/indicator/{indicator}"
        response = requests.get(url, params={"format": "json", "date": f"{start}:{end}", "per_page": 100})
        data = response.json()
        if len(data) > 1 and data[1] is not None:
            for item in data[1]:
                record_data = {"category": "S", "risk_type": "unemployment_risk", "country": item["country"]["value"], "country_code": item["countryiso3code"], "indicator": item["indicator"]["value"], "indicator_code": indicator, "year": int(item["date"]) if item["date"] else 0, "value": float(item["value"]) if item["value"] is not None else 0.0}
                result.append(record_data)
                db.add(ESGStat(**record_data))
    db.commit()
    return result

@app.get("/api/external/life-expectancy/worldbank/multi")
def get_life_expectancy_simple(countries: str = "KOR,USA,CHN,DEU", start: int = 2020, end: int = 2025, db: Session = Depends(get_db)):
    indicator = "SP.DYN.LE00.IN"
    country_list = countries.split(",")
    result = []
    for country in country_list:
        url = f"https://api.worldbank.org/v2/country/{country}/indicator/{indicator}"
        response = requests.get(url, params={"format": "json", "date": f"{start}:{end}", "per_page": 100})
        data = response.json()
        if len(data) > 1 and data[1] is not None:
            for item in data[1]:
                record_data = {"category": "S", "risk_type": "life_expectancy_risk", "country": item["country"]["value"], "country_code": item["countryiso3code"], "indicator": item["indicator"]["value"], "indicator_code": indicator, "year": int(item["date"]) if item["date"] else 0, "value": float(item["value"]) if item["value"] is not None else 0.0}
                result.append(record_data)
                db.add(ESGStat(**record_data))
    db.commit()
    return result

@app.get("/api/external/governance/freedom-score")
def get_freedom_score(db: Session = Depends(get_db)):
    countries = {"South Korea": "Korea", "United States": "United States", "China": "China", "Germany": "Germany"}
    url = "https://ourworldindata.org/grapher/freedom-score-fh.csv"
    response = requests.get(url)
    csv_file = StringIO(response.text)
    reader = csv.DictReader(csv_file)
    value_column = [col for col in reader.fieldnames if col not in ["Entity", "Code", "Year"]][0]
    result = []
    for row in reader:
        entity = row.get("Entity")
        year = row.get("Year")
        value = row.get(value_column)
        if entity in countries and year and int(year) >= 2020:
            record_data = {"category": "G", "risk_type": "freedom_governance_risk", "country": countries[entity], "country_code": row.get("Code"), "indicator": "Freedom House score", "indicator_code": "freedom-score-fh", "year": int(year), "value": float(value) if value not in [None, ""] else 0.0}
            result.append(record_data)
            db.add(ESGStat(**record_data))
    db.commit()
    return result