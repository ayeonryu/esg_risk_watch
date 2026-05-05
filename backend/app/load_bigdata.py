import pandas as pd
import os
from app.database import SessionLocal
from app.models import News

# 데이터 파일들이 모여있는 폴더 경로 (현재 backend 폴더 기준)
DATA_DIR = "./data"  # 파일들이 'backend/data' 폴더 안에 있다고 가정

def load_bigdata_files():
    db = SessionLocal()
    try:
        # 폴더 내 모든 파일 목록 가져오기
        files = [f for f in os.listdir(DATA_DIR) if f.startswith("news-bigdata-esg")]
        
        for file_name in files:
            file_path = os.path.join(DATA_DIR, file_name)
            print(f"[{file_name}] 처리 중...")
            
            # CSV 또는 Excel 읽기 (파일명에 따라 수정 가능)
            df = pd.read_csv(file_path) if file_path.endswith('.csv') else pd.read_excel(file_path)
            
            for _, row in df.iterrows():
                # 중복 확인
                ext_id = str(row.get('id') or row.get('title'))
                if db.query(News).filter(News.external_id == ext_id).first():
                    continue
                
                # DB에 추가
                db.add(News(
                    external_id=ext_id,
                    category="BIGDATA",
                    title=row.get('title'),
                    content=row.get('content'),
                    media=row.get('media', 'Legacy Data'),
                    published_at=row.get('date')
                ))
            
            db.commit()
            print(f"[{file_name}] 완료!")
            
    except Exception as e:
        print(f"에러 발생: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    load_bigdata_files()