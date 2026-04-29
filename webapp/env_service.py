from __future__ import annotations

import importlib
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class EnvStatus:
    """설정 화면에서 필요한 최소 상태(비밀번호는 값 자체를 들고 다니지 않음)."""
    email: str
    has_password: bool


def _project_root() -> Path:
    # webapp/ 바로 위가 프로젝트 루트(.env가 있는 위치)
    return Path(__file__).resolve().parents[1]


def env_path() -> Path:
    return _project_root() / ".env"


def get_env_status() -> EnvStatus:
    # config.py는 .env를 읽어 os.environ에 반영하므로,
    # 웹에서도 동일 키(TASK_EMAIL/TASK_PASSWORD)를 기준으로 상태를 판단한다.
    email = (os.environ.get("TASK_EMAIL") or "").strip()
    password = (os.environ.get("TASK_PASSWORD") or "").strip()
    return EnvStatus(email=email, has_password=bool(password))


def mask_secret(value: str, keep_last: int = 2) -> str:
    """보안 표시용 마스킹. (실제 비밀번호를 UI에 재표시하지 않기 위한 용도)"""
    if not value:
        return ""
    raw = value.strip()
    if len(raw) <= keep_last:
        return "*" * len(raw)
    return "*" * (len(raw) - keep_last) + raw[-keep_last:]


def upsert_env_values(values: dict[str, str]) -> None:
    """
    .env 파일을 안전하게 갱신한다.
    - 기존 라인/주석은 최대한 유지
    - 동일 키가 있으면 값을 갱신
    - 없으면 파일 끝에 추가

    주의:
    - 비밀번호는 UI에서 “공란이면 유지” 전략을 사용하므로,
      여기서는 전달된 키만 변경한다.
    """
    path = env_path()
    existing_lines: list[str] = []
    if path.exists():
        existing_lines = path.read_text(encoding="utf-8").splitlines()

    target_keys = set(values.keys())
    out_lines: list[str] = []
    seen: set[str] = set()

    for raw_line in existing_lines:
        line = raw_line
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in line:
            out_lines.append(line)
            continue

        key, _ = line.split("=", 1)
        key = key.strip()
        if key in target_keys:
            new_value = values[key]
            # 공백/특수문자 대응을 위해 기본적으로 쿼팅한다.
            rendered = f"{key}={_quote_env_value(new_value)}"
            out_lines.append(rendered)
            seen.add(key)
        else:
            out_lines.append(line)

    for key in values:
        if key in seen:
            continue
        out_lines.append(f"{key}={_quote_env_value(values[key])}")

    path.write_text("\n".join(out_lines).rstrip() + "\n", encoding="utf-8")

    # 현재 프로세스에도 반영 + config 재로딩(웹에서 즉시 사용)
    for key, value in values.items():
        os.environ[key] = value

    try:
        import config

        # config는 import 시점에 .env를 읽고 상수(EMAIL/PASSWORD)를 만든다.
        # 설정 저장 후 바로 테스트/동기화를 누르면 최신 값이 필요하므로 reload한다.
        importlib.reload(config)
    except Exception:
        pass


def _quote_env_value(value: str) -> str:
    # .env는 단순 KEY=VALUE 포맷이므로, 공백이 있는 값(앱 비밀번호 등)은 쿼팅이 안전하다.
    raw = (value or "").strip()
    escaped = raw.replace('"', '\\"')
    return f"\"{escaped}\""

