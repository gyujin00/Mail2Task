from __future__ import annotations

import mimetypes
from datetime import date, datetime, timedelta
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import config
from mail_reader import fetch_target_mails
from stats import get_stats
from todo_manager_adapter import update_status

from .env_service import EnvStatus, get_env_status, mask_secret, upsert_env_values
from .pipeline_service import sync_inbound
from .repositories import get_mail, get_task, list_tasks


BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
DOWNLOADS_DIR = Path(config.SAVE_DIR)

# 웹 UI는 “기존 파이프라인을 그대로 호출”하는 얇은 레이어다.
# - 메일 수집/Task 추출/통계/알림은 기존 모듈을 직접 재사용한다.
# - 이 파일은 라우팅(Jinja2 렌더링)과 사용자 입력(.env 저장)만 담당한다.
app = FastAPI(title="Mail2Task Web")

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

static_dir = BASE_DIR / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


def _today_range():
    """대시보드 확장 시(예: 오늘/주간 필터)용 날짜 범위 유틸."""
    today = date.today()
    start = datetime(today.year, today.month, today.day)
    end = start + timedelta(days=1)
    return start, end


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    # 메인은 To-do 리스트로 진입(실사용 흐름 우선)
    return RedirectResponse(url="/tasks", status_code=303)


@app.get("/settings", response_class=HTMLResponse)
def settings_page(request: Request):
    # 보안: 실제 비밀번호는 노출하지 않고 “설정됨 여부 + 마스킹”만 보여준다.
    status: EnvStatus = get_env_status()
    masked_pw = mask_secret(config.PASSWORD, keep_last=2) if status.has_password else ""
    return templates.TemplateResponse(
        request,
        "settings.html",
        {
            "email": status.email,
            "has_password": status.has_password,
            "masked_password": masked_pw,
            "message": None,
            "error": None,
        },
    )


@app.post("/settings/save", response_class=HTMLResponse)
def settings_save(
    request: Request,
    email: str = Form(""),
    app_password: str = Form(""),
):
    """
    설정 저장:
    - TASK_EMAIL은 항상 갱신
    - TASK_PASSWORD는 공란이면 “기존값 유지”(재노출/자동 덮어쓰기 방지)
    """
    email = (email or "").strip()
    app_password = (app_password or "").strip()

    if not email:
        status = get_env_status()
        return templates.TemplateResponse(
            request,
            "settings.html",
            {
                "email": status.email,
                "has_password": status.has_password,
                "masked_password": mask_secret(config.PASSWORD, keep_last=2)
                if status.has_password
                else "",
                "message": None,
                "error": "Gmail 주소를 입력하세요.",
            },
            status_code=400,
        )

    values = {"TASK_EMAIL": email}
    # 비밀번호는 공란이면 기존값 유지
    if app_password:
        values["TASK_PASSWORD"] = app_password

    # .env 갱신 후 config를 reload해서 웹에서 즉시 적용되도록 한다.
    upsert_env_values(values)
    status = get_env_status()
    return templates.TemplateResponse(
        request,
        "settings.html",
        {
            "email": status.email,
            "has_password": status.has_password,
            "masked_password": mask_secret(config.PASSWORD, keep_last=2)
            if status.has_password
            else "",
            "message": "설정이 저장되었습니다.",
            "error": None,
        },
    )


@app.post("/settings/test", response_class=HTMLResponse)
def settings_test(request: Request):
    try:
        if not config.EMAIL or not config.PASSWORD:
            raise RuntimeError("메일 계정 정보가 설정되지 않았습니다.")
        # 테스트는 “실제 수집 파이프라인”이 아니라,
        # IMAP 접속 + 최근 메일 조회 가능 여부까지만 확인한다.
        _ = fetch_target_mails()
        status = get_env_status()
        return templates.TemplateResponse(
            request,
            "settings.html",
            {
                "email": status.email,
                "has_password": status.has_password,
                "masked_password": mask_secret(config.PASSWORD, keep_last=2)
                if status.has_password
                else "",
                "message": "메일 연결 테스트 성공 (최근 메일 조회 가능).",
                "error": None,
            },
        )
    except Exception as e:
        status = get_env_status()
        return templates.TemplateResponse(
            request,
            "settings.html",
            {
                "email": status.email,
                "has_password": status.has_password,
                "masked_password": mask_secret(config.PASSWORD, keep_last=2)
                if status.has_password
                else "",
                "message": None,
                "error": f"메일 연결 테스트 실패: {e}",
            },
            status_code=400,
        )


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    # 통계는 반드시 tasks 기준으로 계산(기존 stats.get_stats 재사용)
    stats = get_stats()
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {"stats": stats},
    )


@app.get("/tasks", response_class=HTMLResponse)
def tasks_page(
    request: Request,
    q: str | None = None,
    status: str | None = None,
    urgency: str | None = None,
    task_type: str | None = None,
    category: str | None = None,
    sort: str | None = "latest",
):
    # 리스트는 “tasks 컬렉션”을 기준으로 제공한다.
    # (메일 1건에서 task N건이 나오는 구조 유지)
    tasks = list_tasks()

    def _matches(task: dict) -> bool:
        # 필터는 단순/명시적 규칙으로 구성(유지보수/현업 사용성 우선)
        if status and (task.get("status") or "미분류") != status:
            return False
        if urgency and (task.get("urgency_level") or "미분류") != urgency:
            return False
        if task_type and (task.get("task_type") or "미분류") != task_type:
            return False
        if category and (task.get("mail_category") or "미분류") != category:
            return False
        if q:
            needle = q.strip().lower()
            hay = " ".join(
                [
                    str(task.get("title") or ""),
                    str(task.get("subject") or ""),
                    str(task.get("sender") or ""),
                    str(task.get("summary") or ""),
                    str(task.get("raw_body") or ""),
                ]
            ).lower()
            if needle not in hay:
                return False
        return True

    filtered = [t for t in tasks if _matches(t)]

    def _deadline_key(task: dict):
        # 마감일이 없는 업무는 항상 뒤로 보내기 위해 9999-12-31을 사용한다.
        return (task.get("deadline_date") or "9999-12-31", task.get("deadline_time") or "")

    if sort == "deadline":
        filtered.sort(key=_deadline_key)
    elif sort == "urgency":
        filtered.sort(key=lambda t: int(t.get("urgency_score") or 0), reverse=True)
    else:  # latest
        filtered.sort(key=lambda t: (t.get("received_at") or ""), reverse=True)

    # 필터 옵션 생성
    def _uniq(key: str):
        # UI 선택지용 유니크 값 목록(등장 순서를 유지해 사용자가 자연스럽게 보게 함)
        values = []
        for t in tasks:
            v = t.get(key) or "미분류"
            if v not in values:
                values.append(v)
        return values

    options = {
        "statuses": _uniq("status"),
        "urgencies": _uniq("urgency_level"),
        "types": _uniq("task_type"),
        "categories": _uniq("mail_category"),
    }

    return templates.TemplateResponse(
        request,
        "tasks.html",
        {
            "tasks": filtered,
            "options": options,
            "q": q or "",
            "status": status or "",
            "urgency": urgency or "",
            "task_type": task_type or "",
            "category": category or "",
            "sort": sort or "latest",
        },
    )


@app.get("/tasks/{task_id}", response_class=HTMLResponse)
def task_detail(request: Request, task_id: str):
    # 상세 페이지는 task 문서 + (가능하면) mails 문서를 함께 보여준다.
    task = get_task(task_id)
    if not task:
        return templates.TemplateResponse(
            request,
            "error.html",
            {"error": "업무(Task)를 찾을 수 없습니다."},
            status_code=404,
        )
    mail = get_mail(task.get("mail_id", "")) if task.get("mail_id") else None
    return templates.TemplateResponse(
        request,
        "task_detail.html",
        {"task": task, "mail": mail},
    )


@app.post("/tasks/{task_id}/complete", response_class=HTMLResponse)
def task_complete(request: Request, task_id: str):
    """
    완료 처리:
    1) tasks.status를 '완료'로 변경
    2) 기존 outbound(완료 알림 발송) 파이프라인을 재사용해 메일 발송
    3) 발송 성공 시 tasks.notified=True로 마킹(중복 발송 방지)
    """
    task = get_task(task_id)
    if not task:
        return templates.TemplateResponse(
            request,
            "error.html",
            {"error": "업무(Task)를 찾을 수 없습니다."},
            status_code=404,
        )

    try:
        update_status(task_id, status="완료")
        # dev 쪽의 “완료 알림 발송” 로직(필터/데이터 모양/전송 조건)이 계속 바뀔 수 있으므로,
        # 웹에서는 status만 바꾼 뒤 메인 outbound 파이프라인을 그대로 호출한다.
        #
        # - 이 함수는 완료 + 미통지(notified=False) 태스크를 찾아 notifier로 메일을 보낸다.
        # - 성공 시 tasks.notified=True로 업데이트한다.
        from main import run_outbound_pipeline

        run_outbound_pipeline()

        updated = get_task(task_id)
        done = bool(updated and updated.get("notified") is True)
        return RedirectResponse(url=f"/tasks/{task_id}?done={1 if done else 0}", status_code=303)
    except Exception as e:
        return templates.TemplateResponse(
            request,
            "error.html",
            {"error": f"완료 처리 실패: {e}"},
            status_code=400,
        )


@app.post("/sync", response_class=HTMLResponse)
def sync_now(request: Request):
    # 상단 “메일 새로 불러오기” 버튼이 호출하는 엔드포인트.
    # 내부는 기존 수신 파이프라인을 웹용 서비스에서 그대로 재사용한다.
    try:
        result = sync_inbound()
        return templates.TemplateResponse(
            request,
            "sync_result.html",
            {"result": result},
        )
    except Exception as e:
        return templates.TemplateResponse(
            request,
            "error.html",
            {"error": f"메일 동기화 실패: {e}"},
            status_code=400,
        )


@app.get("/downloads/{mail_id}/{filename}")
def download_pdf(mail_id: str, filename: str):
    """
    첨부 PDF 다운로드:
    - mails 문서에 저장된 pdf_paths 목록을 allow-list로 사용해 경로 조작(path traversal)을 막는다.
    """
    mail = get_mail(mail_id)
    if not mail:
        return HTMLResponse("메일을 찾을 수 없습니다.", status_code=404)

    allowed_paths = set()
    for path in mail.get("pdf_paths", []) or []:
        try:
            allowed_paths.add(str(Path(path).resolve()))
        except Exception:
            continue

    candidate = (DOWNLOADS_DIR / filename).resolve()
    if str(candidate) not in allowed_paths or not candidate.exists():
        return HTMLResponse("첨부 파일을 찾을 수 없습니다.", status_code=404)

    content_type, _ = mimetypes.guess_type(str(candidate))
    return FileResponse(
        str(candidate),
        media_type=content_type or "application/pdf",
        filename=filename,
    )

