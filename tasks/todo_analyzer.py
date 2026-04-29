from __future__ import annotations
from transformers import pipeline

class TodoAnalyzer:
    def __init__(self, model_name: str = "klue/bert-base"):
        self.model_name = model_name
        self._ner_pipeline = None
        
        # 기존 패턴 로직 그대로 유지
        self.NEGATIVE_PATTERNS = [
            "좋다", "춥다", "덥다", "행복", "피곤", "힘들", "재미", "지루", "슬프", "기분", 
            "느낌", "아프", "졸리", "점심", "저녁", "아침", "커피", "밥", "식사", "날씨", 
            "운동", "게임", "영화", "음악", "쉬", "자다", "퇴근", "출근", "집", "귀가", "외출"
        ]
        self.POSITIVE_PATTERNS = [
            "해야", "하자", "할 것", "할게", "합시다", "부탁", "요청", "바랍니다", "부탁드립니다", 
            "드립니다", "확인", "검토", "리뷰", "점검", "진행", "작성", "제출", "준비", "참석", 
            "예약", "필요", "처리", "수행", "조치", "공유", "전달", "보고", "회신", "답변", 
            "승인", "결재", "까지", "이내", "전까지", "내일", "오늘", "이번 주", "다음 주", 
            "금요일", "월요일", "회의", "보고서", "문서", "자료", "기획", "개발", "테스트", "배포",
            "미팅", "발표", "운영", "공지", "안내", "협조", "관리", "신청", "등록", "계약", "발주"
        ]
        self.PAST_PATTERNS = [
            "했다", "했어", "했습니다", "했음", "완료했", "완료됨", "완료되었습니다", "완료됐습니다", "끝냈", 
            "끝남", "마쳤", "마침", "수행함", "수행했", "처리했", "진행했", "작성했", "제출했", "참석했"
        ]
        self.TYPE_RULES = {
            "보고서": [
                "보고서", "작성", "문서", "자료", "초안", "최종안", "기안", "작성본",
                "첨부", "정리", "취합", "제출자료", "발표자료", "공유자료",
            ],
            "회의": [
                "회의", "미팅", "협의", "논의", "회의실", "안건", "회의록", "참석",
                "참여", "일정 조율", "인터뷰", "브리핑", "킥오프",
            ],
            "검토": [
                "검토", "리뷰", "확인", "피드백", "의견", "코멘트", "재검토", "점검",
                "검수", "보완", "수정 요청", "검토 요청",
            ],
            "결재": [
                "결재", "승인", "전결", "품의", "기안", "상신", "재가", "결재 요청",
                "승인 요청", "전표", "처리 승인",
            ],
            "개발": [
                "개발", "코드", "패치", "배포", "빌드", "테스트", "디버깅", "버그",
                "수정", "개선", "기능", "API", "서버", "앱", "시스템", "장애",
            ],
            "프로젝트": [
                "프로젝트", "시안", "구축", "런칭", "오픈", "고도화", "일정", "마일스톤",
                "산출물", "범위", "과업", "착수", "제안", "제안서", "PM", "WBS",
            ],
            "루틴": [
                "정기", "매일", "매주", "반복", "월간", "주간", "분기", "반기",
                "연간", "상시", "주기", "데일리", "정례",
            ],
            "행정": [
                "행정", "정산", "결산", "비품", "증빙", "보고", "운영", "관리", "신청",
                "등록", "접수", "발급", "갱신", "공지", "안내", "협조", "요청",
                "전달", "회신", "응답", "문의", "출장", "휴가", "근태", "비용",
                "예산", "세금계산서", "계약", "구매", "발주", "입금", "지출",
            ],
        }

    def _load_ner(self):
        """모델 지연 로딩"""
        if self._ner_pipeline is None:
            self._ner_pipeline = pipeline(
                "ner", 
                model=self.model_name, 
                aggregation_strategy="simple"
            )
        return self._ner_pipeline

    def is_actual_todo(self, text: str) -> bool:
        """기존 To-do 판별 로직"""
        if not text or len(text.strip()) < 3:
            return False

        structured_markers = [
            "과업명:", "업무명:", "업무유형:", "마감일:", "마감기한:", "요청사항:",
            "대상:", "우선순위:",
        ]
        if any(marker in text for marker in structured_markers):
            return True
            
        # 1. 강화된 룰 필터
        if any(p in text for p in self.PAST_PATTERNS): return False
        if "완료" in text and not any(
            marker in text for marker in ("완료 후", "완료시", "완료 시", "완료하면", "완료하기")
        ):
            if not any(p in text for p in self.POSITIVE_PATTERNS):
                return False
        if text.strip().endswith("?"): return False
        if sum(1 for p in self.NEGATIVE_PATTERNS if p in text) >= 2: return False
        if sum(1 for p in self.POSITIVE_PATTERNS if p in text) >= 2: return True
        
        # 2. 점수 기반 필터
        score = sum(2 for p in self.POSITIVE_PATTERNS if p in text) - \
                sum(3 for p in self.NEGATIVE_PATTERNS if p in text)
        return score >= 3

    def classify_task_type(self, text: str) -> str:
        """기존 유형 분류 로직"""
        for label, keywords in self.TYPE_RULES.items():
            if any(k in text for k in keywords):
                return label
        return "기타"

    def extract_entities(self, text: str) -> dict:
        """기존 NER 추출 로직"""
        try:
            results = self._load_ner()(text)
            extracted = {"time": [], "target": [], "action": []}
            for r in results:
                label, word = r["entity_group"], r["word"]
                if label in ["DAT", "TIM"]:
                    extracted["time"].append(word)
                elif label in ["ORG", "LOC"]:
                    extracted["target"].append(word)
                else:
                    extracted["action"].append(word)
            return extracted
        except:
            return {"time": [], "target": [], "action": []}

    def analyze(self, text: str) -> dict | None:
        """통합 분석 메서드 (To-do일 경우만 결과 반환)"""
        if not self.is_actual_todo(text):
            return None
            
        return {
            "task_type": self.classify_task_type(text),
            "entities": self.extract_entities(text)
        }
