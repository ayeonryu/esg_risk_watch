from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.db.session import engine, Base
from app.api.v1.endpoints import news, briefings, countries, risks, trends, health
from app import scheduler

Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("전체 동기화 프로세스 시작")
    scheduler.run_all_syncs()
    print("전체 동기화 프로세스 종료")
    sc = scheduler.start_scheduler()
    print("정보: 1시간 간격 실시간 스케줄러 가동")
    yield
    sc.shutdown()
    print("정보: 서버 종료 - 스케줄러 정지")

app = FastAPI(title="ESG Watch", lifespan=lifespan)

# 모든 라우터 등록
app.include_router(health.router, prefix="/api/v1/health", tags=["health"])
app.include_router(news.router, prefix="/api/v1/news", tags=["news"])
app.include_router(briefings.router, prefix="/api/v1/briefings", tags=["briefings"])
app.include_router(countries.router, prefix="/api/v1/countries", tags=["countries"])
app.include_router(risks.router, prefix="/api/v1/risks", tags=["risks"])
app.include_router(trends.router, prefix="/api/v1/trends", tags=["trends"])

@app.get("/")
def read_root():
    return {"status": "running", "message": "ESG Watch API is running"}