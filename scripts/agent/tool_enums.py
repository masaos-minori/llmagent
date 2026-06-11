"""agent/tool_enums.py
Enum types for the tool execution subsystem.
"""

from __future__ import annotations

from enum import StrEnum


class RiskLevel(StrEnum):
    NONE = "none"
    MEDIUM = "medium"
    HIGH = "high"


class OperationType(StrEnum):
    WRITE = "write"
    DELETE = "delete"
    EXECUTE = "execute"
    API_WRITE = "api_write"
    READ = "read"


class ApprovalDecisionType(StrEnum):
    AUTO = "auto"
    APPROVED = "approved"
    DENIED = "denied"
    DRY_RUN = "dry_run"
    PLAN_BLOCKED = "plan_blocked"


class GuardDecisionType(StrEnum):
    PASS = "pass"
    CYCLE = "cycle"
    DEDUP = "dedup"
    RETRY = "retry"
    ERROR_LIMIT = "error_limit"
