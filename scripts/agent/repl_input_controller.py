"""scripts/agent/repl_input_controller.py — the sole owner of REPL stdin reads.

Every prompt (normal, multiline, tool approval, Memory delete, Memory prune) is one
request submitted here. A request has an immutable identity; its result is delivered
only to the caller that submitted it, and a timed-out or cancelled request is
abandoned (a blocked ``input()`` cannot be interrupted, so its late line is dropped).
The controller also holds the interrupt state that decides what Ctrl-C does.
"""

from __future__ import annotations

import asyncio
import contextlib
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum

from agent.stdin_reader import StdinReader, get_stdin_reader

MULTILINE_TIMEOUT_S = 30.0


class PromptKind(StrEnum):
    """What a request asks the operator for."""

    NORMAL = "normal"
    MULTILINE = "multiline"
    TOOL_APPROVAL = "tool_approval"
    MEMORY_DELETE = "memory_delete"
    MEMORY_PRUNE = "memory_prune"


class InputOutcome(StrEnum):
    """How a request ended."""

    COMPLETED = "completed"
    TIMED_OUT = "timed_out"
    CANCELLED = "cancelled"
    EOF = "eof"
    SHUTDOWN = "shutdown"


class InputState(StrEnum):
    """What the REPL is doing; Ctrl-C acts by this state."""

    PROMPT = "prompt"
    TURN = "turn"
    JOB = "job"
    SHUTDOWN = "shutdown"


class InterruptAction(StrEnum):
    """What ``handle_interrupt`` did."""

    DISCARD_INPUT = "discard_input"
    CANCEL_TURN = "cancel_turn"
    CANCEL_JOB = "cancel_job"
    SHUTDOWN_IN_PROGRESS = "shutdown_in_progress"


class InputBusyError(RuntimeError):
    """A request was refused because another read is active or unresolved."""


class _InputAborted(Exception):
    """Internal: the read ended with KeyboardInterrupt/SystemExit."""


@dataclass(frozen=True)
class InputRequest:
    """One immutable prompt request."""

    prompt_kind: PromptKind
    prompt: str
    operation_id: str = ""
    timeout_s: float | None = None
    destructive: bool = False
    request_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    created_at: float = field(default_factory=time.time)


@dataclass(frozen=True)
class InputResult:
    """The outcome of one request; ``text`` is set only when it completed."""

    request: InputRequest
    outcome: InputOutcome
    text: str = ""


class ReplInputController:
    """Owns stdin: one active request at a time, results bound to their request."""

    def __init__(self, reader: StdinReader | None = None) -> None:
        """Use ``reader`` or, by default, the process-shared reader (looked up lazily)."""
        self._reader = reader
        self._state = InputState.PROMPT
        self._state_before_job = InputState.PROMPT
        self._active: InputRequest | None = None
        self._task: asyncio.Future[str] | None = None
        self._stop: InputOutcome | None = None
        self._turn_cancel: Callable[[], object] | None = None
        self._job_cancel: Callable[[], object] | None = None

    def _reader_obj(self) -> StdinReader:
        return self._reader if self._reader is not None else get_stdin_reader()

    @property
    def state(self) -> InputState:
        """The current interrupt state."""
        return self._state

    def set_state(self, state: InputState) -> None:
        """Set the interrupt state directly (used by tests and the shutdown path)."""
        self._state = state

    async def _read(self, prompt: str) -> str:
        try:
            return await self._reader_obj().read(prompt=prompt)
        except (KeyboardInterrupt, SystemExit) as exc:
            raise _InputAborted from exc

    async def submit(self, request: InputRequest) -> InputResult:
        """Run one request to its outcome; refuse it while the stdin is not free."""
        if self._active is not None:
            raise InputBusyError("another input request is active")
        if request.destructive and self._reader_obj().orphaned_read:
            raise InputBusyError("an earlier stdin read is still unresolved")
        self._active = request
        self._stop = None
        task = asyncio.ensure_future(self._read(request.prompt))
        self._task = task
        try:
            done, _ = await asyncio.wait({task}, timeout=request.timeout_s)
            if task not in done:
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task
                return InputResult(request, InputOutcome.TIMED_OUT)
            return self._finish(request, task)
        except asyncio.CancelledError:
            task.cancel()
            raise
        finally:
            self._active = None
            self._task = None

    def _finish(self, request: InputRequest, task: asyncio.Future[str]) -> InputResult:
        """Map a finished read task to the request's outcome."""
        if task.cancelled():
            return InputResult(request, self._stop or InputOutcome.CANCELLED)
        exc = task.exception()
        if isinstance(exc, (EOFError, _InputAborted)):
            return InputResult(request, InputOutcome.EOF)
        if exc is not None:
            raise exc
        return InputResult(request, InputOutcome.COMPLETED, task.result())

    async def collect_multiline(
        self, first_line: str, notify: Callable[[str], None], interactive: bool
    ) -> InputResult:
        """Collect backslash-continued lines; never submit partial text after a timeout."""
        parts = [first_line[:-1]]
        while True:
            result = await self.submit(
                InputRequest(
                    PromptKind.MULTILINE, "... ", timeout_s=MULTILINE_TIMEOUT_S
                )
            )
            if result.outcome is InputOutcome.COMPLETED:
                cont = result.text
                if cont.endswith("\\"):
                    parts.append(cont[:-1])
                    continue
                if cont:
                    parts.append(cont)
                break
            if result.outcome is InputOutcome.EOF:
                break
            if result.outcome is not InputOutcome.TIMED_OUT:
                return InputResult(result.request, result.outcome)
            choice = await self._offer_partial(parts, notify, interactive)
            if choice == "continue":
                continue
            if choice == "send":
                break
            return InputResult(result.request, InputOutcome.TIMED_OUT)
        return InputResult(
            InputRequest(PromptKind.MULTILINE, ""),
            InputOutcome.COMPLETED,
            "\n".join(parts),
        )

    async def _offer_partial(
        self, parts: list[str], notify: Callable[[str], None], interactive: bool
    ) -> str:
        """Return send, continue, or discard for timed-out partial multiline input."""
        count = len(parts)
        if not interactive:
            notify(f"Multiline input timed out; {count} partial line(s) discarded")
            return "discard"
        notify(
            f"Multiline input timed out with {count} partial line(s). "
            "Press Enter first: the line typed now belongs to the abandoned read "
            "and is dropped."
        )
        answer = await self.submit(
            InputRequest(PromptKind.NORMAL, "  [s]end / [c]ontinue / [d]iscard: ")
        )
        if answer.outcome is not InputOutcome.COMPLETED:
            return "discard"
        key = answer.text.strip().lower()[:1]
        return {"s": "send", "c": "continue"}.get(key, "discard")

    def begin_turn(self, cancel: Callable[[], object]) -> None:
        """Enter the turn state; ``cancel`` cancels the running turn."""
        self._turn_cancel = cancel
        if self._state is not InputState.SHUTDOWN:
            self._state = InputState.TURN

    def end_turn(self) -> None:
        """Leave the turn state."""
        self._turn_cancel = None
        if self._state is InputState.TURN:
            self._state = InputState.PROMPT

    def begin_job(self, cancel: Callable[[], object]) -> None:
        """Enter the job state; ``cancel`` requests job cancellation (seam)."""
        self._job_cancel = cancel
        if self._state is not InputState.SHUTDOWN:
            self._state_before_job = self._state
            self._state = InputState.JOB

    def end_job(self) -> None:
        """Leave the job state, restoring the previous one."""
        self._job_cancel = None
        if self._state is InputState.JOB:
            self._state = self._state_before_job

    def cancel_current(self) -> bool:
        """Discard the active read; return True when a request was active."""
        return self._stop_active(InputOutcome.CANCELLED)

    def shutdown(self) -> None:
        """Enter the shutdown state and end the active read with ``shutdown``."""
        self._state = InputState.SHUTDOWN
        self._stop_active(InputOutcome.SHUTDOWN)

    def _stop_active(self, outcome: InputOutcome) -> bool:
        task = self._task
        if self._active is None or task is None or task.done():
            return False
        self._stop = outcome
        task.cancel()
        return True

    def handle_interrupt(self) -> InterruptAction:
        """Act on Ctrl-C according to the current state and report the action."""
        if self._state is InputState.SHUTDOWN:
            return InterruptAction.SHUTDOWN_IN_PROGRESS
        if self._state is InputState.JOB and self._job_cancel is not None:
            self._job_cancel()
            return InterruptAction.CANCEL_JOB
        if self._state is InputState.TURN and self._turn_cancel is not None:
            self._turn_cancel()
            return InterruptAction.CANCEL_TURN
        self.cancel_current()
        return InterruptAction.DISCARD_INPUT


_shared_controller: ReplInputController | None = None


def get_input_controller() -> ReplInputController:
    """Return the process-shared controller, creating it on first use."""
    global _shared_controller
    if _shared_controller is None:
        _shared_controller = ReplInputController()
    return _shared_controller


def reset_input_controller() -> None:
    """Drop the shared instance so the next get_input_controller() builds a fresh one."""
    global _shared_controller
    _shared_controller = None
