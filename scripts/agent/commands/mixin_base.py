"""agent/commands/mixin_base.py
Common type-annotation base for all CommandRegistry mixin classes.

Each mixin inherits MixinBase so that the _ctx: AgentContext annotation
is declared exactly once rather than repeated in every mixin body.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agent.commands.output_port import CliOutputPort, OutputPort

if TYPE_CHECKING:
    from agent.context import AgentContext


def reset_session_stats(ctx: AgentContext) -> None:
    """Reset all per-session counters to zero.

    Used by _cmd_clear, _load_session, and session_restore service.
    """
    ctx.stats.stat_turns = 0
    ctx.stats.stat_tool_calls = 0
    ctx.stats.stat_tool_errors = 0
    ctx.stats.stat_latency = {}
    ctx.stats.stat_semantic_cache_hits = 0
    if ctx.services.llm is not None:
        ctx.services.llm.stat_retries = 0


class MixinBase:
    """Shared annotation base for CommandRegistry mixins.

    Declares _ctx so all mixin subclasses satisfy the type checker without
    each repeating 'if TYPE_CHECKING: _ctx: AgentContext'.
    Provides shared helpers used across multiple mixins.
    """

    _ctx: AgentContext
    _out: OutputPort = CliOutputPort()  # overridden by CommandRegistry.__init__
