from __future__ import annotations

import asyncio
import json
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator

from ..errors import ApiError


class JsonStore:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = Path(data_dir)
        for name in ("sessions", "plans", "jobs", "idempotency", "logs"):
            (self.data_dir / name).mkdir(parents=True, exist_ok=True)
        self._locks: dict[str, asyncio.Lock] = {}

    def _lock(self, key: str) -> asyncio.Lock:
        if key not in self._locks:
            self._locks[key] = asyncio.Lock()
        return self._locks[key]

    @asynccontextmanager
    async def lock(self, key: str) -> AsyncIterator[None]:
        async with self._lock(key):
            yield

    def _path(self, relative: str) -> Path:
        path = (self.data_dir / relative).resolve()
        if self.data_dir.resolve() not in path.parents:
            raise ApiError(500, "INTERNAL_ERROR", "内部路径校验失败。")
        return path

    async def write_json(self, relative: str, payload: dict[str, Any]) -> None:
        path = self._path(relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.name + ".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, path)

    async def read_json(self, relative: str) -> dict[str, Any] | None:
        path = self._path(relative)
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ApiError(500, "INTERNAL_ERROR", "数据文件损坏，请联系维护者。") from exc

    async def delete(self, relative: str) -> None:
        path = self._path(relative)
        if path.exists():
            path.unlink()

    def session_rel(self, session_id: str) -> str:
        return f"sessions/{session_id}.json"

    def plan_rel(self, session_id: str, version: int) -> str:
        return f"plans/{session_id}/{version}.json"

    def job_rel(self, job_id: str) -> str:
        return f"jobs/{job_id}.json"

    async def load_session(self, session_id: str) -> dict[str, Any] | None:
        return await self.read_json(self.session_rel(session_id))

    async def save_session(self, payload: dict[str, Any]) -> None:
        await self.write_json(self.session_rel(payload["id"]), payload)

    async def load_plan(self, session_id: str, version: int) -> dict[str, Any] | None:
        return await self.read_json(self.plan_rel(session_id, version))

    async def save_plan(self, payload: dict[str, Any]) -> None:
        await self.write_json(self.plan_rel(payload["session_id"], payload["version"]), payload)

    async def load_job(self, job_id: str) -> dict[str, Any] | None:
        return await self.read_json(self.job_rel(job_id))

    async def save_job(self, payload: dict[str, Any]) -> None:
        await self.write_json(self.job_rel(payload["id"]), payload)

    def check_writable(self) -> bool:
        probe = self.data_dir / ".healthcheck"
        try:
            probe.write_text("ok", encoding="utf-8")
            probe.unlink()
            return True
        except OSError:
            return False