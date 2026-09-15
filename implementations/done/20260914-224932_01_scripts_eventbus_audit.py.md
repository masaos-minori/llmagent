# Implementation Procedure: Extend AuditRecord TypedDict to include request_id; extend _build_audit_record() to accept request_id parameter

## Goal

Update `scripts/eventbus/audit.py` to extend the `AuditRecord` TypedDict to include `request_id` as a required field, and update `_build_audit_record()` to accept `request_id` as a parameter.

## Scope

- Add `request_id` field to `AuditRecord` TypedDict.
- Add `request_id` parameter to `_build_audit_record()`.
- Include `request_id` in the audit record dict.

## Assumptions

- A: The existing `scripts/eventbus/audit.py` module provides the infrastructure for structured audit logging — confirmed by `audit.py:45-145`.
- B: The `log_auth_failure()` and `log_privileged_action()` functions already exist with the correct signature — confirmed by `audit.py:94-145`.
- C: The `_build_audit_record()` function accepts `consumer_id`, `route`, `target`, `outcome`, `error_type`, and optional `detail` — confirmed by `audit.py:59-91`.
- D: The `X-Request-Id` header is already injected by the auth middleware — confirmed by `auth.py:276-281`.
- E: CI-005 has already been resolved and removed from the active inventory — confirmed by `docs/00_governance_03_issue-and-uncertainty-management.md:313-315`.

## Design decisions

- **Additive change**: Only add `request_id` field to the TypedDict; do not remove or modify existing fields.
- **Required field**: `request_id` is always present in new records; existing consumers that don't use the TypedDict directly are unaffected.
- **Fail-closed**: Reject requests where identity resolution fails or authorization context is missing.
- **Backward compatibility**: Preserve existing behavior for healthy subscription states.

## Alternatives considered

- **Keep single-token design**: Continue using only `auth_token` and per-role tokens. This was rejected because it doesn't provide the granularity needed for REQ-007—REQ-009.
- **Separate authorization config file**: Have a separate YAML/TOML file for authorization rules. This adds complexity without security benefit.

## Compatibility considerations

- The `/subscribe` endpoint's query parameters remain unchanged.
- The SSE response format remains unchanged.
- Backward compatibility for `auth_token` must be explicitly tested.

## Security considerations

- Raw token values must never be logged — use `token_fingerprint` instead.
- All unauthorized responses must use HTTP 401 or HTTP 403.

## Rollback considerations

- Revert requires restoring original AuditRecord TypedDict definition.
- The revert is mechanical — no semantic changes beyond restoring original data structures.

## Implementation

### Target file

`scripts/eventbus/audit.py`

### Procedure

#### Step 1: Extend AuditRecord TypedDict to include request_id (REQ-003)

Replace the current `AuditRecord` TypedDict definition (lines 45-56):

Current code:
```python
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
```

New code:
```python
class AuditRecord(TypedDict):
    """Structured payload for one EventBus audit record."""

    event: str
    source: str
    ts: float
    consumer_id: str
    request_id: str  # NEW: request identity for correlation
    route: str
    target: str
    outcome: str
    error_type: str
    detail: NotRequired[str]
```

Key changes:
- Added `request_id: str` field after `consumer_id`.

#### Step 2: Extend _build_audit_record() to accept request_id parameter (REQ-003)

Replace the current `_build_audit_record()` function (lines 59-91):

Current code:
```python
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
```

New code:
```python
def _build_audit_record(
    event: str,
    consumer_id: str,
    request_id: str,  # NEW: required parameter
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
        error_type: Failure-mode identifier (see module docstring for vocabularies).
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
```

Key changes:
- Added `request_id: str` parameter after `consumer_id`.
- Added `"request_id": request_id` to the record dict.

### Details

- REQ-003: `request_id` added to AuditRecord TypedDict and _build_audit_record().

## Compatibility considerations

- The `/subscribe` endpoint's query parameters remain unchanged.
- The SSE response format remains unchanged.
- Backward compatibility for `auth_token` must be explicitly tested.

## Security considerations

- Raw token values must never be logged — use `token_fingerprint` instead.
- All unauthorized responses must use HTTP 401 or HTTP 403.

## Rollback considerations

- Revert requires restoring original AuditRecord TypedDict definition.
- The revert is mechanical — no semantic changes beyond restoring original data structures.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/eventbus/audit.py | Unit: request_id field inclusion | uv run pytest tests/eventbus/test_eventbus_auth.py -v | Audit record field test passes |
| scripts/eventbus/audit.py | Static analysis: no credential exposure in logs | uv run bandit -r scripts/eventbus/ -c pyproject.toml | No high/medium findings |
| scripts/eventbus/audit.py | Type checking | uv run mypy scripts/eventbus/audit.py | No new type errors |

## Completion criteria

- [ ] `request_id` field added to AuditRecord TypedDict.
- [ ] `request_id` parameter added to _build_audit_record().
- [ ] `request_id` included in the audit record dict.
- [ ] All existing tests pass without modification.
- [ ] No new static analysis or type-checking errors are introduced.

## Out of scope

- Changes to the `/subscribe` endpoint's query parameters or HTTP response format.
- Changes to the `broker.py` subscriber lifecycle or disconnect mechanism.
- Changes to the `db.py` consumer offset storage logic.
- Changes to the `config.py` replay_batch_size parameter.
- Documentation updates (handled separately per REQ-010).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extend AuditRecord TypedDict to include request_id | Completed | — | — | |
| 2 | Extend _build_audit_record() to accept request_id parameter | Completed | — | — | |

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
- **Requirement ID**: REQ-003
- **Source issue**: issues/20260914-102405_eventbus05_structured-auth-audit-logging.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-173340_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-224932
- **Related target files**: scripts/eventbus/audit.py
