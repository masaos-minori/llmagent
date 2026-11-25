"""scripts/agent/services/exceptions.py

Domain exceptions for the agent/services subsystem.
"""

from __future__ import annotations

from shared.config_field_types import ConfigFieldTypeError


class McpProbeError(RuntimeError):
    """Raised when an MCP server probe encounters an unrecoverable error."""


class SessionTitleGenerationError(RuntimeError):
    """Raised when LLM-based session title generation fails."""


class ConfigReloadError(ConfigFieldTypeError):
    """Base for configuration reload failures.

    Attributes:
        field_path: Config key the failure names, or an empty string when the
            failure belongs to a commit or rollback step rather than one field.
        rule: Name of the violated rule, or an empty string for a step failure.
        stage: `ReloadStage` value the transaction reached before raising, or an
            empty string for a failure that never reached a stage.  A validator
            failure raises before any commit, so it carries none; a commit or
            rollback failure names `rolled_back` or `degraded` (REQ-005).

    Subclasses `ConfigFieldTypeError` so one `except ConfigFieldTypeError` at the
    command boundary also catches errors raised directly by the shared primitives
    (REQ-011).
    """

    def __init__(
        self,
        message: str,
        *,
        field_path: str = "",
        rule: str = "",
        stage: str = "",
    ) -> None:
        super().__init__(field_path, rule, message)
        self.stage = stage


class ConfigReloadValidationError(ConfigReloadError):
    """Raised when a config reload request or candidate value fails a declared rule.

    Stays a `ValueError` subclass through `ConfigFieldTypeError`, so callers that
    catch `ValueError` keep working.
    """


class ConfigReloadCommitError(ConfigReloadError):
    """Raised when a commit step failed after the transaction undid the applied steps."""


class ConfigReloadRollbackError(ConfigReloadError):
    """Raised when a rollback step failed, leaving live state inconsistent.

    Attributes:
        service: Live service left inconsistent by the failed restore, which is
            what the `degraded` stage reports.
    """

    def __init__(
        self,
        message: str,
        *,
        field_path: str = "",
        rule: str = "",
        service: str = "",
        stage: str = "",
    ) -> None:
        super().__init__(message, field_path=field_path, rule=rule, stage=stage)
        self.service = service


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


class SessionNoMessagesError(RuntimeError):
    """Raised when a requested session exists but has no messages."""


class NothingToUndoError(RuntimeError):
    """Raised when undo is requested but no user message is in history."""
