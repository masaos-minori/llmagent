"""scripts/eventbus/audit.py

Structured audit logging helper for EventBus authorization failures,
authorization changes, and privileged actions.

Error Type Vocabulary
---------------------
The ``error_type`` field carries a lowercase-snake identifier for the failure
mode, drawn from the module constants:

1. ``AUTHENTICATION_FAILED``: the caller's credential check failed.
2. ``AUTHORIZATION_FAILED``: an authenticated caller lacks the required role.
3. ``CONSUMER_IDENTITY_REJECTED``: the consumer identity does not match the
   credential's grants.
4. ``TOPIC_AUTHORIZATION_REJECTED``: the caller's consumer grants do not
   cover the requested topic.

Successful privileged-action and authorization-change records carry
``error_type=""``.

Detail Field Semantics
----------------------
The ``detail`` field (optional, ``NotRequired[str]``) contains machine-parseable
key=value pairs when present. Never emit an empty string — omit the field entirely
when there is nothing to report. Example::

    detail="previous_generation=3 new_generation=4"
"""

from __future__ import annotations

import logging
import time
from typing import NotRequired, TypedDict

import orjson

logger = logging.getLogger(__name__)

AUTHENTICATION_FAILED = "authentication_failed"
AUTHORIZATION_FAILED = "authorization_failed"
CONSUMER_IDENTITY_REJECTED = "consumer_identity_rejected"
TOPIC_AUTHORIZATION_REJECTED = "topic_authorization_rejected"


class AuditRecord(TypedDict):
    """Structured payload for one EventBus audit record."""

    event: str
    source: str
    ts: float
    consumer_id: str
    request_id: str
    route: str
    target: str
    outcome: str
    error_type: str
    detail: NotRequired[str]
    actor: NotRequired[str]


class AuthzChangeRecord(AuditRecord):
    """Audit record for an authorization change; both generations are required."""

    previous_generation: int
    new_generation: int


def _build_audit_record(
    event: str,
    consumer_id: str,
    request_id: str,
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
        request_id: Request identity for correlation.
        route: Route being accessed.
        target: Resource identifier (event_id, topic, etc.).
        outcome: One of "rejected", "allowed".
        error_type: Failure-mode identifier (see the module constants).
        detail: Optional key=value pairs (omit when empty).
    """
    record: AuditRecord = {
        "event": event,
        "source": "eventbus",
        "ts": time.time(),
        "consumer_id": consumer_id or "-",
        "request_id": request_id,
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
    request_id: str,
    route: str,
    target: str,
    error_type: str = AUTHORIZATION_FAILED,
    detail: str = "",
) -> None:
    """Emit one JSON-lines audit record for an authorization failure.

    Args:
        consumer_id: Caller's consumer identity (if available).
        request_id: Request identity for correlation.
        route: Route being accessed.
        target: Resource identifier (event_id, topic, etc.).
        error_type: Failure-mode identifier.
        detail: Optional key=value pairs (omit when empty).
    """
    record = _build_audit_record(
        event="auth_failure",
        consumer_id=consumer_id,
        request_id=request_id,
        route=route,
        target=target,
        outcome="rejected",
        error_type=error_type,
        detail=detail,
    )
    logger.warning(orjson.dumps(record, option=orjson.OPT_SORT_KEYS).decode())


def log_privileged_action(
    consumer_id: str,
    request_id: str,
    route: str,
    target: str,
    detail: str = "",
    actor: str = "",
) -> None:
    """Emit one JSON-lines audit record for a privileged action.

    Args:
        consumer_id: Caller's consumer identity (if available).
        request_id: Request identity for correlation.
        route: Route being accessed.
        target: Resource identifier (event_id, topic, etc.).
        detail: Optional key=value pairs (omit when empty).
        actor: Non-secret token fingerprint of the acting principal.
    """
    record = _build_audit_record(
        event="privileged_action",
        consumer_id=consumer_id,
        request_id=request_id,
        route=route,
        target=target,
        outcome="allowed",
        error_type="",
        detail=detail,
    )
    if actor:
        record["actor"] = actor
    logger.info(orjson.dumps(record, option=orjson.OPT_SORT_KEYS).decode())


def log_authorization_change(
    consumer_id: str,
    request_id: str,
    route: str,
    target: str,
    detail: str = "",
    actor: str = "",
    *,
    previous_generation: int,
    new_generation: int,
) -> None:
    """Emit one JSON-lines audit record for an authorization change.

    The record keeps the "privileged_action" event type and every audit key,
    plus the two required generation fields.

    Args:
        consumer_id: Caller's consumer identity (if available).
        request_id: Request identity for correlation.
        route: Route being accessed.
        target: Resource identifier (topic, etc.).
        detail: key=value pairs (omit when empty).
        actor: Non-secret token fingerprint of the acting principal.
        previous_generation: Generation number in force before this change.
        new_generation: Generation number published by this change.
    """
    base = _build_audit_record(
        event="privileged_action",
        consumer_id=consumer_id,
        request_id=request_id,
        route=route,
        target=target,
        outcome="allowed",
        error_type="",
        detail=detail,
    )
    record: AuthzChangeRecord = {
        **base,
        "previous_generation": previous_generation,
        "new_generation": new_generation,
    }
    if actor:
        record["actor"] = actor
    logger.info(orjson.dumps(record, option=orjson.OPT_SORT_KEYS).decode())
