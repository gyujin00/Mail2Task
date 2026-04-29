from __future__ import annotations

import mimetypes
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from core import config
from core.pdf_related import find_related_pdfs, find_related_pdfs_for_text
from mail.mail_reader import fetch_target_mails
from mail.notifier import send_completion_notice
from monitoring.stats import get_stats
from tasks.todo_manager_adapter import update_status

from .env_service import (
    EnvStatus,
    get_env_status,
    mask_secret,
    reload_runtime_config,
    upsert_env_values,
)
from .pipeline_service import sync_inbound
from .repositories import (
    get_mail,
    get_task,
    list_pdfs,
    list_pdfs_by_mail,
    list_tasks,
    refresh_task_summary,
)


BASE_DIR = Path(__file__).resolve().parent
DOWNLOADS_DIR = Path(config.SAVE_DIR)

# The web layer stays thin on purpose and delegates most business logic
# to the existing mail/pipeline modules.
app = FastAPI(title="Mail2Task Web")

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

static_dir = BASE_DIR / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    del request
    return RedirectResponse(url="/tasks", status_code=303)


@app.get("/settings", response_class=HTMLResponse)
def settings_page(request: Request):
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
    """Save mail credentials to `.env` and reload runtime config."""
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
                "error": "Gmail 주소를 입력해주세요.",
            },
            status_code=400,
        )

    values = {"TASK_EMAIL": email}
    if app_password:
        values["TASK_PASSWORD"] = app_password

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
        reload_runtime_config()
        if not config.EMAIL or not config.PASSWORD:
            raise RuntimeError("메일 계정 정보가 설정되지 않았습니다.")

        # Test only the mail connection here. Full sync stays behind `/sync`.
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
    except Exception as exc:
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
                "error": f"메일 연결 테스트 실패: {exc}",
            },
            status_code=400,
        )


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
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
    sort: str | None = "urgency",
):
    tasks = list_tasks()

    def _matches(task: dict) -> bool:
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

    filtered = [task for task in tasks if _matches(task)]

    def _deadline_key(task: dict):
        # Push items without a deadline to the end of deadline sorting.
        return (task.get("deadline_date") or "9999-12-31", task.get("deadline_time") or "")

    def _latest_key(task: dict):
        return task.get("received_at") or ""

    if sort == "deadline":
        filtered.sort(key=_deadline_key)
    elif sort == "urgency":
        filtered.sort(
            key=lambda task: (int(task.get("urgency_score") or 0), _latest_key(task)),
            reverse=True,
        )
    else:
        filtered.sort(key=_latest_key, reverse=True)

    def _uniq(key: str):
        values = []
        for task in tasks:
            value = task.get(key) or "미분류"
            if value not in values:
                values.append(value)
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
            "sort": sort or "urgency",
        },
    )


@app.get("/tasks/{task_id}", response_class=HTMLResponse)
def task_detail(request: Request, task_id: str):
    task = get_task(task_id)
    if not task:
        return templates.TemplateResponse(
            request,
            "error.html",
            {"error": "업무(Task)를 찾을 수 없습니다."},
            status_code=404,
        )

    mail = get_mail(task.get("mail_id", "")) if task.get("mail_id") else None
    pdf_documents = list_pdfs_by_mail(task.get("mail_id", "")) if task.get("mail_id") else []
    related_pdfs = {}
    attached_pdfs = []
    body_related_pdfs = []
    if pdf_documents:
        other_pdfs = list_pdfs(
            exclude_pdf_ids=[pdf.get("pdf_id", "") for pdf in pdf_documents if pdf.get("pdf_id")],
            limit=200,
        )
        for pdf_document in pdf_documents:
            related_pdfs[pdf_document.get("pdf_id", "")] = find_related_pdfs(
                pdf_document,
                other_pdfs,
                limit=5,
            )
        body_source_text = (mail.get("body", "") if mail else "") or task.get("raw_body", "")
        if body_source_text.strip():
            body_related_pdfs = find_related_pdfs_for_text(
                body_source_text,
                other_pdfs,
                limit=5,
                source_name=f"mail-body-{task.get('task_id', '')}",
            )
    if mail and mail.get("pdf_files"):
        pdf_by_filename = {
            pdf.get("filename", ""): pdf
            for pdf in pdf_documents
            if pdf.get("filename")
        }
        for pdf_file in mail.get("pdf_files", []):
            filename = pdf_file.get("filename", "")
            matched_pdf = pdf_by_filename.get(filename)
            attached_pdfs.append(
                {
                    "filename": filename,
                    "pdf_id": matched_pdf.get("pdf_id", "") if matched_pdf else "",
                    "related": related_pdfs.get(matched_pdf.get("pdf_id", ""), []) if matched_pdf else [],
                }
            )
    task = refresh_task_summary(task, mail)
    return templates.TemplateResponse(
        request,
        "task_detail.html",
        {
            "task": task,
            "mail": mail,
            "pdf_documents": pdf_documents,
            "related_pdfs": related_pdfs,
            "attached_pdfs": attached_pdfs,
            "body_related_pdfs": body_related_pdfs,
        },
    )


@app.post("/tasks/{task_id}/complete", response_class=HTMLResponse)
def task_complete(request: Request, task_id: str):
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
        reload_runtime_config()

        updated_task = get_task(task_id)
        if updated_task and send_completion_notice(updated_task):
            update_status(task_id, notified=True)

        updated = get_task(task_id)
        done = bool(updated and updated.get("notified") is True)
        return RedirectResponse(url=f"/tasks/{task_id}?done={1 if done else 0}", status_code=303)
    except Exception as exc:
        return templates.TemplateResponse(
            request,
            "error.html",
            {"error": f"완료 처리 실패: {exc}"},
            status_code=400,
        )


@app.post("/sync", response_class=HTMLResponse)
def sync_now(request: Request):
    try:
        reload_runtime_config()
        result = sync_inbound()
        return templates.TemplateResponse(
            request,
            "sync_result.html",
            {"result": result},
        )
    except Exception as exc:
        return templates.TemplateResponse(
            request,
            "error.html",
            {"error": f"메일 동기화 실패: {exc}"},
            status_code=400,
        )


@app.get("/downloads/{mail_id}/{filename}")
def download_pdf(mail_id: str, filename: str):
    """Use the stored attachment paths as an allow-list for safe downloads."""
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
