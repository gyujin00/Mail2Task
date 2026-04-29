from __future__ import annotations

import importlib
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class EnvStatus:
    """Minimal settings-page state without exposing the raw password."""

    email: str
    has_password: bool


def _project_root() -> Path:
    """Return the project root where `.env` lives."""
    return Path(__file__).resolve().parents[1]


def env_path() -> Path:
    return _project_root() / ".env"


def get_env_status() -> EnvStatus:
    """Read the current credential status from process environment variables."""
    email = (os.environ.get("TASK_EMAIL") or "").strip()
    password = (os.environ.get("TASK_PASSWORD") or "").strip()
    return EnvStatus(email=email, has_password=bool(password))


def reload_runtime_config():
    """Reload `core.config` so running web requests see the latest `.env` values."""
    config_module = importlib.import_module("core.config")
    return importlib.reload(config_module)


def mask_secret(value: str, keep_last: int = 2) -> str:
    """Mask sensitive values before showing them in the UI."""
    if not value:
        return ""
    raw = value.strip()
    if len(raw) <= keep_last:
        return "*" * len(raw)
    return "*" * (len(raw) - keep_last) + raw[-keep_last:]


def upsert_env_values(values: dict[str, str]) -> None:
    """
    Update `.env` while preserving unrelated lines and comments.

    Matching keys are replaced in place, and missing keys are appended.
    """
    path = env_path()
    existing_lines: list[str] = []
    if path.exists():
        existing_lines = path.read_text(encoding="utf-8").splitlines()

    target_keys = set(values.keys())
    out_lines: list[str] = []
    seen: set[str] = set()

    for raw_line in existing_lines:
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#") or "=" not in raw_line:
            out_lines.append(raw_line)
            continue

        key, _ = raw_line.split("=", 1)
        key = key.strip()
        if key in target_keys:
            out_lines.append(f"{key}={_quote_env_value(values[key])}")
            seen.add(key)
        else:
            out_lines.append(raw_line)

    for key in values:
        if key not in seen:
            out_lines.append(f"{key}={_quote_env_value(values[key])}")

    path.write_text("\n".join(out_lines).rstrip() + "\n", encoding="utf-8")

    for key, value in values.items():
        os.environ[key] = value

    try:
        reload_runtime_config()
    except Exception:
        pass


def _quote_env_value(value: str) -> str:
    """Quote values safely for `.env` storage."""
    raw = (value or "").strip()
    escaped = raw.replace('"', '\\"')
    return f"\"{escaped}\""
