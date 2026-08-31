#!/usr/bin/env python3
"""scripts/agent/conversation_state_manager.py

Conversation history manipulation (memory injection, history compression),
extracted from Orchestrator (see
`issues/done/20260829-080923_refactor_001_orchestrator_separation.md`).
"""

from __future__ import annotations

from agent.context import AgentContext
from agent.llm_turn_runner import LLMTurnRunner

# Keys that mark a conversation-history message as ephemeral/injected for the
# current turn only — stripped from history at the start of every turn by
# `TurnCoordinator.clear_previous_turn_ephemeral_messages` before this turn's
# own injections run.
EPHEMERAL_KEYS: frozenset[str] = frozenset(
    {"_ephemeral", "_memory_injected", "_skill_ephemeral"}
)


class ConversationStateManager:
    """Injects memory context and compresses conversation history."""

    def __init__(self, llm_runner: LLMTurnRunner) -> None:
        """Initialize with the LLMTurnRunner used for compression's tracing span."""
        self._llm_runner = llm_runner

    async def handle_memory_injection(self, ctx: AgentContext, line: str) -> None:
        """Retrieve relevant memory snippets and inject them into conversation history."""
        if ctx.services_required.memory is not None:
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

    async def handle_history_compression(self, ctx: AgentContext) -> None:
        """Compress conversation history and replace messages if compression occurred.

        Note: ephemeral/memory-injected messages are NOT filtered here because
        `TurnCoordinator.clear_previous_turn_ephemeral_messages()` already
        strips them before every turn. Passing the full history avoids
        double-filtering.

        Note: the compressed history is also NOT routed through
        ConversationState.replace_history() — hist_mgr.compress() only produces
        role/content-only summary messages (see history.py's
        _build_summary_message()), which are already schema-conformant by
        construction, so re-validating here would be redundant.
        """
        with self._llm_runner._span_ctx("compress"):
            ctx.conv.history, result = await ctx.services_required.hist_mgr.compress(
                ctx.conv.history
            )
            if (
                result.compressed_count > 0
                or result.summary_added
                or result.is_fallback
            ):
                ctx.session.replace_messages(ctx.conv.history)
