from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .api import health, jobs, sessions
from .config import Settings, load_settings
from .errors import ApiError, error_body
from .ids import new_id
from .logging_config import setup_logging
from .models.job import JobOut
from .services.job_service import JobService
from .services.model_client import ModelClient
from .services.plan_service import PlanService
from .services.store import JsonStore

logger = logging.getLogger("tutorial_coach.api")


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or load_settings()
    setup_logging(app_settings.log_dir)
    store = JsonStore(app_settings.data_dir)
    model_client = ModelClient(app_settings)
    plan_service = PlanService(app_settings, model_client)
    job_service = JobService(app_settings, store, plan_service)

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        await job_service.recover()
        logger.info("server_started", extra={"route": "startup", "status": "ok"})
        yield
        logger.info("server_stopped", extra={"route": "shutdown", "status": "ok"})

    app = FastAPI(title="实践陪练 API", version="0.1.0", lifespan=lifespan)
    app.state.settings = app_settings
    app.state.store = store
    app.state.model_client = model_client
    app.state.plan_service = plan_service
    app.state.job_service = job_service

    @app.middleware("http")
    async def request_context(request: Request, call_next):
        request_id = new_id("request")
        request.state.request_id = request_id
        started = time.perf_counter()
        response = await call_next(request)
        duration_ms = int((time.perf_counter() - started) * 1000)
        response.headers["X-Request-Id"] = request_id
        logger.info(
            "request_completed",
            extra={
                "request_id": request_id,
                "route": request.url.path,
                "status": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        return response

    @app.exception_handler(ApiError)
    async def handle_api_error(request: Request, exc: ApiError) -> JSONResponse:
        request_id = getattr(request.state, "request_id", new_id("request"))
        return JSONResponse(
            status_code=exc.status_code,
            content=error_body(
                exc.code,
                exc.message,
                request_id,
                retryable=exc.retryable,
                retry_after_s=exc.retry_after_s,
                details=exc.details,
            ),
            headers={"X-Request-Id": request_id},
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        request_id = getattr(request.state, "request_id", new_id("request"))
        field = None
        for item in exc.errors():
            location = [part for part in item.get("loc", ()) if part != "body"]
            if location:
                field = ".".join(str(part) for part in location)
                break
        details = {"reason": "validation_error"}
        if field:
            details["field"] = field
        return JSONResponse(
            status_code=422,
            content=error_body("INVALID_REQUEST", "请求参数不符合契约。", request_id, details=details),
            headers={"X-Request-Id": request_id},
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        request_id = getattr(request.state, "request_id", new_id("request"))
        if exc.status_code == 404:
            code, message = "NOT_FOUND", "资源不存在。"
        elif exc.status_code == 405:
            code, message = "METHOD_NOT_ALLOWED", "请求方法不支持。"
        else:
            code, message = "INTERNAL_ERROR", "请求处理失败。"
        return JSONResponse(
            status_code=exc.status_code,
            content=error_body(code, message, request_id),
            headers={"X-Request-Id": request_id},
        )

    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        request_id = getattr(request.state, "request_id", new_id("request"))
        logger.exception(
            "request_unexpected_error",
            extra={"request_id": request_id, "route": request.url.path, "error_code": "INTERNAL_ERROR"},
        )
        return JSONResponse(
            status_code=500,
            content=error_body("INTERNAL_ERROR", "服务内部错误，请稍后重试。", request_id, retryable=True),
            headers={"X-Request-Id": request_id},
        )

    app.include_router(health.router, prefix="/v1")
    app.include_router(sessions.router, prefix="/v1")
    app.include_router(jobs.router, prefix="/v1")
    return app


app = create_app()