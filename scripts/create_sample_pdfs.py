"""
10개의 샘플 기술 문서 PDF를 downloads/ 폴더에 생성합니다.
한국어 + 영어 혼합 내용으로 PDF 추천 시스템 테스트에 적합합니다.

실행: python -m scripts.create_sample_pdfs
"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
except ModuleNotFoundError:
    print("[오류] reportlab이 설치되어 있지 않습니다. pip install reportlab")
    sys.exit(1)

ROOT_DIR = Path(__file__).resolve().parents[1]
DOWNLOADS_DIR = ROOT_DIR / "downloads"
DOWNLOADS_DIR.mkdir(exist_ok=True)

# 나눔고딕 폰트 등록 (없으면 Helvetica fallback)
KOREAN_FONT = "Helvetica"
try:
    import urllib.request, os, tempfile

    font_candidates = [
        Path("C:/Windows/Fonts/malgun.ttf"),
        Path("C:/Windows/Fonts/NanumGothic.ttf"),
        Path("/usr/share/fonts/truetype/nanum/NanumGothic.ttf"),
    ]
    for fc in font_candidates:
        if fc.exists():
            pdfmetrics.registerFont(TTFont("Korean", str(fc)))
            KOREAN_FONT = "Korean"
            break
except Exception:
    pass


DOCS = [
    {
        "filename": "cicd_pipeline_guide.pdf",
        "title": "CI/CD 파이프라인 구축 및 운영 가이드",
        "subtitle": "CI/CD Pipeline Build & Operations Guide",
        "pages": [
            {
                "heading": "1. CI/CD 개요 (Overview)",
                "body": [
                    "CI/CD(지속적 통합/지속적 배포)는 소프트웨어 개발 생산성을 높이는 핵심 DevOps 관행입니다.",
                    "Continuous Integration and Continuous Deployment (CI/CD) automates the software delivery process.",
                    "",
                    "주요 도구 (Key Tools):",
                    "- Jenkins, GitHub Actions, GitLab CI, CircleCI",
                    "- Docker, Kubernetes (K8s)",
                    "- SonarQube (코드 품질 분석)",
                    "",
                    "파이프라인 단계 (Pipeline Stages):",
                    "1. 코드 커밋 (Code Commit) → 트리거",
                    "2. 빌드 (Build) — Maven, Gradle, npm run build",
                    "3. 단위 테스트 (Unit Test) — JUnit, pytest, Jest",
                    "4. 코드 분석 (Static Analysis) — SonarQube, ESLint",
                    "5. 아티팩트 생성 (Artifact) — Docker image, JAR, WAR",
                    "6. 스테이징 배포 (Staging Deploy)",
                    "7. 통합 테스트 (Integration Test)",
                    "8. 프로덕션 배포 (Production Deploy)",
                ],
            },
            {
                "heading": "2. 빌드 오류 대응 (Build Error Handling)",
                "body": [
                    "파이프라인 빌드 오류 시 즉각적인 알림 및 롤백이 필요합니다.",
                    "Common build failures and resolution steps:",
                    "",
                    "오류 유형 (Error Types):",
                    "- 컴파일 오류 (Compile Error): 의존성 충돌, 문법 오류",
                    "- 테스트 실패 (Test Failure): 단위/통합 테스트 불통과",
                    "- 도커 빌드 실패 (Docker Build Failure): Dockerfile 문제",
                    "- 배포 오류 (Deploy Error): 환경 설정 불일치",
                    "",
                    "긴급 대응 절차:",
                    "1. 파이프라인 로그 확인 → 오류 원인 파악",
                    "2. 이전 정상 빌드로 롤백 (Rollback)",
                    "3. 오류 수정 후 재배포 (Redeploy)",
                    "4. 장애 리포트 작성 및 공유",
                ],
            },
        ],
    },
    {
        "filename": "backend_api_manual.pdf",
        "title": "백엔드 API 개발 매뉴얼",
        "subtitle": "Backend API Development Manual — FastAPI / Spring Boot",
        "pages": [
            {
                "heading": "1. REST API 설계 원칙",
                "body": [
                    "RESTful API 설계는 리소스 중심의 URL 구조와 HTTP 메서드를 따릅니다.",
                    "REST API design follows resource-oriented URL structure with HTTP methods.",
                    "",
                    "HTTP 메서드 사용 규칙:",
                    "- GET: 리소스 조회 (Read)",
                    "- POST: 리소스 생성 (Create)",
                    "- PUT/PATCH: 리소스 수정 (Update)",
                    "- DELETE: 리소스 삭제 (Delete)",
                    "",
                    "상태 코드 (Status Codes):",
                    "- 200 OK, 201 Created, 204 No Content",
                    "- 400 Bad Request, 401 Unauthorized, 403 Forbidden",
                    "- 404 Not Found, 409 Conflict, 500 Internal Server Error",
                    "",
                    "인증 방식 (Authentication):",
                    "- JWT (JSON Web Token) Bearer Token",
                    "- OAuth 2.0 / OpenID Connect",
                    "- API Key 헤더 방식",
                ],
            },
            {
                "heading": "2. FastAPI 서버 구축",
                "body": [
                    "FastAPI는 Python 기반의 고성능 비동기 웹 프레임워크입니다.",
                    "FastAPI provides automatic OpenAPI documentation and async support.",
                    "",
                    "의존성 설치: pip install fastapi uvicorn",
                    "",
                    "주요 기능:",
                    "- 자동 OpenAPI(Swagger) 문서 생성",
                    "- Pydantic 모델 기반 요청/응답 검증",
                    "- 비동기(async/await) 처리",
                    "- 의존성 주입(Dependency Injection)",
                    "",
                    "배포 방법:",
                    "uvicorn main:app --host 0.0.0.0 --port 8000",
                    "Docker 컨테이너로 패키징 후 Kubernetes 배포 가능",
                ],
            },
        ],
    },
    {
        "filename": "frontend_react_guide.pdf",
        "title": "프론트엔드 React 개발 가이드",
        "subtitle": "Frontend React Development Guide — TypeScript, Tailwind CSS",
        "pages": [
            {
                "heading": "1. React 프로젝트 구조",
                "body": [
                    "React는 컴포넌트 기반의 사용자 인터페이스 라이브러리입니다.",
                    "React is a component-based UI library for building interactive web applications.",
                    "",
                    "권장 프로젝트 구조:",
                    "src/",
                    "  components/   # 재사용 가능한 UI 컴포넌트",
                    "  pages/        # 페이지 컴포넌트 (라우팅)",
                    "  hooks/        # 커스텀 훅",
                    "  services/     # API 호출 레이어",
                    "  store/        # 전역 상태관리 (Redux, Zustand)",
                    "",
                    "주요 패키지 (Key Packages):",
                    "- React 18 + TypeScript",
                    "- React Router v6 (라우팅)",
                    "- TanStack Query (서버 상태 관리)",
                    "- Tailwind CSS (스타일링)",
                    "- Vite (빌드 도구)",
                ],
            },
            {
                "heading": "2. 성능 최적화",
                "body": [
                    "React 성능 최적화는 불필요한 리렌더링 방지가 핵심입니다.",
                    "React performance optimization prevents unnecessary re-renders.",
                    "",
                    "최적화 기법:",
                    "- React.memo: 컴포넌트 메모이제이션",
                    "- useMemo / useCallback: 값/함수 캐싱",
                    "- 코드 스플리팅 (Code Splitting): React.lazy + Suspense",
                    "- 가상 스크롤 (Virtual Scroll): react-window",
                    "- 이미지 최적화: WebP 포맷, lazy loading",
                    "",
                    "Lighthouse 성능 지표 목표:",
                    "- FCP (First Contentful Paint) < 1.8s",
                    "- LCP (Largest Contentful Paint) < 2.5s",
                    "- CLS (Cumulative Layout Shift) < 0.1",
                ],
            },
        ],
    },
    {
        "filename": "mobile_app_development.pdf",
        "title": "모바일 앱 개발 가이드 (Flutter)",
        "subtitle": "Mobile App Development — Flutter Cross-Platform",
        "pages": [
            {
                "heading": "1. Flutter 소개 및 구조",
                "body": [
                    "Flutter는 Google이 개발한 크로스플랫폼 모바일 앱 프레임워크입니다.",
                    "Flutter enables building iOS and Android apps from a single Dart codebase.",
                    "",
                    "프로젝트 구조:",
                    "lib/",
                    "  main.dart          # 앱 진입점",
                    "  screens/           # 화면 위젯",
                    "  widgets/           # 재사용 위젯",
                    "  models/            # 데이터 모델",
                    "  services/          # API/Firebase 연동",
                    "  providers/         # 상태 관리 (Riverpod)",
                    "",
                    "주요 패키지:",
                    "- flutter_riverpod (상태 관리)",
                    "- dio (HTTP 클라이언트)",
                    "- go_router (네비게이션)",
                    "- firebase_core (Firebase 연동)",
                    "- hive (로컬 스토리지)",
                ],
            },
            {
                "heading": "2. 앱 배포 및 출시",
                "body": [
                    "Flutter 앱 배포는 iOS App Store와 Android Google Play를 통해 이루어집니다.",
                    "App deployment requires signing configuration for both platforms.",
                    "",
                    "Android 배포:",
                    "- keystore 서명 설정",
                    "- build.gradle 버전 업데이트",
                    "- flutter build appbundle --release",
                    "- Google Play Console 업로드",
                    "",
                    "iOS 배포:",
                    "- Apple Developer 인증서 설정",
                    "- Xcode 빌드 설정",
                    "- TestFlight 내부 테스트",
                    "- App Store Connect 제출",
                    "",
                    "자동화 도구: Fastlane, GitHub Actions 연동",
                ],
            },
        ],
    },
    {
        "filename": "cloud_aws_infrastructure.pdf",
        "title": "클라우드 인프라 설계 문서 (AWS)",
        "subtitle": "Cloud Infrastructure Architecture — AWS / GCP / Azure",
        "pages": [
            {
                "heading": "1. AWS 아키텍처 설계",
                "body": [
                    "클라우드 인프라는 고가용성(HA), 확장성, 보안을 기본 원칙으로 설계합니다.",
                    "Cloud infrastructure is designed for high availability, scalability, and security.",
                    "",
                    "핵심 AWS 서비스:",
                    "- EC2: 가상 서버 (Virtual Machines)",
                    "- EKS: Kubernetes 관리형 클러스터",
                    "- RDS: 관계형 데이터베이스 (MySQL, PostgreSQL)",
                    "- S3: 오브젝트 스토리지",
                    "- CloudFront: CDN (콘텐츠 배포 네트워크)",
                    "- VPC: 가상 사설 네트워크",
                    "- IAM: 접근 권한 관리",
                    "- CloudWatch: 모니터링 및 로깅",
                    "",
                    "네트워크 설계:",
                    "- Public Subnet: Load Balancer, NAT Gateway",
                    "- Private Subnet: 애플리케이션 서버, DB",
                    "- Multi-AZ 배포로 장애 대비",
                ],
            },
            {
                "heading": "2. 인프라 비용 최적화",
                "body": [
                    "클라우드 비용 최적화는 Reserved Instance와 Auto Scaling을 활용합니다.",
                    "Cost optimization uses Reserved Instances, Spot instances, and Auto Scaling.",
                    "",
                    "비용 절감 전략:",
                    "- Reserved Instance: 1년 약정으로 최대 40% 절감",
                    "- Spot Instance: 배치 작업에 활용, 최대 90% 절감",
                    "- Auto Scaling: 트래픽에 따라 자동 스케일 인/아웃",
                    "- S3 Intelligent-Tiering: 접근 패턴 기반 자동 스토리지 최적화",
                    "",
                    "모니터링 도구:",
                    "- AWS Cost Explorer",
                    "- CloudWatch Dashboards",
                    "- Grafana + Prometheus",
                    "- Datadog APM",
                ],
            },
        ],
    },
    {
        "filename": "ai_ml_serving_guide.pdf",
        "title": "AI/ML 모델 서빙 가이드",
        "subtitle": "AI/ML Model Serving — FastAPI, TorchServe, Triton",
        "pages": [
            {
                "heading": "1. 모델 서빙 아키텍처",
                "body": [
                    "AI/ML 모델 서빙은 훈련된 모델을 프로덕션 환경에서 API로 제공하는 과정입니다.",
                    "Model serving exposes trained ML models as REST or gRPC APIs in production.",
                    "",
                    "서빙 프레임워크 비교:",
                    "- TorchServe: PyTorch 모델 전용 서버",
                    "- TensorFlow Serving: TF 모델 최적화",
                    "- NVIDIA Triton: 다중 프레임워크 지원, GPU 최적화",
                    "- FastAPI + ONNX: 경량 커스텀 서버",
                    "",
                    "성능 최적화:",
                    "- 배치 추론 (Batch Inference): 처리량 향상",
                    "- 모델 양자화 (Quantization): INT8, FP16",
                    "- ONNX 변환: 프레임워크 독립적 최적화",
                    "- TensorRT: NVIDIA GPU 추론 최적화",
                ],
            },
            {
                "heading": "2. MLOps 파이프라인",
                "body": [
                    "MLOps는 머신러닝 모델의 개발, 배포, 모니터링을 자동화하는 방법론입니다.",
                    "MLOps automates the ML lifecycle from training to production monitoring.",
                    "",
                    "MLOps 도구 스택:",
                    "- 실험 추적: MLflow, Weights & Biases",
                    "- 데이터 버전 관리: DVC",
                    "- 피처 스토어: Feast",
                    "- 파이프라인 오케스트레이션: Kubeflow, Airflow",
                    "- 모델 레지스트리: MLflow Model Registry",
                    "",
                    "모델 모니터링 지표:",
                    "- 데이터 드리프트 (Data Drift) 감지",
                    "- 모델 성능 저하 (Model Degradation) 알림",
                    "- 추론 지연시간 (Latency) P50/P95/P99",
                    "- 처리량 (Throughput) RPS 모니터링",
                ],
            },
        ],
    },
    {
        "filename": "security_compliance_policy.pdf",
        "title": "정보보안 정책 및 컴플라이언스 가이드",
        "subtitle": "Information Security Policy & Compliance Guide",
        "pages": [
            {
                "heading": "1. 보안 정책 개요",
                "body": [
                    "정보보안 정책은 조직의 데이터 자산을 보호하기 위한 규정과 절차를 정의합니다.",
                    "Information security policy defines rules to protect organizational data assets.",
                    "",
                    "보안 원칙 (Security Principles):",
                    "- 기밀성 (Confidentiality): 인가된 사용자만 접근",
                    "- 무결성 (Integrity): 데이터 변조 방지",
                    "- 가용성 (Availability): 서비스 지속 가용성 확보",
                    "",
                    "접근 제어 (Access Control):",
                    "- 최소 권한 원칙 (Principle of Least Privilege)",
                    "- 다중 인증 (MFA: Multi-Factor Authentication)",
                    "- 역할 기반 접근 제어 (RBAC)",
                    "- 정기적 권한 검토 (Quarterly Access Review)",
                ],
            },
            {
                "heading": "2. 취약점 관리 및 대응",
                "body": [
                    "취약점 관리는 정기적인 스캔과 신속한 패치 적용이 핵심입니다.",
                    "Vulnerability management requires regular scanning and timely patching.",
                    "",
                    "취약점 대응 프로세스:",
                    "1. 취약점 스캔 (Vulnerability Scan): Nessus, OpenVAS",
                    "2. 위험도 평가 (Risk Assessment): CVSS 점수 기준",
                    "3. 패치 우선순위 결정 (Critical > High > Medium)",
                    "4. 패치 적용 및 검증 (Patch & Verify)",
                    "5. 재스캔으로 확인 (Rescan)",
                    "",
                    "보안 사고 대응 (Incident Response):",
                    "- SIEM 알림 수신 → 1차 분류",
                    "- 격리 (Containment) → 분석 → 복구",
                    "- 사후 분석 (Post-Incident Review)",
                ],
            },
        ],
    },
    {
        "filename": "data_pipeline_etl_spec.pdf",
        "title": "데이터 파이프라인 ETL 설계 명세서",
        "subtitle": "Data Pipeline ETL Architecture Specification",
        "pages": [
            {
                "heading": "1. ETL 파이프라인 설계",
                "body": [
                    "ETL(Extract-Transform-Load) 파이프라인은 데이터 수집, 변환, 적재 프로세스입니다.",
                    "ETL pipeline automates data extraction, transformation, and loading into data warehouses.",
                    "",
                    "파이프라인 구성:",
                    "- 소스 (Source): MySQL, PostgreSQL, MongoDB, S3, Kafka",
                    "- 변환 (Transform): Apache Spark, dbt, Pandas",
                    "- 목적지 (Sink): Snowflake, BigQuery, Redshift",
                    "",
                    "오케스트레이션 도구:",
                    "- Apache Airflow: DAG 기반 워크플로우",
                    "- Prefect: Python 네이티브 워크플로우",
                    "- dbt: SQL 기반 데이터 변환",
                    "",
                    "스케줄링:",
                    "- 배치 처리 (Batch): 일별/주별 집계",
                    "- 실시간 처리 (Streaming): Apache Kafka + Spark Streaming",
                    "- 마이크로 배치 (Micro-batch): 5분 단위",
                ],
            },
            {
                "heading": "2. 데이터 품질 관리",
                "body": [
                    "데이터 품질 관리는 데이터의 정확성, 완전성, 일관성을 보장합니다.",
                    "Data quality management ensures accuracy, completeness, and consistency.",
                    "",
                    "품질 검증 항목:",
                    "- Null 값 비율 체크 (Null Check)",
                    "- 중복 데이터 제거 (Deduplication)",
                    "- 값 범위 검증 (Range Validation)",
                    "- 참조 무결성 검사 (Referential Integrity)",
                    "- 스키마 변경 감지 (Schema Drift Detection)",
                    "",
                    "모니터링 도구:",
                    "- Great Expectations: 데이터 검증 프레임워크",
                    "- Soda Core: 데이터 품질 모니터링",
                    "- Monte Carlo: 데이터 옵저버빌리티",
                ],
            },
        ],
    },
    {
        "filename": "database_mongodb_guide.pdf",
        "title": "데이터베이스 설계 및 MongoDB 운영 가이드",
        "subtitle": "Database Design & MongoDB Operations Guide",
        "pages": [
            {
                "heading": "1. MongoDB 스키마 설계",
                "body": [
                    "MongoDB는 도큐먼트 지향 NoSQL 데이터베이스로 유연한 스키마를 제공합니다.",
                    "MongoDB is a document-oriented NoSQL database with flexible schema design.",
                    "",
                    "설계 원칙:",
                    "- 임베딩 (Embedding): 자주 함께 조회되는 데이터는 하나의 도큐먼트에",
                    "- 참조 (Reference): 대용량 또는 공유 데이터는 별도 컬렉션으로 분리",
                    "- 인덱스 전략: 조회 패턴 기반 인덱스 설계",
                    "",
                    "주요 인덱스 유형:",
                    "- 단일 필드 인덱스 (Single Field)",
                    "- 복합 인덱스 (Compound Index)",
                    "- 텍스트 인덱스 (Text Index): 전문 검색",
                    "- 지리공간 인덱스 (Geospatial Index)",
                    "- TTL 인덱스: 만료 데이터 자동 삭제",
                ],
            },
            {
                "heading": "2. 성능 튜닝 및 운영",
                "body": [
                    "MongoDB 성능 튜닝은 explain() 분석과 인덱스 최적화가 핵심입니다.",
                    "MongoDB performance tuning relies on explain() analysis and index optimization.",
                    "",
                    "성능 진단:",
                    "- db.collection.explain('executionStats'): 쿼리 실행 계획 분석",
                    "- mongotop: 컬렉션별 I/O 사용량 모니터링",
                    "- mongostat: 실시간 서버 상태 확인",
                    "- Atlas Performance Advisor: 인덱스 추천",
                    "",
                    "백업 및 복구:",
                    "- mongodump / mongorestore: 논리적 백업",
                    "- Replica Set: 자동 장애 복구",
                    "- Atlas Backup: 지속적 클라우드 백업",
                    "",
                    "보안 설정:",
                    "- 인증 활성화 (Authentication)",
                    "- TLS/SSL 암호화 통신",
                    "- 네트워크 접근 제어 (IP Allowlist)",
                ],
            },
        ],
    },
    {
        "filename": "project_management_guide.pdf",
        "title": "프로젝트 관리 및 애자일 스프린트 가이드",
        "subtitle": "Project Management & Agile Sprint Guide — Scrum / Kanban",
        "pages": [
            {
                "heading": "1. 스크럼 방법론",
                "body": [
                    "스크럼은 2~4주 스프린트 단위로 반복적 개발을 진행하는 애자일 방법론입니다.",
                    "Scrum is an agile framework using 2-4 week sprints for iterative development.",
                    "",
                    "스크럼 이벤트 (Scrum Events):",
                    "- 스프린트 계획 (Sprint Planning): 백로그 아이템 선택",
                    "- 데일리 스크럼 (Daily Standup): 15분 일일 동기화",
                    "- 스프린트 리뷰 (Sprint Review): 결과물 시연",
                    "- 스프린트 회고 (Retrospective): 개선점 도출",
                    "",
                    "산출물 (Artifacts):",
                    "- 제품 백로그 (Product Backlog)",
                    "- 스프린트 백로그 (Sprint Backlog)",
                    "- 번다운 차트 (Burndown Chart)",
                    "- 완료 기준 (Definition of Done)",
                ],
            },
            {
                "heading": "2. 업무 협업 도구",
                "body": [
                    "협업 도구를 활용하여 팀 생산성과 가시성을 높입니다.",
                    "Collaboration tools improve team productivity and work visibility.",
                    "",
                    "프로젝트 관리 (Project Management):",
                    "- Jira: 이슈 트래킹, 스프린트 보드",
                    "- Notion: 문서화, 위키",
                    "- Confluence: 기술 문서 관리",
                    "- Linear: 개발팀 이슈 관리",
                    "",
                    "커뮤니케이션:",
                    "- Slack: 채널 기반 팀 메시지",
                    "- Zoom / Google Meet: 화상 회의",
                    "- GitHub / GitLab: 코드 리뷰 (PR/MR)",
                    "",
                    "업무 요청 프로세스:",
                    "1. 요청자 → Jira 티켓 생성",
                    "2. 담당자 배정 및 우선순위 설정",
                    "3. 스프린트 백로그 추가",
                    "4. 개발 → 코드 리뷰 → 테스트 → 배포",
                    "5. 완료 알림 및 티켓 클로즈",
                ],
            },
        ],
    },
]


def draw_page(c: "canvas.Canvas", doc_title: str, heading: str, body_lines: list[str], width: float, height: float) -> None:
    y = height - 50
    c.setFont(KOREAN_FONT if KOREAN_FONT != "Helvetica" else "Helvetica-Bold", 10)
    c.setFillColorRGB(0.5, 0.5, 0.5)
    c.drawString(50, y, doc_title[:80])
    y -= 30

    c.setFont(KOREAN_FONT if KOREAN_FONT != "Helvetica" else "Helvetica-Bold", 13)
    c.setFillColorRGB(0.1, 0.2, 0.6)
    c.drawString(50, y, heading[:70])
    y -= 25

    c.setFillColorRGB(0, 0, 0)
    c.setFont(KOREAN_FONT if KOREAN_FONT != "Helvetica" else "Helvetica", 10)
    for line in body_lines:
        if y < 60:
            c.showPage()
            y = height - 60
            c.setFont(KOREAN_FONT if KOREAN_FONT != "Helvetica" else "Helvetica", 10)
        c.drawString(50, y, line[:90])
        y -= 16


def create_pdf(doc: dict) -> Path:
    out_path = DOWNLOADS_DIR / doc["filename"]
    c = canvas.Canvas(str(out_path), pagesize=A4)
    width, height = A4

    # Cover page
    c.setFont(KOREAN_FONT if KOREAN_FONT != "Helvetica" else "Helvetica-Bold", 18)
    c.setFillColorRGB(0.1, 0.2, 0.6)
    title = doc["title"]
    c.drawString(50, height - 80, title[:40])
    if len(title) > 40:
        c.drawString(50, height - 105, title[40:80])

    c.setFont(KOREAN_FONT if KOREAN_FONT != "Helvetica" else "Helvetica", 12)
    c.setFillColorRGB(0.3, 0.3, 0.3)
    c.drawString(50, height - 135, doc["subtitle"])

    c.setFont(KOREAN_FONT if KOREAN_FONT != "Helvetica" else "Helvetica", 10)
    c.setFillColorRGB(0.5, 0.5, 0.5)
    c.drawString(50, height - 160, "Mail2Task Sample Document — 2026")

    c.showPage()

    for page_data in doc["pages"]:
        draw_page(c, doc["title"], page_data["heading"], page_data["body"], width, height)
        c.showPage()

    c.save()
    return out_path


def main():
    print(f"[INFO] PDF 저장 경로: {DOWNLOADS_DIR}")
    print(f"[INFO] 한국어 폰트: {KOREAN_FONT}")
    print()

    for doc in DOCS:
        try:
            path = create_pdf(doc)
            print(f"[OK] {path.name}")
        except Exception as e:
            print(f"[FAIL] {doc['filename']}: {e}")

    print(f"\n총 {len(DOCS)}개 PDF 생성 완료 → {DOWNLOADS_DIR}")


if __name__ == "__main__":
    main()
