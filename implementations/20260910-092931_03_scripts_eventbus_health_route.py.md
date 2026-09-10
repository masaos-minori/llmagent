## Goal
Surface the new overflow-disconnect/duplicate-rejection counters (row 01) in the JSON
health response, following the existing `slow_consumers` field's pattern (REQ-005;
AC-5).

## Scope
In scope: `health_check()`'s broker-health-metrics block and its returned JSON
payload. Out of scope: the DB/DLQ-task status logic in the same function — unrelated
to this Requirement.

## Assumptions
- `broker.overflow_disconnect_count()`/`broker.duplicate_rejection_count()` (row 01)
  are plain getter calls with no side effects, matching `slow_consumer_count()`'s
  existing pattern — adding them does not grow `health_check()`'s cyclomatic
  complexity beyond its current pre-existing `C (11)` grade (a plain field read adds
  no new branch).

## Design decisions
Add two new fields to the JSON response (`overflow_disconnects`,
`duplicate_connection_rejections`), read via the new broker getters in the same
`if broker is not None:` block that already reads `subscriber_count()`/
`max_queue_depth()`/`slow_consumer_count()` — no new `if` branch, no new
`degraded_reasons` entry (these are observability counters, not new degraded-status
triggers, since the Plan's Acceptance Criteria (AC-5) require observability, not a new
health-status semantic).

## Alternatives considered
Adding a new `degraded_reasons` entry when either counter is nonzero (e.g.
"overflow_disconnect_occurred") was considered and rejected: the Plan's REQ-005 asks
for observable counters/logs, not a new health-degradation trigger — a historical
overflow-disconnect count staying nonzero forever would otherwise permanently mark the
service `degraded`, which misrepresents current health.

## Implementation
### Target file
`scripts/eventbus/health_route.py`

### Procedure
1. In the existing `if broker is not None:` block, add two more getter calls
   alongside `active_subscribers`/`max_queue_depth`/`slow_consumers`.
2. Add the two new keys to the returned `JSONResponse` content dict, alongside the
   existing `slow_consumers` key.

### Method
Two added lines inside the existing block and two added dict keys; no new branching
logic.

### Details
```python
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

...

return JSONResponse(
    content={
        "status": overall,
        "db": db_status,
        "dlq_task": dlq_task_status,
        "active_subscribers": active_subscribers,
        "max_queue_depth": max_queue_depth,
        "slow_consumers": slow_consumers,
        "overflow_disconnects": overflow_disconnects,
        "duplicate_connection_rejections": duplicate_connection_rejections,
        "degraded_reasons": degraded_reasons,
    },
    status_code=status_code,
)
```

## Compatibility considerations
Purely additive JSON fields — no existing key is removed or renamed; any client
parsing this response by known keys is unaffected.

## Security considerations
Counters expose only aggregate counts, no consumer identities or payload data.

## Rollback considerations
Revert this file's diff. Since the counters are read-only getters with no side
effects, reverting this file alone (without reverting row 01) is safe — the getters
simply go uncalled.

## Validation plan
`uv run pytest tests/eventbus/test_eventbus_health.py -v` (row 07): new counter fields
present and correct in the health response.

## Completion criteria
The health JSON response includes `overflow_disconnects` and
`duplicate_connection_rejections`, correctly reflecting `EventBroker`'s counters
(AC-5); `degraded_reasons`/`status`/`db`/`dlq_task` logic is unchanged.

## Out of scope
Any change to the DB-connectivity or DLQ-task-status checks in this same function.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the two new counter getter calls to the broker-metrics block | Pending | — | — | |
| 2 | Add the two new keys to the JSON response | Pending | — | — | |
| 3 | Add or update tests per Validation plan (row 07) | Pending | — | — | |
| 4 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Generated at**: 20260910-092931
- **Related target files**: scripts/eventbus/health_route.py
