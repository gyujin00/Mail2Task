from __future__ import annotations

import shutil
import uuid
from email.message import EmailMessage
from pathlib import Path

try:
    from tests._bootstrap import ROOT_DIR
except ModuleNotFoundError:
    from _bootstrap import ROOT_DIR

from core import config
from core.classifier import score_urgency
from core.deadline_parser import parse_deadline
from mail.mail_reader import _download_pdfs, _is_target_mail, fetch_target_mails


def _safe_console_text(value: str) -> str:
    """Avoid crashing on Windows terminals that cannot render some symbols."""
    return str(value).encode("cp949", errors="replace").decode("cp949")


def main() -> int:
    print(f"EMAIL configured: {'O' if config.EMAIL else 'X'}")
    print(f"PASSWORD configured: {'O' if config.PASSWORD else 'X'}")

    if not config.EMAIL or not config.PASSWORD:
        print("\n[ERROR] Set TASK_EMAIL and TASK_PASSWORD in .env first.")
        return 1

    mails = fetch_target_mails()
    print(f"\nFetched mails: {len(mails)}")

    if not mails:
        print("No matching mail found.")
        return 0

    for mail in mails:
        full_text = "\n".join(part for part in [mail["subject"], mail["body"]] if part)
        deadline = parse_deadline(full_text, mail["received_at"])
        score, level, deadline = score_urgency(
            full_text,
            mail["received_at"],
            deadline=deadline,
        )

        print("-" * 40)
        print(f"Subject:       {_safe_console_text(mail['subject'])}")
        print(f"Sender:        {_safe_console_text(mail['sender'])}")
        print(f"Received at:   {_safe_console_text(mail['received_at'])}")
        print(f"Body preview:  {_safe_console_text(mail['body'][:80])}")
        print(f"PDF files:     {_safe_console_text(mail['pdf_paths'])}")
        print(
            f"Urgency:       {_safe_console_text(level)} ({score}) | "
            f"Deadline: {_safe_console_text(deadline)}"
        )

    return 0


def test_pdf_filename_collision() -> int:
    """Ensure duplicate PDF names get a numeric suffix instead of overwriting."""
    temp_dir = ROOT_DIR / "downloads" / f"_mail_reader_collision_{uuid.uuid4().hex}"
    original_save_dir = config.SAVE_DIR

    try:
        shutil.rmtree(temp_dir, ignore_errors=True)
        temp_dir.mkdir(parents=True, exist_ok=True)
        config.SAVE_DIR = str(temp_dir)

        paths = []
        for content in (b"first", b"second", b"third"):
            msg = EmailMessage()
            msg.add_attachment(
                content,
                maintype="application",
                subtype="pdf",
                filename="report.pdf",
            )
            paths.extend(_download_pdfs(msg))

        names = [Path(path).name for path in paths]
        expected = ["report.pdf", "report (2).pdf", "report (3).pdf"]

        print("\n[Collision Test]")
        print(f"saved:    {names}")
        print(f"expected: {expected}")
        return 0 if names == expected else 1
    finally:
        config.SAVE_DIR = original_save_dir
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_target_mail_detection() -> None:
    """Completion notices should be excluded while task mail is still detected."""
    assert _is_target_mail("[업무요청] 로고 수정 검토", "")
    assert _is_target_mail("디자인 검토 요청", "이번 주 마감입니다.")
    assert not _is_target_mail("[완료] package regroup verify", "완료 메일입니다.")
    assert not _is_target_mail("점심 메뉴 투표", "오늘 뭐 먹을까요?")


if __name__ == "__main__":
    raise SystemExit(main())
