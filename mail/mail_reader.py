"""Gmail IMAP reader and attachment downloader for inbound task mail."""

from __future__ import annotations

import email
import imaplib
import os
import re
from email.header import decode_header
from email.utils import parseaddr, parsedate_to_datetime
from pathlib import Path

from core import config


def fetch_target_mails():
    """
    Fetch recent task-related mails and download attached PDFs.

    Returns a list of dict objects containing subject, sender, body, PDF paths,
    and received timestamp text.
    """
    os.makedirs(config.SAVE_DIR, exist_ok=True)
    results = []

    mail = imaplib.IMAP4_SSL(config.IMAP_SERVER)
    mail.login(config.EMAIL, config.PASSWORD)
    mail.select("inbox")

    _, data = mail.search(None, "ALL")
    mail_ids = data[0].split()[-50:]

    print(f"최근 {len(mail_ids)}개 메일 검색 중...")
    for mail_id in reversed(mail_ids):
        _, data = mail.fetch(mail_id, "(RFC822)")
        msg = email.message_from_bytes(data[0][1])

        subject = _decode_str(msg["Subject"])
        sender = parseaddr(msg["From"])[1]
        received_at = _parse_date(msg["Date"])
        body = _extract_body(msg)
        if not _is_target_mail(subject, body):
            continue

        pdf_paths = _download_pdfs(msg)
        results.append(
            {
                "subject": subject,
                "sender": sender,
                "body": body,
                "pdf_paths": pdf_paths,
                "received_at": received_at,
            }
        )

    mail.logout()
    return results


def _decode_str(value):
    """Decode an encoded mail header value."""
    if not value:
        return ""
    decoded, encoding = decode_header(value)[0]
    if isinstance(decoded, bytes):
        return decoded.decode(encoding or "utf-8", errors="replace")
    return decoded


def _parse_date(date_str):
    """Convert a mail Date header into `YYYY-MM-DD HH:MM` text."""
    try:
        dt = parsedate_to_datetime(date_str)
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return ""


def _extract_body(msg):
    """Extract the plain-text body from a multipart mail message."""
    body = ""
    for part in msg.walk():
        if part.get_content_type() == "text/plain" and not part.get_filename():
            charset = part.get_content_charset() or "utf-8"
            body += part.get_payload(decode=True).decode(charset, errors="replace")
    return body


def _is_target_mail(subject, body):
    """Treat bracketed work mail as inbound tasks, except completion notices."""
    normalized_subject = (subject or "").strip().lower()
    if normalized_subject.startswith("[완료]"):
        return False

    if re.search(config.SUBJECT_PATTERN, subject or ""):
        return True

    text = "\n".join(part for part in [subject, body] if part).lower()
    task_keywords = (
        "업무",
        "과업",
        "요청",
        "마감",
        "task",
        "todo",
        "deadline",
    )
    return any(keyword in text for keyword in task_keywords)


def _download_pdfs(msg):
    """Download attached PDF files and return their saved paths."""
    pdf_paths = []

    for part in msg.walk():
        if part.get("Content-Disposition") is None:
            continue
        filename = part.get_filename()
        if not filename:
            continue

        filename = _decode_str(filename)
        if not filename.lower().endswith(".pdf"):
            continue

        filepath = _build_unique_pdf_path(filename)
        with open(filepath, "wb") as file_handle:
            file_handle.write(part.get_payload(decode=True))
        pdf_paths.append(filepath)

    return pdf_paths


def _build_unique_pdf_path(filename):
    """Create a unique file path by appending numeric suffixes when needed."""
    candidate = Path(config.SAVE_DIR) / filename
    if not candidate.exists():
        return str(candidate)

    stem = candidate.stem
    suffix = candidate.suffix
    index = 2

    while True:
        renamed = candidate.with_name(f"{stem} ({index}){suffix}")
        if not renamed.exists():
            return str(renamed)
        index += 1
