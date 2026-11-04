from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"
load_dotenv(ENV_FILE, override=False)


@dataclass(frozen=True)
class Settings:
    base_url: str
    api_key: str | None
    text_model: str | None
    vision_model: str | None
    model_timeout_s: float
    job_timeout_s: float
    data_dir: Path
    log_dir: Path
    queue_max: int

    @property
    def model_configured(self) -> bool:
        return bool(self.api_key and self.text_model)


def _float_env(name: str, default: float) -> float:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def load_settings() -> Settings:
    data_dir = Path(os.getenv("TUTORIAL_DATA_DIR", str(BASE_DIR / "data"))).resolve()
    return Settings(
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/"),
        api_key=(os.getenv("DEEPSEEK_API_KEY") or "").strip() or None,
        text_model=(os.getenv("DEEPSEEK_TEXT_MODEL") or "").strip() or None,
        vision_model=(os.getenv("DEEPSEEK_VISION_MODEL") or "").strip() or None,
        model_timeout_s=_float_env("DEEPSEEK_TIMEOUT_S", 90.0),
        job_timeout_s=_float_env("JOB_TIMEOUT_S", 180.0),
        data_dir=data_dir,
        log_dir=data_dir / "logs",
        queue_max=_int_env("JOB_QUEUE_MAX", 20),
    )