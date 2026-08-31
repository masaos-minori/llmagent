#!/usr/bin/env python3
"""scripts/agent/signal_handler.py

SignalHandler — platform-specific signal handling for graceful shutdown.

Responsibilities:
  - Registering SIGTERM/SIGINT handlers on Unix (loop.add_signal_handler)
  - Registering Windows console control handler fallback
  - Cancelling input coroutine during shutdown
"""

from __future__ import annotations

import asyncio
import logging
import signal

logger = logging.getLogger(__name__)

# Lazy imports inside methods to avoid circular dependency at module level.
# sys/win32api are only needed for Windows fallback path.


class SignalHandler:
    """Encapsulates platform-specific signal handling for graceful shutdown.

    Encapsulates the signal registration logic extracted from AgentREPL.run().
    """

    def __init__(
        self,
        ctx: object,
        shutdown_event: asyncio.Event | None,
    ) -> None:
        """Initialize with AgentContext and shutdown event references."""
        self._ctx = ctx
        self._shutdown_event = shutdown_event
        self._turn_active: bool = False
        self._input_coro: asyncio.Task[str] | None = None

    def register(self, loop: asyncio.AbstractEventLoop) -> None:
        """Register signal handlers for SIGTERM and SIGINT."""

        def _sigterm_handler() -> None:
            """Handle SIGTERM by cancelling input and setting shutdown flag."""
            self._ctx.conv.shutdown_requested = True  # type: ignore[attr-defined]  # — shutdown_requested is a dynamic flag not declared on ConversationState's dataclass fields
            if self._shutdown_event is not None:
                self._shutdown_event.set()
            if (
                not self._turn_active
                and self._input_coro is not None
                and not self._input_coro.done()
            ):
                try:
                    self._input_coro.cancel()
                except RuntimeError:
                    pass
            logger.info("SIGTERM received; graceful shutdown initiated")

        for sig in (signal.SIGTERM, signal.SIGINT):
            try:
                loop.add_signal_handler(sig, _sigterm_handler)
            except NotImplementedError:
                try:
                    import sys  # noqa: PLC0414 — deferred import: only needed on the NotImplementedError (non-POSIX) fallback path, not at module load time

                    if hasattr(sys, "frozen"):
                        try:
                            import win32api  # noqa: PLC0414 — Windows-only dependency; a top-level import would break non-Windows platforms
                            import win32con  # noqa: PLC0414 — Windows-only dependency; a top-level import would break non-Windows platforms

                            def _console_ctrl_handler(ctrl_type: int) -> bool:
                                if ctrl_type == win32con.CTRL_CLOSE_EVENT:
                                    loop.call_soon_threadsafe(_sigterm_handler)
                                return True

                            win32api.SetConsoleCtrlHandler(_console_ctrl_handler, True)
                            logger.debug(
                                "Registered Windows console control handler for %s",
                                sig,
                            )
                        except ImportError:
                            logger.warning(
                                "pywin32 not available; signal handling disabled on Windows. "
                                "Install pywin32 for Ctrl+C/Ctrl+Break support."
                            )
                        except Exception as e:  # noqa: BLE001 — best-effort Windows fallback registration must not crash startup
                            logger.error(
                                "Failed to set Windows console control handler: %s", e
                            )
                    else:
                        logger.warning(
                            "Signal handling not available on Windows outside console; "
                            "use Ctrl+C or close the terminal to shut down"
                        )
                except Exception:  # noqa: BLE001 — best-effort non-POSIX signal fallback must not crash startup even on unexpected failures
                    pass

    def set_shutdown_event(self, event: asyncio.Event | None) -> None:
        """Update the shutdown event reference after run() initializes it."""
        self._shutdown_event = event
