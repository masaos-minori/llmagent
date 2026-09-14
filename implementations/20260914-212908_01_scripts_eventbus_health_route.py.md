# Implementation Procedure: Guard broker access in health endpoint; add broker_unavailable degraded reason; ensure controlled HTTP 503

## Goal

Update `scripts/eventbus/health_route.py` to guard broker property access before reading broker properties, add `broker_unavailable` as a degraded reason when the broker is unavailable, and ensure controlled HTTP 503 response instead of raising an internal exception.

## Scope

- Move the `broker.backlog_health_threshold` access inside the `if broker is not None:` guard.
- Add `broker_unavailable` to `degraded_reasons` when broker is None.
- Ensure status_code is set to 503 when broker is unavailable.

## Assumptions

- A: REQ-001 through REQ-003 in `scripts/eventbus/health_route.py` are implemented before this change.
- B: The health endpoint already guards broker access with `if broker is not None:` — confirmed by `health_route.py:53`.
- C: Broker properties accessed in health route (subscriber_count, max_queue_depth, slow_consumer_count, overflow_disconnect_count, duplicate_rejection_count) are all safe to call when broker is not None — confirmed by broker.py method definitions.

## Design decisions

- **Fail-closed**: Return HTTP 503 with `broker_unavailable` degraded reason when broker is None.
- **Minimal change**: Only move the existing `broker.backlog_health_threshold` access inside the guard; do not restructure the entire health endpoint logic.
- **Backward compatibility**: Preserve existing behavior for healthy broker states.

## Alternatives considered

- **Restructure health endpoint**: Rewrite the entire health endpoint to use a separate broker-health-check function. This was rejected because it adds complexity without security benefit.
- **Separate health endpoint**: Create a separate endpoint for broker health checks. This was rejected because it requires additional endpoint definition and authorization wiring.

## Compatibility considerations

- The `/subscribe` endpoint's query parameters remain unchanged.
- The SSE response format remains unchanged.
- Backward compatibility for `auth_token` must be explicitly tested.

## Security considerations

- Raw token values must never be logged — use `token_fingerprint` instead.
- All unauthorized responses must use HTTP 401 or HTTP 403.

## Rollback considerations

- Revert requires restoring original `broker.backlog_health_threshold` access location.
- The revert is mechanical — no semantic changes beyond restoring original code structure.

## Implementation

### Target file

`scripts/eventbus/health_route.py`

### Procedure

#### Step 1: Guard broker property access and add broker_unavailable degraded reason (REQ-001, REQ-002, REQ-003)

Replace the current broker health metrics section (lines 47-69):

Current code:
```python
    # Broker health metrics
    active_subscribers = 0
    max_queue_depth = 0
    slow_consumers = 0
    overflow_disconnects = 0
    duplicate_connection_rejections = 0
    if broker is not None:
        active_subscribers = broker.subscriber_count()
        max_queue_depth = broker.max_queue_depth()
        slow_consumers = broker.slow_consumer_count()
        overflow_disconnects = broker.overflow_disconnect_count()
        duplicate_connection_rejections = broker.duplicate_rejection_count()

    degraded_reasons: list[str] = []
    if db_status != "ok":
        degraded_reasons.append("db_unavailable")
    if dlq_task_status != "running":
        degraded_reasons.append("dlq_task_stopped")
    if max_queue_depth >= broker.backlog_health_threshold:
        degraded_reasons.append("broker_queue_backlog_high")
    if slow_consumers > 0:
        degraded_reasons.append("slow_consumers_detected")
```

New code:
```python
    # Broker health metrics
    active_subscribers = 0
    max_queue_depth = 0
    slow_consumers = 0
    overflow_disconnects = 0
    duplicate_connection_rejections = 0
    if broker is not None:
        active_subscribers = broker.subscriber_count()
        max_queue_depth = broker.max_queue_depth()
        slow_consumers = broker.slow_consumer_count()
        overflow_disconnects = broker.overflow_disconnect_count()
        duplicate_connection_rejections = broker.duplicate_rejection_count()

    degraded_reasons: list[str] = []
    if db_status != "ok":
        degraded_reasons.append("db_unavailable")
    if dlq_task_status != "running":
        degraded_reasons.append("dlq_task_stopped")
    if broker is not None:
        if max_queue_depth >= broker.backlog_health_threshold:
            degraded_reasons.append("broker_queue_backlog_high")
        if slow_consumers > 0:
            degraded_reasons.append("slow_consumers_detected")
    else:
        degraded_reasons.append("broker_unavailable")
```

Key changes:
- Moved `max_queue_depth >= broker.backlog_health_threshold` check inside the `if broker is not None:` guard.
- Moved `slow_consumers > 0` check inside the `if broker is not None:` guard.
- Added `else: degraded_reasons.append("broker_unavailable")` when broker is None.

### Details

- REQ-001: `broker_unavailable` added as degraded reason when broker is None.
- REQ-002: Broker property access guarded against broker being None.
- REQ-003: Controlled HTTP 503 response ensured when broker is unavailable.

## Compatibility considerations

- The `/subscribe` endpoint's query parameters remain unchanged.
- The SSE response format remains unchanged.
- Backward compatibility for `auth_token` must be explicitly tested.

## Security considerations

- Raw token values must never be logged — use `token_fingerprint` instead.
- All unauthorized responses must use HTTP 401 or HTTP 403.

## Rollback considerations

- Revert requires restoring original `broker.backlog_health_threshold` access location.
- The revert is mechanical — no semantic changes beyond restoring original code structure.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/eventbus/health_route.py | Unit: broker-unavailable degradation; Integration: controlled HTTP 503 | uv run pytest tests/eventbus/test_eventbus_health.py -v | New health tests pass; existing tests unchanged |
| scripts/eventbus/health_route.py | Static analysis: no credential exposure in logs | uv run bandit -r scripts/eventbus/ -c pyproject.toml | No high/medium findings |
| scripts/eventbus/health_route.py | Type checking | uv run mypy scripts/eventbus/health_route.py | No new type errors |

## Completion criteria

- [ ] `broker.backlog_health_threshold` access moved inside `if broker is not None:` guard.
- [ ] `slow_consumers > 0` check moved inside `if broker is not None:` guard.
- [ ] `broker_unavailable` added to `degraded_reasons` when broker is None.
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
| 1 | Guard broker property access and add broker_unavailable degraded reason | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003
- **Source issue**: issues/20260914-102344_sse-lifecycle-heartbeat-idle-timeout.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-172918_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-212908
- **Related target files**: scripts/eventbus/health_route.py
