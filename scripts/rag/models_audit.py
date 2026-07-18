#!/usr/bin/env python3
"""rag/models_audit.py

Audit DTOs for tool execution and approval workflows.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AuditLogRecord:
    """Immutable audit log entry capturing tool execution details."""

    tool_name: str
    args_masked: str
    result_summary: str
    is_error: bool
    session_id: int | None


@dataclass(frozen=True)
class ApprovalDecision:
    """Immutable record of an approval decision with its rationale."""

    approved: bool
    reason: str
    risk_level: str
