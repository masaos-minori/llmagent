"""scripts/mcp_servers/audit.py

Structured audit logging helper extracted from mcp/server.py.

Emits one JSON-lines record per MCP tool execution event.
"""

from __future__ import annotations

import json
import logging
import time
from typing import NotRequired, TypedDict

from shared.logger import Logger as _SharedLogger


class AuditRecord(TypedDict):
    """Structured payload for one MCP tool execution audit record."""

    event: str
    source: str
    ts: float
    session_id: str
    request_id: str
    tool: str
    target: str
    outcome: str
    server_key: str
    error_type: str
    detail: NotRequired[str]


def _build_audit_record(
    session_id: str,
    request_id: str,
    action: str,
    target: str,
    outcome: str,
    detail: str = "",
    server_key: str = "",
    error_type: str = "",
) -> AuditRecord:
    """Build the structured record for one MCP tool execution audit event."""
    record: AuditRecord = {
        "event": "mcp_tool_exec",
        "source": "mcp_server",
        "ts": time.time(),
        "session_id": session_id or "-",
        "request_id": request_id or "-",
        "tool": action,
        "target": target,
        "outcome": outcome,
        "server_key": server_key,
        "error_type": error_type,
    }
    if detail:
        record["detail"] = detail
    return record


def _audit_log(
    server_logger: logging.Logger | _SharedLogger,
    session_id: str,
    request_id: str,
    action: str,
    target: str,
    outcome: str,
    detail: str = "",
    server_key: str = "",
    error_type: str = "",
) -> None:
    """Emit one JSON-lines audit record for an MCP tool execution."""
    record = _build_audit_record(
        session_id=session_id,
        request_id=request_id,
        action=action,
        target=target,
        outcome=outcome,
        detail=detail,
        server_key=server_key,
        error_type=error_type,
    )
    server_logger.info(json.dumps(record, ensure_ascii=False))
