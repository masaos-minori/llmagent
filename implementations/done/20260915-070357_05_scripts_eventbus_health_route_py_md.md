# Implementation Procedure: Read Health Endpoint Contract Evidence

## Goal

Read `scripts/eventbus/health_route.py` to gather evidence for documenting health endpoint contract (status codes, response format) in the EventBus API reference under `docs/eventbus/`. This is a read-only step — no modifications to this file.

## Scope

- Read `scripts/eventbus/health_route.py`: understand health endpoint contract (status codes, response format)
- No modifications to this file

## Assumptions

- REQ-004 requires documentation of health status codes and degraded reasons
- The health endpoint is documented in the `Document Health Endpoint Contract (REQ-004)` section of the plan
- Authentication: Monitoring role required (after eventbus02/03)

## Design decisions

N/A: This is a read-only reference step. The design decisions are captured in the `docs/eventbus/` implementation procedure.

## Alternatives considered

### Alternative A: Modify health_route.py to add documentation comments

**Reason for rejection:** Would violate the read-only discipline. Documentation should be in `docs/eventbus/`, not inline code comments.

## Implementation

### Target file

`scripts/eventbus/health_route.py` (read-only)

### Procedure

#### Step 1: Locate health_check function

Find the `health_check()` function in `health_route.py`. Focus on lines 24-121 as referenced in the plan.

Current state in `health_route.py`:
```python
async def health_check(request: Request) -> JSONResponse:
    # Returns JSONResponse with status_code 200 (ok) or 503 (degraded)
    # Response body includes:
    #   - status: "ok" | "degraded"
    #   - db: "ok" | "unavailable"
    #   - dlq_task: "running" | "stopped"
    #   - active_subscribers: int
    #   - max_queue_depth: int
    #   - slow_consumers: int
    #   - overflow_disconnects: int
    #   - duplicate_connection_rejections: int
    #   - degraded_reasons: list[str]
    #   - metrics: {lock_wait_avg_seconds, query_duration_avg_seconds, lock_contention_total}
```

#### Step 2: Verify health endpoint contract accuracy

Compare the plan's documented contracts against the actual health endpoint contract:

##### Success (HTTP 200)

Documented contract:
```json
{
    "status": "ok",
    "db": "ok",
    "dlq_task": "running",
    "active_subscribers": 5,
    "max_queue_depth": 120,
    "slow_consumers": 0,
    "overflow_disconnects": 0,
    "duplicate_connection_rejections": 0,
    "degraded_reasons": [],
    "metrics": {
        "lock_wait_avg_seconds": 0.002,
        "query_duration_avg_seconds": 0.001,
        "lock_contention_total": 0
    }
}
```

Verify:
- [ ] All fields present in the documented contract exist in the actual implementation
- [ ] Field types match the documented contract
- [ ] Default values match the documented contract

##### Degraded (HTTP 503)

Documented contract:
```json
{
    "status": "degraded",
    "db": "ok",
    "dlq_task": "running",
    "active_subscribers": 10,
    "max_queue_depth": 600,
    "slow_consumers": 2,
    "overflow_disconnects": 0,
    "duplicate_connection_rejections": 0,
    "degraded_reasons": [
        "broker_queue_backlog_high",
        "slow_consumers_detected",
        "subscribers_at_capacity"
    ],
    "metrics": {
        "lock_wait_avg_seconds": 0.015,
        "query_duration_avg_seconds": 0.06,
        "lock_contention_total": 5
    }
}
```

Verify:
- [ ] All fields present in the documented contract exist in the actual implementation
- [ ] Field types match the documented contract
- [ ] Degraded reasons match the documented contract

##### Degraded Reasons

Documented degraded reasons:
- `db_unavailable`: Database connectivity check failed
- `dlq_task_stopped`: DLQ background task is not running
- `broker_queue_backlog_high`: Queue depth >= `backlog_health_threshold`
- `slow_consumers_detected`: Slow consumers detected (>0)
- `subscribers_at_capacity`: Active subscribers >= `subscriber_count`
- `lock_wait_high`: Average lock wait time > 10ms
- `query_duration_high`: Average query duration > 50ms

Verify:
- [ ] All degraded reasons listed in the documented contract exist in the actual implementation
- [ ] Reason descriptions match the documented contract

#### Step 3: Document findings for API reference

Record any discrepancies between the documented contract and the actual health endpoint contract. Key questions to answer:
1. Are there any differences in response format?
2. Are there any additional HTTP status codes not documented?
3. Is the authentication requirement accurate?

### Method

Manual code review — read the relevant sections of `health_route.py` and verify the health endpoint contract.

### Details

#### Verification checklist

- [ ] health_check() function understood
- [ ] Success (HTTP 200) response verified
- [ ] Degraded (HTTP 503) response verified
- [ ] Degraded reasons verified
- [ ] Authentication requirements verified

## Compatibility considerations

- No compatibility impact — this is a read-only step
- Findings will inform the `docs/eventbus/` API reference documentation

## Security considerations

- No security impact — this is a read-only step
- Understanding authentication requirements is critical for accurate documentation

## Rollback considerations

- N/A: No modifications made to this file

## Validation plan

1. Confirm understanding of health endpoint contract matches the documented behavior
2. Verify that response formats match the documented contracts
3. Verify that HTTP status codes match the documented contracts
4. Verify that degraded reasons match the documented contract

## Completion criteria

- [ ] health_check() function understood
- [ ] Success (HTTP 200) response verified
- [ ] Degraded (HTTP 503) response verified
- [ ] Degraded reasons verified
- [ ] Authentication requirements verified

## Out of scope

- Modifying health endpoint logic
- Adding new health checks
- Changing the health response format

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Locate health_check function | Completed | 20260915-230000 | 20260915-230000 |  |
| 2 | Verify health endpoint contract accuracy | Completed | 20260915-230000 | 20260915-230000 |  |
| 3 | Document findings for API reference | Completed | 20260915-230000 | 20260915-230000 |  |

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
- **Requirement ID**: REQ-004 (document health status codes and degraded reasons)
- **Source issue**: issues/20260914-102632_eventbus11_api-reference-endpoint-contracts.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-181638_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-070357
- **Related target files**: scripts/eventbus/health_route.py