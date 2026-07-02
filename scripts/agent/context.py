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

Access pattern:
  ctx.conv.*    — ConversationState fields (history, system_prompt_*, llm_url, …)
  ctx.turn.*    — TurnState fields (current_turn_id)
  ctx.stats.*   — RuntimeStats fields (stat_turns, stat_tool_calls, …)
  ctx.services  — AppServices (llm, tools, lifecycle, …)
  ctx.cfg       — AgentConfig
  ctx.session   — AgentSession
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from db.tool_results import ToolResultStore
from shared.mcp_config import McpServerHealthRegistry
from shared.types import LLMMessage

from agent.config import build_agent_config
from agent.session import AgentSession

if TYPE_CHECKING:
    import httpx
    from shared.llm_client import LLMClient
    from shared.logger import Logger
    from shared.tool_executor import ToolExecutor

    from agent.diagnostic_store import DiagnosticStore
    from agent.history import HistoryManager
    from agent.lifecycle_protocol import LifecycleManagerProtocol
    from agent.memory.services import MemoryServices
    from agent.repository_gateway import RepositoryGateway


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
    is_processing: bool = False  # True while handle_turn() is executing


@dataclass
class TurnState:
    """Per-turn transient state; reset each turn by Orchestrator."""

    # UUID4 set by Orchestrator.handle_turn(); None between turns
    current_turn_id: str | None = None
    # Background tasks spawned during this turn; tracked for clean shutdown
    background_tasks: set[asyncio.Task[Any]] = field(default_factory=set)
    # Error kind from the most recent turn failure; None when last turn succeeded
    last_error_kind: str | None = None
    # Display cache for the current pending approval ID.
    # Populated from durable storage (StateStore) at startup by _recover_pending_approvals().
    # Use StateStore.find_latest_pending_approval() as the authoritative source.
    pending_approval_id: str | None = None
    # Task ID to resume after /approve; set by /approve command, cleared by Orchestrator.handle_turn.
    pending_approval_task_id: str | None = None


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
    # Per-round serialization events captured from _execute_standard/_execute_with_dag
    stat_serialization_events: list[dict] = field(default_factory=list)
    stat_serialization_total_overhead_ms: float = 0.0
    stat_memory_consistency_failures: int = 0
    stat_memory_circuit_open: bool = False
    stat_memory_fts_fallback_count: int = 0


@dataclass
class WorkflowState:
    """Per-session workflow runtime state; transient, not persisted.

    Display cache only — not the authoritative source of truth.
    The authoritative state is in workflow.sqlite (StateStore).
    Populated at startup by _recover_pending_approvals(); cleared by /approve and /reject.
    """

    active: bool = False
    current_task_id: str | None = None
    workflow_id: str | None = None
    current_workflow_version: str | None = None
    approval_pending: bool = False
    last_session_id: str | None = None


class AppServices:
    """Fully-initialized service references built by factory.py.

    All required services are non-None.  memory is None when
    use_memory_layer=False (intentionally absent, not uninitialised).
    gateway is None until factory.py constructs and injects RepositoryGateway.
    """

    def __init__(
        self,
        http: httpx.AsyncClient,
        llm: LLMClient,
        tools: ToolExecutor,
        lifecycle: LifecycleManagerProtocol,
        hist_mgr: HistoryManager,
        audit_logger: Logger,
        memory: MemoryServices | None,
        health_registry: McpServerHealthRegistry | None = None,
        gateway: RepositoryGateway | None = None,
    ) -> None:
        self.http = http
        self.llm = llm
        self.tools = tools
        self.lifecycle = lifecycle
        self.hist_mgr = hist_mgr
        self.audit_logger = audit_logger
        self.memory = memory
        self.health_registry = health_registry
        self.gateway: RepositoryGateway | None = gateway
        self.serialization_events: int = 0
        self.serialization_tools_affected: int = 0


# ---------------------------------------------------------------------------
# Composite context
# ---------------------------------------------------------------------------


class AgentContext:
    """Mutable runtime state shared between AgentREPL and CommandRegistry.

    Composes ConversationState, TurnState, RuntimeStats, WorkflowState, and AppServices.
    Access sub-structures directly: ctx.conv.*, ctx.turn.*, ctx.stats.*, ctx.workflow.*.

    ctx.services is None until factory.build_agent_context() completes.
    """

    def __init__(self) -> None:
        self.conv = ConversationState()
        self.turn = TurnState()
        self.stats = RuntimeStats()
        self.workflow = WorkflowState()
        self.cfg = build_agent_config()
        self.session = AgentSession()
        # Persistent store for full tool results; /tool show <id> retrieves them
        self.tool_result_store = ToolResultStore()
        # Wired by Orchestrator.__init__() to its DiagnosticStore instance.
        # None until an Orchestrator is constructed with this context.
        self.diagnostics: DiagnosticStore | None = None
        # Set to AppServices by factory.build_agent_context() before first use.
        self.services: AppServices | None = None

    @property
    def services_required(self) -> AppServices:
        """Return services, raising RuntimeError when not yet initialized."""
        svc: AppServices | None = self.services
        if svc is None:
            raise RuntimeError(
                "AgentContext.services not initialized — call build_agent_context() first"
            )
        return svc
