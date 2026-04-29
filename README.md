# Mail2Task

Mail2Task는 Gmail 메일과 PDF 첨부를 읽어 할 일을 추출하고, MongoDB에 저장한 뒤, FastAPI 웹 화면에서 관리하고 완료 시 회신 메일까지 보내는 메일 기반 업무 자동화 프로젝트입니다.

## 1. 프로젝트가 하는 일

메일이 들어오면 아래 순서로 처리합니다.

1. Gmail IMAP으로 최근 메일을 조회합니다.
2. 제목과 본문을 기준으로 업무 메일인지 판별합니다.
3. 첨부 PDF가 있으면 `downloads/`에 저장하고 텍스트를 추출합니다.
4. 메일 본문과 PDF 텍스트를 합쳐 Task를 하나 이상 추출합니다.
5. 각 Task의 마감일, 긴급도, 유형, 요약을 생성합니다.
6. MongoDB의 `mails`, `tasks` 컬렉션에 저장합니다.
7. 웹 화면에서 목록, 상세, 통계를 보여줍니다.
8. 사용자가 완료 버튼을 누르면 완료 상태를 저장하고 완료 메일을 발송합니다.

## 2. 주요 기능

- Gmail 메일 수집
- 업무 메일 필터링
- PDF 첨부 다운로드 및 텍스트 추출
- 메일 1건에서 Task 여러 건 추출
- 마감일 파싱과 긴급도 계산
- MongoDB 기반 메일/Task 저장
- FastAPI 기반 웹 UI
- OpenAI 기반 짧은 업무 요약 생성
- 완료 처리 시 발신자에게 완료 메일 발송
- 상태/유형/긴급도/카테고리 통계 조회

## 3. 전체 흐름

### 수집 파이프라인

```text
Gmail Inbox
  -> mail/mail_reader.py
  -> mail/pdf_extractor.py
  -> tasks/task_extractor.py
  -> core/summarizer.py
  -> tasks/todo_manager_adapter.py / storage/mongo_task_store.py
  -> MongoDB (mails, tasks)
  -> webapp/app.py
  -> Browser UI
```

### 완료 메일 파이프라인

```text
Task detail page
  -> webapp/app.py
  -> tasks.todo_manager_adapter.update_status()
  -> mail.notifier.send_completion_notice()
  -> Gmail SMTP
  -> tasks.notified = True
```

## 4. 폴더 구조

```text
Mail2Task/
├─ core/
│  ├─ config.py
│  ├─ classifier.py
│  ├─ deadline_parser.py
│  └─ summarizer.py
├─ mail/
│  ├─ mail_reader.py
│  ├─ notifier.py
│  └─ pdf_extractor.py
├─ monitoring/
│  └─ stats.py
├─ scripts/
│  └─ create_test_pdf.py
├─ storage/
│  ├─ database.py
│  └─ mongo_task_store.py
├─ tasks/
│  ├─ task_extractor.py
│  ├─ todo_analyzer.py
│  ├─ todo_manager.py
│  └─ todo_manager_adapter.py
├─ tests/
│  ├─ _bootstrap.py
│  ├─ test_classifier.py
│  ├─ test_mail_reader.py
│  ├─ test_notification.py
│  ├─ test_pdf_extractor.py
│  ├─ test_pdf_pipeline.py
│  └─ test_todo.py
├─ webapp/
│  ├─ app.py
│  ├─ env_service.py
│  ├─ pipeline_service.py
│  ├─ repositories.py
│  ├─ templates/
│  └─ static/
├─ downloads/
├─ main.py
├─ docker-compose.yml
├─ requirements.txt
├─ .env.example
├─ README.md
└─ README_WEB.md
```

## 5. 패키지별 역할

### `core/`

공통 설정과 텍스트 처리 로직을 담습니다.

- `core/config.py`
  `.env` 로드, Gmail, MongoDB, OpenAI, 저장 경로 설정
- `core/classifier.py`
  긴급도 계산, 중복 판별, 유사 업무 그룹화
- `core/deadline_parser.py`
  본문/제목에서 마감일과 시간을 추출
- `core/summarizer.py`
  상세 화면용 1~2줄 요약 생성

### `mail/`

메일 입출력과 PDF 처리 로직을 담습니다.

- `mail/mail_reader.py`
  Gmail IMAP 조회, 본문 추출, PDF 다운로드
- `mail/pdf_extractor.py`
  `pdfplumber`로 PDF 텍스트 추출
- `mail/notifier.py`
  Gmail SMTP로 완료 메일 발송

### `tasks/`

Task 생성과 Task 관리 로직을 담습니다.

- `tasks/task_extractor.py`
  메일 1건에서 Task 여러 건 추출
- `tasks/todo_manager.py`
  기존 To-do 분류 및 엔티티 추출 로직
- `tasks/todo_manager_adapter.py`
  기존 로직과 현재 Mongo 저장 구조를 연결하는 어댑터
- `tasks/todo_analyzer.py`
  Transformers 기반 분석기

### `storage/`

MongoDB 저장과 조회를 담당합니다.

- `storage/mongo_task_store.py`
  실제 메일/Task 저장소
- `storage/database.py`
  웹 레이어에서 쓰기 쉬운 조회/업데이트 래퍼

### `monitoring/`

대시보드와 통계 계산을 담당합니다.

- `monitoring/stats.py`
  상태, 긴급도, 유형, 마감 통계 집계

### `webapp/`

웹 UI 계층입니다.

- `webapp/app.py`
  FastAPI 라우팅 진입점
- `webapp/env_service.py`
  `.env` 읽기/쓰기, 런타임 설정 재로딩
- `webapp/pipeline_service.py`
  웹에서 수집 파이프라인을 재사용하는 서비스
- `webapp/repositories.py`
  화면용 조회와 요약 갱신 로직
- `webapp/templates/`
  Jinja2 템플릿
- `webapp/static/`
  CSS 등 정적 파일

### `tests/`와 `scripts/`

- `tests/`
  메일, PDF, 알림, 분류기, 웹 흐름을 점검하는 테스트 스크립트
- `scripts/`
  샘플 PDF 생성 같은 수동 실행 유틸리티

## 6. 웹 애플리케이션 구조

### `webapp/app.py`

주요 엔드포인트는 아래와 같습니다.

- `/`
  기본 진입 시 `/tasks`로 리다이렉트
- `/settings`
  Gmail 계정과 앱 비밀번호 설정
- `/settings/save`
  `.env` 저장
- `/settings/test`
  실제 IMAP 연결 테스트
- `/dashboard`
  통계 화면
- `/tasks`
  Task 목록, 검색, 필터, 정렬
- `/tasks/{task_id}`
  Task 상세 화면
- `/tasks/{task_id}/complete`
  완료 처리와 완료 메일 발송
- `/sync`
  메일 새로 불러오기
- `/downloads/{mail_id}/{filename}`
  첨부 PDF 다운로드

## 7. 데이터 저장 구조

MongoDB는 기본적으로 두 컬렉션을 사용합니다.

### `mails`

메일 원문과 첨부 정보를 저장합니다.

대표 필드:

- `mail_id`
- `subject`
- `mail_category`
- `sender`
- `received_at`
- `body`
- `pdf_files`
- `pdf_paths`
- `has_pdf`
- `pdf_count`

### `tasks`

실제 To-do 목록의 기준이 되는 컬렉션입니다.

대표 필드:

- `task_id`
- `mail_id`
- `task_order`
- `title`
- `subject`
- `sender`
- `status`
- `task_type`
- `urgency_score`
- `urgency_level`
- `deadline_date`
- `deadline_time`
- `deadline_at`
- `summary`
- `source_text`
- `raw_body`
- `has_pdf`
- `pdf_paths`
- `notified`

웹 목록은 `mails`가 아니라 `tasks` 컬렉션을 직접 읽습니다.

## 8. 환경 변수

`.env.example` 기준으로 아래 값을 사용합니다.

```env
TASK_EMAIL=your_gmail@gmail.com
TASK_PASSWORD=your_16_char_app_password
MONGODB_URI=mongodb://...
MONGODB_DB=mail2task
MONGODB_MAILS_COLLECTION=mails
MONGODB_TASKS_COLLECTION=tasks
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-5.4-mini
```

설명:

- `TASK_EMAIL`
  메일 수집/발송에 사용할 Gmail 계정
- `TASK_PASSWORD`
  Gmail 앱 비밀번호
- `MONGODB_URI`
  MongoDB 연결 문자열
- `OPENAI_API_KEY`
  LLM 요약 기능에 필요한 OpenAI API 키
- `OPENAI_MODEL`
  요약 생성에 사용할 OpenAI 모델

## 9. 실행 방법

### 1) 가상환경 및 패키지 설치

```powershell
cd "D:\Metanet\메일 자동화 프로젝트\Mail2Task"
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### 2) `.env` 준비

`.env.example`을 참고해서 `.env`를 만들거나 웹의 `/settings` 화면에서 직접 저장할 수 있습니다.

중요:

- Gmail 일반 비밀번호가 아니라 앱 비밀번호를 사용해야 합니다.
- OpenAI 키가 없으면 요약은 fallback 방식으로 동작합니다.

### 3) MongoDB 실행

로컬 MongoDB가 없다면 `docker-compose.yml`을 사용하면 됩니다.

```powershell
docker compose up -d
```

### 4) CLI 파이프라인 실행

```powershell
.\.venv\Scripts\python.exe main.py
```

이 명령은 메일 수집, Task 저장, 완료 메일 발송, 통계 출력까지 한 번에 수행합니다.

### 5) 웹 실행

```powershell
.\.venv\Scripts\python.exe -m uvicorn webapp.app:app --reload --port 8000
```

접속 주소:

- `http://127.0.0.1:8000`
- `http://127.0.0.1:8000/tasks`
- `http://127.0.0.1:8000/dashboard`
- `http://127.0.0.1:8000/settings`

## 10. 화면에서 볼 수 있는 것

### 설정 화면

- Gmail 계정 입력
- Gmail 앱 비밀번호 입력
- 연결 테스트

### 대시보드

- 전체 Task 수
- 상태별 수
- 긴급도별 수
- 유형별 수
- 마감 관련 통계

### Task 목록

- 검색
- 상태 필터
- 긴급도 필터
- 유형 필터
- 카테고리 필터
- 긴급도/마감/최신순 정렬

### Task 상세

- 제목
- 발신자
- 수신 시각
- 긴급도
- 마감일
- 요약
- 원문 내용
- 첨부 PDF 다운로드
- 완료 처리
