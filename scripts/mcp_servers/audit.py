"""scripts/mcp_servers/audit.py

Structured audit logging helper extracted from mcp/server.py.

Emits one JSON-lines record per MCP tool execution event.

Error Type Vocabulary
---------------------
The ``error_type`` field carries a short identifier for the failure mode.
Two vocabularies currently exist:

1. ``mdq``: Python exception-class names (e.g., ``"MdqValidationError"``,
   ``"MdqAuthorizationError"``). Source: ``type(exc).__name__``.
2. ``web_search``: lowercase-snake identifiers (e.g., ``"validation_error"``,
   ``"authorization_error"``, ``"timeout"``). Preferred for new code.

Recommendation: Adopt the ``web_search`` style for new MCP servers.
Rationale: more stable across Python versions, more readable in log queries,
and consistent with RFC 7807 Problem Details conventions.

Detail Field Semantics
----------------------
The ``detail`` field (optional, ``NotRequired[str]``) contains machine-parseable
key=value pairs when present. Never emit an empty string — omit the field entirely
when there is nothing to report. Examples::

    detail="duration_ms=42 result_count=5"
    detail="latency_ms=120 query_preview='search term'"
"""

from __future__ import annotations

import logging
import time
from typing import NotRequired, TypedDict

import orjson
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
    pre_condition: NotRequired[dict[str, object]]
    post_condition: NotRequired[dict[str, object]]


def _build_audit_record(
    session_id: str,
    request_id: str,
    action: str,
    target: str,
    outcome: str,
    detail: str = "",
    server_key: str = "",
    error_type: str = "",
    pre_condition: dict[str, object] | None = None,
    post_condition: dict[str, object] | None = None,
) -> AuditRecord:
    """Build the structured record for one MCP tool execution audit event.

    Args:
        session_id: Session identifier from the request context.
        request_id: Per-call request ID from the request context.
        action: Tool name or action being audited.
        target: Canonical repository identity or resource identifier.
        outcome: One of ``"ok"``, ``"error"``, ``"rejected"``.
        detail: Optional key=value pairs (omit when empty).
        server_key: Identifying key for the MCP server emitting this record.
        error_type: Failure-mode identifier (see module docstring for vocabularies).
        pre_condition: Pre-condition state snapshot (optional).
        post_condition: Post-condition state snapshot (optional).
    """
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
    if pre_condition is not None:
        record["pre_condition"] = {
            k: v
            for k, v in pre_condition.items()
            if isinstance(v, (str, int, float, bool, type(None)))
        }
    if post_condition is not None:
        record["post_condition"] = {
            k: v
            for k, v in post_condition.items()
            if isinstance(v, (str, int, float, bool, type(None)))
        }
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
    pre_condition: dict[str, object] | None = None,
    post_condition: dict[str, object] | None = None,
) -> None:
    """Emit one JSON-lines audit record for an MCP tool execution.

    Args:
        server_logger: Logger instance for the calling MCP server.
        session_id: Session identifier from the request context.
        request_id: Per-call request ID from the request context.
        action: Tool name or action being audited.
        target: Canonical repository identity or resource identifier.
        outcome: One of ``"ok"``, ``"error"``, ``"rejected"``.
        detail: Optional key=value pairs (omit when empty).
        server_key: Identifying key for the MCP server emitting this record.
        error_type: Failure-mode identifier (see module docstring for vocabularies).
        pre_condition: Pre-condition state snapshot (optional).
        post_condition: Post-condition state snapshot (optional).
    """
    record = _build_audit_record(
        session_id=session_id,
        request_id=request_id,
        action=action,
        target=target,
        outcome=outcome,
        detail=detail,
        server_key=server_key,
        error_type=error_type,
        pre_condition=pre_condition,
        post_condition=post_condition,
    )
    server_logger.info(orjson.dumps(record, option=orjson.OPT_SORT_KEYS).decode())
