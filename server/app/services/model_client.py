from __future__ import annotations

import json
import logging
import re
import time
from typing import Any

import httpx

from ..config import Settings
from ..errors import ApiError
from ..logging_config import redact

_FENCE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL)
logger = logging.getLogger("tutorial_coach.model")
_REFUSAL_MARKERS = (
    "content policy",
    "content_filter",
    "content filter",
    "safety policy",
    "refus",
    "violat",
    "敏感",
    "违规",
    "风险内容",
)


class ModelClient:
    def __init__(
        self,
        settings: Settings,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.settings = settings
        self.transport = transport

    async def chat_json(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str | None = None,
        timeout_s: float | None = None,
    ) -> dict[str, Any]:
        if not self.settings.api_key or not (model or self.settings.text_model):
            raise ApiError(503, "MODEL_NOT_CONFIGURED", "服务端未配置模型 Key，请检查 server/.env。")
        selected_model = model or self.settings.text_model
        timeout = timeout_s if timeout_s is not None else self.settings.model_timeout_s
        payload = {
            "model": selected_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
            "max_tokens": 8192,
            "stream": False,
        }
        headers = {
            "Authorization": f"Bearer {self.settings.api_key}",
            "Content-Type": "application/json",
        }
        started = time.perf_counter()
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(timeout, connect=10.0),
                transport=self.transport,
            ) as client:
                response = await client.post(
                    f"{self.settings.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                )
        except httpx.TimeoutException as exc:
            raise ApiError(504, "MODEL_TIMEOUT", "模型请求超时，请稍后重试。", retryable=True) from exc
        except httpx.HTTPError as exc:
            raise ApiError(500, "INTERNAL_ERROR", "无法连接模型服务。", retryable=True) from exc
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        if response.status_code == 401:
            logger.warning(
                "model_call_failed",
                extra={"model": selected_model, "duration_ms": elapsed_ms, "error_code": "MODEL_AUTH_FAILED"},
            )
            raise ApiError(502, "MODEL_AUTH_FAILED", "模型 Key 无效。")
        if response.status_code == 402:
            logger.warning(
                "model_call_failed",
                extra={"model": selected_model, "duration_ms": elapsed_ms, "error_code": "MODEL_INSUFFICIENT_BALANCE"},
            )
            raise ApiError(502, "MODEL_INSUFFICIENT_BALANCE", "模型账户余额不足。")
        if response.status_code == 429:
            retry_after = response.headers.get("retry-after")
            logger.warning(
                "model_call_failed",
                extra={"model": selected_model, "duration_ms": elapsed_ms, "error_code": "MODEL_RATE_LIMITED"},
            )
            raise ApiError(
                429,
                "MODEL_RATE_LIMITED",
                "模型限流，请稍后重试。",
                retryable=True,
                retry_after_s=int(retry_after) if retry_after and retry_after.isdigit() else None,
            )
        if response.status_code >= 400:
            upstream_text = response.text[:1000].lower()
            if response.status_code in (400, 403, 422) and any(
                marker in upstream_text for marker in _REFUSAL_MARKERS
            ):
                logger.warning(
                    "model_call_failed",
                    extra={
                        "model": selected_model,
                        "duration_ms": elapsed_ms,
                        "status": response.status_code,
                        "error_code": "MODEL_REFUSED",
                    },
                )
                raise ApiError(
                    422,
                    "MODEL_REFUSED",
                    "模型拒绝处理该请求，请修改内容后重试。",
                    details={"upstream_status": response.status_code},
                )
            logger.warning(
                "model_call_failed",
                extra={
                    "model": selected_model,
                    "duration_ms": elapsed_ms,
                    "status": response.status_code,
                    "error_code": "MODEL_BAD_OUTPUT",
                },
            )
            raise ApiError(
                502,
                "MODEL_BAD_OUTPUT",
                "模型返回错误，请重试。",
                retryable=True,
                details={"upstream_status": response.status_code, "reason": "upstream_error"},
            )
        try:
            body = response.json()
            choice = body["choices"][0]
            message = choice.get("message") or {}
            content = message.get("content") or ""
            reasoning_content = message.get("reasoning_content") or ""
            finish_reason = choice.get("finish_reason")
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            logger.warning(
                "model_call_failed",
                extra={"model": selected_model, "duration_ms": elapsed_ms, "error_code": "MODEL_BAD_OUTPUT"},
            )
            raise ApiError(502, "MODEL_BAD_OUTPUT", "模型响应结构异常。", details={"reason": "bad_structure"}) from exc
        usage = body.get("usage") or {}
        if finish_reason == "content_filter":
            logger.warning(
                "model_call_failed",
                extra={"model": selected_model, "duration_ms": elapsed_ms, "error_code": "MODEL_REFUSED"},
            )
            raise ApiError(422, "MODEL_REFUSED", "模型拒绝处理该请求，请修改内容后重试。")
        if finish_reason == "length":
            logger.warning(
                "model_call_failed",
                extra={
                    "model": selected_model,
                    "duration_ms": elapsed_ms,
                    "tokens": usage.get("total_tokens"),
                    "error_code": "MODEL_BAD_OUTPUT",
                },
            )
            raise ApiError(
                502,
                "MODEL_BAD_OUTPUT",
                "模型输出达到长度上限，未生成完整 JSON；请重试或缩短输入。",
                retryable=True,
                details={
                    "finish_reason": finish_reason,
                    "completion_tokens": usage.get("completion_tokens"),
                    "content_chars": len(content),
                    "reasoning_chars": len(reasoning_content),
                    "reason": "length",
                },
            )
        if not content.strip():
            logger.warning(
                "model_call_failed",
                extra={
                    "model": selected_model,
                    "duration_ms": elapsed_ms,
                    "tokens": usage.get("total_tokens"),
                    "error_code": "MODEL_BAD_OUTPUT",
                },
            )
            raise ApiError(
                502,
                "MODEL_BAD_OUTPUT",
                "模型未返回最终内容，请重试。",
                retryable=True,
                details={
                    "finish_reason": finish_reason,
                    "content_chars": 0,
                    "reasoning_chars": len(reasoning_content),
                    "reason": "empty_content",
                },
            )
        text = content.strip()
        fenced = _FENCE.match(text)
        if fenced:
            text = fenced.group(1).strip()
        try:
            result = _parse_json_object(text)
        except ValueError as exc:
            logger.warning(
                "model_call_failed",
                extra={"model": selected_model, "duration_ms": elapsed_ms, "error_code": "MODEL_BAD_OUTPUT"},
            )
            raise ApiError(
                502,
                "MODEL_BAD_OUTPUT",
                "模型未返回可解析的 JSON。",
                retryable=True,
                details={"reason": "invalid_json"},
            ) from exc
        tokens = usage.get("total_tokens")
        logger.info(
            "model_call_succeeded",
            extra={
                "model": selected_model,
                "duration_ms": elapsed_ms,
                "tokens": tokens,
                "status": "ok",
            },
        )
        return result


def _parse_json_object(text: str) -> dict[str, Any]:
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(redact(str(exc))) from exc
    if not isinstance(value, dict):
        raise ValueError("top-level JSON must be an object")
    return value