from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from app.config import Settings
from app.errors import ApiError
from app.services.model_client import ModelClient


def make_settings(tmp_path: Path, api_key: str | None = "test-key-value") -> Settings:
    data_dir = tmp_path / "data"
    return Settings(
        base_url="https://api.deepseek.com",
        api_key=api_key,
        text_model="deepseek-flash",
        vision_model="deepseek-flash",
        model_timeout_s=10.0,
        job_timeout_s=20.0,
        data_dir=data_dir,
        log_dir=data_dir / "logs",
        queue_max=5,
    )


def make_client(tmp_path: Path, handler, api_key: str | None = "test-key-value") -> ModelClient:
    return ModelClient(
        make_settings(tmp_path, api_key),
        transport=httpx.MockTransport(handler),
    )


async def test_missing_key_fails_without_calling_transport(tmp_path):
    called = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        called["count"] += 1
        return httpx.Response(200, json={})

    client = make_client(tmp_path, handler, api_key=None)
    with pytest.raises(ApiError) as error:
        await client.chat_json("system", "user")
    assert error.value.code == "MODEL_NOT_CONFIGURED"
    assert error.value.status_code == 503
    assert called["count"] == 0


async def test_rate_limit_maps_retry_after(tmp_path):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            429,
            headers={"retry-after": "7"},
            json={"error": {"message": "rate limited"}},
        )

    client = make_client(tmp_path, handler)
    with pytest.raises(ApiError) as error:
        await client.chat_json("system", "user")
    assert error.value.code == "MODEL_RATE_LIMITED"
    assert error.value.status_code == 429
    assert error.value.retryable is True
    assert error.value.retry_after_s == 7


async def test_timeout_maps_to_model_timeout(tmp_path):
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timed out", request=request)

    client = make_client(tmp_path, handler)
    with pytest.raises(ApiError) as error:
        await client.chat_json("system", "user")
    assert error.value.code == "MODEL_TIMEOUT"
    assert error.value.status_code == 504
    assert error.value.retryable is True


async def test_invalid_json_maps_to_bad_output_with_reason(tmp_path):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {"content": "this is not json"},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"total_tokens": 12},
            },
        )

    client = make_client(tmp_path, handler)
    with pytest.raises(ApiError) as error:
        await client.chat_json("system", "user")
    assert error.value.code == "MODEL_BAD_OUTPUT"
    assert error.value.retryable is True
    assert error.value.details["reason"] == "invalid_json"


async def test_empty_content_maps_with_reason(tmp_path):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {"content": "", "reasoning_content": "thinking"},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"total_tokens": 40},
            },
        )

    client = make_client(tmp_path, handler)
    with pytest.raises(ApiError) as error:
        await client.chat_json("system", "user")
    assert error.value.code == "MODEL_BAD_OUTPUT"
    assert error.value.details["reason"] == "empty_content"


async def test_refusal_http_error_maps_to_model_refused(tmp_path):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            400,
            json={"error": {"message": "Content policy violation"}},
        )

    client = make_client(tmp_path, handler)
    with pytest.raises(ApiError) as error:
        await client.chat_json("system", "user")
    assert error.value.code == "MODEL_REFUSED"
    assert error.value.status_code == 422


async def test_content_filter_finish_reason_maps_to_model_refused(tmp_path):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {"content": "blocked"},
                        "finish_reason": "content_filter",
                    }
                ]
            },
        )

    client = make_client(tmp_path, handler)
    with pytest.raises(ApiError) as error:
        await client.chat_json("system", "user")
    assert error.value.code == "MODEL_REFUSED"


async def test_success_returns_parsed_json(tmp_path):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {"content": '{"status":"ok","value":42}'},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"total_tokens": 8},
            },
        )

    client = make_client(tmp_path, handler)
    assert await client.chat_json("system", "user") == {"status": "ok", "value": 42}