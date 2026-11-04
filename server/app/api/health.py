from __future__ import annotations

import asyncio
import json
import logging
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request

logger = logging.getLogger("tutorial_coach.health")

router = APIRouter()


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _ffmpeg_available() -> bool:
    executable = shutil.which("ffmpeg")
    if not executable:
        return False
    try:
        result = subprocess.run(
            [executable, "-version"],
            capture_output=True,
            timeout=5,
            check=False,
            text=True,
        )
        return result.returncode == 0 and result.stdout.startswith("ffmpeg version")
    except (OSError, subprocess.SubprocessError):
        return False


def _read_probe(data_dir: Path) -> dict[str, Any] | None:
    path = data_dir / "model_probe.json"
    if not path.exists():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


@router.get("/health")
async def health(request: Request) -> dict[str, Any]:
    settings = request.app.state.settings
    store = request.app.state.store
    checks = {
        "store": store.check_writable(),
        "ffmpeg": await asyncio.to_thread(_ffmpeg_available),
        "model_configured": settings.model_configured,
    }
    return {
        "status": "ok" if all(checks.values()) else "degraded",
        "api_version": "v1",
        "time": _now(),
        "checks": checks,
    }


@router.get("/capabilities")
async def capabilities(request: Request) -> dict[str, Any]:
    settings = request.app.state.settings
    probe = _read_probe(settings.data_dir)
    vision_supported = None
    probe_at = None
    if probe:
        vision = (probe.get("image") or {}).get("status")
        if vision in ("ok", "unsupported", "failed"):
            vision_supported = vision == "ok"
            probe_at = probe.get("finished_at")
    return {
        "api_version": "v1",
        "domains": ["cooking", "photography", "software", "coffee"],
        "media": {
            "image_max_bytes": 10485760,
            "image_max_count": 4,
            "image_mimes": ["image/jpeg", "image/png", "image/webp"],
            "video_max_bytes": 104857600,
            "video_max_duration_s": 30,
            "video_mimes": ["video/mp4", "video/quicktime"],
            "document_max_bytes": 5242880,
            "text_max_chars": 20000,
            "url_max_bytes": 2097152,
        },
        "model": {
            "text_model": settings.text_model,
            "vision_model": settings.vision_model,
            "configured": settings.model_configured,
            "vision_supported": vision_supported,
            "probe_at": probe_at,
            "audio_analysis": False,
        },
        "limits": {
            "plan_steps_max": 15,
            "feedback_images_max": 4,
            "video_frames_max": 8,
            "motion_fps": 10,
            "motion_frames_max": 300,
            "reference_text_max_chars": 20000,
            "reference_total_max_chars": 20000,
        },
    }