from __future__ import annotations

import argparse
import json
import os
import struct
import sys
import time
import zlib
from datetime import datetime, timezone
from pathlib import Path

import httpx
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ENV = PROJECT_ROOT / "server" / ".env"
DEFAULT_OUTPUT = PROJECT_ROOT / "codearts_proof" / "day1" / "model_probe.json"
DATA_COPY = PROJECT_ROOT / "server" / "data" / "model_probe.json"


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def redact(text: str, api_key: str | None) -> str:
    value = str(text)
    if api_key:
        value = value.replace(api_key, "[REDACTED]")
    if len(value) > 400:
        value = value[:400] + "…"
    return value


def make_png(width: int = 64, height: int = 64) -> bytes:
    def chunk(kind: bytes, payload: bytes) -> bytes:
        return (
            struct.pack(">I", len(payload))
            + kind
            + payload
            + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
        )

    row = b"\x00" + bytes([230, 130, 40] * width)
    raw = row * height
    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(raw))
        + chunk(b"IEND", b"")
    )


def request_json(
    client: httpx.Client,
    method: str,
    url: str,
    api_key: str,
    payload: dict | None = None,
) -> tuple[int | None, dict | None, str | None, int]:
    started = time.perf_counter()
    try:
        response = client.request(
            method,
            url,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
        )
    except httpx.HTTPError as exc:
        return None, None, redact(str(exc), api_key), int((time.perf_counter() - started) * 1000)
    elapsed = int((time.perf_counter() - started) * 1000)
    try:
        body = response.json()
    except ValueError:
        body = {"_raw": redact(response.text, api_key)}
    return response.status_code, body, None, elapsed


def summarize_error(body: dict | None, api_key: str) -> str:
    if not isinstance(body, dict):
        return "invalid response"
    error = body.get("error")
    if isinstance(error, dict):
        return redact(f"{error.get('type', '')}: {error.get('message', '')}".strip(": "), api_key)
    return redact(str(body)[:300], api_key)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-file", default=str(DEFAULT_ENV))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--data-copy", default=str(DATA_COPY))
    args = parser.parse_args()

    env_path = Path(args.env_file)
    load_dotenv(env_path, override=False)
    api_key = (os.getenv("DEEPSEEK_API_KEY") or "").strip() or None
    base_url = (os.getenv("DEEPSEEK_BASE_URL") or "https://api.deepseek.com").rstrip("/")
    text_model = (os.getenv("DEEPSEEK_TEXT_MODEL") or "").strip() or None
    vision_model = (os.getenv("DEEPSEEK_VISION_MODEL") or "").strip() or None
    output_path = Path(args.output)
    data_copy = Path(args.data_copy)
    started_at = now()

    if not api_key:
        result = {"blocked": "NO_KEY", "checked_at": started_at}
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False))
        return 2

    result: dict = {
        "started_at": started_at,
        "finished_at": None,
        "base_url": base_url,
        "text_model": text_model,
        "vision_model": vision_model,
        "key_present": True,
        "models": {},
        "text": {},
        "json": {},
        "image": {},
        "tool_call": {"status": "skipped", "reason": "P0 不依赖工具调用"},
    }

    with httpx.Client(timeout=httpx.Timeout(120.0, connect=15.0)) as client:
        status, body, error, elapsed = request_json(client, "GET", f"{base_url}/models", api_key)
        model_ids = []
        if isinstance(body, dict) and isinstance(body.get("data"), list):
            model_ids = [item.get("id") for item in body["data"] if isinstance(item, dict) and item.get("id")]
        result["models"] = {
            "status": "ok" if status == 200 else "failed",
            "http_status": status,
            "latency_ms": elapsed,
            "model_ids": model_ids,
            "error": None if status == 200 else (error or summarize_error(body, api_key)),
        }

        text_payload = {
            "model": text_model,
            "messages": [{"role": "user", "content": "只回复两个字：收到"}],
            "max_tokens": 64,
            "temperature": 0,
            "stream": False,
        }
        status, body, error, elapsed = request_json(client, "POST", f"{base_url}/chat/completions", api_key, text_payload)
        content = None
        usage = None
        finish_reason = None
        if isinstance(body, dict):
            choices = body.get("choices")
            if isinstance(choices, list) and choices:
                message = choices[0].get("message") or {}
                content = message.get("content")
                finish_reason = choices[0].get("finish_reason")
            usage = body.get("usage")
        result["text"] = {
            "status": "ok" if status == 200 and content else "failed",
            "http_status": status,
            "latency_ms": elapsed,
            "model": text_model,
            "finish_reason": finish_reason,
            "output_excerpt": redact(content, api_key) if content else None,
            "usage": usage,
            "error": None if status == 200 and content else (error or summarize_error(body, api_key)),
        }

        json_payload = {
            "model": text_model,
            "messages": [
                {"role": "system", "content": "只输出 JSON，不要 Markdown。"},
                {"role": "user", "content": '输出 JSON：{"status":"ok","value":42}'},
            ],
            "response_format": {"type": "json_object"},
            "max_tokens": 256,
            "temperature": 0,
            "stream": False,
        }
        status, body, error, elapsed = request_json(client, "POST", f"{base_url}/chat/completions", api_key, json_payload)
        parsed = None
        raw_content = None
        if isinstance(body, dict):
            choices = body.get("choices")
            if isinstance(choices, list) and choices:
                raw_content = (choices[0].get("message") or {}).get("content")
        if status == 200 and raw_content:
            try:
                parsed = json.loads(raw_content)
            except json.JSONDecodeError:
                parsed = None
        json_ok = (
            isinstance(parsed, dict)
            and parsed.get("status") == "ok"
            and parsed.get("value") == 42
        )
        result["json"] = {
            "status": "ok" if json_ok else "failed",
            "http_status": status,
            "latency_ms": elapsed,
            "model": text_model,
            "parsed": parsed,
            "output_excerpt": redact(raw_content, api_key) if raw_content else None,
            "error": None if json_ok else (error or summarize_error(body, api_key)),
        }

        png_base64 = __import__("base64").b64encode(make_png()).decode("ascii")
        vision_payload = {
            "model": vision_model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "这张图主要是什么颜色？只回答颜色。"},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{png_base64}"},
                        },
                    ],
                }
            ],
            "max_tokens": 512,
            "temperature": 0,
            "stream": False,
        }
        status, body, error, elapsed = request_json(client, "POST", f"{base_url}/chat/completions", api_key, vision_payload)
        vision_content = None
        vision_finish_reason = None
        if isinstance(body, dict):
            choices = body.get("choices")
            if isinstance(choices, list) and choices:
                vision_content = (choices[0].get("message") or {}).get("content")
                vision_finish_reason = choices[0].get("finish_reason")
        if status == 200 and vision_content:
            image_status = "ok"
            image_error = None
        elif status in (400, 404, 422):
            image_status = "unsupported"
            image_error = error or summarize_error(body, api_key)
        else:
            image_status = "failed"
            if status == 200:
                image_error = f"empty content (finish_reason={vision_finish_reason})"
            else:
                image_error = error or summarize_error(body, api_key)
        result["image"] = {
            "status": image_status,
            "http_status": status,
            "latency_ms": elapsed,
            "model": vision_model,
            "finish_reason": vision_finish_reason,
            "output_excerpt": redact(vision_content, api_key) if vision_content else None,
            "error": image_error,
            "note": "使用本地生成的 64x64 橙色 PNG；未上传任何个人图片。",
        }

    result["finished_at"] = now()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    data_copy.parent.mkdir(parents=True, exist_ok=True)
    data_copy.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "text": result["text"]["status"],
                "json": result["json"]["status"],
                "image": result["image"]["status"],
                "output": str(output_path),
            },
            ensure_ascii=False,
        )
    )
    return 0 if result["text"]["status"] == "ok" and result["json"]["status"] == "ok" else 3


if __name__ == "__main__":
    sys.exit(main())