"""
담당: 승민 홍
역할: Gmail IMAP 접속 → [업무협조] 메일 필터링 → PDF 첨부파일 다운로드
"""
import imaplib
import email
from email.header import decode_header
import os
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

    # TODO: 메일 검색 → [업무협조] 필터링 → PDF 다운로드 → results에 추가
    # 아래 구조를 참고해서 구현하세요.
    #
    # result, data = mail.search(None, "ALL")
    # for mail_id in reversed(data[0].split()):
    #     msg = ...fetch and parse...
    #     if config.KEYWORD_FILTER in subject:
    #         pdf_paths = _download_pdfs(msg)
    #         results.append({
    #             "subject": subject,
    #             "sender": sender,
    #             "body": body,
    #             "pdf_paths": pdf_paths,
    #             "received_at": received_at,  # "YYYY-MM-DD HH:MM" 형식
    #         })

    mail.logout()
    return results


def _download_pdfs(msg):
    """msg에서 PDF 첨부파일을 downloads/ 폴더에 저장하고 경로 목록을 반환한다."""
    pdf_paths = []

    # TODO: msg.walk()로 첨부파일 순회 → .pdf 파일 저장
    # 강의안 3/4 슬라이드 코드 참고

    return pdf_paths
