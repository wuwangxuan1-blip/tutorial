from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from httpx import ASGITransport, AsyncClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "server"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from app.config import load_settings  # noqa: E402
from app.main import create_app  # noqa: E402
from win_asgi_runtime import install_win_asgi_workaround  # noqa: E402

PROOF_PATH = PROJECT_ROOT / "codearts_proof" / "day1" / "vertical_flow.json"
HEALTH_PATH = PROJECT_ROOT / "codearts_proof" / "day1" / "health.json"
SESSION_PATH = PROJECT_ROOT / "codearts_proof" / "day1" / "session_create.json"
FULL_PLAN_PATH = PROJECT_ROOT / "server" / "data" / "vertical_flow_plan.json"

PRESET_ANSWERS = {
    "skill_level": "beginner",
    "time_budget_min": 30,
    "people": 2,
    "servings": 2,
    "stove_type": "gas",
    "oven_available": False,
    "allergies": "无",
    "available_equipment": "炒锅、汤锅、刀、砧板",
    "dietary_preferences": "无",
}


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def answer_for(question: dict) -> object:
    field = question.get("field")
    if field in PRESET_ANSWERS:
        return PRESET_ANSWERS[field]
    kind = question.get("kind")
    if kind == "single_choice":
        options = question.get("options") or []
        return options[0] if options else "无"
    if kind == "number":
        return 1
    if kind == "boolean":
        return False
    return "无"


async def wait_job(client: AsyncClient, job_id: str, timeout_s: float) -> dict:
    deadline = asyncio.get_running_loop().time() + timeout_s
    while asyncio.get_running_loop().time() < deadline:
        response = await client.get(f"/v1/jobs/{job_id}")
        job = response.json()
        if job.get("status") in ("succeeded", "failed", "cancelled"):
            return job
        await asyncio.sleep(2)
    return {"id": job_id, "status": "timeout"}


async def run() -> int:
    settings = load_settings()
    app = create_app(settings)
    run_id = str(int(time.time()))
    started_at = now()
    summary: dict = {
        "started_at": started_at,
        "finished_at": None,
        "real_model_call": True,
        "text_model": settings.text_model,
    }
    exit_code = 0
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://tutorial-coach") as client:
            health = await client.get("/v1/health")
            capabilities = await client.get("/v1/capabilities")
            summary["health"] = health.json()
            summary["capabilities_model"] = capabilities.json().get("model")
            HEALTH_PATH.parent.mkdir(parents=True, exist_ok=True)
            HEALTH_PATH.write_text(
                json.dumps(
                    {
                        "http_status": health.status_code,
                        "content_type": health.headers.get("content-type"),
                        "contains_api_key_pattern": "sk-" in health.text,
                        "body": health.json(),
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            if health.json().get("checks", {}).get("model_configured") is not True:
                summary["blocked"] = "MODEL_NOT_CONFIGURED"
                exit_code = 2
            else:
                created = await client.post(
                    "/v1/sessions",
                    json={
                        "domain": "cooking",
                        "goal": "2 人份番茄鸡蛋面，30 分钟内完成",
                        "reference_ids": [],
                    },
                    headers={"Idempotency-Key": f"vertical-flow-{run_id}"},
                )
                session = created.json()
                SESSION_PATH.write_text(
                    json.dumps(
                        {
                            "http_status": created.status_code,
                            "status": session.get("status"),
                            "domain": session.get("domain"),
                            "question_count": len(session.get("questions") or []),
                            "question_fields": [item.get("field") for item in session.get("questions") or []],
                            "question_kinds": [item.get("kind") for item in session.get("questions") or []],
                            "body": session,
                        },
                        ensure_ascii=False,
                        indent=2,
                    ),
                    encoding="utf-8",
                )
                summary["session"] = {
                    "id": session.get("id"),
                    "status_after_create": session.get("status"),
                    "question_rounds": [],
                    "final_status": session.get("status"),
                }
                rounds = 0
                while session.get("status") == "clarifying" and rounds < 2:
                    rounds += 1
                    answers = [
                        {"question_id": item["id"], "value": answer_for(item)}
                        for item in session.get("questions") or []
                    ]
                    summary["session"]["question_rounds"].append(
                        {
                            "round": rounds,
                            "count": len(answers),
                            "fields": [item["field"] for item in session.get("questions") or []],
                        }
                    )
                    answered = await client.post(
                        f"/v1/sessions/{session['id']}/answers",
                        json={"answers": answers},
                        headers={"Idempotency-Key": f"vertical-flow-answers-{run_id}-{rounds}"},
                    )
                    session = answered.json()
                summary["session"]["final_status"] = session.get("status")
                summary["session"]["conditions"] = session.get("conditions")

                if session.get("status") != "ready":
                    summary["error"] = "session did not reach ready"
                    exit_code = 3
                else:
                    job_response = await client.post(
                        f"/v1/sessions/{session['id']}/plan-jobs",
                        json={"base_plan_version": None},
                        headers={"Idempotency-Key": f"vertical-flow-plan-{run_id}"},
                    )
                    job = job_response.json()
                    summary["job_created"] = {
                        "http_status": job_response.status_code,
                        "id": job.get("id"),
                        "status": job.get("status"),
                    }
                    job = await wait_job(client, job["id"], 180.0)
                    summary["job_final"] = {
                        "status": job.get("status"),
                        "progress": job.get("progress"),
                        "stage": job.get("stage"),
                        "error": job.get("error"),
                    }
                    if job.get("status") == "succeeded":
                        plan_response = await client.get(f"/v1/sessions/{session['id']}/plan")
                        plan = plan_response.json()
                        FULL_PLAN_PATH.parent.mkdir(parents=True, exist_ok=True)
                        FULL_PLAN_PATH.write_text(
                            json.dumps(plan, ensure_ascii=False, indent=2),
                            encoding="utf-8",
                        )
                        summary["plan"] = {
                            "http_status": plan_response.status_code,
                            "id": plan.get("id"),
                            "version": plan.get("version"),
                            "title": plan.get("title"),
                            "summary": plan.get("summary"),
                            "total_estimated_min": plan.get("total_estimated_min"),
                            "step_count": len(plan.get("steps") or []),
                            "assumptions": plan.get("assumptions"),
                            "safety_notes": plan.get("safety_notes"),
                            "steps": [
                                {
                                    "id": item.get("id"),
                                    "order": item.get("order"),
                                    "title": item.get("title"),
                                    "duration_s": item.get("duration_s"),
                                    "completion_criteria": item.get("completion_criteria"),
                                }
                                for item in plan.get("steps") or []
                            ],
                        }
                    else:
                        summary["error"] = "plan job failed"
                        exit_code = 4
    summary["finished_at"] = now()
    PROOF_PATH.parent.mkdir(parents=True, exist_ok=True)
    PROOF_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"session": summary.get("session", {}).get("final_status"), "job": summary.get("job_final", {}).get("status"), "steps": summary.get("plan", {}).get("step_count")}, ensure_ascii=False))
    sys.stdout.flush()
    os._exit(exit_code)


if __name__ == "__main__":
    install_win_asgi_workaround()
    sys.exit(asyncio.run(run()))