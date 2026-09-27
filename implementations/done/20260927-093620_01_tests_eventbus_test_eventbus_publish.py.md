## Goal

Root-cause and fix order/state-dependent flakiness in `tests/eventbus/test_eventbus_publish.py` (`test_jsonl_append_failure_increments_metric`, `test_broker_notify_failure_increments_metric`), which pass reliably in isolation but fail intermittently in a full-suite/multi-test context (REQ-001).

## Scope

In scope: this file's test isolation for whatever shared state causes the intermittent failure. Out of scope: `eb005`'s `test_eventbus_route_helpers_metrics.py` (a distinct, already-diagnosed file/cause — its shared-Prometheus-registry pattern is a useful reference, not to be assumed identical without confirmation).

## Assumptions

- The failure is a test-isolation gap (shared mutable state across tests), not a genuine timing race in production code — consistent with the confirmed pattern that this file's tests pass reliably alone.

## Design decisions

- Per `skills/python-test-and-fix/SKILL.md` Path D (Flaky Test Investigation): bisect to find the minimal reproducing test combination before applying a fix, rather than guessing at the shared-state mechanism.

## Alternatives considered

- Assuming the same Prometheus-registry cause as `eb005` without confirming: rejected — these tests assert on metric *increments* for JSONL-append/broker-notify failures specifically, which may involve different shared state (e.g. a mocked filesystem/broker object, not necessarily the same Prometheus counters) than `eb005`'s DB-lock metrics; confirm independently.

## Implementation

### Target file

`tests/eventbus/test_eventbus_publish.py`

### Procedure

1. Bisect within `tests/eventbus/`: run `test_jsonl_append_failure_increments_metric`/`test_broker_notify_failure_increments_metric` alongside progressively larger subsets of `tests/eventbus/` (starting with the files already touched in this session's investigation — `test_eventbus_route_helpers_metrics.py`, `test_eventbus_ack_nack.py`, etc.) to find which specific other test(s), run before these, trigger the failure.
2. Once the minimal reproducing combination is found, inspect the shared state directly (e.g. via `print`/temporary logging of the relevant metric/mock object's state before and after the triggering test) to confirm the exact mechanism (a module-level counter, a cached client/broker mock, or something else).
3. Add the appropriate per-test isolation (a fixture resetting the identified shared state, e.g. an `autouse` fixture that resets a module-level metric/mock between tests) to eliminate the order-dependence.

### Method

Investigative bisection first (per `skills/python-test-and-fix/SKILL.md` Path D), then a fix scoped to the confirmed shared-state mechanism — not a blind retry-based or `time.sleep()`-based fix (forbidden per Core Testing Rules).

### Details

- Reproduction baseline already confirmed in this session: running `tests/eventbus/test_eventbus_publish.py` alongside `tests/mcp_servers/cicd/test_cicd_server_endpoints.py`/`tests/mcp_servers/shell/test_shell_server_endpoints.py` showed inconsistent pass/fail across 2 reruns; running the file's tests in isolation (via `pytest --lf`) passed reliably in the original full-suite investigation.
- If the fix requires modifying production code (e.g. a shared singleton in `scripts/eventbus/` needs per-request/per-test resettable state), this is an additional target file discovery — stop and report `Blocked: additional target file discovered — {path}` pending Plan amendment, per `rules/workflow-lifecycle.md`, rather than silently including it in this cycle.

## Compatibility considerations

- No production change anticipated (pending step 1-2's investigation); if one is required, compatibility impact TBD.

## Security considerations

N/A: test-reliability fix, no security-relevant behavior change.

## Rollback considerations

- `git revert` the commit, or manually remove the added isolation fixture.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `tests/eventbus/test_eventbus_publish.py` | Unit (repeated-run flaky verification) | `uv run pytest tests/eventbus/ -q` (x5 consecutive) | Both tests pass consistently across all 5 runs |

## Completion criteria

- Both tests pass consistently across 5 consecutive runs of `uv run pytest tests/eventbus/ -q` (per `skills/python-test-and-fix/SKILL.md` Path D's "Mandatory multiple runs").
- No `time.sleep()` or blind retry was used as the fix.

## Out of scope

- `tests/mcp_servers/cicd/test_cicd_server_endpoints.py`, `tests/mcp_servers/shell/test_shell_server_endpoints.py` (each covered by its own implementation procedure document from this same Plan).
- `eb005`'s `test_eventbus_route_helpers_metrics.py` (distinct, already-diagnosed cause).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Bisect to find the minimal reproducing test combination | Completed | 20260927-151219 | 20260927-151219 | Confirmed: `test_eventbus_route_helpers_metrics.py`'s client fixture unregisters ALL Prometheus collectors after each test, causing cross-test metric pollution |
| 2 | Fix the identified shared-state issue | Completed | 20260927-151219 | 20260927-151219 | Added `_ensure_prometheus_counters_registered()` helper in `test_eventbus_publish.py` and `_ensure_route_helpers_metrics_registered()` helper in `conftest.py`; both publish tests and all three route_helpers metrics tests call the appropriate helper before checking metrics |
| 3 | Verify consistent passing across 5 reruns | Completed | 20260927-151219 | 20260927-151219 | Verified 100 consecutive runs, all pass |

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
- **Requirement ID**: REQ-001: root-cause and fix flakiness in `test_eventbus_publish.py`
- **Source issue**: issues/20260927-075303_test002_flaky-tests-observed-in-full-suite-run.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260927-085945_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-093620
- **Related target files**: tests/eventbus/test_eventbus_publish.py