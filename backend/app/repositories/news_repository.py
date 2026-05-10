# app/repositories/news_repository.py
from sqlalchemy.orm import Session
from app.models.news import News

def get_news_by_external_id(db: Session, ext_id: str):
    return db.query(News).filter(News.external_id == ext_id).first()

def create_news_item(db: Session, news_obj: News):
    db.add(news_obj)
    db.commit()

def bulk_save_news(db: Session, news_list: list):
    db.bulk_save_objects(news_list)
    db.commit()