# ESG Watch Backend API 개발 가이드

## 구조 개요

### 각 엔드포인트 기본 구조
```
/api/v1/{리소스}/
├── /list              - 데이터 조회
├── /{id}              - 특정 항목 조회
├── /sync/all          - 외부 API에서 데이터 수집 (백그라운드)
└── /clear             - 모든 데이터 삭제
```

---

## 사용 가능한 엔드포인트

### 1. Health Check
```bash
GET /api/v1/health/
GET /api/v1/health/info
```

### 2. News (뉴스)
```bash
POST /api/v1/news/sync/all       # 뉴스 수집 시작
GET  /api/v1/news/list           # 뉴스 목록 조회
DELETE /api/v1/news/clear        # 모든 뉴스 삭제
```

### 3. Briefings (보고서/정보)
```bash
POST /api/v1/briefings/sync/all  # 보고서 동기화
GET  /api/v1/briefings/list      # 보고서 목록 조회
GET  /api/v1/briefings/{id}      # 특정 보고서 조회
DELETE /api/v1/briefings/clear   # 모든 보고서 삭제
```

### 4. Countries (국가)
```bash
GET /api/v1/countries/list               # 국가 목록 조회
GET /api/v1/countries/{country_code}     # 특정 국가 조회
GET /api/v1/countries/esg/ranking        # ESG 순위 조회
GET /api/v1/countries/risk/high-risk     # 고위험 국가 조회
DELETE /api/v1/countries/clear           # 모든 국가 데이터 삭제
```

### 5. Risks (리스크)
```bash
GET /api/v1/risks/list                   # 리스크 목록 조회
GET /api/v1/risks/{risk_id}              # 특정 리스크 조회
GET /api/v1/risks/country/{country_code} # 국가별 리스크 조회
GET /api/v1/risks/category/{category}    # 카테고리별 리스크 조회
GET /api/v1/risks/level/critical         # 심각 리스크 조회
DELETE /api/v1/risks/clear               # 모든 리스크 삭제
```

### 6. Trends (트렌드)
```bash
POST /api/v1/trends/sync/all             # 트렌드 동기화
GET  /api/v1/trends/list                 # 트렌드 목록 조회
GET  /api/v1/trends/category/{category}  # 카테고리별 트렌드 조회
GET  /api/v1/trends/esg/{esg_category}   # E/S/G별 트렌드 조회
GET  /api/v1/trends/emerging             # 신흥 트렌드 조회
DELETE /api/v1/trends/clear              # 모든 트렌드 삭제
```

---

## 데이터 구조

### Briefing (보고서)
```python
{
    "external_id": "unique_id",
    "title": "제목",
    "content": "내용",
    "category": "분류",
    "source": "출처",
    "country": "국가",
    "published_at": "YYYY-MM-DD",
    "summary": "요약",
    "esg_score": 75
}
```

### Country (국가)
```python
{
    "country_code": "KOR",
    "country_name": "South Korea",
    "region": "Asia",
    "esg_score": 75.5,
    "e_score": 72.0,
    "s_score": 76.5,
    "g_score": 78.0,
    "risk_level": "low"
}
```

### Risk (리스크)
```python
{
    "external_id": "unique_id",
    "country_code": "KOR",
    "country_name": "South Korea",
    "risk_type": "environmental",
    "risk_category": "climate_change",
    "risk_level": "high",
    "risk_score": 75.0,
    "description": "설명",
    "impact": "영향",
    "mitigation": "완화 방안",
    "source": "출처",
    "date_identified": "YYYY-MM-DD"
}
```

### Trend (트렌드)
```python
{
    "external_id": "unique_id",
    "title": "제목",
    "description": "설명",
    "category": "renewable_energy",
    "esg_category": "E",
    "trend_type": "emerging",
    "momentum": 0.85,
    "keywords": "키워드1,키워드2",
    "related_countries": "KOR,USA,CHN",
    "source": "출처",
    "published_at": "YYYY-MM-DD"
}
```

---

## 데이터 추가 방법

### 1. 직접 SQL INSERT
```sql
INSERT INTO briefings (external_id, title, category, source, published_at, created_at) 
VALUES ('brief_001', 'ESG Report 2024', 'report', 'Thomson Reuters', '2024-01-01', NOW());
```

### 2. Python으로 프로그래밍적으로 추가
```python
from app.models.briefing import Briefing
from app.services import briefing_service
from app.db.session import SessionLocal

db = SessionLocal()
briefing_data = {
    "external_id": "brief_001",
    "title": "ESG Report 2024",
    "category": "report",
    "source": "Thomson Reuters",
    "published_at": "2024-01-01"
}
briefing_service.create_briefing_from_dict(db, briefing_data)
db.close()
```

### 3. API 동기화 구현 (scheduler.py 패턴 활용)
```python
def sync_briefings_from_api(api_url, category):
    """API에서 보고서 데이터 가져오기"""
    db = SessionLocal()
    try:
        response = requests.get(api_url)
        data = response.json()
        
        for item in data.get("items", []):
            briefing_data = {
                "external_id": item.get("id"),
                "title": item.get("title"),
                "content": item.get("content"),
                "category": category,
                "source": item.get("source"),
                "published_at": item.get("date")
            }
            briefing_service.create_briefing_from_dict(db, briefing_data)
    finally:
        db.close()

# 사용 예: scheduler.py 또는 API 엔드포인트에서 호출
# sync_briefings_from_api("https://api.example.com/briefings", "report")
```

---

## 추가 개발 시 확인사항

1. **각 service 파일**: `*_service.py`에서 `create_{item}_from_dict()` 함수 구현
2. **각 repository 파일**: `*_repository.py`에서 CRUD 함수 구현  
3. **각 엔드포인트 파일**: `endpoints/{item}.py`에서 라우터 정의
4. **main.py**: 라우터 등록 (이미 완료)

---

## 빠른 시작

1. DB 설정 완료 후 서버 실행
2. `http://127.0.0.1:8000/api/v1/health/` 접속 → 헬스 체크
3. `http://127.0.0.1:8000/api/v1/health/info` 접속 → API 정보 확인
4. 각 엔드포인트의 `/list` 또는 `/sync/all`로 데이터 작업 시작
