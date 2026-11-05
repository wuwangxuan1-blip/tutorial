from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ..enums import Domain, SessionStatus
from ..errors import ApiError, invalid_request, not_found
from ..ids import new_id
from ..models.job import JobOut
from ..models.plan import PlanOut
from ..models.session import (
    AnswerSubmission,
    ConditionImpact,
    Conditions,
    ConditionsPatchRequest,
    ConditionsPatchResponse,
    CreatePlanJobRequest,
    CreateSessionRequest,
    KEY_CONDITIONS,
    Progress,
    Question,
    SessionOut,
)
from ..services.answers import normalize_condition_value, validate_answer
from ..services.job_service import has_progress
from ..services.questions import build_questions

logger = logging.getLogger("tutorial_coach.sessions")

router = APIRouter()


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def session_out(data: dict[str, Any]) -> SessionOut:
    return SessionOut(
        id=data["id"],
        domain=Domain(data["domain"]),
        goal=data["goal"],
        status=SessionStatus(data["status"]),
        conditions=dict(data.get("conditions") or {}),
        questions=[Question.model_validate(item) for item in data.get("questions") or []],
        reference_ids=list(data.get("reference_ids") or []),
        current_plan_version=data.get("current_plan_version"),
        progress=Progress.model_validate(data["progress"]),
        outcome=data.get("outcome"),
        created_at=data["created_at"],
        updated_at=data["updated_at"],
    )


def job_out(data: dict[str, Any]) -> JobOut:
    return JobOut(
        id=data["id"],
        type=data["type"],
        status=data["status"],
        progress=data["progress"],
        stage=data["stage"],
        session_id=data["session_id"],
        created_at=data["created_at"],
        updated_at=data["updated_at"],
        expires_at=data["expires_at"],
        result=data.get("result"),
        error=data.get("error"),
    )


def _validate_idempotency_key(request: Request) -> str | None:
    key = request.headers.get("Idempotency-Key")
    if key is None:
        return None
    if not 16 <= len(key) <= 128 or not all(33 <= ord(char) <= 126 for char in key):
        raise invalid_request("Idempotency-Key 必须为 16–128 个可打印 ASCII 字符。")
    return key


def _request_hash(request: Any) -> str:
    canonical = json.dumps(request.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _idem_rel(method: str, path: str, key: str) -> str:
    digest = hashlib.sha256(f"{method}|{path}|{key}".encode("utf-8")).hexdigest()
    return f"idempotency/{digest}.json"


@router.post("/sessions", response_model=SessionOut, status_code=201)
async def create_session(request: Request, payload: CreateSessionRequest) -> Any:
    store = request.app.state.store
    key = _validate_idempotency_key(request)
    body_hash = _request_hash(payload)
    record_rel = _idem_rel("POST", "/v1/sessions", key) if key else None
    if record_rel:
        async with store.lock(record_rel):
            existing = await store.read_json(record_rel)
            if existing:
                if existing.get("body_hash") != body_hash:
                    raise ApiError(
                        409,
                        "IDEMPOTENCY_CONFLICT",
                        "同一幂等键对应了不同的请求内容。",
                    )
                if existing.get("state") == "in_progress":
                    raise ApiError(
                        409,
                        "IDEMPOTENCY_IN_PROGRESS",
                        "相同请求仍在处理中，请稍后重试。",
                        retryable=True,
                        retry_after_s=1,
                    )
                return JSONResponse(status_code=existing.get("status_code", 201), content=existing["body"])
            await store.write_json(
                record_rel,
                {"state": "in_progress", "body_hash": body_hash},
            )
    try:
        provided = payload.conditions.model_dump(exclude_unset=True)
        for field in KEY_CONDITIONS:
            if field in provided and provided[field] is None:
                raise invalid_request(
                    f"{field} 是关键条件，不能为空；请提供数值或新建会话。",
                    {"field": field, "reason": "key_condition_null"},
                )
        if payload.reference_ids:
            raise invalid_request(
                "本阶段尚未启用参考教程导入，reference_ids 必须为空。",
                {"field": "reference_ids", "reason": "not_available_in_p0"},
            )
        conditions = payload.conditions.model_dump(exclude_none=True)
        questions = build_questions(payload.domain, conditions, 0)
        status = SessionStatus.clarifying if questions else SessionStatus.ready
        now = _now()
        session = {
            "id": new_id("session"),
            "domain": payload.domain.value,
            "goal": payload.goal,
            "status": status.value,
            "conditions": conditions,
            "questions": [question.model_dump(mode="json") for question in questions],
            "reference_ids": [],
            "current_plan_version": None,
            "progress": {
                "current_step_id": None,
                "step_statuses": {},
                "evidence_levels": {},
                "timer": None,
                "updated_at": now,
            },
            "outcome": None,
            "clarify_round": 0,
            "created_at": now,
            "updated_at": now,
        }
        await store.save_session(session)
        response = session_out(session).model_dump(mode="json")
        if record_rel:
            await store.write_json(
                record_rel,
                {"state": "completed", "body_hash": body_hash, "status_code": 201, "body": response},
            )
        return response
    except Exception:
        if record_rel:
            await store.delete(record_rel)
        raise


@router.get("/sessions/{session_id}", response_model=SessionOut)
async def get_session(request: Request, session_id: str) -> SessionOut:
    session = await request.app.state.store.load_session(session_id)
    if not session:
        raise not_found("会话不存在。")
    return session_out(session)


@router.post("/sessions/{session_id}/answers", response_model=SessionOut)
async def submit_answers(request: Request, session_id: str, payload: AnswerSubmission) -> SessionOut:
    store = request.app.state.store
    async with store.lock(store.session_rel(session_id)):
        session = await store.load_session(session_id)
        if not session:
            raise not_found("会话不存在。")
        if session["status"] != SessionStatus.clarifying.value:
            raise invalid_request("当前会话不在澄清状态。", {"reason": "session_not_clarifying"})
        questions = [Question.model_validate(item) for item in session.get("questions") or []]
        question_map = {question.id: question for question in questions}
        provided_ids = [item.question_id for item in payload.answers]
        if len(set(provided_ids)) != len(provided_ids):
            raise invalid_request("同一问题不能重复提交。")
        conditions = dict(session.get("conditions") or {})
        for item in payload.answers:
            question = question_map.get(item.question_id)
            if not question:
                raise invalid_request(
                    "只能回答当前轮次的问题。",
                    {"field": "question_id"},
                )
            value = normalize_condition_value(question.field, validate_answer(question, item.value))
            conditions[question.field] = value
        try:
            conditions = Conditions.model_validate(conditions).model_dump(exclude_none=True)
        except Exception as exc:
            raise invalid_request("条件值未通过校验。") from exc
        round_no = int(session.get("clarify_round", 0)) + 1
        domain = Domain(session["domain"])
        next_questions = build_questions(domain, conditions, round_no)
        if round_no >= 2 or not next_questions:
            status = SessionStatus.ready
            next_questions = []
        else:
            status = SessionStatus.clarifying
        session.update(
            {
                "conditions": conditions,
                "questions": [question.model_dump(mode="json") for question in next_questions],
                "status": status.value,
                "clarify_round": round_no,
                "updated_at": _now(),
            }
        )
        await store.save_session(session)
    return session_out(session)


@router.patch("/sessions/{session_id}/conditions", response_model=ConditionsPatchResponse)
async def patch_conditions(
    request: Request,
    session_id: str,
    payload: ConditionsPatchRequest,
) -> ConditionsPatchResponse:
    store = request.app.state.store
    async with store.lock(store.session_rel(session_id)):
        session = await store.load_session(session_id)
        if not session:
            raise not_found("会话不存在。")
        if session["status"] in (
            SessionStatus.completed.value,
            SessionStatus.abandoned.value,
        ):
            raise ApiError(409, "SESSION_NOT_EDITABLE", "会话已结束，不能修改条件。")
        current_version = session.get("current_plan_version")
        if current_version is not None:
            if payload.base_plan_version is None:
                raise ApiError(
                    409,
                    "VERSION_CONFLICT",
                    "已有计划时必须提供 base_plan_version。",
                    details={"current_plan_version": current_version},
                )
            if payload.base_plan_version != current_version:
                raise ApiError(
                    409,
                    "VERSION_CONFLICT",
                    "计划版本已变化，请刷新后重试。",
                    details={"current_plan_version": current_version},
                )
        provided = payload.conditions.model_dump(exclude_unset=True)
        if not provided:
            raise invalid_request(
                "conditions 至少提供一个字段。",
                {"field": "conditions", "reason": "empty_conditions"},
            )
        for field, value in provided.items():
            if field in KEY_CONDITIONS and value is None:
                raise invalid_request(
                    f"{field} 是关键条件，不能清空；请提供新的数值或新建会话。",
                    {"field": field, "reason": "key_condition_null"},
                )
        conditions = dict(session.get("conditions") or {})
        changed_fields: list[str] = []
        for field, value in provided.items():
            if value is None:
                if field in conditions:
                    conditions.pop(field, None)
                    changed_fields.append(field)
            elif conditions.get(field) != value:
                conditions[field] = value
                changed_fields.append(field)
        if changed_fields:
            try:
                conditions = Conditions.model_validate(conditions).model_dump(exclude_none=True)
            except Exception as exc:
                raise invalid_request("条件值未通过校验。") from exc
        if session["status"] == SessionStatus.clarifying.value:
            round_no = int(session.get("clarify_round") or 0)
            questions = build_questions(Domain(session["domain"]), conditions, round_no)
            session["questions"] = [question.model_dump(mode="json") for question in questions]
            session["status"] = (
                SessionStatus.ready.value if not questions else SessionStatus.clarifying.value
            )
        session["conditions"] = conditions
        session["updated_at"] = _now()
        locked = has_progress(session)
        has_plan = current_version is not None
        requires_regeneration = has_plan and not locked
        requires_revision = has_plan and locked
        if requires_revision:
            message = (
                "已有步骤进度，不能全量重新生成。请用条件修订调整未完成步骤，或新建会话。"
            )
        elif requires_regeneration:
            message = "当前计划尚未开始，可全量重新生成或新建会话。"
        else:
            message = "条件已更新。"
        await store.save_session(session)
    return ConditionsPatchResponse(
        session=session_out(session),
        impact=ConditionImpact(
            requires_regeneration=requires_regeneration,
            requires_revision=requires_revision,
            changed_fields=changed_fields,
            message=message,
        ),
    )


@router.post("/sessions/{session_id}/plan-jobs", response_model=JobOut, status_code=202)
async def create_plan_job(
    request: Request,
    session_id: str,
    payload: CreatePlanJobRequest,
) -> Any:
    store = request.app.state.store
    key = _validate_idempotency_key(request)
    body_hash = _request_hash(payload)
    record_rel = (
        _idem_rel("POST", f"/v1/sessions/{session_id}/plan-jobs", key) if key else None
    )
    if record_rel:
        async with store.lock(record_rel):
            existing = await store.read_json(record_rel)
            if existing:
                if existing.get("body_hash") != body_hash:
                    raise ApiError(
                        409,
                        "IDEMPOTENCY_CONFLICT",
                        "同一幂等键对应了不同的请求内容。",
                    )
                if existing.get("state") == "in_progress":
                    raise ApiError(
                        409,
                        "IDEMPOTENCY_IN_PROGRESS",
                        "相同请求仍在处理中，请稍后重试。",
                        retryable=True,
                        retry_after_s=1,
                    )
                return JSONResponse(
                    status_code=existing.get("status_code", 202),
                    content=existing["body"],
                )
            await store.write_json(
                record_rel,
                {"state": "in_progress", "body_hash": body_hash},
            )
    try:
        async with store.lock(store.session_rel(session_id)):
            session = await store.load_session(session_id)
            if not session:
                raise not_found("会话不存在。")
            if session["domain"] not in (
                Domain.cooking.value,
                Domain.software.value,
                Domain.photography.value,
            ):
                raise ApiError(
                    422,
                    "DOMAIN_MISMATCH",
                    "本阶段仅启用烹饪、软件与摄影领域的计划生成；其它领域将在后续阶段开放。",
                )
            if session["status"] == SessionStatus.clarifying.value:
                raise invalid_request("请先完成澄清问题。", {"reason": "clarification_incomplete"})
            if session["status"] in (
                SessionStatus.completed.value,
                SessionStatus.abandoned.value,
            ):
                raise ApiError(409, "SESSION_NOT_EDITABLE", "会话已结束，不能生成计划。")
            if has_progress(session):
                raise ApiError(
                    409,
                    "PLAN_LOCKED",
                    "已有步骤进度，不能全量重新生成；请使用条件修订或新建会话。",
                )
            current = session.get("current_plan_version")
            if current is not None and payload.base_plan_version is None:
                raise ApiError(
                    409,
                    "VERSION_CONFLICT",
                    "已有计划时必须提供 base_plan_version。",
                    details={"current_plan_version": current},
                )
            if current != payload.base_plan_version:
                raise ApiError(
                    409,
                    "VERSION_CONFLICT",
                    "计划版本已变化，请刷新后重试。",
                    details={"current_plan_version": current},
                )
            job = await request.app.state.job_service.create_plan_job(
                session, payload.base_plan_version
            )
            response = job_out(job).model_dump(mode="json")
        if record_rel:
            await store.write_json(
                record_rel,
                {
                    "state": "completed",
                    "body_hash": body_hash,
                    "status_code": 202,
                    "body": response,
                },
            )
        return response
    except Exception:
        if record_rel:
            await store.delete(record_rel)
        raise


@router.get("/sessions/{session_id}/plan", response_model=PlanOut)
async def get_plan(request: Request, session_id: str) -> PlanOut:
    store = request.app.state.store
    session = await store.load_session(session_id)
    if not session:
        raise not_found("会话不存在。")
    version = session.get("current_plan_version")
    if version is None:
        raise not_found("该会话还没有计划。")
    plan = await store.load_plan(session_id, version)
    if not plan:
        raise not_found("该会话还没有计划。")
    return PlanOut.model_validate(plan)