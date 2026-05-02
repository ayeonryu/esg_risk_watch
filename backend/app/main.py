from fastapi import FastAPI
from app.db.session import engine, Base
from app.models import news 
import requests #외부 호출 위해 추가


Base.metadata.create_all(bind=engine)# 서버 시작 시 테이블 x-> 자동으로 생성

app = FastAPI()# 이 아래부터 API를 작성하시면 됩니다. 위쪽은 건들이지 말아주세요

@app.get("/")
def read_root():
    return {"message": "ESG Watch Server is running!"}

# 외부 ESG 뉴스 API 호출
#대한무역투자진흥공사_ESG 동향뉴스
@app.get("/api/external/esg-news")
def get_external_esg_news(page: int = 1, size: int = 10):
    service_key = "43b016f2295f780a65665aa1587a7f80e7f3be918cfacf883a66488069cd075c"

    url = "https://apis.data.go.kr/B410001/trend-news/getTrend-news"

    params = {
        "serviceKey": service_key,
        "type": "json",
        "numOfRows": size,
        "pageNo": page
    }

    response = requests.get(url, params=params)
    return response.json()

#대한무역투자진흥공사_중국 글로벌 이슈 모니터링 정보
@app.get("/api/external/china-global-issues")
def get_external_china_global_issues(page: int = 1, size: int = 10):
    service_key = "43b016f2295f780a65665aa1587a7f80e7f3be918cfacf883a66488069cd075c"

    url = "https://apis.data.go.kr/B410001/chinaGlobalIssueMonitoring/getChinaGlobalIssueMonitoring"

    params = {
        "serviceKey": service_key,
        "type": "json",
        "numOfRows": size,
        "pageNo": page
    }

    response = requests.get(url, params=params)
    return response.json()


#대한무역투자진흥공사_미국 글로벌 이슈 모니터링 정보
@app.get("/api/external/usa-global-issues")
def get_external_usa_global_issues(page: int = 1, size: int = 10):
    service_key = "43b016f2295f780a65665aa1587a7f80e7f3be918cfacf883a66488069cd075c"

    url = "https://apis.data.go.kr/B410001/usaGlobalIssueMonitoring/getUsaGlobalIssueMonitoring"

    params = {
        "serviceKey": service_key,
        "type": "json",
        "numOfRows": size,
        "pageNo": page,
        "search1": "20240808"
    }

    response = requests.get(url, params=params)

    return response.json()

#한국언론진흥재단_뉴스빅데이터_메타데이터_ESG
@app.get("/api/external/news-bigdata-esg-1")
def get_news_bigdata_esg_1(page: int = 1, size: int = 10):
    service_key = "43b016f2295f780a65665aa1587a7f80e7f3be918cfacf883a66488069cd075c"

    url = "https://api.odcloud.kr/api/15097922/v1/uddi:97ce0eff-7786-4ace-ac15-aec8d947112a"

    params = {
        "serviceKey": service_key,
        "page": page,
        "perPage": size,
        "returnType": "JSON"
    }

    response = requests.get(url, params=params)

    return response.json()

@app.get("/api/external/news-bigdata-esg-2")
def get_news_bigdata_esg_2(page: int = 1, size: int = 10):
    service_key = "43b016f2295f780a65665aa1587a7f80e7f3be918cfacf883a66488069cd075c"

    url = "https://api.odcloud.kr/api/15097922/v1/uddi:27150cfe-98f8-4608-9036-d68907d18fad"

    params = {
        "serviceKey": service_key,
        "page": page,
        "perPage": size,
        "returnType": "JSON"
    }

    response = requests.get(url, params=params)

    return response.json()

@app.get("/api/external/news-bigdata-esg-3")
def get_news_bigdata_esg_3(page: int = 1, size: int = 10):
    service_key = "43b016f2295f780a65665aa1587a7f80e7f3be918cfacf883a66488069cd075c"

    url = "https://api.odcloud.kr/api/15097922/v1/uddi:36367d6b-9588-4245-819f-b1f0ba836185"

    params = {
        "serviceKey": service_key,
        "page": page,
        "perPage": size,
        "returnType": "JSON"
    }

    response = requests.get(url, params=params)

    return response.json()

@app.get("/api/external/news-bigdata-esg-4")
def get_news_bigdata_esg_4(page: int = 1, size: int = 10):
    service_key = "43b016f2295f780a65665aa1587a7f80e7f3be918cfacf883a66488069cd075c"

    url = "https://api.odcloud.kr/api/15097922/v1/uddi:729fb13d-78df-47c1-bc75-e8ee986fbd67"

    params = {
        "serviceKey": service_key,
        "page": page,
        "perPage": size,
        "returnType": "JSON"
    }

    response = requests.get(url, params=params)

    return response.json()

# Data Commons - 온실가스 배출량(E)
@app.get("/api/external/datacommons/greenhouse-gas/yearly")
def get_greenhouse_gas_yearly():
    api_key = "3bRAYyaN6gBdO7esp4GkyRlzYETJcXXuGkiAM6fRPf77hOvs"

    countries = {
        "country/KOR": "Korea",
        "country/USA": "United States",
        "country/CHN": "China",
        "country/DEU": "Germany"
    }

    url = "https://api.datacommons.org/v2/observation"
    result = []

    for country_code, country_name in countries.items():
        payload = {
            "date": "",
            "variable": {
                "dcids": ["Annual_Emissions_GreenhouseGas"]
            },
            "entity": {
                "dcids": [country_code]
            },
            "select": ["variable", "entity", "date", "value"]
        }

        response = requests.post(
            url,
            params={"key": api_key},
            json=payload,
        )
        data = response.json()

        ordered_facets = (
            data
            .get("byVariable", {})
            .get("Annual_Emissions_GreenhouseGas", {})
            .get("byEntity", {})
            .get(country_code, {})
            .get("orderedFacets", [])
        )

        for facet in ordered_facets:
            for obs in facet.get("observations", []):
                result.append({
                    "category": "E",
                    "risk_type": "greenhouse_gas_emissions",
                    "country": country_name,
                    "country_code": country_code,
                    "indicator": "Annual Greenhouse Gas Emissions",
                    "indicator_code": "Annual_Emissions_GreenhouseGas",
                    "year": obs.get("date"),
                    "value": obs.get("value")
                })

    return result

# Data Commons - 1인당 CO2 배출량 연도별 조회(E) -> 2024년까지 데이터 제공(중국은 2023년까지)
@app.get("/api/external/energy-use/worldbank/multi")
def get_energy_use_multi(
    countries: str = "KOR,USA,CHN,DEU",
    start: int = 2020,
    end: int = 2024
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
                result.append({
                    "category": "E",
                    "risk_type": "energy_consumption_risk",
                    "country": item["country"]["value"],
                    "country_code": item["countryiso3code"],
                    "indicator": item["indicator"]["value"],
                    "indicator_code": indicator,
                    "year": item["date"],
                    "value": item["value"]
                })

    return result

# World Bank 실업률 데이터(S) -> 2025년까지 데이터 제공
@app.get("/api/external/unemployment/worldbank/multi")
def get_worldbank_multi(
    countries: str = "KOR,USA,CHN,DEU",
    indicator: str = "SL.UEM.TOTL.ZS",
    start: int = 2020,
    end: int = 2025
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
                result.append({
                    "country": item["country"]["value"],
                    "country_code": item["countryiso3code"],
                    "indicator": item["indicator"]["value"],
                    "indicator_code": indicator,
                    "year": item["date"],
                    "value": item["value"]
                })

    return result

# World Bank 기대수명 데이터(코드: SP.DYN.LE00.IN)(S) -> 2024년까지 데이터 제공
@app.get("/api/external/life-expectancy/worldbank/multi")
def get_life_expectancy_simple(
    countries: str = "KOR,USA,CHN,DEU",
    start: int = 2020,
    end: int = 2025
):
    country_list = countries.split(",")
    result = []

    for country in country_list:
        url = f"https://api.worldbank.org/v2/country/{country}/indicator/SP.DYN.LE00.IN"

        params = {
            "format": "json",
            "date": f"{start}:{end}",
            "per_page": 100
        }

        response = requests.get(url, params=params)
        data = response.json()

        if len(data) > 1 and data[1] is not None:
            for item in data[1]:
                result.append({
                    "country": item["country"]["value"],
                    "country_code": item["countryiso3code"],
                    "year": item["date"],
                    "poverty_rate": item["value"],
                    "indicator": item["indicator"]["value"]
                })

    return result


#종합 거버넌스 리스크 수준(G)->2024년까지 데이터 제공, Freedom House 점수 기반으로 계산
import csv
from io import StringIO

@app.get("/api/external/governance/freedom-score")
def get_freedom_score():
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

    # Entity, Code, Year 제외한 실제 값 컬럼 자동 선택
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
            result.append({
                "category": "G",
                "risk_type": "freedom_governance_risk",
                "country": countries[entity],
                "country_original": entity,
                "indicator": "Freedom House score",
                "indicator_code": "freedom-score-fh",
                "year": year,
                "value": float(value) if value not in [None, ""] else None
            })

    return result