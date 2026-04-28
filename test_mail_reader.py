# ============================================================
# mail_reader.py 테스트 스크립트
# ============================================================
# 사전 준비
#   1. Gmail 앱 비밀번호 발급
#      Google 계정 → 보안 → "앱 비밀번호" 검색 → 생성 (16자리 복사)
#
#   2. 환경변수 설정 (이 터미널에서 실행 전 입력)
#      set TASK_EMAIL=본인Gmail@gmail.com
#      set TASK_PASSWORD=앱비밀번호16자리
#
#   3. 테스트 메일 발송 (본인에게)
#      제목: [업무요청] 브랜드 리뉴얼 건 (~05/02)
#      본문 예시:
#        - 과업명: 로고 시안 확정
#        - 마감기한: 2026-05-02 (토) 16:00
#        - 업무유형: 프로젝트
#        - 우선순위: 상
#
#   4. 실행
#      python test_mail_reader.py
#
# 정상 출력 예시
#   수신된 업무 메일: 1건
#   제목:     [업무요청] 브랜드 리뉴얼 건 (~05/02)
#   발신자:   your@gmail.com
#   긴급도:   긴급(80점) | 마감: 2026-05-02
# ============================================================

import config

# 환경변수 확인
print(f"EMAIL 설정 여부: {'O' if config.EMAIL else 'X (환경변수 TASK_EMAIL 미설정)'}")
print(f"PASSWORD 설정 여부: {'O' if config.PASSWORD else 'X (환경변수 TASK_PASSWORD 미설정)'}")

if not config.EMAIL or not config.PASSWORD:
    print("\n[오류] 환경변수를 먼저 설정하세요.")
    print("  set TASK_EMAIL=본인Gmail@gmail.com")
    print("  set TASK_PASSWORD=앱비밀번호16자리")
    exit(1)

from mail_reader import fetch_target_mails
from classifier import score_urgency

try:
    mails = fetch_target_mails()
    print(f"\n수신된 업무 메일: {len(mails)}건")

    if not mails:
        print("→ [업무요청] 형식 제목의 메일이 없습니다. 테스트 메일을 보내고 다시 실행하세요.")

    for m in mails:
        print("─" * 40)
        print(f"제목:        {m['subject']}")
        print(f"발신자:      {m['sender']}")
        print(f"수신일시:    {m['received_at']}")
        print(f"본문 앞부분: {m['body'][:80]}")
        print(f"PDF 파일:    {m['pdf_paths']}")

        score, level, deadline = score_urgency(m['body'], m['received_at'])
        print(f"긴급도:      {level}({score}점) | 마감: {deadline}")

except Exception as e:
    print(f"\n[오류] {e}")
