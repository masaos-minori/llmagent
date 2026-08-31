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
from typing import TYPE_CHECKING, Any

from shared.json_utils import dumps as _json_dumps
from shared.logger import Logger
from shared.types import LLMMessage

from agent.audit_event_emitter import _format_session_id
from agent.context import AgentContext
from agent.conversation_state_manager import EPHEMERAL_KEYS
from agent.message_schema import validate_message

logger = Logger(__name__, "/opt/llm/logs/agent.log")

class TurnCoordinator:
    """Coordinates per-turn lifecycle: start/end audit events, ephemeral
    message cleanup, system prompt sync, and user message append."""

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

    def clear_previous_turn_ephemeral_messages(self, ctx: AgentContext) -> None:
        """Strip ephemeral/memory-injected system messages left over from the
        previous turn. Must run before this turn's own injections
        (ConversationStateManager.handle_memory_injection, classify_and_inject_mode)
        so it never strips content just added for the current turn.
        """
        ctx.conv.history = [
            m
            for m in ctx.conv.history
            if not any(k in EPHEMERAL_KEYS for k in m.keys())
        ]

    def sync_system_prompt(self, ctx: AgentContext) -> None:
        """Sync history[0] from ctx.conv.system_prompt_content before each turn."""
        if not ctx.conv.system_prompt_content:
            return
        if ctx.conv.history and ctx.conv.history[0]["role"] == "system":
            ctx.conv.history[0]["content"] = ctx.conv.system_prompt_content
        else:
            msg: LLMMessage = {
                "role": "system",
                "content": ctx.conv.system_prompt_content,
            }
            result = validate_message(dict(msg))
            if not result.success:
                logger.error(
                    "Dropping system prompt sync message that failed validation: %s",
                    result.reason,
                )
                return
            ctx.conv.history.insert(0, msg)

    async def append_user_message(self, ctx: AgentContext, line: str) -> None:
        """Append user message to history, sync system prompt, and increment turn counter."""
        self.sync_system_prompt(ctx)
        await ctx.conv.append_message({"role": "user", "content": line})
        ctx.stats.stat_turns += 1
        if ctx.stats.stat_turns == 1 and self._on_first_turn is not None:
            _task = asyncio.create_task(
                self._on_first_turn(line),
                name=getattr(self._on_first_turn, "__name__", "unknown_bg_task"),
            )
            self._background_tasks.add(_task)
            _task.add_done_callback(self._discard_and_log)
        ctx.session.save("user", line)
