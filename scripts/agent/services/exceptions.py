"""agent/services/exceptions.py
Domain exceptions for the agent/services subsystem.
"""

from __future__ import annotations

from agent.services.enums import IngestStage


class IngestStageError(RuntimeError):
    """Raised when an ingest pipeline stage fails."""

    def __init__(self, stage: IngestStage, detail: str) -> None:
        super().__init__(f"[{stage.value}] {detail}")
        self.stage = stage
        self.detail = detail


class McpProbeError(RuntimeError):
    """Raised when an MCP server probe encounters an unrecoverable error."""


class SessionTitleGenerationError(RuntimeError):
    """Raised when LLM-based session title generation fails."""


class ConfigReloadValidationError(ValueError):
    """Raised when a config reload request contains invalid field types."""


class ContextStateBuildError(RuntimeError):
    """Raised when context state cannot be built (e.g. hist_mgr is None)."""


class ExportWriteError(OSError):
    """Raised when writing an export file fails."""


class ConversationStateError(RuntimeError):
    """Raised when a conversation state operation fails (e.g. unknown prompt preset)."""


class DbMaintenanceError(RuntimeError):
    """Raised when a DB maintenance operation fails."""


class SessionNotFoundError(RuntimeError):
    """Raised when a requested session does not exist or has no messages."""


class NothingToUndoError(RuntimeError):
    """Raised when undo is requested but no user message is in history."""
