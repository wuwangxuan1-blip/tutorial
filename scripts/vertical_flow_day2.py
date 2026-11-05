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
from app.models.plan import PlanOut  # noqa: E402
from win_asgi_runtime import install_win_asgi_workaround  # noqa: E402

PROOF_DIR = PROJECT_ROOT / "codearts_proof" / "day2"
SUMMARY_PATH = PROOF_DIR / "vertical_flow.json"
PLAN_PATH = PROOF_DIR / "plan_cooking_real.json"
HEALTH_PATH = PROOF_DIR / "health.json"

FIRST_ANSWERS = {
    "skill_level": "beginner",
    "time_budget_min": 30,
}
SECOND_ANSWERS = {
    "people": 2,
    "servings": 2,
    "stove_type": "gas",
}


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


async def wait_job(client: AsyncClient, job_id: str, timeout_s: float) -> dict:
    deadline = asyncio.get_running_loop().time() + timeout_s
    while asyncio.get_running_loop().time() < deadline:
        response = await client.get(f"/v1/jobs/{job_id}")
        job = response.json()
        if job.get("status") in ("succeeded", "failed", "cancelled"):
            return job
        await asyncio.sleep(1)
    return {"id": job_id, "status": "timeout"}


def answer_values(questions: list[dict], mapping: dict) -> list[dict]:
    values = []
    for question in questions:
        field = question.get("field")
        if field in mapping:
            values.append({"question_id": question["id"], "value": mapping[field]})
    return values


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
        "goal": "两人份番茄鸡蛋面，30 分钟内完成",
    }
    exit_code = 0
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://tutorial-coach-day2") as client:
            health = await client.get("/v1/health")
            capabilities = await client.get("/v1/capabilities")
            summary["health"] = health.json()
            summary["capabilities_model"] = capabilities.json().get("model")
            HEALTH_PATH.parent.mkdir(parents=True, exist_ok=True)
            HEALTH_PATH.write_text(
                json.dumps({"http_status": health.status_code, "body": health.json()}, ensure_ascii=False, indent=2),
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
                        "goal": summary["goal"],
                        "reference_ids": [],
                    },
                    headers={"Idempotency-Key": f"day2-session-{run_id}"},
                )
                session = created.json()
                summary["session"] = {
                    "http_status": created.status_code,
                    "id": session.get("id"),
                    "status_after_create": session.get("status"),
                    "rounds": [],
                    "final_status": session.get("status"),
                }
                if session.get("status") != "clarifying":
                    summary["error"] = "expected first-round clarifying session"
                    exit_code = 3
                else:
                    first_questions = session.get("questions") or []
                    summary["session"]["rounds"].append(
                        {
                            "round": 1,
                            "question_count": len(first_questions),
                            "fields": [item.get("field") for item in first_questions],
                            "answered_fields": list(FIRST_ANSWERS),
                            "skipped_fields": [
                                item.get("field") for item in first_questions if item.get("field") not in FIRST_ANSWERS
                            ],
                        }
                    )
                    first = await client.post(
                        f"/v1/sessions/{session['id']}/answers",
                        json={"answers": answer_values(first_questions, FIRST_ANSWERS)},
                        headers={"Idempotency-Key": f"day2-answers-1-{run_id}"},
                    )
                    session = first.json()
                    if session.get("status") != "clarifying":
                        summary["error"] = "expected second-round clarifying session"
                        exit_code = 4
                    else:
                        second_questions = session.get("questions") or []
                        summary["session"]["rounds"].append(
                            {
                                "round": 2,
                                "question_count": len(second_questions),
                                "fields": [item.get("field") for item in second_questions],
                                "answered_fields": list(SECOND_ANSWERS),
                                "skipped_fields": [
                                    item.get("field")
                                    for item in second_questions
                                    if item.get("field") not in SECOND_ANSWERS
                                ],
                            }
                        )
                        second = await client.post(
                            f"/v1/sessions/{session['id']}/answers",
                            json={"answers": answer_values(second_questions, SECOND_ANSWERS)},
                            headers={"Idempotency-Key": f"day2-answers-2-{run_id}"},
                        )
                        session = second.json()
                        summary["session"]["final_status"] = session.get("status")
                        summary["session"]["conditions"] = session.get("conditions")
                        if session.get("status") != "ready":
                            summary["error"] = "session did not reach ready after two rounds"
                            exit_code = 5
                        else:
                            started_job = time.perf_counter()
                            job_response = await client.post(
                                f"/v1/sessions/{session['id']}/plan-jobs",
                                json={"base_plan_version": None},
                                headers={"Idempotency-Key": f"day2-plan-{run_id}"},
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
                                "wall_time_s": round(time.perf_counter() - started_job, 3),
                            }
                            if job.get("status") == "succeeded" and job.get("stage") == "done":
                                plan_response = await client.get(f"/v1/sessions/{session['id']}/plan")
                                plan = PlanOut.model_validate(plan_response.json()).model_dump(mode="json")
                                PLAN_PATH.write_text(
                                    json.dumps(plan, ensure_ascii=False, indent=2),
                                    encoding="utf-8",
                                )
                                summary["plan"] = {
                                    "http_status": plan_response.status_code,
                                    "id": plan["id"],
                                    "version": plan["version"],
                                    "title": plan["title"],
                                    "summary": plan["summary"],
                                    "total_estimated_min": plan["total_estimated_min"],
                                    "step_count": len(plan["steps"]),
                                    "assumption_count": len(plan["assumptions"]),
                                    "preparation_count": len(plan["preparation"]),
                                    "safety_note_count": len(plan["safety_notes"]),
                                    "all_steps_have_criteria": all(
                                        bool(step["completion_criteria"]) for step in plan["steps"]
                                    ),
                                    "steps": [
                                        {
                                            "id": step["id"],
                                            "order": step["order"],
                                            "phase": step["phase"],
                                            "title": step["title"],
                                            "duration_s": step["duration_s"],
                                            "completion_criteria": step["completion_criteria"],
                                            "safety": step["safety"],
                                        }
                                        for step in plan["steps"]
                                    ],
                                }
                                if not 3 <= summary["plan"]["step_count"] <= 15:
                                    summary["error"] = "plan step count out of contract range"
                                    exit_code = 6
                                if not summary["plan"]["all_steps_have_criteria"]:
                                    summary["error"] = "plan step missing completion criteria"
                                    exit_code = 7
                            else:
                                summary["error"] = "plan job failed or stage mismatch"
                                exit_code = 8
    summary["finished_at"] = now()
    PROOF_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "session": summary.get("session", {}).get("final_status"),
                "job": summary.get("job_final", {}).get("status"),
                "stage": summary.get("job_final", {}).get("stage"),
                "steps": summary.get("plan", {}).get("step_count"),
                "exit": exit_code,
            },
            ensure_ascii=False,
        )
    )
    sys.stdout.flush()
    os._exit(exit_code)


if __name__ == "__main__":
    install_win_asgi_workaround()
    asyncio.run(run())