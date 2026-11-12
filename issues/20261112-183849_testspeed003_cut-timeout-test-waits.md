# Remove real waiting from timeout and subprocess startup tests

## Priority
Medium

## Summary
Several unit-style tests spend most of their time waiting for a timeout or a retry interval to elapse in real time. Make those waits injectable or short in tests, so the tests verify the same failure paths without consuming wall time, and classify any test that genuinely needs a real subprocess and real time as an integration test.

## Background
Measured on 2026-11-12 (8-way parallel run of the non-integration suite, 12129 passed, 3m47s wall time). The slowest tests that wait rather than compute:

- `tests/agent/test_http_lifecycle_integration.py::TestSubprocessLifecycle::test_restart_clears_stderr_file`: 30.01 s. The fixture config `_make_cfg` sets `startup_timeout_sec=30`, the test patches `asyncio.sleep` to return immediately, and expects `HttpStartupError`. The duration equals the 30 s startup timeout.
- `tests/deploy/test_setup_services_eventbus.py::test_setup_services_connection_failure_aborts` (17.2 s), `test_setup_services_healthy_start_passes` (6.1 s), `test_setup_services_process_exit_aborts` (3.8 s). The helper runs the real `deploy/setup_services.sh` in a subprocess with `LLM_HEALTH_RETRIES=15` and `LLM_HEALTH_INTERVAL=1`, so a failure path can wait up to 15 s.
- `tests/agent/test_lifecycle.py::TestStartHttpSubprocess::test_raises_on_timeout`: 8.04 s even though the config sets `timeout=1` and the process and HTTP client are mocked.
- `tests/eventbus/` replay and slow-consumer tests: 3 to 8 s each (for example `test_multi_batch_replay_no_duplicates` 7.6 s, `test_overflow_disconnects_subscriber` 5.3 s).

Together the first four groups account for about 65 s of call time. Only `tests/agent/test_lifecycle.py` lines 761, 793 and 825 carry `@pytest.mark.integration`; the tests above do not, so they run in every non-integration run. The mechanism for the 30 s test (a deadline-based wait loop that keeps spinning while `asyncio.sleep` is patched out) is a hypothesis; the code was not read to confirm it.

## Problem
Tests that only need to see that a timeout or retry limit produces the right error instead wait for the real timeout, or for a real script to exhaust its retries. They contribute a fixed cost to every run and, because each is a single test, limit how much parallel execution can help.

## Reason for Change
The development loop is dominated by test wall time. These waits add nothing to what the tests assert, so they can be removed without reducing coverage. Fixing them is also a precondition for getting a useful result from parallel execution (the longest single test sets the floor).

## Implementation Intent
For each test, find what the wait is for and make the duration a test-controlled value: pass a short timeout or retry count through the existing configuration (`startup_timeout_sec`, `LLM_HEALTH_RETRIES`, `LLM_HEALTH_INTERVAL`), or patch the clock the wait loop actually reads (not only `asyncio.sleep`). Where a test must exercise the real script or a real subprocess, keep it but give it the shortest values that still exercise the failure path, or mark it `integration`. Do not change production timeouts or defaults.

## Target Files or Areas
- `tests/agent/test_http_lifecycle_integration.py`
- `tests/agent/test_lifecycle.py`
- `tests/deploy/test_setup_services_eventbus.py`
- `tests/eventbus/test_eventbus_subscribe.py`, `tests/eventbus/test_eventbus_subscribe_transition.py`, `tests/eventbus/test_eventbus_slow_consumer.py` (inspect first; may be legitimately real-time)
- `scripts/agent/http_lifecycle.py` (read only, to find what clock the wait loop uses; change only if an injection point is missing and the Plan approves it)

## Required Changes
- For each test listed in Background, determine why it takes that long and record the cause.
- Reduce the real wait to under about 2 s per test (a proposed threshold) by test-side configuration or clock control, keeping the asserted outcome.
- For tests that need real time or a real subprocess, either shorten via environment values or mark with the existing `integration` marker, and say which in the change record.
- Re-run the duration profile (`--durations=25`) before and after and record the change.

## Constraints
- Production timeouts, retry counts, and defaults stay as they are.
- Each failure path currently asserted (startup timeout, connection failure, process exit) must still be asserted.
- Tests must not become timing-flaky: shortened values need a margin that holds under parallel execution.

## Acceptance Criteria
- Each test named in Background either finishes in under about 2 s in an 8-way parallel run or is marked `integration` with a stated reason.
- The assertions covering the timeout, connection-failure, and process-exit paths still exist and pass.
- A fresh `--durations=25` profile no longer lists these tests among the slowest.
- No production source file changes unless an injection point had to be added with Plan approval.

## Testing Expectations
- `uv run pytest` on the touched files, serially and with `-n auto`, repeated a few times to check for flakiness.
- Full suite once (`uv run pytest`), plus `uv run pytest -m integration` if any test was reclassified.
- `uv run ruff check`, `uv run mypy` on the touched files.

## Documentation Impact
None expected. If a test is reclassified to `integration`, no docs change; the marker is already described in `pyproject.toml`.

## Out of Scope
- Changing production health-check intervals or timeouts.
- The `test_large_string_terminates` test and the repository-scan tests (separate issues).
- Adopting parallel execution as the default.

## Dependencies
- `issues/20261112-183738_testspeed001_mark-repo-scan-tests.md`: related, not blocking. Both add test-selection markers or classifications; if a test here is classified by marker, reuse the marker conventions from that issue.

## Unresolved Questions
- Why `test_raises_on_timeout` takes 8 s with `timeout=1` and mocked process and client: 不明. Not read.
- Whether the 30 s test waits on a deadline loop (hypothesis) or on something else: 不明.
- Whether the `tests/eventbus/` timings are real-time requirements of the behavior under test (such as a replay-to-live transition) or avoidable waits: 不明.

## AI Implementation Instruction
Read each test and the code path it drives before changing anything, and record why it waits. Change test-side values first; touch production code only to add a missing injection point and only after stating it. Do not lower a timeout in a way that makes a failure path stop being exercised. If a wait is part of the behavior being tested, leave the test as is or mark it `integration` and report it.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261112-183849
- **Related target files**: `tests/agent/test_http_lifecycle_integration.py`, `tests/agent/test_lifecycle.py`, `tests/deploy/test_setup_services_eventbus.py`, `tests/eventbus/test_eventbus_subscribe.py`, `tests/eventbus/test_eventbus_subscribe_transition.py`, `tests/eventbus/test_eventbus_slow_consumer.py`, `scripts/agent/http_lifecycle.py`
