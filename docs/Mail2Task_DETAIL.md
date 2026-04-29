# 미니 프로젝트 2 상세 설명서

## 1. 프로젝트 개요

미니 프로젝트 2는 Gmail 메일과 첨부 PDF를 읽어서 업무(Task)를 자동으로 추출하고, 이를 MongoDB에 저장한 뒤 FastAPI 기반 웹 화면에서 조회·필터링·완료 처리까지 할 수 있게 만든 업무 자동화 프로젝트다.

이 프로젝트의 핵심 목표는 단순한 메일 수집이 아니라, 아래 과정을 하나의 파이프라인으로 묶는 것이다.

1. 업무 관련 메일만 선별한다.
2. 메일 본문과 첨부 PDF에서 업무 문맥을 읽는다.
3. 메일 1건에서 업무 여러 건을 분리한다.
4. 각 업무의 마감일, 긴급도, 업무 유형, 요약을 생성한다.
5. 메일 원문, Task, PDF 문서를 각각 저장한다.
6. 웹에서 목록, 상세, 통계, 추천 PDF를 보여준다.
7. 완료 처리 후 발신자에게 완료 메일을 보낸다.


## 2. 전체 구조

프로젝트는 크게 5개 층으로 나뉜다.

- `mail/`
  Gmail IMAP 조회, 본문 추출, 첨부 PDF 다운로드, SMTP 발송을 담당한다.
- `tasks/`
  메일에서 Task를 추출하고, To-do 여부를 판단하고, 업무 유형과 엔티티를 정리한다.
- `core/`
  긴급도 계산, 마감일 해석, 요약 생성, PDF 키워드 추출, 연관 PDF 추천 같은 공통 로직을 담당한다.
- `storage/`
  MongoDB 저장과 조회를 담당한다.
- `webapp/`
  FastAPI 라우트와 화면 렌더링을 담당한다.


## 3. 메인 실행 흐름

### 3.1 CLI 진입점

`main.py`는 두 파이프라인을 순서대로 실행한다.

- `run_inbound_pipeline()`
  신규 메일을 가져와 메일/Task/PDF를 저장한다.
- `run_outbound_pipeline()`
  완료되었지만 아직 알림을 보내지 않은 Task에 대해 완료 메일을 발송한다.

실행 순서는 다음과 같다.

1. `mail.mail_reader.fetch_target_mails()`로 최근 메일을 가져온다.
2. 각 메일의 첨부 PDF를 `mail.pdf_extractor.extract_text_from_pdf()`로 읽는다.
3. 메일 원문을 `save_mail()`로 저장한다.
4. PDF 문서를 `save_pdf_documents()`로 저장한다.
5. 메일을 `tasks.task_extractor.extract_tasks_from_mail()`로 분해한다.
6. 추출된 Task들을 `save_tasks()`로 저장한다.
7. 저장 후 `group_similar_tasks()`로 제목 유사 업무를 묶어 콘솔에서 확인한다.
8. 완료 알림 대상은 `get_completed_unnotified()`로 조회한 뒤 `send_completion_notice()`로 발송한다.


## 4. 메일 수집 로직

### 4.1 Gmail 조회

구현 파일: `mail/mail_reader.py`

`fetch_target_mails()`는 Gmail IMAP 서버에 접속해서 Inbox의 최근 메일을 검색한다.

핵심 로직:

- `IMAP4_SSL`로 Gmail에 접속
- `ALL` 검색 후 최근 50개 메일만 조회
- 각 메일마다 제목, 발신자, 수신시각, 본문, 첨부 PDF 경로를 추출
- `_is_target_mail()`로 업무 메일인지 필터링

### 4.2 제목 기반 메일 필터

업무 메일 여부는 현재 제목 말머리를 기준으로 1차 필터링한다.

설정 위치: `core/config.py`

- `SUBJECT_PATTERN = r"^\[.+\]"`
- `ALLOWED_MAIL_TAGS = ["업무요청", "업무협조", "긴급", "자료공유", "루틴", "운영", "기획"]`

즉 제목이 `[업무요청]`, `[운영]` 같은 형식이어야 통과한다.

### 4.3 메일 본문 추출

기존에는 `text/plain`만 읽었지만, 현재는 `text/html`도 fallback으로 읽는다.

구현 포인트:

- `text/plain` 파트가 있으면 우선 사용
- 없으면 `text/html` 파트를 `_html_to_text()`로 정리해서 사용
- `<br>`, `</p>`, `</div>`, `</li>` 같은 태그는 줄바꿈으로 변환
- 나머지 태그는 제거하고 공백을 정규화

이 로직 덕분에 Gmail 웹에서 수동 작성한 HTML 메일도 본문 분석이 가능해졌다.


## 5. PDF 처리 로직

### 5.1 첨부 PDF 다운로드

`mail/mail_reader.py`의 `_download_pdfs()`가 메일 파트 중 PDF 첨부만 골라 `downloads/`에 저장한다.

구현 포인트:

- `Content-Disposition`이 있는 첨부만 대상
- 파일명이 `.pdf`로 끝나야 함
- 같은 이름이 이미 있으면 `(2)`, `(3)` 같은 suffix를 붙여 중복 저장 방지

### 5.2 PDF 텍스트 추출

구현 파일: `mail/pdf_extractor.py`

`extract_text_from_pdf(pdf_path)`는 `pdfplumber`를 사용해 모든 페이지의 텍스트를 순서대로 이어 붙인다.

특징:

- 페이지별 `extract_text()` 결과를 누적
- 파일이 없거나 읽기 실패 시 빈 문자열 반환
- 파이프라인 전체를 깨지 않기 위해 예외를 잡고 로그만 출력


## 6. 메일 1건에서 Task 여러 건 추출

구현 파일: `tasks/task_extractor.py`

이 프로젝트에서 가장 중요한 설계 중 하나는 메일 1건이 Task 1건이 아니라는 점이다. `extract_tasks_from_mail()`는 메일 본문과 PDF 텍스트를 합쳐 업무 블록 단위로 분리한다.

### 6.1 입력 텍스트 구성

- `subject`
- `body`
- `pdf_files[].text`

이 중 본문과 PDF 텍스트를 `source_text`로 만들고, 제목까지 포함한 전체 문맥은 `full_text`로 만든다.

### 6.2 업무 블록 분리 기준

업무 분리는 현재 규칙 기반이다.

- `과업명:`
- `업무명:`
- `task name:`
- `task:`

같은 줄이 나오면 새 업무 블록의 시작으로 본다.

`_extract_task_blocks()`는 본문을 줄 단위로 순회하며 여러 개의 `과업명:` 블록을 분리한다.

### 6.3 업무 제목 결정

우선순위는 다음과 같다.

1. 블록 내부의 `과업명:` 또는 `업무명:` 값
2. 없으면 메일 제목에서 `[말머리]`, `(~04/30)` 같은 노이즈를 제거한 값

### 6.4 마감일 추출

각 블록에 대해 먼저 `parse_deadline_info(block, received_at)`를 호출한다.

블록 내부에서 마감일을 찾지 못하면 제목과 블록을 합친 `task_scope_text` 또는 전체 문맥으로 다시 보완한다.

### 6.5 업무 유형 분류

`_extract_task_type()`는 다음 순서를 따른다.

1. 구조화된 `업무유형:` 필드 사용
2. 없으면 `classify_task_type()` 키워드 분류 사용

### 6.6 긴급도 계산

`core.classifier.score_urgency()`를 사용한다.

입력 기준:

- 구조화된 `우선순위:`
- 자연어 긴급 키워드
- 마감일과 현재 날짜 간 남은 일수

### 6.7 요약 생성

`core.summarizer.summarize()`를 호출해 상세 화면용 1~2줄 요약을 생성한다.

### 6.8 Task ID 생성

Task ID는 아래 정보를 합쳐 MD5로 만든다.

- `mail_id`
- 블록 순서
- 제목

이렇게 하면 메일 1건 안에서 여러 Task가 생겨도 충돌을 줄일 수 있다.


## 7. To-do 판별 및 엔티티 추출

구현 파일:

- `tasks/todo_manager.py`
- `tasks/todo_analyzer.py`
- `tasks/todo_manager_adapter.py`

### 7.1 왜 어댑터가 필요한가

`todo_manager_adapter.py`는 기존 `todo_manager.py`를 최대한 보존하면서 현재 MongoDB 저장 구조와 연결하기 위한 계층이다.

역할:

- 원본 분류기 로드 시도
- 실패 시 fallback 규칙 사용
- 저장/조회는 `storage.mongo_task_store`로 위임

즉 기존 팀원의 To-do 분류 로직을 살리면서 런타임 안정성을 확보하는 용도다.

### 7.2 To-do 판별 로직

`save_todo()`는 저장 직전에 `is_actual_todo()`를 호출한다. 이 단계에서 false가 나오면 `[필터링] 비 To-Do` 로그를 남기고 저장하지 않는다.

현재 로직 특징:

1. 구조화된 업무 메일이면 우선 통과
   - `과업명:`, `업무유형:`, `마감일:`, `요청사항:` 같은 필드가 있으면 To-do로 본다.
2. 완료 보고 문맥은 걸러냄
   - `완료되었습니다`, `완료됨`, `끝냈`, `마쳤` 등은 과거 완료로 간주
3. 다만 `완료 후 공유`, `완료하기` 같은 후속 업무 문맥은 통과 가능
4. 긍정 패턴과 부정 패턴을 함께 사용
   - 긍정: `요청`, `부탁`, `확인`, `검토` 등
   - 부정: `날씨`, `점심`, `좋다` 등 일상 대화성 표현

### 7.3 업무 유형 분류

현재 분류 카테고리:

- `보고서`
- `회의`
- `검토`
- `결재`
- `개발`
- `프로젝트`
- `루틴`
- `행정`
- `기타`

분류 우선순위:

1. `업무유형:` 구조화 필드
2. `TodoAnalyzer.classify_task_type()`
3. 키워드 규칙

최근에는 `운영`, `공지`, `협조`, `요청`, `계약`, `발주`, `회의록`, `검수`, `배포` 등 회사 업무 메일에 자주 등장하는 키워드를 보강했다.

### 7.4 엔티티 추출

엔티티는 `time`, `target`, `action` 3가지다.

우선순위:

1. `TodoAnalyzer.extract_entities()`의 NER 결과
2. fallback 규칙

fallback 규칙은 아래를 추출한다.

- `과업명:` → action
- `대상:` → target
- 날짜/시간 패턴 → time


## 8. 마감일 해석 로직

구현 파일: `core/deadline_parser.py`

이 프로젝트는 마감일 해석을 한 파일로 집중시켜, 다른 모듈이 제각각 날짜를 읽지 않게 설계되어 있다.

### 8.1 파서 우선순위

`parse_deadline_info()`는 아래 순서로 시도한다.

1. 구조화된 `마감기한`, `deadline` 필드
2. 제목의 `(~04/30)` 형식
3. `YYYY-MM-DD`, `YYYY/MM/DD`, `YYYY.MM.DD`
4. `04/30`
5. `4월 30일`
6. `이번 주 금요일`, `다음 주 월요일`
7. `내일까지`, `3일 이내`

### 8.2 반환 형식

반환값은 단순 날짜 문자열이 아니라 아래 정보를 함께 가진다.

- `date`
- `time`
- `source`
- `raw_text`

이 정보는 상세 화면에서 “어떤 규칙으로 마감일이 해석됐는지” 보여주는 데도 사용된다.


## 9. 긴급도 계산 로직

구현 파일: `core/classifier.py`

`score_urgency(text, received_at, deadline="")`는 점수와 등급을 함께 계산한다.

### 9.1 점수 계산 순서

1. `우선순위: 상/중/하`가 있으면 가장 우선
2. 없으면 긴급 키워드 탐지
3. 이후 마감일이 가까우면 가산점 부여

키워드 예시:

- 강한 긴급: `즉시`, `긴급`, `ASAP`
- 높은 편: `이번 주`, `내일까지`
- 중간: `다음 주`, `이번 달`

### 9.2 마감일 기반 가산점

- 하루 이하 남음: +30
- 3일 이하: +20
- 7일 이하: +10

### 9.3 최종 등급

- `>= URGENCY_HIGH` → `긴급`
- `>= URGENCY_MID` → `보통`
- 그 외 → `상시`


## 10. 요약 생성 로직

구현 파일: `core/summarizer.py`

요약은 OpenAI API를 쓸 수 있으면 LLM 기반으로 생성하고, 키가 없거나 라이브러리가 없으면 fallback 요약을 만든다.

### 10.1 LLM 요약

사용 모델: `config.OPENAI_MODEL`

입력에는 다음을 함께 넣는다.

- 제목
- 업무명
- 업무유형
- 마감일
- 긴급도
- 원문 텍스트

또한 `_collect_summary_hints()`로 놓치기 쉬운 문장들을 미리 골라 프롬프트에 힌트로 넣는다.

힌트 예시:

- `특히`
- `추가로`
- `가능하면`
- `누락`
- `자동화`

이 설계 덕분에 본문 뒤쪽의 보조 요청이나 조건이 요약에서 빠질 가능성을 줄였다.

### 10.2 fallback 요약

LLM을 쓰지 못할 때는 제목, 마감일, 긴급도, 업무유형을 조합해 짧은 1~2줄 요약을 만든다.


## 11. MongoDB 저장 구조

구현 파일:

- `storage/mongo_task_store.py`
- `storage/database.py`

### 11.1 mails 컬렉션

메일 원문을 저장한다.

대표 필드:

- `mail_id`
- `subject`
- `mail_category`
- `sender`
- `received_at`
- `body`
- `pdf_files`
- `pdf_ids`
- `pdf_paths`
- `has_pdf`
- `pdf_count`

### 11.2 tasks 컬렉션

실제 웹 목록과 상세 화면의 기준 데이터다.

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
- `deadline_source`
- `deadline_raw_text`
- `summary`
- `source_text`
- `raw_body`
- `time_entities`
- `target_entities`
- `action_entities`
- `notified`

### 11.3 pdf_documents 컬렉션

첨부 PDF를 문서 단위로 분리해서 저장하고, 추천 기능에서 사용한다.

대표 필드:

- `pdf_id`
- `mail_id`
- `task_ids`
- `filename`
- `path`
- `text`
- `keywords`
- `keyword_count`

### 11.4 중복 방지

메일은 `mail_id(subject + sender + received_at)` 기반으로 중복 체크한다.

최근 보강된 점:

- 메일은 이미 저장되어 있어도
- 그 메일에 연결된 Task가 0건이면
- 웹 동기화 시 다시 처리할 수 있도록 `mail_has_tasks()` 조건을 추가했다.


## 12. PDF 키워드 추출과 연관 PDF 추천

구현 파일:

- `core/pdf_keywords.py`
- `core/pdf_related.py`

### 12.1 PDF 키워드 추출

`extract_pdf_keywords(text, filename)`는 PDF 텍스트와 파일명에서 키워드를 추출한다.

구현 포인트:

- 텍스트는 가중치 3
- 파일명은 가중치 1
- 조사/어미 일부를 suffix 규칙으로 정리
- 불용어 제거
- 상위 빈도 토큰 20개 선택

### 12.2 첨부 PDF 기반 추천

`find_related_pdfs(source_pdf, candidate_pdfs)`는 저장된 다른 PDF와의 연관성을 계산한다.

추천 근거:

1. 공통 키워드 겹침
2. 가능하면 `apyori` 기반 연관 규칙

현재는 `apyori`가 없어도 공통 키워드만으로 fallback 추천이 가능하도록 되어 있다.

### 12.3 메일 본문 기반 추천

`find_related_pdfs_for_text(source_text, candidate_pdfs)`는 메일 본문을 가상의 source document로 만들어 같은 추천 엔진에 넣는다.

이 기능은 최근 수정으로 현재 메일에 첨부 PDF가 없어도 동작한다. 즉 메일 본문만 있어도 저장된 다른 PDF와의 유사도를 계산할 수 있다.


## 13. 웹 애플리케이션 구조

구현 파일: `webapp/app.py`

### 13.1 `/tasks`

Task 목록 화면이다.

지원 기능:

- 검색
- 상태 필터
- 긴급도 필터
- 업무유형 필터
- 말머리 필터
- 정렬

검색은 제목, 원본 제목, 발신자, 요약, 본문을 합친 문자열에 대해 substring 방식으로 수행한다.

### 13.2 `/tasks/{task_id}`

상세 화면이다.

표시 정보:

- 제목, 상태, 긴급도, 마감일
- 요약
- 메일 원문
- 첨부 PDF 목록
- 본문 기반 연관 PDF
- 첨부 PDF별 연관 PDF
- 엔티티 정보

상세 화면은 `refresh_task_summary()`를 통해 오래된 verbose 요약을 짧은 형식으로 자동 갱신할 수도 있다.

### 13.3 `/dashboard`

`monitoring.stats.get_stats()` 결과를 렌더링한다.

### 13.4 `/sync`

웹에서 수집 파이프라인을 실행한다.

실제 로직은 `webapp/pipeline_service.py`로 분리되어 있으며, 전체 파이프라인이 중간 실패 하나로 멈추지 않도록 실패 카운트를 따로 집계한다.

### 13.5 `/settings`

`.env`에 Gmail 계정과 앱 비밀번호를 저장하고, 런타임 설정을 다시 로드한다.


## 14. 통계 로직

구현 파일: `monitoring/stats.py`

통계는 MongoDB의 `tasks` 컬렉션을 기준으로 계산한다.

제공 지표:

- 전체 업무 수
- 상태별 수
- 긴급도별 수
- 업무유형별 수
- 말머리별 수
- PDF 첨부 포함 업무 수
- 오늘 마감 업무 수
- 이번 주 마감 업무 수
- 기한 초과 업무 수

기한 초과 판정은 아래 기준이다.

- `deadline_at`이 있으면 현재 시각보다 이전인지 비교
- 없으면 `deadline_date`가 오늘보다 이전인지 비교
- 상태가 `완료`인 업무는 제외


## 15. 완료 처리와 알림 메일

구현 파일: `mail/notifier.py`

완료 버튼을 누르면:

1. `update_status(task_id, status="완료")`
2. `send_completion_notice(updated_task)`
3. 성공 시 `notified=True`로 갱신

완료 메일은 SMTP를 사용하며, 제목은 `[완료] {업무명}` 형식이다.

본문에는 아래 정보가 포함될 수 있다.

- 업무 제목
- 마감 기한
- 긴급도
- 요청 일시


## 16. 현재 구현의 장점

- 구조화된 업무 메일에 매우 강하다.
- 메일 1건에서 Task 여러 건을 추출할 수 있다.
- 마감일, 긴급도, 유형, 요약이 각각 모듈화되어 있다.
- 원본 로직을 보존하면서도 MongoDB와 웹 구조에 연결하는 어댑터 계층이 있다.
- HTML 메일 본문 fallback, 재동기화 조건 보강, PDF 추천 fallback 등 운영 중 발견된 문제를 반영해 개선되어 있다.


## 17. 현재 한계와 개선 포인트

### 17.1 To-do 추출은 아직 규칙 기반 비중이 높다

현재는 `과업명:`, `요청사항:` 같은 구조화 형식에 최적화되어 있다. 자유로운 자연어 메일만으로 업무를 안정적으로 쪼개는 능력은 아직 제한적이다.

### 17.2 PDF 추천 품질은 저장된 문서량과 키워드 품질에 좌우된다

DB에 저장된 PDF 수가 적거나, 키워드가 약하면 추천이 빈약해질 수 있다.

### 17.3 업무 유형 체계가 프로젝트 상황에 따라 더 세분화될 수 있다

예를 들어 `보안`, `구매`, `인사`, `운영` 같은 별도 유형을 두고 싶다면 `classify_task_type()` 규칙과 UI 필터를 함께 확장해야 한다.

### 17.4 검색은 단순 substring 방식이다

형태소 분석이나 full-text search가 아니기 때문에, 오타나 유의어 대응은 약하다.


## 18. 코드 읽는 순서 추천

처음 코드를 읽는 사람에게는 아래 순서를 추천한다.

1. `main.py`
2. `mail/mail_reader.py`
3. `tasks/task_extractor.py`
4. `tasks/todo_manager_adapter.py`
5. `tasks/todo_manager.py`
6. `core/deadline_parser.py`
7. `core/classifier.py`
8. `core/summarizer.py`
9. `storage/mongo_task_store.py`
10. `webapp/app.py`
11. `core/pdf_related.py`

이 순서로 보면 메일이 들어와서 화면에 보이기까지의 흐름이 가장 자연스럽게 이어진다.


## 19. 한 줄 요약

미니 프로젝트 2는 “업무 메일을 구조적으로 읽고, 업무 단위로 쪼개고, 마감/긴급도/요약/PDF 추천까지 붙여 웹에서 관리하는 메일 기반 Task 자동화 시스템”이다.
