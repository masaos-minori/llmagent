## Goal

Update `tests/eventbus/test_eventbus_route_helpers_metrics.py` so it asserts the timing split:
execution time excludes lock wait, dispatch and lock-wait are separate, and
`lock_wait_high`/`query_duration_high` are independent measurements (REQ-004; Acceptance 3).

## Scope

- Modify only `tests/eventbus/test_eventbus_route_helpers_metrics.py`, covering
  `test_query_duration_metric_observed` (line 104).

## Assumptions

- `test_query_duration_metric_observed` (line 104) asserts `_db_query_duration` is still
  observed after any change; the fix moves that observation inside the lock, so the assertion
  must be updated to assert execution-excludes-lock-wait.

## Design decisions

- **Execution-excludes-lock-wait.** Assert `_db_query_duration` is observed while holding the
  lock and that its value excludes lock-wait; with contention, assert lock-wait is measured
  separately (REQ-004; Acceptance 3).

## Alternatives considered

- Leaving the original "still observed" assertion unchanged: rejected — it would pass even
  though the measurement still overlaps lock wait.

## Implementation

### Target file

`tests/eventbus/test_eventbus_route_helpers_metrics.py`

### Procedure

1. In `test_query_duration_metric_observed` (line 104), keep asserting `_db_query_duration` is
   observed, and additionally assert its value measures execution while holding the lock
   (excludes lock wait) using a contended vs short-query comparison.
2. Add an assertion that lock-wait (`eventbus_db_lock_wait_time_seconds`) is distinct from the
   query duration under contention.

### Method

Adjust assertions in the named test; add a contention scenario if not present.

### Details

- Rely on `run_with_db_lock` (fixed in seq 2); the test validates the independent timings.

## Compatibility considerations

- Test-only change; no runtime impact.

## Security considerations

- N/A.

## Rollback considerations

- Revert the commit.

## Validation plan

- `uv run pytest tests/eventbus/test_eventbus_route_helpers_metrics.py` — `_db_query_duration`
  observed while holding lock; independent timings.
- `uv run pytest tests/eventbus/` — full EventBus suite passes.
- `uv run mypy`, `uv run ruff` on the file.

## Completion criteria

- The test asserts execution time excludes lock wait and the degraded reasons measure
  independent quantities.

## Out of Scope

- The `run_with_db_lock` timing implementation (route_helpers.py, seq 2).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Assert execution time excludes lock wait; lock-wait separate | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-004`
- **Source issue**: `issues/done/20261023-154326_eventbus007_side-effects-metrics-health-recovery.md`
- **Requirement requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-123218_eventbus007_side-effects-metrics-health-recovery.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261026-092908
- **Related target files**: `tests/eventbus/test_eventbus_route_helpers_metrics.py`
