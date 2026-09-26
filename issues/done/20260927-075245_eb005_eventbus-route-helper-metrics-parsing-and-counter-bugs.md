# EventBus route helper metrics parsing and counter bugs

## Priority
Medium

## Summary
`tests/eventbus/test_eventbus_route_helpers_metrics.py::TestRunWithDbLockMetrics` has 2 failures: a `ValueError` parsing a metric value string as `int()` when it is actually a float string (`'1.0'`), and a lock-contention counter that never increments above 0.

## Background
Discovered during the post-docs-reorg full-suite validation sweep (`implementations/20260925-111411_04_tests___full_suite_.md`), which surfaced 97 failing tests; this is one root-cause cluster from that investigation.

## Problem
- `test_lock_contention_counter_increments_on_slow_acquire`: `ValueError: invalid literal for int() with base 10: '1.0'` at `tests/eventbus/test_eventbus_route_helpers_metrics.py:202` — code parses a metrics-text value with `int()` but the value is formatted as a float string.
- `test_lock_wait_time_metric_observed`: `assert 0 > 0` (`len([])`) at line 171 — an expected non-empty metric-samples list is empty, meaning the wait-time metric was never recorded/observed.

## Reason for Change
If these reflect production behavior (not just test bugs), the lock-contention counter and lock-wait-time metric — both used for DB-lock-contention observability — are not being recorded correctly, which would degrade production observability for DB lock contention.

## Implementation Intent
Determine whether `int()` should be `float()`/`int(float(...))` at the parsing call site (test helper or production metrics-reading code — confirm which), and why the wait-time metric sample list is empty (metric not emitted, wrong metric name queried, or a timing/threshold issue in the test's slow-acquire simulation).

## Target Files or Areas
- `tests/eventbus/test_eventbus_route_helpers_metrics.py` (lines ~171, ~202)
- EventBus metrics-emission code for DB-lock contention/wait-time (confirm exact path, likely `scripts/eventbus/` metrics or route-helper module)

## Required Changes
- Fix the `int()`/`float()` parsing mismatch at the confirmed call site.
- Investigate why the wait-time metric sample list is empty and fix the underlying cause (metric not emitted vs. query/threshold issue).

## Constraints
N/A: none

## Acceptance Criteria
- Both listed tests pass.
- Confirm via the fix that the lock-contention counter and wait-time metric are genuinely observed under the tests' slow-acquire simulation, not just made to pass by relaxing the assertion.

## Testing Expectations
Run `tests/eventbus/test_eventbus_route_helpers_metrics.py`; run full suite once after the fix.

## Documentation Impact
N/A: unless the metric's format/type changes are user-visible (e.g. exposed via a `/metrics` endpoint doc), in which case update that documentation (Needs confirmation).

## Out of Scope
Other unrelated eventbus failing tests (tracked as separate issues).

## Dependencies
N/A: none

## Unresolved Questions
Needs confirmation: whether the `int()` parsing bug and empty-samples bug share one root cause (e.g. a metric format change) or are two independent bugs.

## AI Implementation Instruction
Read the exact metrics-parsing call site (line 202) and the metrics-emission code before fixing. Confirm whether the value is genuinely a float (fix: change parsing) or should be an int (fix: change emission format) before choosing a side.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: implementations/20260925-111411_04_tests___full_suite_.md
- **Generated at**: 20260927-075330
- **Related target files**: tests/eventbus/test_eventbus_route_helpers_metrics.py
