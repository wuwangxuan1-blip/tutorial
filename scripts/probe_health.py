from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from pathlib import Path

from httpx import ASGITransport, AsyncClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "server"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from app.config import load_settings  # noqa: E402
from app.main import create_app  # noqa: E402
from win_asgi_runtime import install_win_asgi_workaround  # noqa: E402

PROOF_DIR = PROJECT_ROOT / "codearts_proof" / "day1"


async def main() -> None:
    app = create_app(load_settings())
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://tutorial-coach") as client:
            health = await client.get("/v1/health")
            health_text = health.text
            (PROOF_DIR / "health.json").write_text(
                json.dumps(
                    {
                        "http_status": health.status_code,
                        "content_type": health.headers.get("content-type"),
                        "contains_api_key_pattern": "sk-" in health_text,
                        "body": health.json(),
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            created = await client.post(
                "/v1/sessions",
                json={
                    "domain": "cooking",
                    "goal": "2 人份番茄鸡蛋面，30 分钟内完成",
                    "reference_ids": [],
                },
                headers={"Idempotency-Key": f"session-create-{int(time.time())}"},
            )
            body = created.json()
            (PROOF_DIR / "session_create.json").write_text(
                json.dumps(
                    {
                        "http_status": created.status_code,
                        "status": body.get("status"),
                        "domain": body.get("domain"),
                        "question_count": len(body.get("questions") or []),
                        "question_fields": [item.get("field") for item in body.get("questions") or []],
                        "question_kinds": [item.get("kind") for item in body.get("questions") or []],
                        "body": body,
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            print(
                json.dumps(
                    {
                        "health": health.status_code,
                        "session": created.status_code,
                        "questions": len(body.get("questions") or []),
                    },
                    ensure_ascii=False,
                )
            )
    sys.stdout.flush()
    os._exit(0)


if __name__ == "__main__":
    install_win_asgi_workaround()
    asyncio.run(main())