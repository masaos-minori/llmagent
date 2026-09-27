# Flaky tests observed in full suite run

## Priority
Low

## Summary
4 tests initially reported as failing in a full-suite run passed cleanly on immediate individual re-run with no code changes, indicating flakiness (non-deterministic behavior) rather than a deterministic bug.

## Background
Discovered during the post-docs-reorg full-suite validation sweep (`implementations/20260925-111411_04_tests___full_suite_.md`). While investigating the 97 full-suite failures by re-running failing files individually via `pytest --lf`, these 4 tests passed on the isolated re-run.

## Problem
- `tests/eventbus/test_eventbus_publish.py::test_jsonl_append_failure_increments_metric`
- `tests/eventbus/test_eventbus_publish.py::test_broker_notify_failure_increments_metric`
- `tests/mcp_servers/cicd/test_cicd_server_endpoints.py::TestCallToolEndpoint::test_dispatches_known_tool_and_audit_logs`
- `tests/mcp_servers/shell/test_shell_server_endpoints.py::TestCallToolEndpoint::test_dispatches_known_tool_and_audit_logs`

All 4 failed in the full-suite context (likely due to shared state, timing, port/resource contention, or test-ordering effects from running alongside ~2700 other tests) but passed when run in isolation.

## Reason for Change
Flaky tests reduce confidence in CI/full-suite signal and can mask genuine regressions (or cause false failures that block merges). Root-causing flakiness (test isolation, shared fixtures, timing assumptions) improves suite reliability.

## Implementation Intent
Per `skills/python-test-and-fix/SKILL.md` Path D (Flaky Test Investigation): run each test repeatedly (`--count`/loop or `pytest-randomly` with varying seeds) and alongside its full neighboring test file/module to try to reproduce the failure deterministically. Look for shared mutable state (e.g. a module-level counter/metric registry not reset between tests), port/file conflicts between concurrently-running server-endpoint tests, or ordering-dependent fixtures.

## Target Files or Areas
- `tests/eventbus/test_eventbus_publish.py`
- `tests/mcp_servers/cicd/test_cicd_server_endpoints.py`
- `tests/mcp_servers/shell/test_shell_server_endpoints.py`

## Required Changes
- Reproduce each flaky failure in a full-suite (or larger-scope) run at least once to confirm it is genuinely order/state-dependent rather than a one-off environment fluke.
- Identify and fix the shared-state/timing issue causing the flakiness (e.g. reset a shared metrics registry per test, isolate server test fixtures).

## Constraints
Do not mask flakiness with retries (`pytest-rerunfailures`) as the primary fix — retries may be an acceptable stopgap alongside, but the underlying shared-state/isolation issue should be fixed first per `skills/python-test-and-fix/SKILL.md` Core Testing Rules ("Strictly Forbid Flaky Fix Anti-Patterns").

## Acceptance Criteria
- Each of the 4 tests passes consistently across multiple full-suite runs (or a repeated-run reproduction of the suspected shared-state scenario).

## Testing Expectations
Run the full suite at least twice after the fix to confirm the flakiness no longer reproduces; per `rules/toolchain.md`, avoid `time.sleep()`-based fixes for any timing-related cause found.

## Documentation Impact
N/A: internal test-reliability fix, no expected documentation impact.

## Out of Scope
Other unrelated (deterministically) failing tests from the same full-suite run (tracked as separate issues).

## Dependencies
N/A: none

## Unresolved Questions
Needs confirmation: the exact shared-state/timing mechanism causing each test's flakiness — not yet isolated in this investigation (only the pass/fail inconsistency itself was observed).

## AI Implementation Instruction
Reproduce the flakiness in a full-suite (or same-module, larger-scope) run before attempting any fix — a fix based only on the isolated-passing run risks not addressing the actual shared-state cause. Do not add `time.sleep()` or blind retries as the primary fix.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: implementations/20260925-111411_04_tests___full_suite_.md
- **Generated at**: 20260927-075330
- **Related target files**: tests/eventbus/test_eventbus_publish.py, tests/mcp_servers/cicd/test_cicd_server_endpoints.py, tests/mcp_servers/shell/test_shell_server_endpoints.py
