"""scripts/agent/services/models.py

Immutable DTO models for the agent/services subsystem.

Imports only from agent.services.enums to avoid circular dependencies.
db-layer DTOs (WalCheckpointCounts, PurgeCounts) are defined in
db.models and re-exported here for agent-layer callers.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from db.models import (
    ConsistencyFinding,
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
    """Result of probing a single MCP server's health status.

    Fields:
        key: Server identifier/key
        transport: Transport type string
        startup_mode: Startup mode string
        auth: Whether authentication is enabled
        tier: Tool safety tier classification
        role: Server role string
        availability: Availability status enum
        health: Health state string
        endpoint: Resolved endpoint string
        sandbox_backend: Sandbox backend identifier
        managed: Whether the server is managed
        pid: Process ID of the server
        pgid: Process group ID of the server
        running: Whether the server process is currently running
        lifecycle_state: Current lifecycle state string
        last_exit_code: Exit code of the last server process run
        last_shutdown_result: Result of the last shutdown operation
        restart_recommended: Whether a restart is recommended
        operator_action_required: Whether manual intervention is needed
        health_reason: Reason for current health state
        stderr_log: Stderr log content from the server process
        reachable: Whether the HTTP endpoint was reachable
        body: Raw /health response body (dict or empty dict on failure)
        self_reported_status: Status value reported by the /health response
        dependency_summary: List of failed dependency descriptions
        details_summary: List of detail entry descriptions
        parse_failure_reason: Reason why the /health body could not be parsed
        static_visibility: Whether the server's tools are statically visible to the
            LLM (config-derived; False when startup_mode=none)
    """

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
    reachable: bool = True
    body: dict[str, object] = field(default_factory=dict)
    self_reported_status: str = ""
    dependency_summary: list[str] = field(default_factory=list)
    details_summary: list[str] = field(default_factory=list)
    parse_failure_reason: str | None = None
    static_visibility: bool = True


@dataclass(frozen=True)
class SessionRestoreResult:
    """Result of restoring a session from the database.

    ``fetched`` rows were read from the DB, ``synthesized`` tool rows were added to
    pair interrupted tool calls, ``dropped`` rows failed validation, and ``restored``
    is the length of the rebuilt in-memory history. ``n_messages`` mirrors
    ``fetched``.
    """

    session_id: int
    n_messages: int
    fetched: int = 0
    synthesized: int = 0
    dropped: int = 0
    restored: int = 0


@dataclass(frozen=True)
class DeletedRow:
    """A single deleted message row's identity, returned by the DB-side undo."""

    message_id: int
    role: str
    content: str | None
    tool_call_id: str | None


@dataclass(frozen=True)
class UndoResult:
    """Result of undoing a conversation action.

    `block_reason` is set when the undo was refused because the last turn is at or
    before the compression boundary; otherwise it is `None`.

    `deleted_rows` carries the exact rows the DB deleted (ascending `message_id`);
    the memory side trims to this set to converge memory/DB to parity.
    """

    n_removed: int
    block_reason: str | None = None
    deleted_rows: list[DeletedRow] = field(default_factory=list)


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
    """Result of a database checkpoint operation.

    `verified` is the postcondition result, so a caller cannot report success without
    having measured it (REQ-004). `interrupted` records a run stopped by the job's
    cancellation event, which is never a success.

    `journal_mode` and `wal_size_bytes` are the values measured after the checkpoint,
    not the values the run itself reported.
    """

    mode: str
    pages_written: int
    verified: bool = False
    interrupted: bool = False
    journal_mode: str = ""
    wal_size_bytes: int = 0


@dataclass(frozen=True)
class DbVacuumResult:
    """Result of a vacuum run; the page counts are measured by the postcondition.

    `pages_reclaimed` is the delta between the page count measured before the run and the
    page count measured after it; `verified` is true only when the postcondition showed
    no pages left to reclaim.
    """

    mode: str
    verified: bool = False
    interrupted: bool = False
    page_count_before: int = 0
    page_count_after: int = 0
    pages_reclaimed: int = 0


@dataclass(frozen=True)
class DbPurgeResult:
    """Result of purging old sessions from the database.

    `rows_before` and `rows_after` are the row counts read before and after the delete,
    so `verified` means the re-count agreed with the rows the run reported as removed.
    """

    sessions_removed: int
    kept_active_session: int | None = None  # id exempted from retention, None otherwise
    verified: bool = False
    interrupted: bool = False
    rows_before: int = 0
    rows_after: int = 0


@dataclass(frozen=True)
class DbRecoverResult:
    """Result of a database recovery attempt.

    `post_check` is the integrity result measured after the run; `verified` is true only
    when that re-check passed, so a recovery cannot report success from the pre-run check.
    """

    integrity_ok: bool
    recovered: bool
    detail: str
    logical_ok: bool | None = None
    verified: bool = False
    interrupted: bool = False
    post_check: str = ""


@dataclass(frozen=True)
class RagConsistencyResult:
    """RAG consistency check result with issues, detailed report, and severity.

    `findings` carries the structured per-finding severity/repair actions;
    `fatal_count`/`degraded_count` summarize them so callers can route by severity
    without text-parsing the issue strings.
    """

    is_consistent: bool
    issues: list[str]
    report: RagConsistencyReport
    findings: tuple[ConsistencyFinding, ...] = ()
    fatal_count: int = 0
    degraded_count: int = 0


@dataclass(frozen=True)
class RagFtsRebuildResult:
    """Result of an FTS index rebuild, with the counts the postcondition measured.

    `chunks` and `fts_rows` are read after the insert and the commit, so `verified` means
    the index matches the chunk table, not that the insert ran. A run stopped by the job's
    cancellation event reports the state it was in, never a count it did not measure (REQ-004).
    """

    rows_inserted: int = 0
    chunks: int = 0
    fts_rows: int = 0
    verified: bool = False
    interrupted: bool = False


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
    """One row from session.list_sessions(): session_id, title, created_at, is_current, message_count."""

    session_id: int
    title: str | None
    created_at: str
    is_current: bool
    message_count: int


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
