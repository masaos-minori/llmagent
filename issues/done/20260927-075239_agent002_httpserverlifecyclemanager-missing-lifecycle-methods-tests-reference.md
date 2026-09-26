# HttpServerLifecycleManager missing lifecycle methods tests reference

## Priority
High

## Summary
13 tests across two files reference `HttpServerLifecycleManager` methods `_open_stderr_log` and `_terminate_with_timeout` that no longer exist on the class, failing with `AttributeError`.

## Background
Discovered during the post-docs-reorg full-suite validation sweep (`implementations/20260925-111411_04_tests___full_suite_.md`), which surfaced 97 failing tests; this is one root-cause cluster from that investigation.

## Problem
`AttributeError: <class 'agent.http_lifecycle.HttpServerLifecycleManager'> has no attribute '_open_stderr_log'` and `... has no attribute '_terminate_with_timeout'` occur in:
- `tests/agent/test_lifecycle.py` (12 tests: `TestHttpLifecycleStderrLog`, `TestStartHttpSubprocess`, `TestProcessGroupShutdown`, `TestHttpManagerRestart`)
- `tests/integration/test_mcp_transport_crash.py::test_d05_http_timeout_races_lifecycle_termination` (1 test)

## Reason for Change
Either the class was refactored (methods renamed/removed/merged) without updating tests that assert on its internals, or a genuine regression removed behavior these tests depend on (subprocess stderr-log handling, process-group termination with timeout). Process-group shutdown and stderr handling are operational-reliability concerns (subprocess/resource cleanup), so this is correctness-sensitive.

## Implementation Intent
Read the current `HttpServerLifecycleManager` implementation in `scripts/agent/http_lifecycle.py` (confirm exact path) to determine the current names/locations of the stderr-log-opening and timeout-based-terminate logic. If the functionality still exists under new names, update the tests to reference the current internals. If the functionality was dropped entirely, treat this as a behavior regression and restore it, or confirm with the user that its removal was intentional before touching tests.

## Target Files or Areas
- `scripts/agent/http_lifecycle.py` (confirm exact path for `HttpServerLifecycleManager`)
- `tests/agent/test_lifecycle.py`
- `tests/integration/test_mcp_transport_crash.py`

## Required Changes
- Confirm current method names/structure for stderr-log opening and process-group-timeout-termination logic.
- Update the 13 tests to the current internal API, or restore the missing methods if their removal was unintentional.

## Constraints
Tests reference private (`_`-prefixed) methods directly — preserve this white-box testing style unless a black-box equivalent already exists and is preferred by the surrounding test file's own conventions.

## Acceptance Criteria
- All 13 listed tests pass.
- Subprocess stderr capture and process-group termination-with-timeout behavior is confirmed still present (not silently dropped).

## Testing Expectations
Run `tests/agent/test_lifecycle.py` and `tests/integration/test_mcp_transport_crash.py`; run full suite once after the fix.

## Documentation Impact
N/A: unless the class's public/internal contract changes as part of the fix, in which case update any doc describing `HttpServerLifecycleManager`'s lifecycle (Needs confirmation).

## Out of Scope
Other unrelated failing tests from the same full-suite run (tracked as separate issues).

## Dependencies
N/A: none

## Unresolved Questions
Needs confirmation: whether `_open_stderr_log`/`_terminate_with_timeout` were renamed (test-only fix) or removed as an unintentional regression (production fix) — requires reading current `http_lifecycle.py` source.

## AI Implementation Instruction
Read the current `HttpServerLifecycleManager` source first before touching any test. Do not assume the tests are simply stale — confirm whether the referenced behavior (stderr log capture, timeout-based process-group termination) still exists anywhere in the class before deciding whether this is a rename or a dropped feature.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: implementations/20260925-111411_04_tests___full_suite_.md
- **Generated at**: 20260927-075330
- **Related target files**: tests/agent/test_lifecycle.py, tests/integration/test_mcp_transport_crash.py
