from __future__ import annotations

from typing import Any


class ApiError(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        retryable: bool = False,
        retry_after_s: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.retryable = retryable
        self.retry_after_s = retry_after_s
        self.details = details if details is not None else {}


def invalid_request(message: str, details: dict[str, Any] | None = None) -> ApiError:
    return ApiError(422, "INVALID_REQUEST", message, details=details)


def not_found(message: str = "资源不存在。") -> ApiError:
    return ApiError(404, "NOT_FOUND", message)


def error_body(
    code: str,
    message: str,
    request_id: str,
    retryable: bool = False,
    retry_after_s: int | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "error": {
            "code": code,
            "message": message,
            "retryable": retryable,
            "retry_after_s": retry_after_s,
            "request_id": request_id,
            "details": details if details is not None else {},
        }
    }