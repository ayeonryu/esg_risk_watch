from app.db.session import SessionLocal
from app.services.indicator_sync_service import sync_target_indicators


def main():
    db = SessionLocal()
    try:
        result = sync_target_indicators(db)
        print(result)
    finally:
        db.close()


if __name__ == "__main__":
    main()
