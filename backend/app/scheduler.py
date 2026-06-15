import requests
import math
import hashlib
import json
import csv
import io
import zipfile
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
import time
import urllib.parse
from io import StringIO
from datetime import datetime, date, timedelta
from app.db.session import SessionLocal
from app.models.news import News
from app.models.esg_stat import ESGStat
from app.core.config import SERVICE_KEY
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy import func

current_year = datetime.now().year
TARGET_COUNTRIES = {"KOR", "USA", "CHN", "DEU"}
COUNTRY_KEYWORDS = {
    "KOR": ("대한민국", "한국", "서울", "부산", "Korea"),
    "USA": ("미국", "워싱턴", "뉴욕", "실리콘밸리", "달라스", "로스앤젤레스", "시카고", "United States", "USA"),
    "CHN": ("중국", "베이징", "상하이", "광저우", "선전", "청두", "China"),
    "DEU": ("독일", "프랑크푸르트", "뮌헨", "함부르크", "베를린", "Germany", "Deutschland"),
}

BIGDATA_CONFIGS = [
    {"url": "https://api.odcloud.kr/api/15097922/v1/uddi:97ce0eff-7786-4ace-ac15-aec8d947112a", "year_min": 2020, "year_max": current_year, "name": "NEWS_BIGDATA_ESG_1"},
    {"url": "https://api.odcloud.kr/api/15097922/v1/uddi:27150cfe-98f8-4608-9036-d68907d18fad", "year_min": 2020, "year_max": current_year, "name": "NEWS_BIGDATA_ESG_2"},
    {"url": "https://api.odcloud.kr/api/15097922/v1/uddi:36367d6b-9588-4245-819f-b1f0ba836185", "year_min": 2020, "year_max": current_year, "name": "NEWS_BIGDATA_ESG_3"},
    {"url": "https://api.odcloud.kr/api/15097922/v1/uddi:729fb13d-78df-47c1-bc75-e8ee986fbd67", "year_min": 2020, "year_max": current_year, "name": "NEWS_BIGDATA_ESG_4"},
]

RECENT_NEWS_FALLBACKS = {
    "KOR": {
        "label": "South Korea",
        "query": '(ESG OR sustainability OR "carbon neutral" OR "climate risk") ("South Korea" OR Korean)',
        "rss_query": 'ESG OR sustainability "South Korea"',
    },
    "DEU": {
        "label": "Germany",
        "query": '(ESG OR sustainability OR "carbon neutral" OR "climate risk") (Germany OR German)',
        "rss_query": 'ESG OR sustainability Germany',
    },
}

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

def _parse_gdelt_date(value):
    text = str(value or "").strip()
    if not text:
        return None
    for fmt in ("%Y%m%dT%H%M%SZ", "%Y%m%d%H%M%S", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None

def _parse_rss_date(value):
    try:
        parsed = parsedate_to_datetime(str(value or ""))
        return parsed.date()
    except Exception:
        return None

def sync_google_news_country(country_code, db, max_records=10):
    config = RECENT_NEWS_FALLBACKS.get(country_code)
    if not config:
        return 0

    try:
        res = requests.get(
            "https://news.google.com/rss/search",
            params={
                "q": config["rss_query"],
                "hl": "ko",
                "gl": "KR",
                "ceid": "KR:ko",
            },
            headers={"User-Agent": "ESG Risk Watch data sync"},
            timeout=15,
        )
        res.raise_for_status()
        root = ET.fromstring(res.content)
        added = 0

        for item in root.findall(".//item")[:max_records]:
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            pub_date = _parse_rss_date(item.findtext("pubDate"))
            source = item.find("source")
            media = (source.text if source is not None and source.text else "Google News")[:100]
            if not title or not link:
                continue

            digest = hashlib.sha256(link.encode("utf-8")).hexdigest()
            ext_id = f"GOOGLE_NEWS:{country_code}:{digest}"
            if db.query(News).filter(News.external_id == ext_id).first():
                continue

            db.add(News(
                external_id=ext_id,
                category="RECENT_NEWS",
                title=title[:500],
                content=link,
                media=media,
                country=country_code,
                region=config["label"],
                published_at=pub_date,
            ))
            added += 1

        db.commit()
        return added
    except Exception as e:
        db.rollback()
        print(f"[WARN] Google News fallback failed for {country_code}: {e}", flush=True)
        return 0

def sync_recent_country_news(country_code, db, max_records=10):
    config = RECENT_NEWS_FALLBACKS.get(country_code)
    if not config:
        return 0

    return sync_google_news_country(country_code, db, max_records)

def ensure_recent_country_news(country_code, db, stale_days=30):
    if country_code not in RECENT_NEWS_FALLBACKS:
        return 0

    latest = (
        db.query(func.max(News.published_at))
        .filter(News.country == country_code)
        .scalar()
    )
    if latest and latest >= date.today() - timedelta(days=stale_days):
        return 0

    return sync_recent_country_news(country_code, db)

def _infer_country_code(item=None, category=None, text=None):
    if category == "USA":
        return "USA"
    if category == "CHINA":
        return "CHN"
    parts = []
    if item:
        parts.extend(str(value) for value in item.values() if value is not None)
    if text:
        parts.append(str(text))
    haystack = " ".join(parts)
    for country_code, keywords in COUNTRY_KEYWORDS.items():
        if any(keyword in haystack for keyword in keywords):
            return country_code
    return None

def fetch_all_news(url, category, db):
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
                    
                    ntt_sn = item.get("nttSn")
                    if ntt_sn:
                        news_url = f"https://dream.kotra.or.kr/kotranews/cms/news/actionKotraBoardDetail.do?SITE_NO=3&MENU_ID=290&CONTENTS_NO=1&bbsGbn=464&bbsSn=464&pNttSn={ntt_sn}"
                    else:
                        raw_url = item.get("urlAddr") or ""
                        if raw_url:
                            if "pNttSn=" in raw_url:
                                parts = raw_url.split("pNttSn=")
                                sn_val = parts[1].split("&")[0] if "&" in parts[1] else parts[1]
                                news_url = f"https://dream.kotra.or.kr/kotranews/cms/news/actionKotraBoardDetail.do?SITE_NO=3&MENU_ID=290&CONTENTS_NO=1&bbsGbn=464&bbsSn=464&pNttSn={sn_val}"
                            elif "nttSn=" in raw_url:
                                parts = raw_url.split("nttSn=")
                                sn_val = parts[1].split("&")[0] if "&" in parts[1] else parts[1]
                                news_url = f"https://dream.kotra.or.kr/kotranews/cms/news/actionKotraBoardDetail.do?SITE_NO=3&MENU_ID=290&CONTENTS_NO=1&bbsGbn=464&bbsSn=464&pNttSn={sn_val}"
                            else:
                                news_url = raw_url if raw_url.startswith("http") else f"https://dream.kotra.or.kr{raw_url}"
                        else:
                            news_url = ""

                    if "news.joins.com" in news_url:
                        news_url = ""

                    if not news_url and item.get("nttSj"):
                        news_url = f"https://search.naver.com/search.naver?where=news&query={urllib.parse.quote(item.get('nttSj'))}"

                    db.add(News(
                        external_id=ext_id,
                        category=category,
                        title=item.get("nttSj") or "No Title",
                        content=item.get("smmarCn") or "",
                        media=item.get("kbc") or "KOTRA",
                        country=_infer_country_code(item, category),
                        published_at=_parse_bigdata_date(item.get("regDt")),
                        url=news_url
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
    finally:
        db.close()

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
                    
                    title = item.get("제목") or "No Title"
                    news_url = item.get("URL") or item.get("url") or item.get("원본주소") or item.get("링크") or item.get("urlAddr") or item.get("링크주소") or item.get("원문링크") or item.get("newsUrl") or ""
                    
                    if "news.joins.com" in news_url:
                        news_url = ""
                    
                    if not news_url and title != "No Title":
                        news_url = f"https://search.naver.com/search.naver?where=news&query={urllib.parse.quote(title)}"

                    new_rows.append({
                        "external_id": ext_id,
                        "category": source_name,
                        "title": title,
                        "content": item.get("본문") or "",
                        "media": item.get("언론사") or "ODcloud",
                        "published_at": published_at,
                        "url": news_url
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
    db = SessionLocal()
    try:
        url = f"https://api.worldbank.org/v2/en/indicator/{indicator_code}?downloadformat=csv"
        res = requests.get(url, timeout=60)
        res.raise_for_status()
        with zipfile.ZipFile(io.BytesIO(res.content)) as archive:
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
            if country_code not in TARGET_COUNTRIES:
                continue
            year_values = []
            for year, value in row.items():
                if year.isdigit() and value:
                    year_values.append((int(year), float(value)))
            for year, value in sorted(year_values, reverse=True)[:6]:
                existing = (
                    db.query(ESGStat)
                    .filter(
                        ESGStat.country_code == country_code,
                        ESGStat.risk_type == risk_type,
                        ESGStat.indicator_code == indicator_code,
                        ESGStat.year == year,
                    )
                    .first()
                )
                if existing:
                    existing.category = category
                    existing.country = row.get("Country Name")
                    existing.indicator = row.get("Indicator Name")
                    existing.value = value
                    continue
                db.add(ESGStat(
                    category=category,
                    risk_type=risk_type,
                    country=row.get("Country Name"),
                    country_code=country_code,
                    indicator=row.get("Indicator Name"),
                    indicator_code=indicator_code,
                    year=year,
                    value=value,
                ))
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[오류] 월드뱅크 지표({indicator_code}) 수집 무시: {e}", flush=True)
    finally:
        db.close()

def backfill_news_countries():
    db = SessionLocal()
    updated = 0
    try:
        rows = db.query(News).filter(News.country.is_(None)).all()
        for row in rows:
            country_code = _infer_country_code(
                category=row.category,
                text=" ".join(
                    str(value)
                    for value in (row.title, row.content, row.media, row.region)
                    if value
                ),
            )
            if country_code:
                row.country = country_code
                updated += 1
        db.commit()
        return updated
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def sync_freedom_score():
    db = SessionLocal()
    try:
        url = "https://ourworldindata.org/grapher/freedom-score-fh.csv?v=1&csvType=full&useColumnShortNames=false"
        res = requests.get(
            url,
            headers={"User-Agent": "ESG Risk Watch data sync"},
            timeout=20,
        )
        res.raise_for_status()
        reader = csv.DictReader(StringIO(res.text))
        for row in reader:
            country_code = row.get("Code")
            score = row.get("Total democracy score")
            if country_code in TARGET_COUNTRIES and score not in (None, ""):
                entity = row.get("Entity")
                year = int(row.get("Year"))
                value = float(score)
                existing = (
                    db.query(ESGStat)
                    .filter(
                        ESGStat.country_code == country_code,
                        ESGStat.risk_type == "freedom_governance_risk",
                        ESGStat.indicator_code == "freedom-score-fh",
                        ESGStat.year == year,
                    )
                    .first()
                )
                if existing:
                    existing.category = "G"
                    existing.country = entity
                    existing.indicator = "Freedom House score"
                    existing.value = value
                    continue
                db.add(ESGStat(
                    category="G", risk_type="freedom_governance_risk", country=entity, country_code=country_code,
                    indicator="Freedom House score", indicator_code="freedom-score-fh", year=year,
                    value=value
                ))
        db.commit()
    finally:
        db.close()

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
    print("[4-1/8] KOR/DEU recent news fallback")
    c5 = 0
    for country_code in ("KOR", "DEU"):
        c5 += sync_recent_country_news(country_code, db)
    print(f"-> recent fallback added: {c5}")
    backfilled = backfill_news_countries()
    print(f"-> 국가 코드 보정: {backfilled}건")
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