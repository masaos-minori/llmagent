"""agent/tool_enums.py

Enum types for the tool execution subsystem.
"""

from __future__ import annotations

from enum import StrEnum


class RiskLevel(StrEnum):
    """Risk level classification for tool operations."""

    NONE = "none"
    MEDIUM = "medium"
    HIGH = "high"


class OperationType(StrEnum):
    """Categorization of tool operation kinds."""

    WRITE = "write"
    DELETE = "delete"
    EXECUTE = "execute"
    API_WRITE = "api_write"
    READ = "read"
    UNKNOWN = "unknown"


class ApprovalDecisionType(StrEnum):
    """Possible outcomes of an approval gate evaluation."""

    AUTO = "auto"
    APPROVED = "approved"
    DENIED = "denied"
    DRY_RUN = "dry_run"
    PLAN_BLOCKED = "plan_blocked"


class GuardDecisionType(StrEnum):
    """Decisions made by the tool guardrail system."""

    PASS = "pass"
    CYCLE = "cycle"
    DEDUP = "dedup"
    RETRY = "retry"
    ERROR_LIMIT = "error_limit"
