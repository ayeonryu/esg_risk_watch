from contextlib import asynccontextmanager
import os
from app.models.news import News
from app.models.esg_stat import ESGStat
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.session import engine, Base
from app.api.v1.endpoints import news, briefings, countries, risks, trends, health, indicators
from app import scheduler

Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    sc = scheduler.start_scheduler()
    if os.environ.get("FULL_SYNC") == "true":
        asyncio.create_task(asyncio.to_thread(scheduler.run_all_syncs))
    yield
    sc.shutdown()

app = FastAPI(title="ESG Watch", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/v1/health", tags=["health"])
app.include_router(news.router, prefix="/api/v1/news", tags=["news"])
app.include_router(briefings.router, prefix="/api/v1/briefings", tags=["briefings"])
app.include_router(countries.router, prefix="/api/v1/countries", tags=["countries"])
app.include_router(risks.router, prefix="/api/v1/risks", tags=["risks"])
app.include_router(trends.router, prefix="/api/v1/trends", tags=["trends"])
app.include_router(indicators.router, prefix="/api/v1/indicators", tags=["indicators"])

@app.get("/")
def read_root():
    return {"status": "running", "message": "ESG Watch API is running"}
