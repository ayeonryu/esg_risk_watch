from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.db.session import engine, Base
from app.api.v1.endpoints import news
from app import scheduler
from app.models.news import News
from app.models.esg_stat import ESGStat

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
app.include_router(news.router, prefix="/api/v1/news", tags=["news"])

@app.get("/")
def read_root():
    return {"status": "running"}