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
        for name in (
            "sessions",
            "plans",
            "jobs",
            "idempotency",
            "revisions",
            "media",
            "feedback",
            "feedback_frames",
            "recipes",
            "tastings",
            "adjustments",
            "logs",
        ):
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

    def revision_rel(self, session_id: str, revision_id: str) -> str:
        return f"revisions/{session_id}/{revision_id}.json"

    def revisions_dir_rel(self, session_id: str) -> str:
        return f"revisions/{session_id}"

    async def load_revision(self, session_id: str, revision_id: str) -> dict[str, Any] | None:
        return await self.read_json(self.revision_rel(session_id, revision_id))

    async def save_revision(self, payload: dict[str, Any]) -> None:
        await self.write_json(
            self.revision_rel(payload["session_id"], payload["id"]),
            payload,
        )

    def media_json_rel(self, media_id: str) -> str:
        return f"media/{media_id}.json"

    def media_file_path(self, media_id: str, extension: str) -> Path:
        return self.data_dir / "media" / f"{media_id}{extension}"

    async def load_media(self, media_id: str) -> dict[str, Any] | None:
        return await self.read_json(self.media_json_rel(media_id))

    async def save_media(self, payload: dict[str, Any]) -> None:
        await self.write_json(self.media_json_rel(payload["id"]), payload)

    def feedback_rel(self, feedback_id: str) -> str:
        return f"feedback/{feedback_id}.json"

    async def load_feedback(self, feedback_id: str) -> dict[str, Any] | None:
        return await self.read_json(self.feedback_rel(feedback_id))

    async def save_feedback(self, payload: dict[str, Any]) -> None:
        await self.write_json(self.feedback_rel(payload["id"]), payload)

    def feedback_frames_dir_rel(self, feedback_id: str) -> str:
        return f"feedback_frames/{feedback_id}"

    def feedback_frame_path(self, feedback_id: str, frame_index: int) -> Path:
        return self._path(
            f"{self.feedback_frames_dir_rel(feedback_id)}/frame_{int(frame_index)}.jpg"
        )

    async def save_feedback_frames(
        self,
        feedback_id: str,
        frames: list[tuple[int, bytes]],
    ) -> None:
        directory = self._path(self.feedback_frames_dir_rel(feedback_id))
        directory.mkdir(parents=True, exist_ok=True)
        for frame_index, data in frames:
            path = directory / f"frame_{int(frame_index)}.jpg"
            tmp = path.with_name(path.name + ".tmp")
            tmp.write_bytes(data)
            os.replace(tmp, path)

    async def load_feedback_frame(
        self,
        feedback_id: str,
        frame_index: int,
    ) -> bytes | None:
        path = self.feedback_frame_path(feedback_id, frame_index)
        if not path.exists():
            return None
        try:
            return path.read_bytes()
        except OSError as exc:
            raise ApiError(500, "INTERNAL_ERROR", "证据帧读取失败。") from exc

    def recipe_rel(self, session_id: str, recipe_id: str) -> str:
        return f"recipes/{session_id}/{recipe_id}.json"

    def tasting_rel(self, recipe_id: str, tasting_id: str) -> str:
        return f"tastings/{recipe_id}/{tasting_id}.json"

    def adjustment_rel(self, recipe_id: str, adjustment_id: str) -> str:
        return f"adjustments/{recipe_id}/{adjustment_id}.json"

    async def load_recipe(self, session_id: str, recipe_id: str) -> dict[str, Any] | None:
        return await self.read_json(self.recipe_rel(session_id, recipe_id))

    async def find_recipe(self, recipe_id: str) -> dict[str, Any] | None:
        root = self.data_dir / "recipes"
        if not root.exists():
            return None
        for session_dir in root.iterdir():
            if not session_dir.is_dir():
                continue
            data = await self.read_json(f"recipes/{session_dir.name}/{recipe_id}.json")
            if data:
                return data
        return None

    async def save_recipe(self, payload: dict[str, Any]) -> None:
        await self.write_json(
            self.recipe_rel(payload["session_id"], payload["id"]),
            payload,
        )

    async def list_recipes(self, session_id: str) -> list[dict[str, Any]]:
        directory = self.data_dir / "recipes" / session_id
        if not directory.exists():
            return []
        items = []
        for path in directory.glob("*.json"):
            try:
                items.append(json.loads(path.read_text(encoding="utf-8")))
            except (OSError, json.JSONDecodeError) as exc:
                raise ApiError(500, "INTERNAL_ERROR", "数据文件损坏，请联系维护者。") from exc
        items.sort(key=lambda item: item.get("version", 0))
        return items

    async def load_tasting(self, recipe_id: str, tasting_id: str) -> dict[str, Any] | None:
        return await self.read_json(self.tasting_rel(recipe_id, tasting_id))

    async def save_tasting(self, payload: dict[str, Any]) -> None:
        await self.write_json(
            self.tasting_rel(payload["recipe_id"], payload["id"]),
            payload,
        )

    async def list_tastings(self, recipe_id: str) -> list[dict[str, Any]]:
        directory = self.data_dir / "tastings" / recipe_id
        if not directory.exists():
            return []
        items = []
        for path in directory.glob("*.json"):
            try:
                items.append(json.loads(path.read_text(encoding="utf-8")))
            except (OSError, json.JSONDecodeError) as exc:
                raise ApiError(500, "INTERNAL_ERROR", "数据文件损坏，请联系维护者。") from exc
        items.sort(key=lambda item: item.get("created_at", ""), reverse=True)
        return items

    async def save_adjustment(self, payload: dict[str, Any]) -> None:
        await self.write_json(
            self.adjustment_rel(payload["recipe_id"], payload["id"]),
            payload,
        )

    async def list_adjustments(self, recipe_id: str) -> list[dict[str, Any]]:
        directory = self.data_dir / "adjustments" / recipe_id
        if not directory.exists():
            return []
        items = []
        for path in directory.glob("*.json"):
            try:
                items.append(json.loads(path.read_text(encoding="utf-8")))
            except (OSError, json.JSONDecodeError) as exc:
                raise ApiError(500, "INTERNAL_ERROR", "数据文件损坏，请联系维护者。") from exc
        items.sort(key=lambda item: item.get("created_at", ""))
        return items

    async def list_feedback(self, session_id: str) -> list[dict[str, Any]]:
        directory = self.data_dir / "feedback"
        if not directory.exists():
            return []
        items: list[dict[str, Any]] = []
        for path in directory.glob("*.json"):
            try:
                item = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise ApiError(500, "INTERNAL_ERROR", "数据文件损坏，请联系维护者。") from exc
            if item.get("session_id") == session_id:
                items.append(item)
        items.sort(key=lambda item: item.get("created_at", ""), reverse=True)
        return items

    async def media_referenced(self, media_id: str) -> bool:
        directory = self.data_dir / "feedback"
        if not directory.exists():
            return False
        for path in directory.glob("*.json"):
            try:
                item = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if media_id in (item.get("media_ids") or []):
                return True
        return False

    async def list_revisions(self, session_id: str) -> list[dict[str, Any]]:
        directory = self.data_dir / self.revisions_dir_rel(session_id)
        if not directory.exists():
            return []
        items: list[dict[str, Any]] = []
        for path in directory.glob("*.json"):
            try:
                items.append(json.loads(path.read_text(encoding="utf-8")))
            except (OSError, json.JSONDecodeError) as exc:
                raise ApiError(500, "INTERNAL_ERROR", "数据文件损坏，请联系维护者。") from exc
        items.sort(key=lambda item: item.get("created_at", ""), reverse=True)
        return items

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