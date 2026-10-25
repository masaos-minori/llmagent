"""scripts/agent/commands/mixin_base.py

Common type-annotation base for all CommandRegistry mixin classes.

Each mixin inherits MixinBase so that the _ctx: AgentContext annotation
is declared exactly once rather than repeated in every mixin body.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

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


def refresh_session_correlation(ctx: AgentContext) -> None:
    """Refresh the MCP transport correlation id after a session-id change.

    MUST be called by every flow that changes the active session id outside the
    one-time startup wiring in repl_input_loop (session restore, new-session
    clear). No-op when MCP tools are disabled (tools is None) or the session id
    is not yet assigned.
    """
    if ctx.services_required.tools is not None and ctx.session.session_id is not None:
        ctx.services_required.tools.set_session_id(str(ctx.session.session_id))


class MixinBase:
    """Shared annotation base for CommandRegistry mixins.

    Declares _ctx so all mixin subclasses satisfy the type checker without
    each repeating 'if TYPE_CHECKING: _ctx: AgentContext'.
    Provides shared helpers used across multiple mixins.
    """

    _ctx: AgentContext
    _out: OutputPort = CliOutputPort()  # overridden by CommandRegistry.__init__

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """No-op initializer; subclasses forward to this base via super().__init__()."""
        pass
