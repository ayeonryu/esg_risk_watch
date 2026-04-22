# ESG Risk Watch 작업 메뉴얼

## 1. Git 저장소 접근 방법

우리 프로젝트는 GitHub 저장소로 같이 관리하면 됩니다.

### 저장소 주소
```bash
https://github.com/ayeonryu/esg_risk_watch.git
```

### 접근 방법
1. GitHub Collaborator 초대를 받으면 먼저 수락합니다.
2. 본인 PC에서 원하는 위치에 저장소를 clone 합니다.

```bash
git clone https://github.com/ayeonryu/esg_risk_watch.git
```

3. clone이 끝나면 VS Code에서 해당 폴더를 엽니다.

---

## 2. 프로젝트 기본 구조

현재 프로젝트 구조는 아래와 같습니다.

```text
esg_risk_watch/
├─ .gitignore
├─ README.md
├─ frontend/
├─ backend/
│  ├─ app/
│  ├─ tests/
│  ├─ .env
│  ├─ requirements.txt
│  └─ venv/   ← 이건 git에 안 올라감
├─ data/
└─ docs/
```

### 폴더 역할
- `frontend` : 프론트 작업
- `backend` : 백엔드 API 작업
- `data` : 데이터 수집, 전처리, 분석 관련
- `docs` : 문서, 회의 내용, 정리본

---

## 3. 처음 받은 사람이 해야 할 것

### 1) 저장소 clone
```bash
git clone https://github.com/ayeonryu/esg_risk_watch.git
```

### 2) 프로젝트 폴더 열기
VS Code에서 `esg_risk_watch` 루트 폴더를 열면 됩니다.

### 3) backend 폴더로 이동
```bash
cd backend
```

---

## 4. 백엔드 환경 설정 방법

백엔드는 Python 가상환경 기준으로 맞추면 됩니다.

### 1) 가상환경 생성
처음 받았으면 본인 컴퓨터에서 직접 만들어야 합니다.

```bash
py -m venv venv
```

### 2) 가상환경 실행

#### PowerShell 기준
```bash
.\venv\Scripts\Activate.ps1
```

실행 정책 때문에 막히면 아래 명령어를 한 번 실행한 뒤 다시 시도하면 됩니다.

```bash
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

그다음 다시 실행합니다.

```bash
.\venv\Scripts\Activate.ps1
```

### 3) 패키지 설치
```bash
python -m pip install -r requirements.txt
```

이렇게 하면 현재 백엔드에 필요한 라이브러리 버전을 동일하게 맞출 수 있습니다.

---

## 5. requirements.txt 관련

`requirements.txt`는 **백엔드 환경을 맞추기 위한 파일**입니다.

즉,
- 백엔드 담당자는 `backend/requirements.txt` 기준으로 환경을 맞추면 됩니다.
- 프론트 담당자는 프론트 환경을 따로 맞추면 됩니다.
- 데이터 파트가 백엔드와 다른 Python 환경을 쓸 경우 나중에 `data/requirements.txt`를 따로 둘 수 있습니다.

현재 기준으로는 **백엔드 담당자들만 맞추면 됩니다.**

---

## 6. .env 관련

`.env`는 환경변수 파일이라 Git에 올라가지 않도록 설정해두었습니다.

즉, clone을 해도 `.env` 파일은 자동으로 들어오지 않습니다.  
필요하면 `backend/.env` 파일을 직접 만들어서 아래 내용을 넣으면 됩니다.

```env
PROJECT_NAME=ESG Risk Watch API
API_V1_PREFIX=/api/v1
ENV=dev
ALLOWED_ORIGINS=*
```

나중에 API 키나 DB 정보가 들어가면 그때 추가하면 됩니다.

---

## 7. 현재 .gitignore에 들어간 것

현재는 아래 항목들이 Git에서 제외되도록 설정해두었습니다.

- `backend/venv/`
- `backend/.env`
- `__pycache__`
- `*.pyc`
- `.vscode/`
- `Thumbs.db`
- `.DS_Store`

즉, 가상환경과 환경변수 파일은 각자 로컬에서만 관리하면 됩니다.

---

## 8. 백엔드 실행 방법

`backend` 폴더 기준으로 실행하면 됩니다.

### 기본 실행
```bash
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

정상 실행되면 아래 주소로 접속하면 됩니다.

```text
http://127.0.0.1:8000
```

---

## 9. VS Code에서 빨간 줄 뜰 때

이건 대부분 **Python 인터프리터가 잘못 잡혀서** 생기는 경우가 많습니다.

특히 Python이 여러 개 설치되어 있으면 다른 Python을 잡아서 오류처럼 보일 수 있습니다.

### 해결 방법
VS Code에서 아래 순서대로 들어갑니다.

`Ctrl + Shift + P`  
→ `Python: Select Interpreter`  
→ 아래 경로 선택

```text
backend\venv\Scripts\python.exe
```

이걸로 맞추면 대부분 해결됩니다.

---

## 10. Git 작업 기본 순서

작업하기 전에 먼저 최신 내용을 받아옵니다.

```bash
git pull origin main
```

작업 후에는 아래 순서대로 진행하면 됩니다.

```bash
git add .
git commit -m "작업 내용"
git push origin main
```

---

## 11. 작업할 때 주의할 점

### 1) `venv`는 올리지 않기
가상환경은 각자 로컬에서 만드는 것이므로 Git에 올리면 안 됩니다.

### 2) `.env` 올리지 않기
API 키나 민감한 값이 들어갈 수 있으므로 Git에 올리면 안 됩니다.

### 3) 작업 전에 pull 먼저 하기
작업 전에 `git pull origin main`을 먼저 해야 충돌이 덜 납니다.

### 4) 루트 폴더 기준으로 작업하기
`backend`만 따로 여는 것보다 프로젝트 전체 루트를 여는 편이 덜 헷갈립니다.

---

## 12. 추천 작업 방식

### 백엔드 담당
- `backend/app` 중심 작업
- API, 서비스, 리포지토리 관련 수정

### 데이터 담당
- `data` 폴더 중심 작업
- 수집, 전처리, 분석 스크립트 작성

### 프론트 담당
- `frontend` 폴더 중심 작업

---

## 13. 백엔드 작업 시작 전 체크리스트

백엔드 작업하는 사람은 시작 전에 아래 항목만 확인하면 됩니다.

1. 저장소 clone 했는지
2. `backend` 폴더로 들어왔는지
3. `py -m venv venv`로 가상환경 생성했는지
4. 가상환경 실행했는지
5. `python -m pip install -r requirements.txt` 했는지
6. VS Code 인터프리터를 `backend\venv\Scripts\python.exe`로 맞췄는지