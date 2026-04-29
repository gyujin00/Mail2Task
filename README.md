# Mail2Task

메일을 읽어서 할 일을 추출하고, MongoDB에 저장하고, 웹 화면에서 확인하고, 완료 시 회신 메일까지 보내는 자동화 프로젝트입니다.

이 프로젝트는 크게 두 층으로 구성됩니다.

- 기존 파이프라인: Gmail IMAP 수집, PDF 본문 추출, Task 생성, MongoDB 저장, 완료 알림 발송
- 웹 레이어: FastAPI 기반 설정 화면, 대시보드, To-do 목록, 상세 화면, 메일 동기화 버튼

핵심 포인트는 "메일 1건에서 Task 여러 건이 나올 수 있는 구조"와 "웹이 별도 비즈니스 로직을 많이 가지지 않고 기존 파이프라인을 최대한 재사용한다"는 점입니다.

## 1. 이 프로젝트가 하는 일

메일이 들어오면 다음 순서로 처리합니다.

1. Gmail IMAP으로 최근 메일을 조회합니다.
2. 제목이나 본문이 업무 메일 조건에 맞는지 판별합니다.
3. 첨부된 PDF가 있으면 `downloads/`에 저장하고 텍스트를 추출합니다.
4. 메일 본문과 PDF 텍스트를 합쳐서 Task를 하나 이상 추출합니다.
5. 각 Task의 마감일, 긴급도, 유형, 요약을 생성합니다.
6. MongoDB의 `mails`, `tasks` 컬렉션에 저장합니다.
7. 웹에서 목록/상세/통계를 확인합니다.
8. 사용자가 완료 버튼을 누르면 완료 상태를 저장하고 발신자에게 완료 메일을 보냅니다.

## 2. 주요 기능

- Gmail 메일 수집
- 업무 메일 필터링
- PDF 첨부파일 다운로드 및 텍스트 추출
- 메일 1건에서 Task N건 추출
- 마감일 추론 및 긴급도 점수 계산
- MongoDB 기반 메일/Task 저장
- FastAPI 기반 웹 UI
- OpenAI 기반 짧은 업무 요약 생성
- 완료 처리 시 발신자에게 알림 메일 발송
- 상태/유형/긴급도/카테고리 통계 조회

## 3. 전체 구조 한눈에 보기

### 처리 흐름

```text
Gmail Inbox
  -> mail_reader.py
  -> pdf_extractor.py
  -> task_extractor.py
  -> summarizer.py
  -> todo_manager_adapter.py / mongo_task_store.py
  -> MongoDB (mails, tasks)
  -> webapp/app.py
  -> 브라우저 UI
```

### 완료 메일 흐름

```text
사용자 상세 화면에서 완료 클릭
  -> webapp/app.py
  -> todo_manager_adapter.update_status()
  -> notifier.send_completion_notice()
  -> Gmail SMTP 발송
  -> tasks.notified = True
```

## 4. 폴더 / 파일 구조

```text
Mail2Task/
├─ scripts/
│  └─ create_test_pdf.py
├─ tests/
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
├─ config.py
├─ main.py
├─ mail_reader.py
├─ pdf_extractor.py
├─ task_extractor.py
├─ summarizer.py
├─ classifier.py
├─ deadline_parser.py
├─ notifier.py
├─ mongo_task_store.py
├─ todo_manager_adapter.py
├─ database.py
├─ stats.py
├─ todo_manager.py
├─ todo_analyzer.py
├─ docker-compose.yml
├─ requirements.txt
├─ README_WEB.md
├─ .env.example
└─ README.md
```

### 핵심 디렉터리 설명

- `scripts/`
  샘플 PDF 생성처럼 수동 실행이 필요한 유틸리티 스크립트 모음입니다.
- `tests/`
  메일, PDF, 알림, 분류기 점검용 테스트 스크립트 모음입니다.
- `webapp/`
  FastAPI와 Jinja2 기반 웹 UI 레이어입니다.
- `downloads/`
  메일에서 내려받은 PDF 파일이 저장되는 폴더입니다.
- 루트의 `*.py`
  메일 수집, PDF 처리, Task 추출, 저장, 알림 발송 같은 핵심 파이프라인 모듈입니다.

## 5. 핵심 모듈 역할

### `config.py`

프로젝트의 공통 설정을 들고 있습니다.

- `.env` 로드
- Gmail IMAP/SMTP 계정 정보
- MongoDB 연결 정보
- OpenAI API 정보
- PDF 저장 경로
- 메일 제목 필터 패턴
- 긴급도 기준값

### `main.py`

CLI 기준 메인 실행 파일입니다.

- `run_inbound_pipeline()`
  메일 수집 -> PDF 추출 -> Task 저장
- `run_outbound_pipeline()`
  완료되었지만 아직 알림이 안 간 Task를 찾아 메일 발송

즉, 웹 없이도 기본 파이프라인만 돌릴 수 있는 진입점입니다.

### `mail_reader.py`

Gmail IMAP으로 메일을 읽어오는 모듈입니다.

- 최근 50개 메일 조회
- 제목/본문 기준 업무 메일 판별
- 메일 본문 추출
- PDF 첨부파일 다운로드

현재 필터는 비교적 넓습니다.

- 제목이 `[...]` 형태로 시작하면 수집 대상
- 또는 본문/제목에 업무 관련 키워드가 있으면 대상

즉 현재 구조상 `[완료] ...` 같은 메일도 제목 패턴만 맞으면 대상이 될 수 있습니다.

### `pdf_extractor.py`

`pdfplumber`로 PDF 텍스트를 추출합니다.

- 첨부 PDF의 페이지 텍스트 수집
- 텍스트를 한 문자열로 합쳐 후속 Task 추출에 전달
- 파일 없음/추출 실패 시 빈 문자열 반환

### `task_extractor.py`

메일 1건에서 Task 여러 건을 뽑는 핵심 모듈입니다.

- 본문과 PDF 텍스트를 합쳐 분석
- `과업명`, `업무유형`, `우선순위` 같은 구조화된 필드 우선 사용
- 여러 Task 블록이 있으면 분리 저장
- 마감일, 긴급도, 요약 생성

중요한 점은 이 프로젝트가 "메일 = Task 1개"가 아니라 "메일 = Task 여러 개"를 지원한다는 점입니다.

### `summarizer.py`

상세 화면에 보여줄 짧은 요약을 생성합니다.

- OpenAI API가 설정되어 있으면 LLM 요약 사용
- 제목, 본문, PDF 텍스트를 함께 사용
- 보통 1~2줄 요약 생성
- API를 쓸 수 없으면 fallback 요약 사용

현재 LLM은 "Task 추출 자체"보다는 "상세 화면용 짧은 자연어 요약"에 집중되어 있습니다.

### `classifier.py`

업무 보조 판단 로직을 담당합니다.

- 긴급도 점수 계산
- 중복 여부 판단
- 제목 유사도 기반 유사 Task 그룹화

### `deadline_parser.py`

본문이나 제목에서 날짜/시간 표현을 읽어 마감일 정보를 정리합니다.

실제 마감일 계산은 이 모듈이 맡고, 긴급도 계산은 `classifier.py`가 이어받아 사용합니다.

### `notifier.py`

완료 메일 발송 전용 모듈입니다.

- Gmail SMTP 로그인
- 완료 알림 메일 제목/본문 구성
- 발신자에게 완료 회신 전송

### `mongo_task_store.py`

실제 MongoDB 저장소 역할을 합니다.

- `mails` 컬렉션 저장
- `tasks` 컬렉션 저장
- 상태 변경
- 미통지 완료 Task 조회
- 메일 중복 검사

사실상 현재 저장/조회의 메인 백엔드입니다.

### `todo_manager_adapter.py`

기존 `todo_manager.py` 로직과 현재 Mongo 저장 구조를 연결하는 어댑터입니다.

- 기존 분류/엔티티 추출 로직 fallback 활용
- MongoDB 저장 로직으로 위임
- 웹/CLI가 공통으로 쓰는 저장 함수 제공

프로젝트가 확장되면서 생긴 "호환 레이어"라고 보면 됩니다.

### `database.py`

웹 레이어에서 쓰기 쉬운 간단한 조회/업데이트 래퍼입니다.

- Task 목록/단건 조회
- Mail 단건 조회
- Task 업데이트

`mongo_task_store.py`와 일부 역할이 겹치지만, 현재는 웹 계층에서 편하게 쓰는 얇은 접근 모듈로 남아 있습니다.

### `stats.py`

MongoDB에 저장된 Task를 기반으로 대시보드 통계를 만듭니다.

- 전체 Task 수
- 상태별 개수
- 긴급도별 개수
- 유형별 개수
- 카테고리별 개수
- 오늘 마감 / 이번 주 마감 / 기한 초과

## 6. 웹 애플리케이션 구조

웹은 `webapp/` 아래에 모여 있습니다.

### `webapp/app.py`

웹 진입점입니다.

- `/`
  기본 진입 시 `/tasks`로 리다이렉트
- `/settings`
  메일 계정과 앱 비밀번호 설정
- `/settings/save`
  `.env` 저장
- `/settings/test`
  실제 IMAP 연결 테스트
- `/dashboard`
  통계 화면
- `/tasks`
  Task 목록, 필터, 검색, 정렬
- `/tasks/{task_id}`
  Task 상세 화면
- `/tasks/{task_id}/complete`
  완료 처리 + 완료 메일 발송
- `/sync`
  메일 새로 불러오기
- `/downloads/{mail_id}/{filename}`
  첨부 PDF 다운로드

### `webapp/env_service.py`

설정 파일 관련 유틸리티입니다.

- `.env` 읽기/갱신
- 런타임 설정 다시 로드
- 비밀번호 마스킹

### `webapp/pipeline_service.py`

웹에서 메일 동기화를 누를 때 기존 파이프라인을 재사용하는 서비스입니다.

- `fetch_target_mails()`
- `extract_text_from_pdf()`
- `extract_tasks_from_mail()`
- `save_mail()`
- `save_tasks()`

즉 웹은 새 로직을 따로 만들지 않고, 기존 메일 처리 흐름을 서비스 레이어로 감싼 구조입니다.

### `webapp/repositories.py`

화면에서 필요한 Task/Mail 조회와 요약 갱신을 담당합니다.

### `webapp/templates/`

Jinja2 템플릿 모음입니다.

- `base.html`
- `dashboard.html`
- `settings.html`
- `tasks.html`
- `task_detail.html`
- `sync_result.html`
- `error.html`

### `webapp/static/app.css`

웹 전용 스타일 파일입니다.

## 7. 데이터 저장 구조

MongoDB 컬렉션은 기본적으로 두 개를 씁니다.

### `mails`

메일 원문 보존용입니다.

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

즉, 웹 리스트는 메일 컬렉션이 아니라 `tasks` 컬렉션을 직접 읽습니다.

## 8. 환경 변수

`.env.example`을 기준으로 보면 다음 값을 사용합니다.

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
  LLM 요약 기능 사용 시 필요
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

`.env.example`을 참고해서 `.env`를 만들거나, 웹의 `/settings` 화면에서 직접 저장해도 됩니다.

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

이 명령은 메일 수집, Task 저장, 완료 알림 발송, 통계 출력까지 한 번에 수행합니다.

### 5) 웹 실행

```powershell
.\.venv\Scripts\python.exe -m uvicorn webapp.app:app --reload --port 8000
```

접속:

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
