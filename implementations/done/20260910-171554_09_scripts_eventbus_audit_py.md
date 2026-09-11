## Goal

Create `scripts/eventbus/audit.py`: structured audit-record emission for authorization failures and privileged actions, with no secret/token values recorded.

## Scope

- New module `scripts/eventbus/audit.py` containing:
  - `AuditRecord` TypedDict for structured audit payload
  - `log_auth_failure()` — emit audit record for authorization failures
  - `log_privileged_action()` — emit audit record for privileged actions (DLQ admin, replay)
- No cross-layer imports (`.importlinter` `eventbus-is-isolated` contract forbids importing `shared`/`mcp_servers`).

## Assumptions

- The audit pattern mirrors `scripts/mcp_servers/audit.py::AuditRecord`'s structured-fields style (event/source/ts/session-or-consumer-id/tool-or-route/target), reimplemented locally.
- Audit records should be emitted as JSON-lines via standard Python logging.
- Secret/token values must never be included in any logged field.

## Design decisions

- **Audit record structure**: Mirrors `scripts/mcp_servers/audit.py::AuditRecord` with fields:
  - `event`: `"auth_failure"` or `"privileged_action"`
  - `source`: `"eventbus"`
  - `ts`: timestamp (float)
  - `consumer_id`: caller's consumer identity (if available)
  - `route`: route being accessed
  - `target`: resource identifier (event_id, topic, etc.)
  - `outcome`: `"rejected"` for auth failures, `"allowed"` for privileged actions
  - `error_type`: failure-mode identifier (`"authorization_failed"`, etc.)
- **JSON-lines output**: Emit one JSON record per event via `logging.info()`.
- **No secret logging**: Never include the Authorization header value or token in any logged field.

## Alternatives considered

- Shared audit module: Cannot import from `mcp_servers`/`shared` per isolation contract; reimplemented locally.
- Structured logging with dict: Less portable than JSON-lines; JSON-lines preferred for log aggregation.
- Separate audit table in SQLite: Overkill for authorization events; log-based auditing sufficient.

## Implementation

### Target file

`scripts/eventbus/audit.py`

### Procedure

Create a new module implementing structured audit logging for authorization failures and privileged actions.

### Method

1. Define `AuditRecord` TypedDict mirroring `scripts/mcp_servers/audit.py::AuditRecord`'s structure.
2. Implement `log_auth_failure()` — emit audit record for authorization failures.
3. Implement `log_privileged_action()` — emit audit record for privileged actions.
4. Use `orjson.dumps()` for deterministic JSON serialization (consistent with existing codebase).

### Details

```python
# scripts/eventbus/audit.py

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
```

## Compatibility considerations

- The `AuditRecord` TypedDict structure must remain compatible with log aggregation tools that parse JSON-lines.
- Using `orjson.dumps()` with `OPT_SORT_KEYS` ensures deterministic output for log analysis.

## Security considerations

- **No secret logging**: The Authorization header value and token are never included in any logged field.
- **Consumer identity logging**: Only the consumer identity (not the token) is logged; this is safe because the consumer identity is public information.
- **Warning vs info level**: Auth failures logged at WARNING level; privileged actions logged at INFO level.

## Rollback considerations

- Rolling back this module means removing it and reverting all callers to use unstructured logging.
- The audit record format can evolve independently; backward compatibility is not required for log parsing tools.

## Validation plan

- Unit test: `log_auth_failure()` emits a valid JSON-lines record without secrets.
- Unit test: `log_privileged_action()` emits a valid JSON-lines record.
- Integration test: Verify audit records appear in logs during auth failures and privileged actions.
- Run `uv run pytest tests/eventbus/test_eventbus_auth.py -v`.

## Completion criteria

- [ ] `scripts/eventbus/audit.py` created with `AuditRecord` TypedDict
- [ ] `log_auth_failure()` implemented
- [ ] `log_privileged_action()` implemented
- [ ] No secret/token values in any logged field
- [ ] All audit tests passing
- [ ] No cross-layer imports (verified via `PYTHONPATH=scripts uv run lint-imports`)

## Out of scope

- Log rotation infrastructure.
- Audit record persistence (SQLite, external log aggregation).
- Token rotation infrastructure.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create audit.py with AuditRecord TypedDict | Completed | — | — | |
| 2 | Implement log_auth_failure() | Completed | — | — | |
| 3 | Implement log_privileged_action() | Completed | — | — | |
| 4 | Add or update tests per Validation plan | Completed | — | — | |
| 5 | Run the validation sequence (rules/toolchain.md) | Completed | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability

- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-006
- **Source issue**: issues/20260907-125042_eb_h04_eventbus_authentication_authorization.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260909-101237_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260910-171554
- **Related target files**: scripts/eventbus/audit.py
