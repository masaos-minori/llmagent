#!/usr/bin/env python3
"""scripts/agent/signal_handler.py

SignalHandler — platform-specific signal handling for the REPL.

Responsibilities:
  - Registering SIGTERM and SIGINT handlers on Unix (loop.add_signal_handler)
  - SIGTERM (and Windows close/logoff/shutdown events) begin graceful shutdown by
    arming the one ShutdownBudget and setting the shutdown_event owned by AgentREPL,
    so the global deadline starts when shutdown is requested, not when the first step
    runs
  - SIGINT (and Windows Ctrl-C/Ctrl-Break) acts by input state through
    ReplInputController: discard the prompt line, cancel the turn, request job
    cancellation, or report that shutdown is already in progress. Once the budget is
    armed it also asks the step in progress to stop, instead of killing the process
    (REQ-002, REQ-011)
  - An opt-in force exit on a second Ctrl-C during shutdown (off by default)
  - Registering Windows console control handler fallback
"""

from __future__ import annotations

import asyncio
import logging
import os
import signal
from collections.abc import Callable
from typing import TYPE_CHECKING

from agent.repl_input_controller import (
    InterruptAction,
    ReplInputController,
    get_input_controller,
)

if TYPE_CHECKING:
    from agent.context import AgentContext
    from agent.shutdown_budget import ShutdownBudget

logger = logging.getLogger(__name__)

# Windows console control event numbers (kernel32 HandlerRoutine contract).
_CTRL_C_EVENT = 0
_CTRL_BREAK_EVENT = 1
_CTRL_CLOSE_EVENT = 2
_CTRL_LOGOFF_EVENT = 5
_CTRL_SHUTDOWN_EVENT = 6
_INTERRUPT_EVENTS = frozenset({_CTRL_C_EVENT, _CTRL_BREAK_EVENT})
_SHUTDOWN_EVENTS = frozenset(
    {_CTRL_CLOSE_EVENT, _CTRL_LOGOFF_EVENT, _CTRL_SHUTDOWN_EVENT}
)
_FORCE_EXIT_STATUS = 130

# Lazy imports inside methods to avoid circular dependency at module level.
# sys/win32api are only needed for Windows fallback path.


def _exit_process(status: int) -> None:
    """Exit immediately without cleanup (the default force-exit action)."""
    os._exit(status)


class SignalHandler:
    """Encapsulates platform-specific signal handling for the REPL.

    Responsibilities:
      - Registering SIGTERM/SIGINT handlers on Unix (loop.add_signal_handler)
      - Beginning graceful shutdown on SIGTERM and console close events, arming the
        process's one shutdown budget as it does
      - Acting on Ctrl-C by input state through the input controller, and asking the
        shutdown step in progress to stop once that budget is armed
      - Registering Windows console control handler fallback
    """

    def __init__(
        self,
        ctx: AgentContext,
        shutdown_event: asyncio.Event | None,
        *,
        controller: ReplInputController | None = None,
        budget: ShutdownBudget | None = None,
        force_exit_on_second_sigint: bool = False,
        force_exit: Callable[[int], None] | None = None,
    ) -> None:
        """Initialize with AgentContext and shutdown event references.

        Precondition: ctx must be an AgentContext instance. Passing other types
        will result in type checker errors but will not raise at runtime due to
        Python's dynamic typing. ``controller`` defaults to the process-shared input
        controller; ``budget`` is the process's one ShutdownBudget, and a handler
        without one keeps the pre-budget behavior of arming nothing. ``force_exit``
        defaults to an immediate process exit and is only called when the force-exit
        flag is set, which comes from ``shutdown_force_exit_on_second_sigint`` read
        once here rather than per signal.
        """
        self._ctx = ctx
        self._shutdown_event = shutdown_event
        self._controller = controller
        self._budget = budget
        # Read the configured flag once: a signal handler does no configuration work.
        # Identity, not truthiness: a non-bool stand-in for cfg must not enable os._exit.
        configured = getattr(ctx.cfg, "shutdown_force_exit_on_second_sigint", False)
        self._force_exit_on_second_sigint = (
            force_exit_on_second_sigint or configured is True
        )
        self._force_exit = force_exit if force_exit is not None else _exit_process
        self._ctypes_callback: object | None = None

    def _controller_obj(self) -> ReplInputController:
        return (
            self._controller if self._controller is not None else get_input_controller()
        )

    def _sigterm_handler(self) -> None:
        """Handle SIGTERM by arming the budget and beginning graceful shutdown."""
        if self._budget is not None:
            # The deadline starts at the request, so every step that follows is bounded
            # by what this request left rather than by a fresh window (REQ-002).
            self._budget.arm()
        self._ctx.conv.shutdown_requested = True
        if self._shutdown_event is not None:
            self._shutdown_event.set()
        self._controller_obj().shutdown()
        logger.info("SIGTERM received; graceful shutdown initiated")

    def _sigint_handler(self) -> None:
        """Handle Ctrl-C by the current input state; never starts shutdown itself."""
        action = self._controller_obj().handle_interrupt()
        logger.info("Interrupt received; action=%s", action.value)
        if self._budget is not None and self._budget.armed:
            # Shutdown is already running: ask the step in progress to stop at its next
            # boundary instead of killing the process (REQ-011). Which step that was,
            # and whether it says timed_out or outcome_unknown, is its own record.
            self._budget.request_interrupt()
            logger.warning("Interrupt requested for the shutdown step in progress")
        if (
            action is InterruptAction.SHUTDOWN_IN_PROGRESS
            and self._force_exit_on_second_sigint
        ):
            logger.warning("Second interrupt during shutdown; forcing exit")
            self._force_exit(_FORCE_EXIT_STATUS)

    def _dispatch_control_event(self, ctrl_type: int) -> bool:
        """Route a Windows console control event; must run on the loop thread.

        Ctrl-C and Ctrl-Break act as an interrupt; close, logoff, and shutdown begin
        graceful shutdown. Returns True when the event was handled.
        """
        if ctrl_type in _INTERRUPT_EVENTS:
            self._sigint_handler()
            return True
        if ctrl_type in _SHUTDOWN_EVENTS:
            self._sigterm_handler()
            return True
        return False

    def register(self, loop: asyncio.AbstractEventLoop) -> None:
        """Register signal handlers for SIGTERM and SIGINT."""
        handlers = {
            signal.SIGTERM: self._sigterm_handler,
            signal.SIGINT: self._sigint_handler,
        }
        fallback_done = False
        for sig, handler in handlers.items():
            try:
                loop.add_signal_handler(sig, handler)
            except NotImplementedError:
                if not fallback_done:
                    fallback_done = True
                    self._register_windows_fallback(loop, sig)

    def _register_windows_fallback(
        self, loop: asyncio.AbstractEventLoop, sig: signal.Signals
    ) -> None:
        """Register the console control handler on platforms without signal support."""

        def _on_control_event(ctrl_type: int) -> bool:
            handled = ctrl_type in _INTERRUPT_EVENTS or ctrl_type in _SHUTDOWN_EVENTS
            if handled:
                loop.call_soon_threadsafe(self._dispatch_control_event, ctrl_type)
            return handled

        try:
            import sys  # noqa: PLC0414 — deferred import: only needed on the NotImplementedError (non-POSIX) fallback path, not at module load time

            if not hasattr(sys, "frozen"):
                logger.warning(
                    "Signal handling not available on Windows outside console; "
                    "use Ctrl+C or close the terminal to shut down"
                )
                return
            try:
                import win32api  # noqa: PLC0414 — Windows-only dependency; a top-level import would break non-Windows platforms

                win32api.SetConsoleCtrlHandler(_on_control_event, True)
                logger.debug("Registered Windows console control handler for %s", sig)
            except ImportError:
                # pywin32 unavailable; try ctypes fallback
                self._register_ctypes_fallback(_on_control_event, sig)
            except Exception as e:  # noqa: BLE001 — best-effort Windows fallback registration must not crash startup
                logger.error("Failed to set Windows console control handler: %s", e)
        except Exception:  # noqa: BLE001 — best-effort non-POSIX signal fallback must not crash startup even on unexpected failures
            pass

    def _register_ctypes_fallback(
        self, on_control_event: Callable[[int], bool], sig: signal.Signals
    ) -> None:
        """Register the control handler through ctypes (no pywin32)."""
        try:
            import ctypes  # noqa: PLC0414 — deferred import: only needed on ImportError path
            import ctypes.wintypes  # noqa: PLC0414 — deferred import

            # Windows-only ctypes APIs are absent from POSIX typeshed stubs;
            # resolve by name so mypy/pyright accept the attribute access.
            winfunctype = getattr(ctypes, "WINFUNCTYPE")
            callback = winfunctype(ctypes.wintypes.BOOL, ctypes.wintypes.DWORD)(
                on_control_event
            )
            self._ctypes_callback = callback  # keep it alive: ctypes does not
            windll = getattr(ctypes, "windll")
            windll.kernel32.SetConsoleCtrlHandler(callback, True)
            logger.debug(
                "Registered Windows console control handler via ctypes for %s", sig
            )
        except Exception as e:  # noqa: BLE001 — best-effort Windows fallback registration must not crash startup
            logger.error(
                "Failed to set Windows console control handler via ctypes: %s", e
            )
            logger.warning(
                "pywin32 not available; signal handling disabled on Windows. "
                "Install pywin32 for Ctrl+C/Ctrl+Break support."
            )
