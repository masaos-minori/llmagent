"""agent/commands/mixin_base.py
Common type-annotation base for all CommandRegistry mixin classes.

Each mixin inherits MixinBase so that the _ctx: AgentContext annotation
is declared exactly once rather than repeated in every mixin body.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agent.context import AgentContext


class MixinBase:
    """Shared annotation base for CommandRegistry mixins.

    Declares _ctx so all mixin subclasses satisfy the type checker without
    each repeating 'if TYPE_CHECKING: _ctx: AgentContext'.
    Provides shared helpers (_reset_session_stats) used across multiple mixins.
    """

    _ctx: AgentContext

    def _reset_session_stats(self, ctx: AgentContext) -> None:
        """Reset all per-session counters to zero.

        Called by _cmd_clear (_ContextMixin) and _load_session (_SessionMixin)
        so the counter reset logic lives in one place.
        """
        ctx.stats.stat_turns = 0
        ctx.stats.stat_tool_calls = 0
        ctx.stats.stat_tool_errors = 0
        ctx.stats.stat_latency = {}
        ctx.stats.stat_semantic_cache_hits = 0
        if ctx.services.llm is not None:
            ctx.services.llm.stat_retries = 0
