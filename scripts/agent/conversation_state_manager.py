#!/usr/bin/env python3
"""scripts/agent/conversation_state_manager.py

Conversation history manipulation: ephemeral cleanup, system prompt sync,
user message append, memory injection, and history compression.

Extracted from orchestrator.py (_append_user_message, _sync_system_prompt,
_clear_previous_turn_ephemeral_messages, _process_turn).
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any

from shared.types import LLMMessage

from agent.message_schema import validate_message

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from agent.context import AgentContext
    from agent.diagnostic_store import DiagnosticStore

# Ephemeral keys used to identify messages that should be cleaned up between turns.
_EPHEMERAL_KEYS: frozenset[str] = frozenset(
    {"_ephemeral", "_memory_injected", "_skill_ephemeral"}
)

# Backward-compatible alias for existing callers that import EPHEMERAL_KEYS
EPHEMERAL_KEYS = _EPHEMERAL_KEYS


class ConversationStateManager:
    """Manages conversation history state across turns.

    Responsibilities:
      - Clear ephemeral/memory-injected messages from previous turn
      - Sync system prompt into history[0] before each turn
      - Append user message and increment turn counter
      - Handle first-turn background task spawning
      - Inject MDQ/RAG mode hints via classify_and_inject_mode
    """

    # Class attribute so _clear_previous_turn_ephemeral_messages can reference it
    # without needing an instance.
    _EPHEMERAL_KEYS = _EPHEMERAL_KEYS

    def __init__(
        self,
        ctx: AgentContext,
        *,
        diagnostic_store: DiagnosticStore | None = None,
        tasks: set[asyncio.Task[Any]],
        on_discard: Callable[[asyncio.Task[Any]], None],
        tracer: Any = None,
        on_first_turn: Callable[[str], Any] | None = None,
        on_turn_start: Callable[[], None] | None = None,
        on_turn_end: Callable[[], None] | None = None,
        on_error: Callable[[Exception], None] | None = None,
    ) -> None:
        """Initialize the conversation state manager."""
        self._ctx = ctx
        self._diagnostic_store = diagnostic_store
        self._tasks = tasks
        self._on_discard = on_discard
        self._tracer = tracer
        self._on_first_turn = on_first_turn
        self._on_turn_start = on_turn_start
        self._on_turn_end = on_turn_end
        self._on_error = on_error

    @property
    def ephemeral_keys(self) -> frozenset[str]:
        """Return the set of ephemeral keys used for message filtering."""
        return self._EPHEMERAL_KEYS

    def clear_previous_turn_ephemeral_messages(self) -> None:
        """Strip ephemeral/memory-injected system messages left over from the previous turn."""
        ctx = self._ctx
        ctx.conv.history = [
            m
            for m in ctx.conv.history
            if not any(k in self._EPHEMERAL_KEYS for k in m.keys())
        ]

    def sync_system_prompt(self) -> None:
        """Sync history[0] from ctx.conv.system_prompt_content before each turn."""
        ctx = self._ctx
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

    async def append_user_message(self, line: str) -> None:
        """Append user message to history, sync system prompt, and increment turn counter."""
        ctx = self._ctx
        self.sync_system_prompt()
        await ctx.conv.append_message({"role": "user", "content": line})
        ctx.stats.stat_turns += 1
        if ctx.stats.stat_turns == 1 and self._on_first_turn is not None:
            _task = asyncio.create_task(
                self._on_first_turn(line),
                name=getattr(self._on_first_turn, "__name__", "unknown_bg_task"),
            )
            self._tasks.add(_task)
            _task.add_done_callback(self._on_discard)
        ctx.session.save("user", line)

    async def handle_memory_injection(self, line: str) -> None:
        """Inject memory-based context into the conversation."""
        ctx = self._ctx
        if ctx.services_required.memory is not None:
            try:
                memory_snippets = await ctx.services_required.memory.on_user_prompt(
                    query=line,
                    session_id=ctx.session.session_id,
                )
                if memory_snippets:
                    memory_block = "--- USER MEMORY ---\n" + "\n".join(
                        f"- {snippet.text}" for snippet in memory_snippets
                    )
                    await ctx.conv.append_message(
                        {
                            "role": "system",
                            "content": memory_block,
                            "_memory_injected": True,
                        },
                        source="memory_injection",
                    )
            except Exception as e:  # noqa: BLE001 — catching all exceptions during memory injection to avoid blocking the turn
                logger.warning("Memory injection failed: %s", e)
                ctx.conv.memory_disabled = True
                if not ctx.conv.memory_warning_shown:
                    ctx.conv.memory_warning_shown = True

    async def handle_history_compression(self) -> None:
        """Compress conversation history if it exceeds configured limits."""
        ctx = self._ctx
        if ctx.services_required.hist_mgr is not None:
            ctx.conv.history, _result = await ctx.services_required.hist_mgr.compress(
                ctx.conv.history
            )

    @contextmanager
    def tool_override(self, allowed: list[str] | None) -> Iterator[None]:
        """Temporarily override allowed_tools for the duration of a turn."""
        original = self._ctx.cfg.tool.allowed_tools
        if allowed is not None:
            self._ctx.cfg.tool.allowed_tools = allowed
        try:
            yield
        finally:
            self._ctx.cfg.tool.allowed_tools = original
