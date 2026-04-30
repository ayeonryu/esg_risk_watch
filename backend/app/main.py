from fastapi import FastAPI
from app.db.session import engine, Base
from app.models import news 

Base.metadata.create_all(bind=engine)# 서버 시작 시 테이블 x-> 자동으로 생성

app = FastAPI()# 이 아래부터 API를 작성하시면 됩니다. 위쪽은 건들이지 말아주세요

@app.get("/")
def read_root():
    return {"message": "ESG Watch Server is running!"}