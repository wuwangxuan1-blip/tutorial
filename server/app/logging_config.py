from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

_PATTERNS = [
    (re.compile(r"(?i)(authorization\s*:\s*bearer\s+)\S+"), r"\1[REDACTED]"),
    (re.compile(r"(?i)(DEEPSEEK_API_KEY\s*=\s*)\S+"), r"\1[REDACTED]"),
    (re.compile(r"(?i)(api_key[\"']?\s*[:=]\s*[\"']?)[^\"'\s,}]+"), r"\1[REDACTED]"),
    (re.compile(r"sk-[A-Za-z0-9_\-]{8,}"), "sk-[REDACTED]"),
    (re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._\-]{16,}"), r"\1[REDACTED]"),
]


def redact(value: Any) -> str:
    text = str(value)
    for pattern, replacement in _PATTERNS:
        text = pattern.sub(replacement, text)
    return text


class RedactFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = redact(record.msg)
        if isinstance(record.args, tuple):
            record.args = tuple(redact(item) for item in record.args)
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "level": record.levelname,
            "logger": record.name,
            "message": redact(record.getMessage()),
        }
        for key in (
            "request_id",
            "job_id",
            "session_id",
            "route",
            "status",
            "duration_ms",
            "model",
            "tokens",
            "error_code",
        ):
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = redact(value)
        if record.exc_info and record.levelno >= logging.ERROR:
            payload["exc_type"] = record.exc_info[0].__name__ if record.exc_info[0] else None
        return json.dumps(payload, ensure_ascii=False)


def setup_logging(log_dir: Path, level: int = logging.INFO) -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    root = logging.getLogger()
    root.setLevel(level)
    for handler in list(root.handlers):
        root.removeHandler(handler)
        handler.close()
    formatter = JsonFormatter()
    stream = logging.StreamHandler()
    stream.setFormatter(formatter)
    stream.addFilter(RedactFilter())
    file_handler = RotatingFileHandler(
        log_dir / "app.log", maxBytes=2 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    file_handler.addFilter(RedactFilter())
    root.addHandler(stream)
    root.addHandler(file_handler)
    logging.getLogger("uvicorn.access").disabled = True
    logging.getLogger("httpx").setLevel(logging.WARNING)