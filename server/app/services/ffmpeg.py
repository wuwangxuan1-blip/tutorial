from __future__ import annotations

import asyncio
import json
import math
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..errors import ApiError

_FFMPEG = shutil.which("ffmpeg")
_FFPROBE = shutil.which("ffprobe")
_FRAME_HEADER = re.compile(r"Frame\s+(\d+)", re.IGNORECASE)


class FFmpegError(Exception):
    pass


@dataclass
class Frame:
    index: int
    timestamp_s: float
    path: Path


def ffmpeg_available() -> bool:
    return bool(_FFMPEG and _FFPROBE)


def _run_sync(
    args: list[str],
    timeout_s: float,
    cwd: Path | None,
) -> tuple[int, bytes, bytes]:
    try:
        completed = subprocess.run(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_s,
            cwd=str(cwd) if cwd else None,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise FFmpegError("ffmpeg 处理超时") from exc
    except OSError as exc:
        raise FFmpegError("无法启动 ffmpeg/ffprobe") from exc
    return completed.returncode or 0, completed.stdout or b"", completed.stderr or b""


async def _run(args: list[str], timeout_s: float, cwd: Path | None = None) -> tuple[int, bytes, bytes]:
    return await asyncio.to_thread(_run_sync, args, timeout_s, cwd)


async def probe(path: Path) -> dict[str, Any]:
    if not _FFPROBE:
        raise FFmpegError("ffprobe 不可用")
    code, stdout, stderr = await _run(
        [
            _FFPROBE,
            "-v",
            "error",
            "-show_format",
            "-show_streams",
            "-of",
            "json",
            str(path),
        ],
        timeout_s=10,
    )
    if code != 0:
        raise FFmpegError(stderr.decode("utf-8", "replace")[:300] or "ffprobe 失败")
    try:
        return json.loads(stdout.decode("utf-8", "replace"))
    except json.JSONDecodeError as exc:
        raise FFmpegError("ffprobe 输出不可解析") from exc


async def decode_first_frame(path: Path, temp_dir: Path) -> None:
    if not _FFMPEG:
        raise FFmpegError("ffmpeg 不可用")
    output = temp_dir / "decode_probe.jpg"
    code, _, stderr = await _run(
        [
            _FFMPEG,
            "-v",
            "error",
            "-y",
            "-i",
            str(path),
            "-frames:v",
            "1",
            "-q:v",
            "5",
            str(output),
        ],
        timeout_s=15,
    )
    if code != 0 or not output.exists() or output.stat().st_size == 0:
        raise FFmpegError(stderr.decode("utf-8", "replace")[:300] or "视频解码失败")


def _target_size(width: int, height: int, long_edge: int = 1024) -> tuple[int, int]:
    if width >= height:
        target_width = min(width, long_edge)
        target_height = max(2, round(height * target_width / width))
    else:
        target_height = min(height, long_edge)
        target_width = max(2, round(width * target_height / height))
    if target_width % 2:
        target_width -= 1
    if target_height % 2:
        target_height -= 1
    return max(2, target_width), max(2, target_height)


async def extract_frames(
    path: Path,
    width: int,
    height: int,
    duration_s: float,
    temp_dir: Path,
    max_frames: int = 8,
) -> list[Frame]:
    if not _FFMPEG:
        raise FFmpegError("ffmpeg 不可用")
    count = min(max_frames, max(1, math.ceil(duration_s)))
    target_width, target_height = _target_size(width, height)
    frames: list[Frame] = []
    for index in range(count):
        timestamp = float(index)
        if timestamp >= duration_s and duration_s > 0:
            break
        output = temp_dir / f"frame_{index}.jpg"
        code, _, stderr = await _run(
            [
                _FFMPEG,
                "-v",
                "error",
                "-y",
                "-ss",
                f"{timestamp:.3f}",
                "-i",
                str(path),
                "-frames:v",
                "1",
                "-vf",
                f"scale={target_width}:{target_height}",
                "-q:v",
                "3",
                str(output),
            ],
            timeout_s=20,
        )
        if code != 0 or not output.exists() or output.stat().st_size == 0:
            raise FFmpegError(stderr.decode("utf-8", "replace")[:300] or "抽帧失败")
        frames.append(Frame(index=index, timestamp_s=timestamp, path=output))
    if not frames:
        raise FFmpegError("未抽到任何帧")
    return frames


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(round((percentile / 100) * (len(ordered) - 1)))))
    return ordered[index]


def _parse_global_motions(path: Path) -> list[tuple[float, float, float]]:
    if not path.exists():
        raise FFmpegError("vidstabtransform 未生成 global_motions.trf")
    values: list[tuple[float, float, float]] = []
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        try:
            numbers = [float(token) for token in line.replace(",", " ").split()]
        except ValueError:
            continue
        if len(numbers) < 4:
            continue
        dx, dy, angle_rad = numbers[1], numbers[2], numbers[3]
        values.append((dx, dy, abs(angle_rad) * 180 / math.pi))
    if len(values) < 2:
        raise FFmpegError("global_motions.trf 结果不可解析")
    return values


async def motion_metrics(path: Path, temp_dir: Path) -> dict[str, Any] | None:
    if not _FFMPEG:
        return None
    result_file = temp_dir / "transforms.trf"
    filter_expr = (
        "fps=10,scale=320:-2,format=gray,"
        f"vidstabdetect=fileformat=ascii:result={result_file.name}"
    )
    code, _, _ = await _run(
        [
            _FFMPEG,
            "-v",
            "error",
            "-y",
            "-i",
            str(path),
            "-vf",
            filter_expr,
            "-f",
            "null",
            "-",
        ],
        timeout_s=90,
        cwd=temp_dir,
    )
    if code != 0:
        return None
    code, _, _ = await _run(
        [
            _FFMPEG,
            "-v",
            "error",
            "-y",
            "-i",
            str(path),
            "-vf",
            "vidstabtransform=input=transforms.trf:debug=1",
            "-f",
            "null",
            "-",
        ],
        timeout_s=90,
        cwd=temp_dir,
    )
    if code != 0:
        return None
    try:
        transforms = _parse_global_motions(temp_dir / "global_motions.trf")
    except FFmpegError:
        return None
    translations = [math.hypot(dx, dy) for dx, dy, _ in transforms]
    rotations = [rotation for _, _, rotation in transforms]
    direction_changes = 0
    last_sign = 0
    for dx, dy, _ in transforms:
        dominant = dx if abs(dx) >= abs(dy) else dy
        sign = 1 if dominant > 0.05 else (-1 if dominant < -0.05 else 0)
        if sign != 0 and last_sign != 0 and sign != last_sign:
            direction_changes += 1
        if sign != 0:
            last_sign = sign
    return {
        "method": "vidstabdetect_ascii_10fps_320px+global_motions",
        "sample_fps": 10,
        "frame_count": len(transforms),
        "mean_translation_px": round(sum(translations) / len(translations), 3),
        "p95_translation_px": round(_percentile(translations, 95), 3),
        "mean_rotation_deg": round(sum(rotations) / len(rotations), 3),
        "direction_changes": direction_changes,
        "limitations": [
            "基于 2D 图像平面估计，不还原真实 3D 轨迹。",
            "无法可靠区分主体运动与相机运动。",
            "快速运动、低纹理、遮挡会导致估计失败或偏差。",
            "不是 0–100 的稳定性评分，不能用于精确比较。",
        ],
    }
async def with_temp_dir() -> tempfile.TemporaryDirectory[str]:
    return tempfile.TemporaryDirectory(prefix="tutorial_media_")