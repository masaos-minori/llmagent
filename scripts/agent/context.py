#!/usr/bin/env python3
"""agent/context.py
Shared mutable runtime state injected into AgentREPL and CommandRegistry
via dependency injection.

Structure:
  ConversationState — per-session conversation fields
  TurnState         — per-turn transient fields
  RuntimeStats      — accumulated session statistics
  AppServices       — fully-initialized service references (built by factory.py)
  AgentContext      — DI hub; composes all of the above

Backward-compat flat access (e.g. ctx.history, ctx.stat_turns) is preserved
via __getattr__ / __setattr__ on AgentContext.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from rag.types import LLMMessage

from agent.config import build_agent_config
from agent.session import AgentSession
from db.tool_results import ToolResultStore

if TYPE_CHECKING:
    import httpx
    from shared.llm_client import LLMClient
    from shared.logger import Logger
    from shared.tool_executor import StdioTransport, ToolExecutor

    from agent.history import HistoryManager
    from agent.lifecycle import ServerLifecycleManager
    from agent.memory.layer import MemoryLayer


# ---------------------------------------------------------------------------
# Sub-structures
# ---------------------------------------------------------------------------


@dataclass
class ConversationState:
    """Per-session conversation fields."""

    history: list[LLMMessage] = field(default_factory=list)
    llm_url: str = ""
    debug_mode: bool = False
    plan_mode: bool = False
    system_prompt_name: str = "default"
    # Canonical system prompt text; Orchestrator syncs history[0] from this each turn.
    # Avoids direct history[0] writes from command handlers.
    system_prompt_content: str = ""
    shutdown_requested: bool = False


@dataclass
class TurnState:
    """Per-turn transient state; reset each turn by Orchestrator."""

    # UUID4 set by Orchestrator.handle_turn(); None between turns
    current_turn_id: str | None = None


@dataclass
class RuntimeStats:
    """Accumulated session statistics."""

    stat_turns: int = 0
    stat_tool_calls: int = 0
    stat_tool_errors: int = 0
    # Per-step latency samples (seconds); keyed by step name
    stat_latency: dict[str, list[float]] = field(default_factory=dict)
    stat_semantic_cache_hits: int = 0
    # LLM token usage accumulated across turns; None = endpoint did not return usage
    stat_input_tokens: int | None = None
    stat_output_tokens: int | None = None


class AppServices:
    """Fully-initialized service references built by factory.py.

    All required services are non-None.  memory is None when
    use_memory_layer=False (intentionally absent, not uninitialised).
    stdio_procs is populated by AgentREPL._start_stdio_servers() after init.
    """

    def __init__(
        self,
        http: httpx.AsyncClient,
        llm: LLMClient,
        tools: ToolExecutor,
        lifecycle: ServerLifecycleManager,
        hist_mgr: HistoryManager,
        audit_logger: Logger,
        memory: MemoryLayer | None,
        stdio_procs: dict[str, StdioTransport] | None = None,
    ) -> None:
        self.http = http
        self.llm = llm
        self.tools = tools
        self.lifecycle = lifecycle
        self.hist_mgr = hist_mgr
        self.audit_logger = audit_logger
        self.memory = memory
        self.stdio_procs: dict[str, StdioTransport] = (
            stdio_procs if stdio_procs is not None else {}
        )


# ---------------------------------------------------------------------------
# Composite context with backward-compat flat attribute access
# ---------------------------------------------------------------------------


class AgentContext:
    """Mutable runtime state shared between AgentREPL and CommandRegistry.

    Composes ConversationState, TurnState, RuntimeStats, and AppServices.
    Flat attribute access such as ctx.history or ctx.stat_turns is preserved
    via __getattr__ / __setattr__ for backward compatibility.

    ctx.services is None until factory.build_agent_context() completes.
    """

    # Flat-access aliases routed to sub-structures
    _CONV_FIELDS: frozenset[str] = frozenset(
        {
            "history",
            "llm_url",
            "debug_mode",
            "plan_mode",
            "system_prompt_name",
            "system_prompt_content",
            "shutdown_requested",
        }
    )
    _TURN_FIELDS: frozenset[str] = frozenset({"current_turn_id"})
    _STATS_FIELDS: frozenset[str] = frozenset(
        {
            "stat_turns",
            "stat_tool_calls",
            "stat_tool_errors",
            "stat_latency",
            "stat_semantic_cache_hits",
            "stat_input_tokens",
            "stat_output_tokens",
        }
    )
    _ALL_COMPAT: frozenset[str] = _CONV_FIELDS | _TURN_FIELDS | _STATS_FIELDS

    def __init__(self) -> None:
        # Sub-structures (must be set before any alias access)
        object.__setattr__(self, "conv", ConversationState())
        object.__setattr__(self, "turn", TurnState())
        object.__setattr__(self, "stats", RuntimeStats())
        # Config and session (direct fields)
        object.__setattr__(self, "cfg", build_agent_config())
        object.__setattr__(self, "session", AgentSession())
        # Persistent store for full tool results; /tool show <id> retrieves them
        object.__setattr__(self, "tool_result_store", ToolResultStore())
        # Services — None until factory.build_agent_context() assigns AppServices
        object.__setattr__(self, "services", None)

    def __getattr__(self, name: str) -> Any:
        # Called only when normal attribute lookup fails.
        # Delegate to the owning sub-structure for backward-compat flat names.
        if name in AgentContext._CONV_FIELDS:
            conv = self.__dict__.get("conv")
            if conv is not None:
                return getattr(conv, name)
        elif name in AgentContext._TURN_FIELDS:
            turn = self.__dict__.get("turn")
            if turn is not None:
                return getattr(turn, name)
        elif name in AgentContext._STATS_FIELDS:
            stats = self.__dict__.get("stats")
            if stats is not None:
                return getattr(stats, name)
        raise AttributeError(f"{type(self).__name__!r} has no attribute {name!r}")

    def __setattr__(self, name: str, value: Any) -> None:
        if name in AgentContext._ALL_COMPAT:
            # Route flat-name writes to the owning sub-structure.
            if name in AgentContext._CONV_FIELDS:
                sub = self.__dict__.get("conv")
            elif name in AgentContext._TURN_FIELDS:
                sub = self.__dict__.get("turn")
            else:
                sub = self.__dict__.get("stats")
            if sub is not None:
                setattr(sub, name, value)
                return
        object.__setattr__(self, name, value)
