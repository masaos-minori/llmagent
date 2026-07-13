#!/usr/bin/env python3
"""rag/models_audit.py

Audit DTOs for tool execution and approval workflows.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AuditLogRecord:
    tool_name: str
    args_masked: str
    result_summary: str
    is_error: bool
    session_id: int | None


@dataclass(frozen=True)
class ApprovalDecision:
    approved: bool
    reason: str
    risk_level: str
