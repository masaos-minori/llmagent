"""agent/services/models.py

Immutable DTO models for the agent/services subsystem.

Imports only from agent.services.enums to avoid circular dependencies.
db-layer DTOs (WalCheckpointCounts, PurgeCounts) are defined in
db.models and re-exported here for agent-layer callers.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from db.models import (
    PurgeCounts,
    RagConsistencyReport,
    WalCheckpointCounts,
)

from agent.services.enums import (
    ConversationActionType,
    ExportFormat,
    McpAvailability,
    McpTier,
)


@dataclass(frozen=True)
class ProcessInfoSnapshot:
    """Read-only snapshot of an HTTP MCP subprocess's runtime state."""

    server_key: str
    managed: bool
    pid: int | None
    pgid: int | None
    running: bool
    last_exit_code: int | None
    stderr_log: str


@dataclass(frozen=True)
class SessionTitleResult:
    """Result of generating a session title."""

    title: str


@dataclass(frozen=True)
class McpProbeResult:
    """Result of probing an MCP server's health status."""

    key: str
    transport: str
    startup_mode: str
    auth: bool
    tier: McpTier
    role: str
    availability: McpAvailability
    health: str
    endpoint: str
    sandbox_backend: str = ""
    managed: bool = False
    pid: int | None = None
    pgid: int | None = None
    running: bool | None = None
    lifecycle_state: str = ""
    last_exit_code: int | None = None
    last_shutdown_result: str = ""
    restart_recommended: bool = False
    operator_action_required: bool = False
    health_reason: str = ""
    stderr_log: str = ""


@dataclass(frozen=True)
class SessionRestoreResult:
    """Result of restoring a session from the database."""

    session_id: int
    n_messages: int


@dataclass(frozen=True)
class UndoResult:
    """Result of undoing a conversation action."""

    n_removed: int
    warning: str | None = None


@dataclass(frozen=True)
class ConversationActionResult:
    """Result of executing a conversation action."""

    action: ConversationActionType
    message: str


@dataclass(frozen=True)
class ContextStateView:
    """Current context state view including character/token budgets and compression info."""

    total_chars: int
    compress_limit: int
    n_msgs: int
    sys_preview: str
    compress_count: int
    token_is_exact: bool
    token_estimate: int | None
    token_limit: int
    tokenize_configured: bool
    mem_status: str
    git_branch: str | None
    git_commit: str | None
    breakdown: ContextBudget
    fallback_truncate_count: int = 0
    partial_completions: int = 0
    workflow_mode: str = ""
    approval_pending: bool = False


@dataclass(frozen=True)
class DbStats:
    """Database statistics including document, chunk, session, and message counts."""

    docs: int
    chunks: int
    sessions: int
    messages: int


@dataclass(frozen=True)
class DbHealth:
    """Database health check result including integrity, WAL pages, and size."""

    integrity_ok: bool
    wal_pages: int
    size_bytes: int


@dataclass(frozen=True)
class DbCheckpointResult:
    """Result of a database checkpoint operation."""

    mode: str
    pages_written: int


@dataclass(frozen=True)
class DbPurgeResult:
    """Result of purging old sessions from the database."""

    sessions_removed: int


@dataclass(frozen=True)
class DbRecoverResult:
    """Result of a database recovery attempt."""

    integrity_ok: bool
    recovered: bool
    detail: str


@dataclass(frozen=True)
class RagConsistencyResult:
    """RAG consistency check result with issues and detailed report."""

    is_consistent: bool
    issues: list[str]
    report: RagConsistencyReport


@dataclass(frozen=True)
class ExportResult:
    """Result of exporting session data in a specific format."""

    n_messages: int
    content: str
    format: ExportFormat


@dataclass
class ConfigReloadRequest:
    """Typed request for apply_config. All fields optional; missing fields are skipped."""

    mcp_servers: dict | None = field(default=None)
    approval: dict | None = field(default=None)
    llm: dict | None = field(default=None)
    masked_fields: list[str] | None = field(default=None)
    rag_tool: dict | None = field(default=None)
    sse: dict | None = field(default=None)


# ── Re-exports from db.models (available to agent-layer callers) ──────────────

__all__ = [
    "PurgeCounts",
    "WalCheckpointCounts",
]


# ── Agent-layer-only DTOs ─────────────────────────────────────────────────────


@dataclass(frozen=True)
class SessionRow:
    """One row from the sessions table as returned by session.list_sessions()."""

    session_id: int
    title: str | None
    created_at: str
    is_current: bool


@dataclass(frozen=True)
class ContextBudget:
    """Per-category character and token counts for /context budget breakdown.

    Character counts (*system*, *history*, *tool_messages*) are always present.
    Token estimates are ``None`` when the source is exact (LLM usage or
    /tokenize endpoint); they are populated only when a category-aware fallback
    estimate is used.
    """

    system: int
    history: int
    tool_messages: int
    token_system: int | None = None
    token_history: int | None = None
    token_tool_messages: int | None = None
