const PptxGenJS = require("pptxgenjs");

const pptx = new PptxGenJS();
pptx.layout = "LAYOUT_WIDE";
pptx.author = "Codex";
pptx.company = "Mail2Task";
pptx.subject = "Mail2Task dark tech presentation";
pptx.title = "Mail2Task Presentation v3";
pptx.lang = "ko-KR";
pptx.theme = {
  headFontFace: "Malgun Gothic",
  bodyFontFace: "Malgun Gothic",
  lang: "ko-KR",
};

const C = {
  bg: "0A192F",
  bg2: "10243F",
  panel: "132B4B",
  panel2: "173556",
  line: "2A4A6A",
  accent: "64FFDA",
  accentSoft: "163D4C",
  text: "F8FBFF",
  muted: "9AB3C9",
  warning: "8FFFF1",
};

function addBase(slide) {
  slide.background = { color: C.bg };
  slide.addShape(pptx.ShapeType.rect, {
    x: 0,
    y: 0,
    w: 13.333,
    h: 7.5,
    fill: { color: C.bg },
    line: { color: C.bg },
  });
  slide.addShape(pptx.ShapeType.rect, {
    x: 0,
    y: 0,
    w: 13.333,
    h: 0.12,
    fill: { color: C.accent },
    line: { color: C.accent },
  });
  slide.addShape(pptx.ShapeType.line, {
    x: 0.7,
    y: 6.95,
    w: 11.9,
    h: 0,
    line: { color: C.line, pt: 1 },
  });
}

function addTitle(slide, num, title, subtitle) {
  addBase(slide);
  slide.addText(num, {
    x: 0.78,
    y: 0.48,
    w: 0.55,
    h: 0.24,
    fontFace: "Malgun Gothic",
    fontSize: 16,
    bold: true,
    color: C.accent,
    margin: 0,
  });
  slide.addText(title, {
    x: 0.78,
    y: 0.84,
    w: 9.8,
    h: 0.48,
    fontFace: "Malgun Gothic",
    fontSize: 24,
    bold: true,
    color: C.text,
    margin: 0,
  });
  slide.addText(subtitle, {
    x: 0.82,
    y: 1.34,
    w: 10.6,
    h: 0.22,
    fontFace: "Malgun Gothic",
    fontSize: 10.5,
    color: C.muted,
    margin: 0,
  });
}

function footer(slide, page) {
  slide.addText("Mail2Task", {
    x: 0.82,
    y: 7.0,
    w: 1.2,
    h: 0.18,
    fontFace: "Malgun Gothic",
    fontSize: 9,
    color: C.muted,
    margin: 0,
  });
  slide.addText(page, {
    x: 12.0,
    y: 7.0,
    w: 0.4,
    h: 0.18,
    align: "right",
    fontFace: "Malgun Gothic",
    fontSize: 9,
    color: C.muted,
    margin: 0,
  });
}

function card(slide, x, y, w, h, title, body, highlight = false) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x,
    y,
    w,
    h,
    rectRadius: 0.08,
    fill: { color: highlight ? C.panel2 : C.panel, transparency: 0 },
    line: { color: highlight ? C.accent : C.line, pt: highlight ? 1.6 : 1 },
    shadow: highlight
      ? {
          type: "outer",
          color: C.accent,
          blur: 2,
          angle: 45,
          distance: 1,
          opacity: 0.18,
        }
      : undefined,
  });
  slide.addText(title, {
    x: x + 0.18,
    y: y + 0.16,
    w: w - 0.36,
    h: 0.28,
    fontFace: "Malgun Gothic",
    fontSize: 13.5,
    bold: true,
    color: highlight ? C.warning : C.text,
    margin: 0,
  });
  slide.addText(body, {
    x: x + 0.18,
    y: y + 0.5,
    w: w - 0.36,
    h: h - 0.62,
    fontFace: "Malgun Gothic",
    fontSize: 10.3,
    color: C.muted,
    margin: 0.02,
    breakLine: false,
    valign: "top",
  });
}

function bulletText(slide, x, y, w, h, lines, fontSize = 11.5, color = C.muted) {
  slide.addText(
    lines.map((line) => ({ text: line, options: { bullet: { indent: 12 } } })),
    {
      x,
      y,
      w,
      h,
      fontFace: "Malgun Gothic",
      fontSize,
      color,
      margin: 0,
      breakLine: false,
      paraSpaceAfterPt: 7,
      valign: "top",
    }
  );
}

function pill(slide, x, y, w, text, active = false) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x,
    y,
    w,
    h: 0.34,
    rectRadius: 0.14,
    fill: { color: active ? C.accentSoft : C.panel2 },
    line: { color: active ? C.accent : C.line, pt: 1 },
  });
  slide.addText(text, {
    x: x + 0.08,
    y: y + 0.06,
    w: w - 0.16,
    h: 0.16,
    align: "center",
    fontFace: "Malgun Gothic",
    fontSize: 9.5,
    bold: true,
    color: active ? C.warning : C.muted,
    margin: 0,
  });
}

// Cover
{
  const slide = pptx.addSlide();
  addBase(slide);
  slide.addShape(pptx.ShapeType.roundRect, {
    x: 0.9,
    y: 1.0,
    w: 5.9,
    h: 4.9,
    rectRadius: 0.12,
    fill: { color: C.panel, transparency: 10 },
    line: { color: C.line, pt: 1.2 },
  });
  slide.addText("AI Workflow Automation", {
    x: 1.18,
    y: 1.42,
    w: 2.5,
    h: 0.22,
    fontFace: "Malgun Gothic",
    fontSize: 11,
    bold: true,
    color: C.accent,
    margin: 0,
  });
  slide.addText("Mail2Task", {
    x: 1.16,
    y: 1.9,
    w: 4.2,
    h: 0.62,
    fontFace: "Malgun Gothic",
    fontSize: 29,
    bold: true,
    color: C.text,
    margin: 0,
  });
  slide.addText("AI 기반 워크플로우 및 작업 추출 자동화 시스템", {
    x: 1.18,
    y: 2.7,
    w: 4.9,
    h: 0.34,
    fontFace: "Malgun Gothic",
    fontSize: 17,
    color: C.muted,
    margin: 0,
  });
  slide.addText("Gmail · PDF Parsing · Recommendation · MongoDB · Web Dashboard", {
    x: 1.2,
    y: 3.38,
    w: 5.0,
    h: 0.26,
    fontFace: "Malgun Gothic",
    fontSize: 10.5,
    color: C.accent,
    margin: 0,
  });
  slide.addShape(pptx.ShapeType.roundRect, {
    x: 7.45,
    y: 1.0,
    w: 4.95,
    h: 4.95,
    rectRadius: 0.12,
    fill: { color: C.panel2, transparency: 8 },
    line: { color: C.accent, pt: 1.1 },
  });
  const pipeline = [
    ["MAIL", "Input"],
    ["AI", "Process"],
    ["TASK", "Output"],
    ["PDF", "Context"],
  ];
  pipeline.forEach((item, i) => {
    const y = 1.62 + i * 0.95;
    slide.addShape(pptx.ShapeType.roundRect, {
      x: 7.95,
      y,
      w: 1.15,
      h: 0.48,
      rectRadius: 0.08,
      fill: { color: C.accentSoft },
      line: { color: C.accent, pt: 1 },
    });
    slide.addText(item[0], {
      x: 8.04,
      y: y + 0.12,
      w: 0.96,
      h: 0.18,
      align: "center",
      fontFace: "Malgun Gothic",
      fontSize: 11,
      bold: true,
      color: C.warning,
      margin: 0,
    });
    slide.addText(item[1], {
      x: 9.35,
      y: y + 0.1,
      w: 1.0,
      h: 0.18,
      fontFace: "Malgun Gothic",
      fontSize: 11,
      color: C.text,
      margin: 0,
    });
    slide.addText(
      i === 0
        ? "Gmail 수집"
        : i === 1
        ? "LLM 분석 / 추천"
        : i === 2
        ? "실행 가능한 업무"
        : "유사 문서 맥락 보강",
      {
        x: 9.35,
        y: y + 0.26,
        w: 2.25,
        h: 0.18,
        fontFace: "Malgun Gothic",
        fontSize: 9.5,
        color: C.muted,
        margin: 0,
      }
    );
  });
  slide.addText("Team Project Presentation", {
    x: 1.18,
    y: 5.2,
    w: 2.1,
    h: 0.2,
    fontFace: "Malgun Gothic",
    fontSize: 10,
    color: C.muted,
    margin: 0,
  });
}

// Slide 1
{
  const slide = pptx.addSlide();
  addTitle(slide, "01", "프로젝트 배경: 메일 기반 업무 요청의 한계", "분산된 메일과 수동 정리 과정에서 생기는 운영 비효율을 먼저 정의합니다.");
  card(slide, 0.95, 2.0, 3.7, 3.7, "파편화된 업무 채널", "흩어진 메일로 인해 요청 맥락이 단절되고, 어떤 메일부터 우선 처리해야 하는지 즉시 판단하기 어렵습니다.");
  card(slide, 4.82, 2.0, 3.7, 3.7, "휴먼 에러 리스크", "담당자가 제목, 본문, 첨부를 수동으로 정리하는 과정에서 업무 누락과 상태 미반영 문제가 생길 수 있습니다.");
  card(slide, 8.69, 2.0, 3.7, 3.7, "데이터 처리 병목", "첨부 PDF를 따로 열어 확인하고 과거 관련 문서까지 다시 찾는 데 많은 시간이 소요됩니다.");
  slide.addText("Time Loss", {
    x: 10.9,
    y: 5.95,
    w: 1.1,
    h: 0.2,
    fontFace: "Malgun Gothic",
    fontSize: 10,
    bold: true,
    color: C.accent,
    margin: 0,
  });
  footer(slide, "1");
}

// Slide 2
{
  const slide = pptx.addSlide();
  addTitle(slide, "02", "해결 방안: Mail2Task - 메일을 To-do로 즉시 변환", "메일을 읽고 이해해 구조화된 업무 데이터로 바꾸는 AI 워크플로우를 제안합니다.");
  slide.addShape(pptx.ShapeType.roundRect, {
    x: 1.05,
    y: 2.3,
    w: 2.55,
    h: 2.7,
    rectRadius: 0.1,
    fill: { color: C.panel },
    line: { color: C.line, pt: 1 },
  });
  slide.addShape(pptx.ShapeType.roundRect, {
    x: 5.36,
    y: 2.3,
    w: 2.55,
    h: 2.7,
    rectRadius: 0.1,
    fill: { color: C.panel2 },
    line: { color: C.accent, pt: 1.2 },
  });
  slide.addShape(pptx.ShapeType.roundRect, {
    x: 9.67,
    y: 2.3,
    w: 2.55,
    h: 2.7,
    rectRadius: 0.1,
    fill: { color: C.panel },
    line: { color: C.line, pt: 1 },
  });
  const blocks = [
    ["Mail\nInput", "자동 수집", "Gmail 실시간 모니터링 및 메일 수집"],
    ["AI\nProcess", "AI 분석", "본문과 PDF에서 마감일, 긴급도, 핵심 요청 추출"],
    ["Task\nOutput", "구조화", "파편화된 정보를 actionable한 To-do 리스트로 변환"],
  ];
  blocks.forEach((b, i) => {
    const x = 1.32 + i * 4.31;
    slide.addText(b[0], {
      x,
      y: 2.72,
      w: 0.95,
      h: 0.52,
      align: "center",
      fontFace: "Malgun Gothic",
      fontSize: 18,
      bold: true,
      color: i === 1 ? C.warning : C.text,
      margin: 0,
    });
    slide.addText(b[1], {
      x: x + 0.95,
      y: 2.73,
      w: 1.0,
      h: 0.2,
      fontFace: "Malgun Gothic",
      fontSize: 12.5,
      bold: true,
      color: C.accent,
      margin: 0,
    });
    slide.addText(b[2], {
      x: x + 0.95,
      y: 3.08,
      w: 1.28,
      h: 1.1,
      fontFace: "Malgun Gothic",
      fontSize: 10.3,
      color: C.muted,
      margin: 0,
      valign: "mid",
    });
  });
  slide.addShape(pptx.ShapeType.chevron, {
    x: 3.95,
    y: 3.32,
    w: 0.45,
    h: 0.42,
    fill: { color: C.accent },
    line: { color: C.accent, pt: 0.5 },
  });
  slide.addShape(pptx.ShapeType.chevron, {
    x: 8.25,
    y: 3.32,
    w: 0.45,
    h: 0.42,
    fill: { color: C.accent },
    line: { color: C.accent, pt: 0.5 },
  });
  footer(slide, "2");
}

// Slide 3
{
  const slide = pptx.addSlide();
  addTitle(slide, "03", "핵심 기능: 실무 최적화 자동화 기능", "수집, 분석, 추천, 알림까지 이어지는 End-to-End 기능을 사용자 관점으로 설명합니다.");
  card(slide, 0.9, 2.1, 2.85, 3.55, "Smart Extraction", "Gmail IMAP 연동과 PDF 텍스트 정밀 추출로 메일과 첨부문서를 함께 처리합니다.");
  card(
    slide,
    3.95,
    2.1,
    2.85,
    3.55,
    "Contextual Recommendation",
    "첨부 PDF 기준 연관 PDF 추천\n메일 본문 기준 관련 PDF 추천\n기존 데이터베이스 안에서 맥락이 비슷한 문서를 자동으로 찾아줍니다.",
    true
  );
  card(slide, 7.0, 2.1, 2.85, 3.55, "AI Summarization", "LLM 기반 업무 요약과 우선순위 자동 분류로 담당자의 판단 부담을 줄입니다.");
  card(slide, 10.05, 2.1, 2.35, 3.55, "Auto Notification", "통합 웹 대시보드 관리와 작업 완료 시 자동 회신 알림까지 연결합니다.");
  pill(slide, 4.2, 5.95, 1.55, "첨부 PDF 추천", true);
  pill(slide, 5.9, 5.95, 1.55, "본문 기반 추천", true);
  footer(slide, "3");
}

// Slide 4
{
  const slide = pptx.addSlide();
  addTitle(slide, "04", "시스템 흐름: Mail2Task 동작 프로세스", "안정적인 데이터 파이프라인과 추천 로직이 포함된 전체 아키텍처를 보여줍니다.");
  const steps = [
    "Gmail",
    "IMAP 수집",
    "PDF 파싱",
    "유사 문서 매칭",
    "LLM 분석",
    "MongoDB 저장",
    "Web UI",
    "SMTP 알림",
  ];
  steps.forEach((step, i) => {
    const x = 0.88 + i * 1.53;
    slide.addShape(pptx.ShapeType.roundRect, {
      x,
      y: 3.0,
      w: 1.22,
      h: 1.18,
      rectRadius: 0.08,
      fill: { color: i === 3 ? C.accentSoft : C.panel },
      line: { color: i === 3 ? C.accent : C.line, pt: i === 3 ? 1.5 : 1 },
    });
    slide.addText(step, {
      x: x + 0.08,
      y: 3.32,
      w: 1.06,
      h: 0.34,
      align: "center",
      fontFace: "Malgun Gothic",
      fontSize: 11.5,
      bold: true,
      color: i === 3 ? C.warning : C.text,
      margin: 0,
    });
    if (i < steps.length - 1) {
      slide.addShape(pptx.ShapeType.chevron, {
        x: x + 1.27,
        y: 3.36,
        w: 0.18,
        h: 0.28,
        fill: { color: C.accent },
        line: { color: C.accent, pt: 0.5 },
      });
    }
  });
  slide.addText("유사 문서 매칭(DB 검색)", {
    x: 5.25,
    y: 4.45,
    w: 1.9,
    h: 0.2,
    align: "center",
    fontFace: "Malgun Gothic",
    fontSize: 10.5,
    bold: true,
    color: C.accent,
    margin: 0,
  });
  footer(slide, "4");
}

// Slide 5
{
  const slide = pptx.addSlide();
  addTitle(slide, "05", "차별점: 지능형 문서 추천과 닫힌 업무 흐름", "단순 메일 뷰어가 아니라 실무 활용도를 높이는 맥락 인지형 자동화를 강조합니다.");
  card(slide, 0.9, 2.1, 5.65, 3.95, "기존 방식", "메일을 그대로 나열\n본문만 확인 가능\n과거 유사 문서를 직접 검색\n완료 후 회신도 별도 작성");
  card(
    slide,
    6.82,
    2.1,
    5.65,
    3.95,
    "Mail2Task",
    "Actionable Task 중심 설계\n첨부 PDF와 본문까지 함께 분석\nAI 자동 추천으로 유사 PDF 즉시 탐색\n업무 완료 후 자동 회신으로 Closed-loop 완성",
    true
  );
  slide.addText("Intelligent Matching", {
    x: 8.65,
    y: 5.58,
    w: 1.8,
    h: 0.18,
    fontFace: "Malgun Gothic",
    fontSize: 10.5,
    bold: true,
    color: C.accent,
    margin: 0,
  });
  footer(slide, "5");
}

// Slide 6
{
  const slide = pptx.addSlide();
  addTitle(slide, "06", "기대 효과: 업무 효율의 혁신", "누락은 줄이고 속도는 높이는 방향으로 사용자와 팀의 생산성을 개선합니다.");
  card(slide, 0.95, 2.2, 3.8, 3.55, "운영 효율성", "문서 검색과 메일 정리 시간이 줄어들어 실제 업무 처리에 더 많은 시간을 쓸 수 있습니다.");
  card(slide, 4.78, 2.2, 3.8, 3.55, "정확성 제고", "AI 분석으로 업무 누락을 줄이고 마감일과 우선순위를 더 일관되게 관리할 수 있습니다.");
  card(slide, 8.61, 2.2, 3.8, 3.55, "협업 최적화", "완료 회신과 추천 문서 제공으로 팀 내 피드백 속도와 문맥 공유 품질이 높아집니다.");
  slide.addText("Efficiency Up", {
    x: 10.95,
    y: 5.92,
    w: 1.4,
    h: 0.2,
    fontFace: "Malgun Gothic",
    fontSize: 10.5,
    bold: true,
    color: C.accent,
    margin: 0,
  });
  footer(slide, "6");
}

(async () => {
  await pptx.writeFile({ fileName: "Mail2Task_Presentation_v4_darktech.pptx" });
})();
