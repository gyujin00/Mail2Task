"""
담당: 규진 차
역할: Gmail IMAP 접속 → [업무협조] 메일 필터링 → PDF 첨부파일 다운로드
      (핵심 수집 및 추출 기능 - 기본)
"""
import imaplib
import email
from email.header import decode_header
from email.utils import parseaddr, parsedate_to_datetime
import os
import re
import config


def fetch_target_mails():
    """
    [업무협조] 키워드가 포함된 메일을 수신하여 반환한다.

    반환: list[dict], 각 dict의 키:
        - subject    (str): 메일 제목
        - sender     (str): 발신자 이메일
        - body       (str): 메일 본문 텍스트
        - pdf_paths  (list[str]): 다운로드된 PDF 파일 경로 목록
        - received_at(str): 수신 일시 "YYYY-MM-DD HH:MM"
    """
    os.makedirs(config.SAVE_DIR, exist_ok=True)
    results = []

    mail = imaplib.IMAP4_SSL(config.IMAP_SERVER)
    mail.login(config.EMAIL, config.PASSWORD)
    mail.select("inbox")

    _, data = mail.search(None, "ALL")
    mail_ids = data[0].split()[-50:]  # 최근 50개만 확인

    print(f"최근 {len(mail_ids)}개 메일 검색 중...")
    for mail_id in reversed(mail_ids):
        _, data = mail.fetch(mail_id, "(RFC822)")
        msg = email.message_from_bytes(data[0][1])

        subject = _decode_str(msg["Subject"])
        if not re.search(config.SUBJECT_PATTERN, subject):
            continue

        sender = parseaddr(msg["From"])[1]
        received_at = _parse_date(msg["Date"])
        body = _extract_body(msg)
        pdf_paths = _download_pdfs(msg)

        results.append({
            "subject":     subject,
            "sender":      sender,
            "body":        body,
            "pdf_paths":   pdf_paths,
            "received_at": received_at,
        })

    mail.logout()
    return results


def _decode_str(value):
    """인코딩된 메일 헤더 문자열을 디코딩한다."""
    if not value:
        return ""
    decoded, encoding = decode_header(value)[0]
    if isinstance(decoded, bytes):
        return decoded.decode(encoding or "utf-8", errors="replace")
    return decoded


def _parse_date(date_str):
    """메일 Date 헤더를 'YYYY-MM-DD HH:MM' 형식으로 변환한다."""
    try:
        dt = parsedate_to_datetime(date_str)
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return ""


def _extract_body(msg):
    """멀티파트 메일에서 text/plain 본문을 추출한다."""
    body = ""
    for part in msg.walk():
        if part.get_content_type() == "text/plain" and not part.get_filename():
            charset = part.get_content_charset() or "utf-8"
            body += part.get_payload(decode=True).decode(charset, errors="replace")
    return body


def _download_pdfs(msg):
    """msg에서 PDF 첨부파일을 downloads/ 폴더에 저장하고 경로 목록을 반환한다."""
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

        filepath = os.path.join(config.SAVE_DIR, filename)
        with open(filepath, "wb") as f:
            f.write(part.get_payload(decode=True))
        pdf_paths.append(filepath)

    return pdf_paths
