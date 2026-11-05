from __future__ import annotations

import subprocess
from io import BytesIO

from PIL import Image

from app.services import media_service as media_module


def image_bytes(fmt: str = "JPEG", size: tuple[int, int] = (1200, 800), color=(220, 120, 40)) -> bytes:
    output = BytesIO()
    Image.new("RGB", size, color).save(output, format=fmt)
    return output.getvalue()


def video_bytes(duration: int = 2, size: str = "320x240") -> bytes:
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as temporary:
        path = Path(temporary) / "clip.mp4"
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-v",
                "error",
                "-f",
                "lavfi",
                "-i",
                f"testsrc=size={size}:rate=30:duration={duration}",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                str(path),
            ],
            check=True,
        )
        return path.read_bytes()


async def upload(client, data: bytes, mime: str, filename: str = "upload.bin", kind: str | None = None):
    fields = {"kind": kind} if kind else {}
    return await client.post(
        "/v1/media",
        files={"file": (filename, data, mime)},
        data=fields,
    )


async def test_image_formats_are_normalized_and_described(client):
    for fmt, mime, filename in (
        ("JPEG", "image/jpeg", "photo.jpg"),
        ("PNG", "image/png", "photo.png"),
        ("WEBP", "image/webp", "photo.webp"),
    ):
        response = await upload(client, image_bytes(fmt), mime, filename, "image")
        assert response.status_code == 201, response.text
        media = response.json()
        assert media["kind"] == "image"
        assert media["mime"] == "image/jpeg"
        assert media["width"] == 1024
        assert media["height"] <= 1024
        assert media["duration_s"] is None
        assert len(media["sha256"]) == 64
        assert media["status"] == "ready"
        assert any(("JPEG" in warning or "EXIF" in warning or "压缩" in warning) for warning in media["warnings"])

        fetched = await client.get(f"/v1/media/{media['id']}")
        assert fetched.status_code == 200
        assert fetched.json()["id"] == media["id"]


async def test_image_rejects_bad_format_size_and_decode(client, monkeypatch):
    gif = BytesIO()
    Image.new("RGB", (20, 20), (1, 2, 3)).save(gif, format="GIF")
    unsupported = await upload(client, gif.getvalue(), "image/gif", "x.gif", "image")
    assert unsupported.status_code == 415
    assert unsupported.json()["error"]["code"] == "UNSUPPORTED_MEDIA"

    huge = b"\xff\xd8" + b"0" * (10 * 1024 * 1024)
    too_large = await upload(client, huge, "image/jpeg", "huge.jpg", "image")
    assert too_large.status_code == 413
    assert too_large.json()["error"]["code"] == "MEDIA_TOO_LARGE"

    broken = await upload(client, b"not-an-image", "image/jpeg", "broken.jpg", "image")
    assert broken.status_code == 422
    assert broken.json()["error"]["code"] == "MEDIA_DECODE_FAILED"

    heic = await upload(client, b"fake-heic", "image/heic", "photo.heic", "image")
    assert heic.status_code == 415
    assert heic.json()["error"]["code"] == "UNSUPPORTED_MEDIA"


async def test_video_probe_size_duration_and_decode(client, monkeypatch):
    clip = video_bytes(2)
    response = await upload(client, clip, "video/mp4", "clip.mp4", "video")
    assert response.status_code == 201, response.text
    media = response.json()
    assert media["kind"] == "video"
    assert 1.5 <= media["duration_s"] <= 2.5
    assert media["width"] == 320
    assert media["warnings"] == ["本期不分析音频，也不生成转写。"]

    monkeypatch.setattr(media_module, "VIDEO_MAX_BYTES", len(clip) - 1)
    too_large = await upload(client, clip, "video/mp4", "clip.mp4", "video")
    assert too_large.status_code == 413
    assert too_large.json()["error"]["code"] == "MEDIA_TOO_LARGE"
    monkeypatch.setattr(media_module, "VIDEO_MAX_BYTES", 100 * 1024 * 1024)

    long_clip = video_bytes(31, "160x120")
    too_long = await upload(client, long_clip, "video/mp4", "long.mp4", "video")
    assert too_long.status_code == 422
    assert too_long.json()["error"]["code"] == "MEDIA_TOO_LONG"

    broken = await upload(client, b"not-a-video", "video/mp4", "broken.mp4", "video")
    assert broken.status_code == 422
    assert broken.json()["error"]["code"] == "MEDIA_DECODE_FAILED"


async def test_media_delete_blocks_when_feedback_references(client):
    media = (await upload(client, image_bytes(), "image/jpeg", "photo.jpg", "image")).json()
    await client.app.state.store.save_feedback(
        {
            "id": "fb_test_in_use",
            "session_id": "sess_test",
            "media_ids": [media["id"]],
        }
    )
    blocked = await client.delete(f"/v1/media/{media['id']}")
    assert blocked.status_code == 409
    assert blocked.json()["error"]["code"] == "MEDIA_IN_USE"

    client.app.state.store.data_dir.joinpath("feedback", "fb_test_in_use.json").unlink()
    deleted = await client.delete(f"/v1/media/{media['id']}")
    assert deleted.status_code == 204
    missing = await client.get(f"/v1/media/{media['id']}")
    assert missing.status_code == 404