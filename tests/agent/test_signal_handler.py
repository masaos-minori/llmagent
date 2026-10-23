"""tests/agent/test_signal_handler.py

Tests for ``SignalHandler.register()``: the real signal transport on the running loop
and the Windows console-control fallback.

On POSIX CI, CPython's ``ctypes`` exposes neither ``WINFUNCTYPE`` nor ``windll`` --
both are gated on ``os.name == "nt"`` (see ``ctypes/__init__.py``). The complete-failure
contract of the fallback is exercisable by injecting a raising ``WINFUNCTYPE``. The
Windows successful-registration path (``SetConsoleCtrlHandler`` through ctypes) is a
documented path that never executes on this ubuntu-latest CI matrix; it is not kept as a
permanently skipped test. ``test_signal_handler_race.py``, which used to hold the
cross-platform cases, was deleted because it asserted only on state its own tests assigned
to mocks.
"""

from __future__ import annotations

import asyncio
import ctypes
import os
import signal
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from agent.signal_handler import SignalHandler


def _raise_unavailable(*_args, **_kwargs) -> None:
    """Raise to simulate a missing ctypes symbol on POSIX."""
    raise RuntimeError("ctypes.WINFUNCTYPE unavailable on posix")


class TestWindowsCtypesFallback:
    """REQ-001/REQ-002/REQ-003: Windows console-control handler fallback."""

    def test_complete_failure_logs_error(self) -> None:
        """REQ-002: a failed SetConsoleCtrlHandler logs an error, never silently passes."""
        handler = SignalHandler(MagicMock(), None)
        mock_loop = MagicMock()
        with (
            patch.object(
                mock_loop, "add_signal_handler", side_effect=NotImplementedError()
            ),
            patch("sys.frozen", True, create=True),
            patch("agent.signal_handler.logger") as mock_logger,
            patch.dict(ctypes.__dict__, {"WINFUNCTYPE": _raise_unavailable}),
        ):
            handler.register(mock_loop)
        assert mock_logger.error.called


def _dispositions() -> tuple[Any, Any]:
    return signal.getsignal(signal.SIGTERM), signal.getsignal(signal.SIGINT)


def _remove_handlers(loop: asyncio.AbstractEventLoop, before: tuple[Any, Any]) -> None:
    """Remove the installed handlers and restore the captured dispositions.

    remove_signal_handler() resets a signal to its default, which would drop the
    asyncio Runner's own SIGINT handler that was in place before the test.
    """
    loop.remove_signal_handler(signal.SIGTERM)
    loop.remove_signal_handler(signal.SIGINT)
    signal.signal(signal.SIGTERM, before[0])
    signal.signal(signal.SIGINT, before[1])


class TestRealSignalTransport:
    """SignalHandler.register() on the real running loop.

    Both SIGTERM and SIGINT are installed; a real os.kill(os.getpid(), SIGTERM) is observed
    through a real asyncio.Event; and a handler built without an event still sets
    shutdown_requested. Handlers are removed in each finally and signal.getsignal
    dispositions are asserted identical afterwards.
    """

    @pytest.mark.asyncio
    async def test_register_installs_both_signals(self) -> None:
        handler = SignalHandler(MagicMock(), asyncio.Event())
        loop = asyncio.get_running_loop()
        seen: list[int] = []
        real_add = loop.add_signal_handler

        def capture(sig, callback):
            seen.append(sig)
            return real_add(sig, callback)

        before = _dispositions()
        try:
            with patch.object(loop, "add_signal_handler", side_effect=capture):
                handler.register(loop)
            assert signal.SIGTERM in seen
            assert signal.SIGINT in seen
        finally:
            _remove_handlers(loop, before)
        assert _dispositions() == before

    @pytest.mark.asyncio
    async def test_delivered_sigterm_sets_shutdown_on_real_objects(self) -> None:
        ctx = MagicMock()
        ctx.conv.shutdown_requested = False
        event = asyncio.Event()
        handler = SignalHandler(ctx, event)
        loop = asyncio.get_running_loop()
        before = _dispositions()
        try:
            handler.register(loop)
            os.kill(os.getpid(), signal.SIGTERM)
            await asyncio.wait_for(event.wait(), timeout=5.0)
        finally:
            _remove_handlers(loop, before)
        assert ctx.conv.shutdown_requested is True
        assert event.is_set()
        assert _dispositions() == before

    @pytest.mark.asyncio
    async def test_none_event_still_sets_shutdown_without_raising(self) -> None:
        ctx = MagicMock()
        ctx.conv.shutdown_requested = False
        handler = SignalHandler(ctx, None)
        loop = asyncio.get_running_loop()
        before = _dispositions()
        try:
            handler.register(loop)
            os.kill(os.getpid(), signal.SIGTERM)
            for _ in range(50):
                if ctx.conv.shutdown_requested is True:
                    break
                await asyncio.sleep(0.02)
        finally:
            _remove_handlers(loop, before)
        assert ctx.conv.shutdown_requested is True
        assert _dispositions() == before
