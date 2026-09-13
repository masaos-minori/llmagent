#!/usr/bin/env python3
"""scripts/agent/turnd_coordinator.py

Turn lifecycle coordination: start/end events only.

Extracted from orchestrator.py (_handle_turn_start, _handle_turn_end).
"""

from __future__ import annotations

import asyncio
import time
import uuid
from collections.abc import Callable
from typing import Any

from shared.json_utils import dumps as _json_dumps

from agent.audit_event_emitter import _format_session_id
from agent.context import AgentContext


class TurnCoordinator:
    """Coordinates per-turn lifecycle: start/end audit events only."""

    def __init__(
        self,
        background_tasks: set[asyncio.Task[object]],
        *,
        on_first_turn: Callable[[str], Any] | None = None,
        discard_and_log: Callable[[asyncio.Task[Any]], None],
        build_turn_end_event: Callable[
            [AgentContext, float, str | None, str | None, bool],
            dict[str, int | float | str | None],
        ],
    ) -> None:
        """Initialize with the shared background-task set, the first-turn
        callback, and the injected BgTaskMonitor/AuditEventEmitter callables
        this coordinator delegates to."""
        self._background_tasks = background_tasks
        self._on_first_turn = on_first_turn
        self._discard_and_log = discard_and_log
        self._build_turn_end_event = build_turn_end_event

    async def handle_turn_start(self, ctx: AgentContext, line: str) -> None:
        """Assign a turn ID and emit a turn_start audit event."""
        ctx.turn.current_turn_id = str(uuid.uuid4())
        session_id = _format_session_id(ctx.session.session_id) or "none"
        if ctx.services_required.audit_logger is not None:
            ctx.services_required.audit_logger.info(
                _json_dumps(
                    {
                        "event": "turn_start",
                        "task_id": ctx.turn.current_turn_id,
                        "worker_id": session_id,
                        "event_id": str(uuid.uuid4()),
                        "ts": time.time(),
                    },
                ),
            )

    async def handle_turn_end(
        self,
        ctx: AgentContext,
        line: str,
        answer: str,
        turn_started_at: float,
        error_kind: str | None,
        is_partial: bool = False,
    ) -> None:
        """Emit a turn_end audit event and clear the current turn ID."""
        elapsed_ms = round((time.perf_counter() - turn_started_at) * 1000, 1)
        if ctx.services_required.audit_logger is not None:
            event = self._build_turn_end_event(
                ctx, elapsed_ms, error_kind, ctx.turn.current_turn_id, is_partial
            )
            ctx.services_required.audit_logger.info(_json_dumps(event))
        ctx.turn.current_turn_id = None
