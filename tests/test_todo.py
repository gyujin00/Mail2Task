from __future__ import annotations

import unittest

try:
    from tests._bootstrap import ROOT_DIR
except ModuleNotFoundError:
    from _bootstrap import ROOT_DIR

del ROOT_DIR

try:
    from tasks.todo_analyzer import TodoAnalyzer
except ModuleNotFoundError as exc:
    TodoAnalyzer = None
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


@unittest.skipIf(TodoAnalyzer is None, f"TodoAnalyzer dependency missing: {IMPORT_ERROR}")
class TestTodoEvaluation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.analyzer = TodoAnalyzer()

    def test_bulk_evaluation(self):
        test_data = [
            ("보고서 작성", True),
            ("회의 참석", True),
            ("코드 리뷰 진행", True),
            ("내일까지 기획안 제출", True),
            ("결재 요청 바랍니다", True),
            ("메일 확인 후 회신", True),
            ("오늘 날씨가 좋다", False),
            ("점심 뭐 먹지?", False),
            ("업무 완료했습니다", False),
            ("회의 참석 완료", False),
            ("확인 부탁드립니다", True),
            ("확인했어요", False),
        ]

        correct = 0
        total = len(test_data)

        for text, expected in test_data:
            pred = self.analyzer.is_actual_todo(text)
            if pred == expected:
                correct += 1

        accuracy = correct / total
        self.assertGreaterEqual(accuracy, 0.7)


if __name__ == "__main__":
    unittest.main()
