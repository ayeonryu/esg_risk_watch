import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

SERVICE_KEY = os.getenv("SERVICE_KEY", "43b016f2295f780a65665aa1587a7f80e7f3be918cfacf883a66488069cd075c")
DC_API_KEY = "3bRAYyaN6gBdO7esp4GkyRlzYETJcXXuGkiAM6fRPf77hOvs"

BIGDATA_CONFIGS = [
    {"url": "https://api.odcloud.kr/api/15097922/v1/uddi:97ce0eff-7786-4ace-ac15-aec8d947112a", "year_min": 2020, "year_max": datetime.now().year},
    {"url": "https://api.odcloud.kr/api/15097922/v1/uddi:27150cfe-98f8-4608-9036-d68907d18fad", "year_min": 2020, "year_max": datetime.now().year},
    {"url": "https://api.odcloud.kr/api/15097922/v1/uddi:36367d6b-9588-4245-819f-b1f0ba836185", "year_min": 2020, "year_max": datetime.now().year},
    {"url": "https://api.odcloud.kr/api/15097922/v1/uddi:729fb13d-78df-47c1-bc75-e8ee986fbd67", "year_min": 2020, "year_max": datetime.now().year},
]
BIGDATA_BATCH_SIZE = 100
