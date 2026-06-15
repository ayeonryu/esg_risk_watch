import os

if __name__ == '__main__':
    if os.environ.get("FULL_SYNC") is None:
        choice = input("전체 동기화 실행? (y/n): ").strip().lower()
        os.environ["FULL_SYNC"] = "true" if choice == "y" else "false"

    import uvicorn
    uvicorn.run("app.main:app", reload=False)