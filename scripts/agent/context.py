#!/usr/bin/env python3
"""scripts/agent/context.py

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
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from shared.mcp_config import McpServerHealthRegistry
from shared.runtime_tool_registry import RuntimeToolRegistry
from shared.types import LLMMessage

from agent.config_builders import build_agent_config
from agent.message_schema import ROLE_KEY_WHITELIST, TRUSTED_SOURCES, validate_message
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


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Sub-structures
# ---------------------------------------------------------------------------


def _sanitize_message(msg: LLMMessage, *, source: str = "") -> LLMMessage | None:
    """Strip keys not allowed for *msg*'s role, returning ``None`` if unsalvageable.

    Keeps only keys in ``ROLE_KEY_WHITELIST`` for the message's role, plus any
    ephemeral keys authorized for *source* via ``TRUSTED_SOURCES``. Unknown
    roles fall back to the minimal ``{"role", "content"}`` whitelist. Returns
    ``None`` when the sanitized result would be missing ``role`` or
    ``content``, signaling that the message must be dropped entirely.
    """
    role = msg.get("role")
    allowed_keys = ROLE_KEY_WHITELIST.get(role, {"role", "content"})
    allowed_ephemeral = TRUSTED_SOURCES.get(source, set())
    sanitized: dict[str, Any] = {
        key: value
        for key, value in msg.items()
        if key in allowed_keys or key in allowed_ephemeral
    }
    if "role" not in sanitized or "content" not in sanitized:
        return None
    return cast(LLMMessage, sanitized)


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
    memory_disabled: bool = False  # True when memory injection failed during startup
    memory_warning_shown: bool = (
        False  # Whether the "memory disabled" warning was displayed
    )

    def append_message(self, msg: LLMMessage, *, source: str = "") -> None:
        """Validate *msg* and append it to history, sanitizing or dropping on failure.

        *source* is validation-only metadata: it authorizes trusted ephemeral
        keys (e.g. ``_memory_injected``) for the validation check, but is never
        persisted onto the stored message or written into ``self.history``.

        On validation failure the message is sanitized (disallowed/unauthorized
        keys stripped) and a warning is logged. If sanitization would leave the
        message without ``role`` or ``content``, it is dropped entirely and an
        error is logged instead of appending a partially-valid message.
        """
        check_view: dict[str, Any] = dict(msg, source=source) if source else dict(msg)
        result = validate_message(check_view)
        if result.success:
            self.history.append(msg)
            return

        role = msg.get("role", "<unknown>")
        logger.warning(
            "Sanitizing invalid message (role=%s, source=%s): %s",
            role,
            source or "<none>",
            result.reason,
        )
        sanitized = _sanitize_message(msg, source=source)
        if sanitized is None:
            logger.error(
                "Dropping message after sanitization removed required fields (role=%s)",
                role,
            )
            return
        self.history.append(sanitized)

    def extend_messages(self, msgs: list[LLMMessage], *, source: str = "") -> None:
        """Validate and append each message in *msgs* independently.

        A single invalid message among several valid ones only affects that
        message (sanitized or dropped); it does not block the others.
        """
        for msg in msgs:
            self.append_message(msg, source=source)

    def replace_history(self, msgs: list[LLMMessage], *, source: str = "") -> None:
        """Clear history, then validate and append each message in *msgs*."""
        self.history = []
        self.extend_messages(msgs, source=source)


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
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    turn_count: int = 0
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def add_tool_call(self, call: dict[str, Any]) -> None:
        """Add a tool call to the current turn. Thread-safe."""
        async with self._lock:
            self.tool_calls.append(call)
            self.turn_count += 1

    async def get_tool_calls(self) -> list[dict[str, Any]]:
        """Get the current tool calls. Thread-safe."""
        async with self._lock:
            return list(self.tool_calls)


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
    stat_partial_completions: int = 0


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
        runtime_tools: RuntimeToolRegistry | None = None,
    ) -> None:
        """Initialize all required service references for the agent runtime."""
        self.http = http
        self.llm = llm
        self.tools = tools
        self.lifecycle = lifecycle
        self.hist_mgr = hist_mgr
        self.audit_logger = audit_logger
        self.memory = memory
        self.health_registry = health_registry
        self.gateway: RepositoryGateway | None = gateway
        self.runtime_tools: RuntimeToolRegistry | None = runtime_tools
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
        """Create an empty AgentContext with default state objects."""
        self.conv = ConversationState()
        self.turn = TurnState()
        self.stats = RuntimeStats()
        self.workflow = WorkflowState()
        try:
            self.cfg = build_agent_config()
        except Exception as e:  # noqa: BLE001 — any config-load failure must be wrapped into one RuntimeError with context
            config_dir = Path(__file__).resolve().parent.parent.parent / "config"
            raise RuntimeError(
                f"Failed to load agent config ({config_dir}): {e.__class__.__name__}: {e}"
            ) from None
        self.session = AgentSession()

        # Wired by Orchestrator.__init__() to its DiagnosticStore instance.
        # None until an Orchestrator is constructed with this context.
        self.diagnostics: DiagnosticStore | None = None
        # Set to AppServices by factory.build_agent_context() before first use.
        self.services: AppServices | None = None

    @property
    def services_required(self) -> AppServices:
        """Return services, raising RuntimeError when not yet initialized."""
        if self.services is None:
            raise RuntimeError(
                "AgentContext.services not initialized — call build_agent_context() first"
            )
        return self.services
