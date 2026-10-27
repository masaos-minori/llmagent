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
from typing import TYPE_CHECKING, Any, cast

from shared.config_loader import ConfigLoader
from shared.mcp_config import McpServerHealthRegistry
from shared.runtime_paths import resolve_config_dir
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
    from agent.turn_persistence import TurnPersistence


logger = logging.getLogger(__name__)

# Sentinel source forced into the validation view during history restore.
# Guaranteed absent from `TRUSTED_SOURCES`, so any ephemeral key on a restored
# row fails `validate_message()` and is stripped by `_sanitize_message()`.
# Restore data comes from session.sqlite, which a local actor may tamper with,
# so every restored row is treated as untrusted regardless of its embedded source.
_UNTRUSTED_RESTORE_SOURCE = "__restore_untrusted__"


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
    """Per-session conversation fields.

    History access is synchronized via asyncio.Lock. The asyncio single-threaded
    model means coroutines do not interleave except at await points. If concurrent
    access ever becomes possible (e.g., multi-loop), locking must be added here.
    """

    _history_lock: asyncio.Lock | None = None
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
    memory_disabled: bool = False  # True when a memory-injection attempt failed; cleared on the next successful attempt
    memory_warning_shown: bool = False  # Whether the "memory degraded" warning was shown; reset on recovery so a later degradation re-warns once
    undo_floor: int = (
        0  # index into history of the /undo compression boundary; 0 = none
    )

    @property
    def _ensure_lock(self) -> asyncio.Lock:
        if self._history_lock is None:
            self._history_lock = asyncio.Lock()
        return self._history_lock

    async def append_message(self, msg: LLMMessage, *, source: str = "") -> None:
        """Validate *msg* and append it to history, sanitizing or dropping on failure.

        *source* is validation-only metadata: it authorizes trusted ephemeral
        keys (e.g. ``_memory_injected``) for the validation check, but is never
        persisted onto the stored message or written into ``self.history``.

        On validation failure the message is sanitized (disallowed/unauthorized
        keys stripped) and a warning is logged. If sanitization would leave the
        message without ``role`` or ``content``, it is dropped entirely and an
        error is logged instead of appending a partially-valid message.
        """
        async with self._ensure_lock:
            await self._append_message_locked(msg, source=source)

    async def _append_message_locked(
        self, msg: LLMMessage, *, source: str = ""
    ) -> None:
        """Append a validated message. Caller MUST hold the lock."""
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

    async def extend_messages(
        self, msgs: list[LLMMessage], *, source: str = ""
    ) -> None:
        """Validate and append each message in *msgs* independently.

        A single invalid message among several valid ones only affects that
        message (sanitized or dropped); it does not block the others.
        """
        async with self._ensure_lock:
            for msg in msgs:
                await self._append_message_locked(msg, source=source)

    async def replace_history(
        self, msgs: list[LLMMessage], *, source: str = ""
    ) -> None:
        """Clear history, then validate and append each message in *msgs*.

        Every restored row is validated as untrusted: the per-message call forces
        ``_UNTRUSTED_RESTORE_SOURCE`` so any ephemeral key embedded in a restored
        row fails validation and is stripped by ``_sanitize_message()``, even when
        the row carries a trusted embedded ``source``.
        """
        async with self._ensure_lock:
            self.history = []
            for msg in msgs:
                await self._append_message_locked(msg, source=_UNTRUSTED_RESTORE_SOURCE)

    async def snapshot_messages(self) -> list[LLMMessage]:
        """Return a defensive copy of history, independent of later mutations.

        Used by the turn-persistence boundary to capture a stable turn-start
        memory image that survives the LLM/tool awaits of the turn.
        """
        async with self._ensure_lock:
            return [cast(LLMMessage, dict(msg)) for msg in self.history]

    async def restore_messages(self, snapshot: list[LLMMessage]) -> None:
        """Restore history to a previously captured snapshot, element-wise.

        Trusts its argument (the boundary's own turn-start snapshot) and does not
        re-validate, so the restored history equals the snapshot exactly
        (REQ-004, AC-004). Untrusted DB restores keep using ``replace_history``.
        """
        async with self._ensure_lock:
            self.history.clear()
            self.history.extend(snapshot)


@dataclass
class TurnState:
    """Per-turn transient state; reset each turn by Orchestrator."""

    # UUID4 set by Orchestrator.handle_turn(); None between turns
    current_turn_id: str | None = None
    # Background tasks registered for this process; written by ConversationStateManager,
    # cleared at shutdown by ResourceShutdownCoordinator. Process-lifetime: TurnState is
    # constructed once with AgentContext (context.py:320) and is not reset between turns.
    background_tasks: set[asyncio.Task[Any]] = field(default_factory=set)
    # The atomic turn-persistence boundary for the running turn (see
    # scripts/agent/turn_persistence.py). Set by Orchestrator._execute_turn at turn
    # start; the write-routing callers route every session-DB write through it so a
    # turn is persisted all-or-nothing (REQ-001, AC-001). None between turns.
    persistence_boundary: TurnPersistence | None = None


@dataclass
class RuntimeStats:
    """Accumulated session statistics."""

    stat_turns: int = 0
    stat_tool_calls: int = 0
    stat_tool_errors: int = 0
    # Per-step latency samples (seconds); keyed by step name
    stat_latency: dict[str, list[float]] = field(default_factory=dict)
    # LLM token usage accumulated across turns; None = endpoint did not return usage
    stat_input_tokens: int | None = None
    stat_output_tokens: int | None = None
    # Per-round serialization events captured from _execute_with_dag()
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
    """

    active: bool = False
    current_task_id: str | None = None
    workflow_id: str | None = None
    current_workflow_version: str | None = None
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
        # REQ-001: enforce invariant — all required services must be non-None
        for _name, _value in [
            ("http", http),
            ("llm", llm),
            ("tools", tools),
            ("lifecycle", lifecycle),
            ("hist_mgr", hist_mgr),
            ("audit_logger", audit_logger),
        ]:
            if _value is None:
                raise RuntimeError(f"AppServices: required service '{_name}' is None")
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
    __init__ restricts ConfigLoader to agent.toml before loading cfg.
    """

    def __init__(self) -> None:
        """Create an empty AgentContext with default state objects."""
        self.conv = ConversationState()
        self.turn = TurnState()
        self.stats = RuntimeStats()
        self.workflow = WorkflowState()
        # REQ-001: unconditional restriction, matching every other process entry point
        ConfigLoader.restrict_to("agent.toml")
        try:
            self.cfg = build_agent_config()
        except Exception as e:  # noqa: BLE001 — any config-load failure must be wrapped into one RuntimeError with context
            config_dir = resolve_config_dir()
            raise RuntimeError(
                f"Failed to load agent config ({config_dir}): {e.__class__.__name__}: {e}"
            )
        self.session = AgentSession()

        # Wired by Orchestrator.__init__() to its DiagnosticStore instance.
        # None until an Orchestrator is constructed with this context.
        self.diagnostics: DiagnosticStore | None = None
        # Set to AppServices by factory.build_agent_context() before first use.
        # Initialized by factory.build_agent_context() before any component
        # that depends on services is used. Never mutated after assignment.
        self.services: AppServices | None = None

    @property
    def services_required(self) -> AppServices:
        """Return services, raising RuntimeError when not yet initialized.

        Precondition: build_agent_context() must complete before accessing
        any service-dependent functionality. This includes tool execution,
        LLM calls, history management, audit logging, and MCP operations.
        All callers across the codebase (100+ references) depend on this
        invariant holding.
        """
        if self.services is None:
            raise RuntimeError(
                "AgentContext.services not initialized — call build_agent_context() first"
            )
        return self.services
