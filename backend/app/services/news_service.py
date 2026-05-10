# app/services/news_service.py
import requests
import math
import hashlib
import json
from datetime import datetime, date
from app.models.news import News
from app.core.config import SERVICE_KEY
from app.repositories import news_repository

def _parse_date(value):
    if value is None: return None
    if isinstance(value, date): return value
    text = str(value).strip()
    for candidate in (text, text[:10]):
        for fmt in ("%Y-%m-%d", "%Y.%m.%d", "%Y/%m/%d", "%Y%m%d"):
            try: return datetime.strptime(candidate, fmt).date()
            except ValueError: continue
    return None

def fetch_all_news_logic(url: str, category: str, db):
    try:
        res = requests.get(url, params={"serviceKey": SERVICE_KEY, "type": "json", "numOfRows": 1, "pageNo": 1}, timeout=10)
        total = int(res.json().get("response", {}).get("body", {}).get("totalCnt", 0))
        if total == 0: return 0

        added, page = 0, 1
        max_page = math.ceil(total / 10)

        while page <= max_page:
            res = requests.get(url, params={"serviceKey": SERVICE_KEY, "type": "json", "numOfRows": 10, "pageNo": page}, timeout=10)
            items = res.json().get("response", {}).get("body", {}).get("itemList", {}).get("item", [])
            if not items: break
            if isinstance(items, dict): items = [items]

            for item in items:
                ext_id = str(item.get("nttSn") or item.get("nttSj"))
                if news_repository.get_news_by_external_id(db, ext_id): continue
                
                new_news = News(
                    external_id=ext_id, category=category,
                    title=item.get("nttSj") or "No Title", 
                    content=item.get("smmarCn") or "",
                    media=item.get("kbc") or "KOTRA", 
                    published_at=_parse_date(item.get("regDt"))
                )
                news_repository.create_news_item(db, new_news)
                added += 1
            page += 1
        return added
    except Exception as e:
        print(f"Error in {category}: {e}")
        return 0