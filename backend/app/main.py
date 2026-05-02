from fastapi import FastAPI, Depends
from app.db.session import engine, Base
from app.models.news import News 
from app.models.esg_stat import ESGStat
from sqlalchemy.orm import Session
from app.db.session import get_db
import requests
from datetime import datetime

Base.metadata.create_all(bind=engine)

app = FastAPI()

def save_to_db(db: Session, items, category):
    # items가 아예 없거나 None인 경우 체크
    if not items:
        print(f"[{category}] No items found in response.")
        return 0
    
    # KOTRA API는 데이터가 1개면 dict, 여러개면 list로 줌 -> 무조건 list로 변환
    if isinstance(items, dict):
        items = [items]
    
    added_count = 0
    for item in items:
        # 필드 추출 (KOTRA 특유의 nttSn, nttSj 등 대소문자 모두 대응)
        title_text = item.get("nttSj") or item.get("ntt_sj") or item.get("title")
        content_text = item.get("nttCn") or item.get("ntt_cn") or item.get("content") or item.get("cnnt")
        raw_id = item.get("nttSn") or item.get("ntt_sn") or item.get("nttSnId")
        
        # 필수값인 external_id 생성 (없으면 저장 안됨)
        ext_id = str(raw_id) if raw_id else f"{category}_{hash(title_text)}"

        # 중복 체크
        if db.query(News).filter(News.external_id == ext_id).first():
            continue

        # 날짜 처리
        raw_date = item.get("regdate") or item.get("reg_dt") or item.get("regDate")
        pub_date = None
        if raw_date:
            try:
                clean_date = "".join(filter(str.isdigit, str(raw_date)))[:8]
                pub_date = datetime.strptime(clean_date, '%Y%m%d').date()
            except:
                pass

        try:
            new_news = News(
                external_id=ext_id,
                title=str(title_text or "제목 없음")[:500],
                content=str(content_text or ""),
                category=category,
                media=item.get("kbcName") or item.get("kbc_nm") or "KOTRA",
                published_at=pub_date
            )
            db.add(new_news)
            added_count += 1
        except Exception as e:
            print(f"Insert Error: {e}")
            continue
    
    if added_count > 0:
        db.commit()
    return added_count

@app.get("/")
def read_root():
    return {"message": "ESG Watch Server is running!"}

@app.get("/api/external/esg-news")
def get_external_esg_news(page: int = 1, size: int = 10, db: Session = Depends(get_db)):
    service_key = "43b016f2295f780a65665aa1587a7f80e7f3be918cfacf883a66488069cd075c"
    url = "https://apis.data.go.kr/B410001/trend-news/getTrend-news"
    params = {"serviceKey": service_key, "type": "json", "numOfRows": size, "pageNo": page}
    
    res = requests.get(url, params=params)
    data = res.json()
    
    # 경로를 한 단계씩 안전하게 탐색
    response_obj = data.get("response", {})
    body_obj = response_obj.get("body", {})
    items_wrapper = body_obj.get("items", {})
    # items가 문자열 ""로 올 때가 있어서 체크 필수
    items = items_wrapper.get("item", []) if isinstance(items_wrapper, dict) else []
    
    count = save_to_db(db, items, "ESG")
    return {"added": count, "data_count": len(items) if isinstance(items, list) else 1 if items else 0, "raw": data}

@app.get("/api/external/china-global-issues")
def get_external_china_global_issues(page: int = 1, size: int = 10, db: Session = Depends(get_db)):
    service_key = "43b016f2295f780a65665aa1587a7f80e7f3be918cfacf883a66488069cd075c"
    url = "https://apis.data.go.kr/B410001/chinaGlobalIssueMonitoring/getChinaGlobalIssueMonitoring"
    params = {"serviceKey": service_key, "type": "json", "numOfRows": size, "pageNo": page}
    
    res = requests.get(url, params=params)
    data = res.json()
    
    response_obj = data.get("response", {})
    body_obj = response_obj.get("body", {})
    items_wrapper = body_obj.get("items", {})
    items = items_wrapper.get("item", []) if isinstance(items_wrapper, dict) else []
    
    count = save_to_db(db, items, "CHINA")
    return {"added": count, "data_count": len(items) if isinstance(items, list) else 1 if items else 0, "raw": data}

@app.get("/api/external/usa-global-issues")
def get_external_usa_global_issues(page: int = 1, size: int = 10, db: Session = Depends(get_db)):
    service_key = "43b016f2295f780a65665aa1587a7f80e7f3be918cfacf883a66488069cd075c"
    url = "https://apis.data.go.kr/B410001/usaGlobalIssueMonitoring/getUsaGlobalIssueMonitoring"
    params = {"serviceKey": service_key, "type": "json", "numOfRows": size, "pageNo": page}
    
    res = requests.get(url, params=params)
    data = res.json()
    
    response_obj = data.get("response", {})
    body_obj = response_obj.get("body", {})
    items_wrapper = body_obj.get("items", {})
    items = items_wrapper.get("item", []) if isinstance(items_wrapper, dict) else []
    
    count = save_to_db(db, items, "USA")
    return {"added": count, "data_count": len(items) if isinstance(items, list) else 1 if items else 0, "raw": data}
  #  ------------------------------------------------------------------ 위쪽 kotra   05/03에 수정할부분
@app.get("/api/external/news-bigdata-esg-1")
def get_news_bigdata_esg_1(page: int = 1, size: int = 10, db: Session = Depends(get_db)):
    service_key = "43b016f2295f780a65665aa1587a7f80e7f3be918cfacf883a66488069cd075c"
    url = "https://api.odcloud.kr/api/15097922/v1/uddi:97ce0eff-7786-4ace-ac15-aec8d947112a"
    params = {
        "serviceKey": service_key,
        "page": page,
        "perPage": size,
        "returnType": "JSON"
    }
    response = requests.get(url, params=params)
    data = response.json()
    
    items = data.get("data", [])
    for item in items:
        new_news = News(
            title=item.get("제목"),
            content=item.get("본문"),
            published_at=item.get("일자")
        )
        db.add(new_news)
    db.commit()
    return data

@app.get("/api/external/news-bigdata-esg-2")
def get_news_bigdata_esg_2(page: int = 1, size: int = 10, db: Session = Depends(get_db)):
    service_key = "43b016f2295f780a65665aa1587a7f80e7f3be918cfacf883a66488069cd075c"
    url = "https://api.odcloud.kr/api/15097922/v1/uddi:27150cfe-98f8-4608-9036-d68907d18fad"
    params = {
        "serviceKey": service_key,
        "page": page,
        "perPage": size,
        "returnType": "JSON"
    }
    response = requests.get(url, params=params)
    data = response.json()
    
    items = data.get("data", [])
    for item in items:
        new_news = News(
            title=item.get("제목"),
            content=item.get("본문"),
            published_at=item.get("일자")
        )
        db.add(new_news)
    db.commit()
    return data

@app.get("/api/external/news-bigdata-esg-3")
def get_news_bigdata_esg_3(page: int = 1, size: int = 10, db: Session = Depends(get_db)):
    service_key = "43b016f2295f780a65665aa1587a7f80e7f3be918cfacf883a66488069cd075c"
    url = "https://api.odcloud.kr/api/15097922/v1/uddi:36367d6b-9588-4245-819f-b1f0ba836185"
    params = {
        "serviceKey": service_key,
        "page": page,
        "perPage": size,
        "returnType": "JSON"
    }
    response = requests.get(url, params=params)
    data = response.json()
    
    items = data.get("data", [])
    for item in items:
        new_news = News(
            title=item.get("제목"),
            content=item.get("본문"),
            published_at=item.get("일자")
        )
        db.add(new_news)
    db.commit()
    return data

@app.get("/api/external/news-bigdata-esg-4")
def get_news_bigdata_esg_4(page: int = 1, size: int = 10, db: Session = Depends(get_db)):
    service_key = "43b016f2295f780a65665aa1587a7f80e7f3be918cfacf883a66488069cd075c"
    url = "https://api.odcloud.kr/api/15097922/v1/uddi:729fb13d-78df-47c1-bc75-e8ee986fbd67"
    params = {
        "serviceKey": service_key,
        "page": page,
        "perPage": size,
        "returnType": "JSON"
    }
    response = requests.get(url, params=params)
    data = response.json()
    
    items = data.get("data", [])
    for item in items:
        new_news = News(
            title=item.get("제목"),
            content=item.get("본문"),
            # 'url' 필드 제거
            published_at=item.get("일자")
        )
        db.add(new_news)
    db.commit()
    return data
# Data Commons - 온실가스 배출량(E)
@app.get("/api/external/datacommons/greenhouse-gas/yearly")
def get_greenhouse_gas_yearly(db: Session = Depends(get_db)):
    api_key = "3bRAYyaN6gBdO7esp4GkyRlzYETJcXXuGkiAM6fRPf77hOvs"

    countries = {
        "country/KOR": "Korea",
        "country/USA": "United States",
        "country/CHN": "China",
        "country/DEU": "Germany"
    }

    url = "https://api.datacommons.org/v2/observation"
    result = [] # 화면 출력용 리스트

   
    for country_code, country_name in countries.items():
        payload = {
            "date": "",
            "variable": {"dcids": ["Annual_Emissions_GreenhouseGas"]},
            "entity": {"dcids": [country_code]},
            "select": ["variable", "entity", "date", "value"]
        }

        response = requests.post(url, params={"key": api_key}, json=payload)
        data = response.json()


        ordered_facets = (
            data.get("byVariable", {})
            .get("Annual_Emissions_GreenhouseGas", {})
            .get("byEntity", {})
            .get(country_code, {})
            .get("orderedFacets", [])
        )

        for facet in ordered_facets:
            for obs in facet.get("observations", []):
                record_data = {
                    "category": "E",
                    "risk_type": "greenhouse_gas_emissions",
                    "country": country_name,
                    "country_code": country_code,
                    "indicator": "Annual Greenhouse Gas Emissions",
                    "indicator_code": "Annual_Emissions_GreenhouseGas",
                    "year": int(obs.get("date")[:4]) if obs.get("date") else 0,
                    "value": float(obs.get("value")) if obs.get("value") else 0.0
                }
                result.append(record_data)

                
                new_record = ESGStat(**record_data)
                db.add(new_record)

    db.commit()

    
    return result

@app.get("/api/external/energy-use/worldbank/multi")
def get_energy_use_multi(
    countries: str = "KOR,USA,CHN,DEU",
    start: int = 2020,
    end: int = 2024,
    db: Session = Depends(get_db) 
):
    indicator = "EG.USE.PCAP.KG.OE"
    country_list = countries.split(",")
    result = []

    for country in country_list:
        url = f"https://api.worldbank.org/v2/country/{country}/indicator/{indicator}"
        params = {
            "format": "json",
            "date": f"{start}:{end}",
            "per_page": 100
        }

        response = requests.get(url, params=params)
        data = response.json()

        if len(data) > 1 and data[1]:
            for item in data[1]:
   
                record_data = {
                    "category": "E",
                    "risk_type": "energy_consumption_risk",
                    "country": item["country"]["value"],
                    "country_code": item["countryiso3code"],
                    "indicator": item["indicator"]["value"],
                    "indicator_code": indicator,
                    "year": int(item["date"]) if item["date"] else 0, # 연도 정수화
                    "value": float(item["value"]) if item["value"] is not None else 0.0
                }
                

                result.append(record_data)


                new_record = ESGStat(**record_data)
                db.add(new_record)


    db.commit()

    return result
# World Bank 실업률 데이터(S) -> 2025년까지 데이터 제공
@app.get("/api/external/unemployment/worldbank/multi")
def get_worldbank_multi(
    countries: str = "KOR,USA,CHN,DEU",
    indicator: str = "SL.UEM.TOTL.ZS",
    start: int = 2020,
    end: int = 2025,
    db: Session = Depends(get_db)
):
    country_list = countries.split(",")
    result = []

    for country in country_list:
        url = f"https://api.worldbank.org/v2/country/{country}/indicator/{indicator}"
        params = {
            "format": "json",
            "date": f"{start}:{end}",
            "per_page": 100
        }

        response = requests.get(url, params=params)
        data = response.json()

        if len(data) > 1 and data[1] is not None:
            for item in data[1]:
                record_data = {
                    "category": "S",
                    "risk_type": "unemployment_risk",
                    "country": item["country"]["value"],
                    "country_code": item["countryiso3code"],
                    "indicator": item["indicator"]["value"],
                    "indicator_code": indicator,
                    "year": int(item["date"]) if item["date"] else 0,
                    "value": float(item["value"]) if item["value"] is not None else 0.0
                }
                
                result.append(record_data)
                new_record = ESGStat(**record_data)
                db.add(new_record)

    db.commit()
    return result

@app.get("/api/external/life-expectancy/worldbank/multi")
def get_life_expectancy_simple(
    countries: str = "KOR,USA,CHN,DEU",
    start: int = 2020,
    end: int = 2025,
    db: Session = Depends(get_db)
):
    indicator = "SP.DYN.LE00.IN"
    country_list = countries.split(",")
    result = []

    for country in country_list:
        url = f"https://api.worldbank.org/v2/country/{country}/indicator/{indicator}"
        params = {
            "format": "json",
            "date": f"{start}:{end}",
            "per_page": 100
        }

        response = requests.get(url, params=params)
        data = response.json()

        if len(data) > 1 and data[1] is not None:
            for item in data[1]:
                record_data = {
                    "category": "S",
                    "risk_type": "life_expectancy_risk",
                    "country": item["country"]["value"],
                    "country_code": item["countryiso3code"],
                    "indicator": item["indicator"]["value"],
                    "indicator_code": indicator,
                    "year": int(item["date"]) if item["date"] else 0,
                    "value": float(item["value"]) if item["value"] is not None else 0.0
                }
                
                result.append(record_data)
                new_record = ESGStat(**record_data)
                db.add(new_record)

    db.commit()
    return result

#종합 거버넌스 리스크 수준(G)->2024년까지 데이터 제공, Freedom House 점수 기반으로 계산
@app.get("/api/external/governance/freedom-score")
def get_freedom_score(db: Session = Depends(get_db)):
    countries = {
        "South Korea": "Korea",
        "United States": "United States",
        "China": "China",
        "Germany": "Germany"
    }

    url = "https://ourworldindata.org/grapher/freedom-score-fh.csv"
    response = requests.get(url)

    csv_file = StringIO(response.text)
    reader = csv.DictReader(csv_file)

    value_column = [
        col for col in reader.fieldnames
        if col not in ["Entity", "Code", "Year"]
    ][0]

    result = []

    for row in reader:
        entity = row.get("Entity")
        year = row.get("Year")
        value = row.get(value_column)

        if entity in countries and year and int(year) >= 2020:
            record_data = {
                "category": "G",
                "risk_type": "freedom_governance_risk",
                "country": countries[entity],
                "country_code": row.get("Code"),
                "indicator": "Freedom House score",
                "indicator_code": "freedom-score-fh",
                "year": int(year),
                "value": float(value) if value not in [None, ""] else 0.0
            }
            
            result.append(record_data)
            new_record = ESGStat(**record_data)
            db.add(new_record)

    db.commit()
    return result