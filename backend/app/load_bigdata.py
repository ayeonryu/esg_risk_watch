import pandas as pd
import os
from app.db.session import SessionLocal
from app.models.news import News

DATA_DIR = "./data"

def load_bigdata_files():
    db = SessionLocal()
    try:
        files = [f for f in os.listdir(DATA_DIR) if f.startswith("news-bigdata-esg")]
        for file_name in files:
            file_path = os.path.join(DATA_DIR, file_name)
            print(f"[{file_name}] 처리 중...")
            df = pd.read_csv(file_path) if file_path.endswith('.csv') else pd.read_excel(file_path)
            for _, row in df.iterrows():
                ext_id = str(row.get('id') or row.get('title'))
                if db.query(News).filter(News.external_id == ext_id).first():
                    continue
                news_url = row.get('url') or row.get('URL') or row.get('원본주소') or row.get('링크') or row.get('urlAddr') or row.get('링크주소') or row.get('원문링크') or row.get('newsUrl') or ""
                db.add(News(
                    external_id=ext_id,
                    category="BIGDATA",
                    title=row.get('title'),
                    content=row.get('content'),
                    media=row.get('media', 'Legacy Data'),
                    published_at=row.get('date'),
                    url=news_url
                ))
            db.commit()
            print(f"[{file_name}] 완료!")
    except Exception as e:
        print(f"에러 발생: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    load_bigdata_files()