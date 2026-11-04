from __future__ import annotations

import asyncio
import selectors
import sys
import time
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

if sys.platform == "win32":
    from asyncio import selector_events

    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    def _noop_make_self_pipe(self):
        self._ssock = None
        self._csock = None
        self._internal_fds += 1

    def _noop_close_self_pipe(self):
        self._internal_fds -= 1

    _original_select = selectors.SelectSelector.select

    def _safe_select(self, timeout=None):
        if not self._readers and not self._writers:
            if timeout is None:
                time.sleep(0.01)
            elif timeout > 0:
                time.sleep(timeout)
            return []
        return _original_select(self, timeout)

    selector_events.BaseSelectorEventLoop._make_self_pipe = _noop_make_self_pipe
    selector_events.BaseSelectorEventLoop._close_self_pipe = _noop_close_self_pipe
    selector_events.BaseSelectorEventLoop._write_to_self = lambda self: None
    selectors.SelectSelector.select = _safe_select

from app.config import Settings
from app.main import create_app


def make_settings(tmp_path: Path, api_key: str | None = None) -> Settings:
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


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return make_settings(tmp_path)


@pytest_asyncio.fixture
async def client(settings: Settings):
    app = create_app(settings)
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as test_client:
            test_client.app = app
            yield test_client