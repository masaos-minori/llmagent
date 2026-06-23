"""agent/services/models.py
Immutable DTO models for the agent/services subsystem.

Imports only from agent.services.enums to avoid circular dependencies.
db-layer DTOs (WalCheckpointCounts, PurgeCounts, ToolResultRow) are defined in
db.models and re-exported here for agent-layer callers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from db.models import PurgeCounts, ToolResultRow, WalCheckpointCounts

from agent.services.enums import (
    ConversationActionType,
    ExportFormat,
    IngestStage,
    McpAvailability,
    McpTier,
)


@dataclass(frozen=True)
class IngestOutcome:
    stage: IngestStage
    n_chunks: int = 0
    messages: tuple[str, ...] = ()


@dataclass(frozen=True)
class SessionTitleResult:
    title: str


@dataclass(frozen=True)
class McpProbeResult:
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


@dataclass(frozen=True)
class SessionRestoreResult:
    session_id: int
    n_messages: int


@dataclass(frozen=True)
class UndoResult:
    n_removed: int


@dataclass(frozen=True)
class ConversationActionResult:
    action: ConversationActionType
    message: str


@dataclass(frozen=True)
class ContextStateView:
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
    docs: int
    chunks: int
    sessions: int
    messages: int


@dataclass(frozen=True)
class DbHealth:
    integrity_ok: bool
    wal_pages: int
    size_bytes: int


@dataclass(frozen=True)
class DbCheckpointResult:
    mode: str
    pages_written: int


@dataclass(frozen=True)
class DbPurgeResult:
    sessions_removed: int


@dataclass(frozen=True)
class DbRecoverResult:
    integrity_ok: bool
    recovered: bool
    detail: str


@dataclass(frozen=True)
class RagConsistencyResult:
    is_consistent: bool
    issues: list[str]
    report: Any  # db.maintenance.RagConsistencyReport


@dataclass(frozen=True)
class ExportResult:
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
    "ToolResultRow",
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

    Character counts (*system*, *history*, *tool_results*) are always present.
    Token estimates are ``None`` when the source is exact (LLM usage or
    /tokenize endpoint); they are populated only when a category-aware fallback
    estimate is used.
    """

    system: int
    history: int
    tool_results: int
    token_system: int | None = None
    token_history: int | None = None
    token_tool_results: int | None = None
