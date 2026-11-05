from __future__ import annotations

import hashlib
import tempfile
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import Image, ImageOps, UnidentifiedImageError

from ..errors import ApiError, not_found
from ..ids import new_id
from ..models.media import MediaOut
from .ffmpeg import FFmpegError, decode_first_frame, probe
from .store import JsonStore

IMAGE_MIMES = {"image/jpeg", "image/png", "image/webp"}
VIDEO_MIMES = {"video/mp4", "video/quicktime"}
IMAGE_MAX_BYTES = 10 * 1024 * 1024
VIDEO_MAX_BYTES = 100 * 1024 * 1024
VIDEO_MAX_SECONDS = 30.0
MODEL_LONG_EDGE = 1024
HEIC_MIMES = {"image/heic", "image/heif"}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def public_media(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": data["id"],
        "kind": data["kind"],
        "mime": data["mime"],
        "size_bytes": data["size_bytes"],
        "width": data["width"],
        "height": data["height"],
        "duration_s": data.get("duration_s"),
        "sha256": data["sha256"],
        "status": data.get("status", "ready"),
        "warnings": data.get("warnings") or [],
        "created_at": data["created_at"],
    }


class MediaService:
    def __init__(self, store: JsonStore) -> None:
        self.store = store

    async def upload(
        self,
        content: bytes,
        content_type: str | None,
        kind_hint: str | None,
        filename: str | None,
    ) -> dict[str, Any]:
        if not content:
            raise ApiError(422, "MEDIA_DECODE_FAILED", "上传文件为空。")
        mime = (content_type or "").split(";")[0].strip().lower()
        if mime in HEIC_MIMES:
            raise ApiError(
                415,
                "UNSUPPORTED_MEDIA",
                "HEIC/HEIF 请先在 App 中转换为 JPEG 再上传。",
            )
        kind = kind_hint if kind_hint in {"image", "video"} else None
        if kind is None:
            if mime in IMAGE_MIMES:
                kind = "image"
            elif mime in VIDEO_MIMES:
                kind = "video"
        if kind == "image":
            return await self._save_image(content, mime, filename)
        if kind == "video":
            return await self._save_video(content, mime, filename)
        raise ApiError(
            415,
            "UNSUPPORTED_MEDIA",
            "仅支持 JPEG/PNG/WebP 图片或 MP4/MOV 视频。",
        )

    async def _save_image(
        self,
        content: bytes,
        mime: str,
        filename: str | None,
    ) -> dict[str, Any]:
        if len(content) > IMAGE_MAX_BYTES:
            raise ApiError(413, "MEDIA_TOO_LARGE", "图片不能超过 10 MiB。")
        try:
            with Image.open(BytesIO(content)) as source:
                image_format = (source.format or "").upper()
                if image_format not in {"JPEG", "PNG", "WEBP"}:
                    raise ApiError(
                        415,
                        "UNSUPPORTED_MEDIA",
                        "仅支持 JPEG/PNG/WebP 图片；HEIC/HEIF 请先在 App 中转换。",
                    )
                original_width, original_height = source.size
                image = ImageOps.exif_transpose(source).convert("RGB")
        except ApiError:
            raise
        except (UnidentifiedImageError, Image.DecompressionBombError, OSError, ValueError) as exc:
            raise ApiError(422, "MEDIA_DECODE_FAILED", "图片无法解码，请换一张图。") from exc

        warnings: list[str] = []
        long_edge = max(original_width, original_height)
        if long_edge > MODEL_LONG_EDGE:
            ratio = MODEL_LONG_EDGE / long_edge
            image = image.resize(
                (max(1, round(original_width * ratio)), max(1, round(original_height * ratio))),
                Image.Resampling.LANCZOS,
            )
            warnings.append("已按长边 1024 压缩，仅用于模型分析与预览。")
        if image_format != "JPEG" or mime != "image/jpeg":
            warnings.append("已转换为 JPEG 并去除 EXIF。")

        output = BytesIO()
        image.save(output, format="JPEG", quality=85, optimize=True)
        stored = output.getvalue()
        if len(stored) > IMAGE_MAX_BYTES:
            raise ApiError(413, "MEDIA_TOO_LARGE", "图片压缩后仍超过 10 MiB。")
        media_id = new_id("media")
        path = self.store.media_file_path(media_id, ".jpg")
        path.write_bytes(stored)
        data = {
            "id": media_id,
            "kind": "image",
            "mime": "image/jpeg",
            "size_bytes": len(stored),
            "width": image.width,
            "height": image.height,
            "duration_s": None,
            "sha256": hashlib.sha256(stored).hexdigest(),
            "status": "ready",
            "warnings": warnings,
            "created_at": _now(),
        }
        await self.store.save_media(data)
        return public_media(data)

    async def _save_video(
        self,
        content: bytes,
        mime: str,
        filename: str | None,
    ) -> dict[str, Any]:
        if len(content) > VIDEO_MAX_BYTES:
            raise ApiError(413, "MEDIA_TOO_LARGE", "视频不能超过 100 MiB。")
        suffix = ".mov" if (mime == "video/quicktime" or (filename or "").lower().endswith(".mov")) else ".mp4"
        with tempfile.TemporaryDirectory(prefix="tutorial_video_") as temporary:
            temp_path = Path(temporary) / f"upload{suffix}"
            temp_path.write_bytes(content)
            try:
                info = await probe(temp_path)
            except FFmpegError as exc:
                raise ApiError(422, "MEDIA_DECODE_FAILED", "视频无法解码，请转为 H.264 MP4 后重试。") from exc
            format_info = info.get("format") or {}
            format_name = str(format_info.get("format_name") or "")
            if not any(name in format_name for name in ("mp4", "mov")):
                raise ApiError(415, "UNSUPPORTED_MEDIA", "仅支持 MP4/MOV 视频。")
            duration = format_info.get("duration")
            try:
                duration_s = float(duration) if duration is not None else 0.0
            except (TypeError, ValueError):
                duration_s = 0.0
            streams = info.get("streams") or []
            video_stream = next((item for item in streams if item.get("codec_type") == "video"), None)
            if video_stream is None or duration_s <= 0:
                raise ApiError(422, "MEDIA_DECODE_FAILED", "视频缺少可解码的画面或时长。")
            if duration_s > VIDEO_MAX_SECONDS + 0.01:
                raise ApiError(422, "MEDIA_TOO_LONG", "视频不能超过 30 秒，请先裁剪。")
            try:
                width = int(video_stream.get("width") or 0)
                height = int(video_stream.get("height") or 0)
            except (TypeError, ValueError):
                width = height = 0
            if width <= 0 or height <= 0:
                raise ApiError(422, "MEDIA_DECODE_FAILED", "视频分辨率无法读取。")
            try:
                await decode_first_frame(temp_path, Path(temporary))
            except FFmpegError as exc:
                raise ApiError(422, "MEDIA_DECODE_FAILED", "视频解码失败，请转为 H.264 MP4。") from exc

        media_id = new_id("media")
        path = self.store.media_file_path(media_id, suffix)
        path.write_bytes(content)
        data = {
            "id": media_id,
            "kind": "video",
            "mime": "video/quicktime" if suffix == ".mov" else "video/mp4",
            "size_bytes": len(content),
            "width": width,
            "height": height,
            "duration_s": round(duration_s, 3),
            "sha256": hashlib.sha256(content).hexdigest(),
            "status": "ready",
            "warnings": ["本期不分析音频，也不生成转写。"],
            "created_at": _now(),
        }
        await self.store.save_media(data)
        return public_media(data)

    async def get(self, media_id: str) -> dict[str, Any]:
        data = await self.store.load_media(media_id)
        if not data:
            raise not_found("媒体不存在。")
        return public_media(data)

    async def get_internal(self, media_id: str) -> dict[str, Any]:
        data = await self.store.load_media(media_id)
        if not data:
            raise not_found("媒体不存在。")
        return data

    async def delete(self, media_id: str) -> None:
        data = await self.store.load_media(media_id)
        if not data:
            raise not_found("媒体不存在。")
        if await self.store.media_referenced(media_id):
            raise ApiError(409, "MEDIA_IN_USE", "媒体已被反馈引用，不能删除。")
        path = self.store.media_file_path(
            media_id,
            ".jpg" if data["kind"] == "image" else (".mov" if data["mime"] == "video/quicktime" else ".mp4"),
        )
        path.unlink(missing_ok=True)
        (self.store.data_dir / self.store.media_json_rel(media_id)).unlink(missing_ok=True)

    def file_path(self, data: dict[str, Any]) -> Path:
        return self.store.media_file_path(
            data["id"],
            ".jpg"
            if data["kind"] == "image"
            else (".mov" if data["mime"] == "video/quicktime" else ".mp4"),
        )