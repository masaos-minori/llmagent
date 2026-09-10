## Goal

Surface the new overflow-disconnect/duplicate-rejection counters (`REQ-005`) in `scripts/eventbus/health_route.py`'s JSON health response, following the existing `slow_consumers` field's pattern.

## Scope

- Add `overflow_disconnects` and `duplicate_rejections` fields to the health response JSON.
- Follow the existing pattern: call `broker.overflow_disconnect_count()` and `broker.duplicate_rejection_count()` when broker is not None.

## Assumptions

- The `broker` object has the new getter methods `overflow_disconnect_count()` and `duplicate_rejection_count()` (added in the related procedure document).
- The existing `slow_consumers` field pattern is sufficient — no new branching logic needed.

## Design decisions

- **Plain getter calls**: Follow the existing pattern of calling `broker.slow_consumer_count()` directly — no new `if` branches.
- **Zero default**: When broker is None or the counters are zero, the fields are omitted from the response (same as existing behavior for `active_subscribers`, `max_queue_depth`, `slow_consumers`).

## Alternatives considered

- **Add degraded_reasons entries**: Would require adding new conditions to the `degraded_reasons` list. Rejected because the Plan doesn't specify that these should trigger degradation — only that they should be observable.

## Implementation

### Target file

`scripts/eventbus/health_route.py`

### Procedure

1. Add `overflow_disconnects` and `duplicate_rejections` variables after the existing `slow_consumers` variable.
2. Add the new fields to the JSON response.

### Method

#### Step 1: Add counter variables

Change lines 37-44:
```python
    # Broker health metrics
    active_subscribers = 0
    max_queue_depth = 0
    slow_consumers = 0
    if broker is not None:
        active_subscribers = broker.subscriber_count()
        max_queue_depth = broker.max_queue_depth()
        slow_consumers = broker.slow_consumer_count()
```

to:
```python
    # Broker health metrics
    active_subscribers = 0
    max_queue_depth = 0
    slow_consumers = 0
    overflow_disconnects = 0
    duplicate_rejections = 0
    if broker is not None:
        active_subscribers = broker.subscriber_count()
        max_queue_depth = broker.max_queue_depth()
        slow_consumers = broker.slow_consumer_count()
        overflow_disconnects = broker.overflow_disconnect_count()
        duplicate_rejections = broker.duplicate_rejection_count()
```

#### Step 2: Add new fields to JSON response

Change lines 58-68:
```python
    return JSONResponse(
        content={
            "status": overall,
            "db": db_status,
            "dlq_task": dlq_task_status,
            "active_subscribers": active_subscribers,
            "max_queue_depth": max_queue_depth,
            "slow_consumers": slow_consumers,
            "degraded_reasons": degraded_reasons,
        },
        status_code=status_code,
    )
```

to:
```python
    return JSONResponse(
        content={
            "status": overall,
            "db": db_status,
            "dlq_task": dlq_task_status,
            "active_subscribers": active_subscribers,
            "max_queue_depth": max_queue_depth,
            "slow_consumers": slow_consumers,
            "overflow_disconnects": overflow_disconnects,
            "duplicate_rejections": duplicate_rejections,
            "degraded_reasons": degraded_reasons,
        },
        status_code=status_code,
    )
```

### Details

The key changes are:

1. **Counter variables**: Added `overflow_disconnects` and `duplicate_rejections` initialized to 0, following the same pattern as `active_subscribers`, `max_queue_depth`, and `slow_consumers`.

2. **Getter calls**: Added `broker.overflow_disconnect_count()` and `broker.duplicate_rejection_count()` calls inside the `if broker is not None:` block, following the same pattern as the existing getters.

3. **JSON response**: Added the two new fields to the JSON response, following the same naming convention as the existing fields.

## Compatibility considerations

- The new fields are additive — they don't modify or remove any existing fields.
- When broker is None, both counters remain 0 (same as existing behavior for other broker metrics).
- No new HTTP status codes or response structure changes.

## Security considerations

- No new authentication or authorization boundaries introduced.
- Counter values are plain integers — no injection risk.
- No user input flows directly into SQL — schema changes are code-only.

## Rollback considerations

- To rollback: remove the counter variables, getter calls, and JSON fields.
- The rollback restores the pre-change state where only `slow_consumers` is surfaced.

## Validation plan

| Target | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/eventbus/health_route.py` | Structural verification | Read file, confirm new fields present | Two new fields added to health response |
| `tests/eventbus/test_eventbus_health.py` | Unit test assertions | `uv run pytest tests/eventbus/test_eventbus_health.py -v` | New counter fields present and correct in health response |

## Completion criteria

- `overflow_disconnects` and `duplicate_rejections` variables are added.
- Getter calls follow the existing pattern.
- JSON response includes the two new fields.
- No regressions in existing tests.

## Out of scope

- Modifying the `degraded_reasons` list — not affected by this change.
- Adding DDL to schema files — covered by separate procedure documents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add counter variables | Completed | — | — | |
| 2 | Add getter calls | Completed | — | — | |
| 3 | Add JSON fields | Completed | — | — | |
| 4 | Run validation (pytest + structural check) | Completed | — | — | Pre-existing errors (auth_token config) |

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
- **Requirement ID**: REQ-005
- **Source issue**: issues/20260907-125042_eb_h02_backpressure_duplicate_consumer_connection.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260909-095501_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260910-161316
- **Related target files**: scripts/eventbus/health_route.py
