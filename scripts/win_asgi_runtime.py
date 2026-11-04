from __future__ import annotations

import asyncio
import selectors
import sys
import time


def install_win_asgi_workaround() -> None:
    if sys.platform != "win32":
        return
    from asyncio import selector_events

    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    def _noop_make_self_pipe(self):
        self._ssock = None
        self._csock = None
        self._internal_fds += 1

    def _noop_close_self_pipe(self):
        self._internal_fds -= 1

    original_select = selectors.SelectSelector.select

    def _safe_select(self, timeout=None):
        if not self._readers and not self._writers:
            if timeout is None:
                time.sleep(0.01)
            elif timeout > 0:
                time.sleep(timeout)
            return []
        return original_select(self, timeout)

    selector_events.BaseSelectorEventLoop._make_self_pipe = _noop_make_self_pipe
    selector_events.BaseSelectorEventLoop._close_self_pipe = _noop_close_self_pipe
    selector_events.BaseSelectorEventLoop._write_to_self = lambda self: None
    selectors.SelectSelector.select = _safe_select