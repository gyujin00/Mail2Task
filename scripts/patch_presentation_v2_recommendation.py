from __future__ import annotations

import shutil
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path


SOURCE = Path("Mail2Task_Presentation_v2.pptx")
TARGET = Path("Mail2Task_Presentation_v2_recommendation.pptx")
WORK_DIR = Path("downloads/_ppt_patch_work")

NS = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}
ET.register_namespace("a", NS["a"])


REPLACEMENTS = {
    "ppt/slides/slide5.xml": {
        "Gmail 수집부터 완료 알림까지, 업무 흐름 전체를 커버": "Gmail 수집부터 PDF 추천과 완료 알림까지, 업무 흐름 전체를 커버",
        "📄  PDF 첨부파일 텍스트 추출": "📄  PDF 첨부파일 분석 + 연관 PDF 추천",
        "pdfplumber를 활용해 첨부 PDF 내용까지 분석 대상에 포함합니다.": "pdfplumber로 첨부 PDF를 분석하고, 기존 DB에서 연관 PDF를 함께 추천합니다.",
        "🧠  업무 요약 · 마감일 · 우선순위 자동 정리": "🧠  본문 기반 관련 PDF 추천 + 업무 자동 정리",
        "OpenAI 기반으로 업무 핵심 내용, 마감일, 긴급도를 자동으로 추출합니다.": "메일 본문 맥락을 기준으로 관련 PDF를 추천하고, 업무 핵심 내용·마감일·긴급도를 자동 추출합니다.",
    },
    "ppt/slides/slide6.xml": {
        "7단계로 연결된 자동화 파이프라인 한눈에 보기": "추천 기능이 포함된 7단계 자동화 파이프라인 한눈에 보기",
        "업무": "추천",
        "분석  ": "추천/분석  ",
        "본문과 첨부 PDF를 함께 분석해 업무 정보를 추출합니다.": "본문과 첨부 PDF를 함께 분석해 업무 정보를 추출하고 관련 PDF를 추천합니다.",
    },
    "ppt/slides/slide7.xml": {
        "·  본문 텍스트만 확인 가능": "·  과거 유사 문서를 직접 찾아야 함",
        "▸  첨부 PDF 내용까지 자동 분석에 반영": "▸  첨부 PDF 기준 연관 PDF 자동 추천",
        "·  중요도는 사람이 직접 판단": "·  메일 본문 기준 관련 자료 연결이 어려움",
        "▸  LLM 기반 긴급도·마감일 자동 계산": "▸  메일 본문 기준 관련 PDF 자동 추천",
    },
    "ppt/slides/slide9.xml": {
        "PDF 첨부 분석 + LLM 요약 + 긴급도 자동 계산": "PDF 첨부 분석 + 연관 PDF 추천 + LLM 요약 + 긴급도 자동 계산",
    },
}


def replace_text_in_xml(xml_bytes: bytes, mapping: dict[str, str]) -> bytes:
    root = ET.fromstring(xml_bytes)
    changed = False
    for node in root.findall(".//a:t", NS):
        if node.text in mapping:
            node.text = mapping[node.text]
            changed = True
    if not changed:
        return xml_bytes
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def build() -> Path:
    if not SOURCE.exists():
        raise FileNotFoundError(f"Source PPT not found: {SOURCE}")

    if WORK_DIR.exists():
        shutil.rmtree(WORK_DIR)

    extracted = WORK_DIR / "extracted"
    extracted.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(SOURCE, "r") as src_zip:
        src_zip.extractall(extracted)

    for slide_name, mapping in REPLACEMENTS.items():
        slide_path = extracted / slide_name
        slide_bytes = slide_path.read_bytes()
        slide_path.write_bytes(replace_text_in_xml(slide_bytes, mapping))

    rebuilt = WORK_DIR / TARGET.name
    with zipfile.ZipFile(rebuilt, "w", compression=zipfile.ZIP_DEFLATED) as out_zip:
        for file_path in extracted.rglob("*"):
            if file_path.is_file():
                out_zip.write(file_path, file_path.relative_to(extracted).as_posix())

    shutil.copy2(rebuilt, TARGET)
    return TARGET


if __name__ == "__main__":
    out = build()
    print(out.resolve())
