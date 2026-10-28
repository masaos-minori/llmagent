# Procedure: replace the vacuous timing tests with sample-value tests

## Goal

Assert histogram sample values for wait and duration, the contention counter and the raising-callback case (Plan REQ-005).

## Scope

- Modify only `tests/eventbus/test_eventbus_route_helpers_metrics.py`.
- Test-only change; no source file is edited.

## Assumptions

- Ordering note: apply this row before the source rows (tests first); the helper `_ensure_route_helpers_metrics_registered` from `tests/eventbus/conftest.py` is reused.
- Overlap (compatible): `plans/done/20261028-092928_ebshutdown002_close-shutdown-admission-race.md` (archived, procedures pending) also targets `scripts/eventbus/route_helpers.py` (a post-lock shutdown re-check placed right after lock acquisition and before the active-user bump) and `docs/24_eventbus/eventbus_07_configuration-and-operations.md` (Shutdown section). This procedure changes the timing statements around the lock and the Metrics section; whichever lands first, re-read the file and keep the other's lines.

## Design decisions

- Locate edit points by test or fixture name, never by line number.
- Assert observable behavior; use barriers or events, never sleeps.

## Alternatives considered

N/A: lightweight row; the Plan fixes the approach.

## Implementation

### Target file

`tests/eventbus/test_eventbus_route_helpers_metrics.py`

### Procedure

- In `test_query_duration_metric_observed`, replace the `len(after_lines) > 0 or before_count == 0` assertions with `REGISTRY.get_sample_value("eventbus_db_query_duration_seconds_count")` before/after, expecting an increase of 1 and a positive `_sum` delta.
- In `test_lock_wait_time_metric_observed`, assert the wait `_count` delta of 1 and that an uncontended call adds less than 1 ms to `_sum`.
- Add `test_contended_call_waits_and_increments_contention_counter` (new): hold the real lock in the test, start the call, release it after a `threading.Event` shows the worker is waiting, and assert the contention counter delta of 1 and a wait that excludes the callback time.
- Add `test_raising_callback_still_records_query_duration` (new): the callback raises, assert the exception propagates and the duration `_count` increased.
- Use barriers or events, never sleeps; bound every wait with a timeout.

### Method

Edit the existing tests in place and reuse the file's fixtures and helpers.

### Details

- Write these before row 1 and confirm `test_query_duration_metric_observed` and the raising-callback test fail on the unmodified code.

## Compatibility considerations

N/A: test-only change.

## Security considerations

N/A: test-only change.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| 1 | `uv run pytest tests/eventbus/test_eventbus_route_helpers_metrics.py -q` | Pass |
| 2 | `uv run ruff format tests/eventbus/test_eventbus_route_helpers_metrics.py`; `uv run ruff check tests/eventbus/test_eventbus_route_helpers_metrics.py` | No finding |

## Completion criteria

- The new assertions fail on the pre-change code and pass after row 1.

## Out of Scope

- Source files and other test files.
- Documentation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add or update tests per Validation plan | Pending | — | — | |
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
- **Requirement ID**: REQ-001, REQ-005 (timing tests that fail on the current code)
- **Source issue**: issues/20261027-155849_ebmetrics006_correct-db-timing-health.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-094217_ebmetrics006_correct-db-timing-health.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-120038
- **Related target files**: tests/eventbus/test_eventbus_route_helpers_metrics.py
