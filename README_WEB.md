## Mail2Task 웹 실행 방법

이 프로젝트는 기존 메일 수집/Task 추출/저장 로직을 그대로 재사용하면서, FastAPI 기반 웹 UI를 추가했습니다.

### 1) 설치

프로젝트 폴더로 이동 후 의존성을 설치합니다.

```bash
cd "d:\Metanet\메일 자동화 프로젝트\Mail2Task"
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### 2) 환경설정(.env)

- 웹에서 설정 페이지(`/settings`)로 들어가 Gmail 주소와 **앱 비밀번호**를 저장하면 `.env`의 `TASK_EMAIL`, `TASK_PASSWORD`가 갱신됩니다.
- MongoDB는 기본값으로 `docker-compose.yml`의 로컬 설정을 사용합니다.

### 3) MongoDB 실행(선택)

로컬 Docker를 쓰는 경우:

```bash
cd "d:\Metanet\메일 자동화 프로젝트\Mail2Task"
docker compose up -d
```

### 4) 웹 서버 실행

```bash
cd "d:\Metanet\메일 자동화 프로젝트\Mail2Task"
.\.venv\Scripts\activate
python -m uvicorn webapp.app:app --reload --host 127.0.0.1 --port 8000
```

접속: `http://127.0.0.1:8000`

### 5) 주요 화면

- `/settings`: Gmail 계정/앱 비밀번호 저장(.env 갱신) + 메일 연결 테스트
- `/dashboard`: tasks 기준 통계 카드 + 차트(Chart.js)
- `/tasks`: To-do 리스트(필터/검색/정렬)
- `/tasks/{task_id}`: 상세 + 완료 처리(완료 알림 메일 발송)
- 상단 버튼 “메일 새로 불러오기”: 기존 수집 파이프라인 실행 후 결과 표시

### 폴더 구조(추가된 것)

- `webapp/`
  - `app.py`: FastAPI 앱/라우팅
  - `env_service.py`: `.env` 안전 갱신 + 즉시 반영
  - `pipeline_service.py`: 기존 수신 파이프라인을 웹에서 호출
  - `repositories.py`: MongoDB 조회 헬퍼
  - `templates/`: Jinja2 템플릿
  - `static/`: CSS

