"""scripts/eventbus/audit.py

Structured audit logging helper for EventBus authorization failures and privileged actions.

Mirrors scripts/mcp_servers/audit.py::AuditRecord's structured-fields style,
reimplemented locally per the eventbus-is-isolated import-linter contract.

Precedent: scripts/mcp_servers/audit.py::AuditRecord

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

logger = logging.getLogger(__name__)


class AuditRecord(TypedDict):
    """Structured payload for one EventBus audit record."""

    event: str
    source: str
    ts: float
    consumer_id: str
    route: str
    target: str
    outcome: str
    error_type: str
    detail: NotRequired[str]

def _build_audit_record(
    event: str,
    consumer_id: str,
    route: str,
    target: str,
    outcome: str,
    error_type: str = "",
    detail: str = "",
) -> AuditRecord:
    """Build the structured record for one EventBus audit event.

    Args:
        event: Event type ("auth_failure" or "privileged_action").
        consumer_id: Caller's consumer identity (if available).
        route: Route being accessed.
        target: Resource identifier (event_id, topic, etc.).
        outcome: One of "rejected", "allowed".
        error_type: Failure-mode identifier (see module docstring for vocabularies).
        detail: Optional key=value pairs (omit when empty).
    """
    record: AuditRecord = {
        "event": event,
        "source": "eventbus",
        "ts": time.time(),
        "consumer_id": consumer_id or "-",
        "route": route,
        "target": target,
        "outcome": outcome,
        "error_type": error_type,
    }
    if detail:
        record["detail"] = detail
    return record

def log_auth_failure(
    consumer_id: str,
    route: str,
    target: str,
    error_type: str = "authorization_failed",
    detail: str = "",
) -> None:
    """Emit one JSON-lines audit record for an authorization failure.

    Args:
        consumer_id: Caller's consumer identity (if available).
        route: Route being accessed.
        target: Resource identifier (event_id, topic, etc.).
        error_type: Failure-mode identifier.
        detail: Optional key=value pairs (omit when empty).
    """
    record = _build_audit_record(
        event="auth_failure",
        consumer_id=consumer_id,
        route=route,
        target=target,
        outcome="rejected",
        error_type=error_type,
        detail=detail,
    )
    logger.warning(orjson.dumps(record, option=orjson.OPT_SORT_KEYS).decode())

def log_privileged_action(
    consumer_id: str,
    route: str,
    target: str,
    detail: str = "",
) -> None:
    """Emit one JSON-lines audit record for a privileged action.

    Args:
        consumer_id: Caller's consumer identity (if available).
        route: Route being accessed.
        target: Resource identifier (event_id, topic, etc.).
        detail: Optional key=value pairs (omit when empty).
    """
    record = _build_audit_record(
        event="privileged_action",
        consumer_id=consumer_id,
        route=route,
        target=target,
        outcome="allowed",
        error_type="",
        detail=detail,
    )
    logger.info(orjson.dumps(record, option=orjson.OPT_SORT_KEYS).decode())
