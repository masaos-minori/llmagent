#!/usr/bin/env python3
"""scripts/db/write_gate.py — Process-wide write gate for the SQLite layer.

cliplc004 REQ-004, REQ-005.

Responsibilities:
  - Decide when a write is allowed: `open` accepts every write, `closing` accepts
    only the steps the shutdown sequence authorized, `closed` accepts none
  - Refuse a disallowed write through one exception type and count it, so a caller
    that swallows the error is still visible in the shutdown report (REQ-012)
  - Name the shutdown step that holds an authorization, and keep that
    authorization scoped to the `with` block that asked for it
  - Classify a SQL statement as a write or a read, so the read paths the shutdown
    sequence depends on are never gated (REQ-006, REQ-008)

The gate decides and records; it owns no connection and runs no statement. The
db layer consults it from `SQLiteHelper`'s write entry points (`db/helper.py`),
which is the only place that covers every caller: the import contract allows only
`agent -> db`, so an agent-side flag could not stop a write made from elsewhere.
"""

from __future__ import annotations

import contextvars
import logging
import re
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from enum import StrEnum
from typing import Final

logger = logging.getLogger(__name__)

# Leading keywords that are reads. Everything else is treated as a write.
_READ_KEYWORDS: Final[frozenset[str]] = frozenset({"SELECT", "EXPLAIN"})

# A PRAGMA is a read only when it queries a setting: an assignment or an
# argument (`PRAGMA journal_mode=WAL`, `PRAGMA wal_checkpoint(TRUNCATE)`) writes.
_PRAGMA_WRITE_MARKERS: Final[tuple[str, ...]] = ("=", "(")

_KEYWORD_RE: Final[re.Pattern[str]] = re.compile(r"[A-Za-z_]+")

# The shutdown steps that currently hold an authorization, innermost last. A
# ContextVar rather than an instance field because the shutdown steps run their
# DB work on asyncio.to_thread workers, which inherit a copy of the caller's
# context, while a thread that was not started inside the with block does not.
_AUTH_STACK: contextvars.ContextVar[tuple[str, ...]] = contextvars.ContextVar(
    "db_write_gate_authorization", default=()
)


class WriteGateState(StrEnum):
    """How strict the gate currently is about writes (REQ-004)."""

    OPEN = "open"
    """Normal operation: every write is allowed."""
    CLOSING = "closing"
    """Shutdown has begun: only the authorized shutdown steps may write."""
    CLOSED = "closed"
    """The settle window is over: no write is allowed at all."""


class WriteGateClosed(RuntimeError):
    """A write was refused by the gate (REQ-004, AC-2).

    The message names the gate state and the refused operation only: never a
    file path, a DSN, or the SQL text (REQ-013).
    """


def _leading_keyword(sql: str) -> str:
    """Return the first keyword of a statement, skipping leading comments.

    An empty result means the statement could not be named, which the classifier
    treats as a write.
    """
    text = sql
    while True:
        text = text.lstrip()
        if text.startswith("--"):
            _, _, text = text.partition("\n")
            continue
        if text.startswith("/*"):
            end = text.find("*/")
            if end == -1:
                return ""
            text = text[end + 2 :]
            continue
        break
    match = _KEYWORD_RE.match(text)
    return match.group(0).upper() if match else ""


def is_write_statement(sql: str) -> bool:
    """True when the statement writes, so the caller must consult the gate.

    Fail closed: a statement whose leading keyword cannot be named, including an
    empty one, counts as a write. `WITH` counts as a write for the same reason;
    no read in `scripts/` is written as a CTE today, so the fail-closed branch
    refuses no read that exists.
    """
    keyword = _leading_keyword(sql)
    if keyword in _READ_KEYWORDS:
        return False
    if keyword == "PRAGMA":
        body = sql[len(keyword) :]
        return any(marker in body for marker in _PRAGMA_WRITE_MARKERS)
    return True


class WriteGate:
    """The gate itself: a state machine, an authorization stack, and a counter.

    State and counter are guarded by a lock because every thread that writes
    consults the same gate, and the shutdown sequence closes it from a different
    thread than the one that runs the steps.
    """

    def __init__(self) -> None:
        """Initialize an open gate with a zero refused-write count."""
        self._lock = threading.Lock()
        self._state = WriteGateState.OPEN
        self._refused_count = 0

    @property
    def state(self) -> WriteGateState:
        """Return how strict the gate currently is."""
        with self._lock:
            return self._state

    @property
    def refused_count(self) -> int:
        """Return how many writes the gate has refused (REQ-012)."""
        with self._lock:
            return self._refused_count

    @property
    def authorized_step(self) -> str | None:
        """Return the innermost shutdown step holding an authorization."""
        stack = _AUTH_STACK.get()
        return stack[-1] if stack else None

    def close(self) -> None:
        """Step the gate one stage stricter: open to closing, closing to closed.

        Idempotent past `closed`. The coordinator calls this before the settle
        step and again after it, which is what turns a late write from a
        background task into a refusal rather than a silent success.
        """
        with self._lock:
            if self._state is WriteGateState.OPEN:
                self._state = WriteGateState.CLOSING
            else:
                self._state = WriteGateState.CLOSED

    def close_now(self) -> None:
        """Move the gate straight to `closed`, skipping the settling window."""
        with self._lock:
            self._state = WriteGateState.CLOSED

    def reset(self) -> None:
        """Return the gate to `open` with a zero counter.

        Called at the start of a fresh app lifecycle, the same role
        `clear_shutdown_flag` plays for the event bus
        (`scripts/eventbus/db_conn.py:54-61`): a restarted process, or a second
        test context in the same worker, must not inherit a closed gate.
        """
        with self._lock:
            self._state = WriteGateState.OPEN
            self._refused_count = 0

    def check_write(self, operation: str = "write") -> None:
        """Raise `WriteGateClosed` unless this write is allowed.

        Allowed while the gate is `open`, and in any state while the calling
        context holds an authorization from `authorize`. A refusal is counted
        before it is raised, so a caller that swallows the exception is still in
        the refused-write count.
        """
        authorized = bool(_AUTH_STACK.get())
        with self._lock:
            state = self._state
            if state is WriteGateState.OPEN or authorized:
                return
            self._refused_count += 1
        logger.debug(
            "write refused by the db write gate: state=%s operation=%s",
            state.value,
            operation,
        )
        raise WriteGateClosed(
            f"write refused: db write gate is {state.value} (operation={operation})"
        )

    @contextmanager
    def authorize(self, step_name: str) -> Iterator[str]:
        """Permit writes for the duration of the block, named by the step.

        The authorization is scoped: it is gone when the block exits, including
        when the block raises, and it does not reach a thread that was not
        started inside it. Nest is allowed, so a step may wrap a sub-step.
        """
        if not step_name:
            raise ValueError("step_name must be a non-empty string")
        token = _AUTH_STACK.set((*_AUTH_STACK.get(), step_name))
        try:
            yield step_name
        finally:
            _AUTH_STACK.reset(token)


_GATE = WriteGate()


def get_write_gate() -> WriteGate:
    """Return the process-wide gate every db write path consults.

    The gate is process-wide and owned by the db layer, not passed per call: the
    shutdown coordinator closes this instance once and every write path consults
    the same object (REQ-005).
    """
    return _GATE
