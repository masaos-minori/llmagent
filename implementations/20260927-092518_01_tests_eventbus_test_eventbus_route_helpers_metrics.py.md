## Goal

Fix `tests/eventbus/test_eventbus_route_helpers_metrics.py::TestRunWithDbLockMetrics`'s 2 order-dependent flaky failures: an `int()`-vs-`float()` parsing bug reading a Prometheus counter's text-exposition value (REQ-001), and both tests' dependence on the shared, process-global default `prometheus_client.REGISTRY` (REQ-002).

## Scope

In scope: this file's metric-value parsing and both tests' before/after-delta isolation. Out of scope: `scripts/eventbus/route_helpers.py`'s `_db_lock_wait_time`/`_db_lock_contention` metric definitions and `run_with_db_lock`'s `.observe()`/`.inc()` calls — confirmed already correct and unconditionally invoked.

## Assumptions

- A before/after-delta assertion approach is sufficient to eliminate the order-dependence without requiring `route_helpers.py`'s metrics to become registry-configurable (per the Plan's own stated assumption) — if this cycle's Phase 1 bisection (below) shows this is insufficient, escalate per the Plan's Unknown UNK-01 rather than proceeding with an incomplete fix.

## Design decisions

- Fix `int()` → `float()` first (a deterministic bug, independent of ordering), then add before/after-delta capture to both tests so their assertions no longer depend on the shared registry's accumulated state from other tests.

## Alternatives considered

- Introducing a test-scoped `CollectorRegistry` (would require making `route_helpers.py`'s metrics registry-configurable, a production code change): deferred per the Plan's own stated preference — attempt the delta-based, test-only fix first.

## Implementation

### Target file

`tests/eventbus/test_eventbus_route_helpers_metrics.py`

### Procedure

1. **Phase 1 (bisection, per the Plan's UNK-01 resolution path)**: run `test_lock_wait_time_metric_observed` alone (`uv run pytest tests/eventbus/test_eventbus_route_helpers_metrics.py::TestRunWithDbLockMetrics::test_lock_wait_time_metric_observed -q`) repeated 5x to confirm whether it is genuinely order-dependent on ANOTHER test, or whether its intermittent failure (observed in this session's investigation) has a different, additional cause beyond registry sharing — add temporary `print(generate_latest().decode())` output during one failing repro run if the cause remains unclear after the delta fix (step 3 below).
2. **REQ-001**: fix the parsing bug in `test_lock_contention_counter_increments_on_slow_acquire` — change `count_after = int(lines_after[-1].split(" ")[-1]) if lines_after else 0` to use `float(...)` instead of `int(...)`.
3. **REQ-002**: in both `test_lock_wait_time_metric_observed` and `test_lock_contention_counter_increments_on_slow_acquire`, capture each relevant metric's value from `generate_latest()` immediately *before* the test's `run_with_db_lock` calls, then assert on the delta (after − before) rather than the raw cumulative value.

### Method

Step 2: single-token type-fix (`int` → `float`). Step 3: add a "before" snapshot capture at the start of each test (before any `run_with_db_lock` call), then change the final assertion to compare `after - before` against the expected increment, rather than asserting on the raw `after` value.

### Details

- `test_lock_contention_counter_increments_on_slow_acquire` before: `count_after = int(lines_after[-1].split(" ")[-1]) if lines_after else 0`; after: `count_after = float(lines_after[-1].split(" ")[-1]) if lines_after else 0.0`, then assert `count_after >= 0.0` (preserving the test's own already-lenient intent, per its comment "Counter may or may not have incremented... just verify it's a valid number").
- For the delta-based fix in both tests: capture `text_before = generate_latest().decode()` and parse the same target metric's before-value at the top of the test (before any `run_with_db_lock` call), then compute `delta = after_value - before_value` and assert on `delta` matching the test's original intent (e.g. `delta >= 0` for the lenient counter test, `count of new histogram samples added > 0` for the wait-time-observed test — confirm the exact original intent per test via Read before finalizing the delta assertion's exact form).
- Re-confirm exact current line numbers via `rg -n "generate_latest\(\)|lines_after\[-1\]"  tests/eventbus/test_eventbus_route_helpers_metrics.py` before editing (adversarial re-verification).

## Compatibility considerations

- No production code changes; test-only fix.

## Security considerations

N/A: test-only fix, no security-relevant behavior change.

## Rollback considerations

- `git revert` the commit, or manually restore the prior `int()` parsing and raw-value assertions.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `tests/eventbus/test_eventbus_route_helpers_metrics.py` | Unit (repeated-run flaky verification) | `uv run pytest tests/eventbus/test_eventbus_route_helpers_metrics.py -q` (x5 consecutive) | Both tests pass consistently across all 5 runs |

## Completion criteria

- `uv run pytest tests/eventbus/test_eventbus_route_helpers_metrics.py -q` passes consistently across 5 consecutive runs (per `skills/python-test-and-fix/SKILL.md` Path D's "Mandatory multiple runs").
- No `time.sleep()` or blind retry was used as the fix (per Core Testing Rules).

## Out of scope

- `scripts/eventbus/route_helpers.py`'s metric definitions (confirmed already correct).
- Escalating to a test-scoped `CollectorRegistry`/production registry-configurability change, unless Phase 1's bisection shows the delta approach is insufficient (in which case, report `Blocked: additional target file discovered` pending Plan amendment, per `rules/workflow-lifecycle.md`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Blocked | 20260927-185547 | — | Aborted per Step 3 Pre-execution Stale Detection: tools/stale_detector.py reports symbol_missing (CollectorRegistry, referenced only in Alternatives considered). Independently confirmed via Read: target file tests/eventbus/test_eventbus_route_helpers_metrics.py already has uncommitted working-tree changes (concurrent process) implementing an equivalent/superset fix (float() parsing + before/after delta isolation for both affected tests, plus an unrelated _ensure_route_helpers_metrics_registered() guard). Per Step 3's abort-and-report rule and to avoid clobbering another process's in-flight uncommitted work, this cycle stops here without re-implementing. Not moved to done/ — left as-is for the concurrent process or a future re-run to reconcile once that work is committed. |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: fixing the existing 2 tests' parsing/isolation is itself the fix |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: no docs/00_index.md task-scope mapping for this test file |

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
- **Requirement ID**: REQ-001, REQ-002: fix parsing bug and add before/after-delta isolation
- **Source issue**: issues/20260927-075245_eb005_eventbus-route-helper-metrics-parsing-and-counter-bugs.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260927-083524_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-092518
- **Related target files**: tests/eventbus/test_eventbus_route_helpers_metrics.py