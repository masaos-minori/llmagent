## Goal
- Remove the avoidable real-time cost from seven slow tests (a deadline busy-loop, a terminate wait, script retry loops, and event-publish volume) by test-side configuration only, so each failure path stays asserted, no production source changes, and each named test either finishes in about 2 s or carries a stated reason for staying slower or for the `integration` marker.

## Priority
Medium

## Scope
- **In-Scope**: record why each named test takes its time; shorten the waits through test-side values (a short `startup_timeout_sec`, patched module constants, script retry values, reduced event counts through the existing configuration fields); classify tests that must use a real script or subprocess as shortened, kept with a stated reason, or `integration`; record the duration profile before and after.
- **Out-of-Scope**: production timeouts, retry counts, intervals, and defaults; any file under `scripts/`, `config/`, or `deploy/`; `test_large_string_terminates` and the repository-scan tests; adopting parallel execution as the default; eventbus tests that no profile shows slow.
- **Dependencies**: `issues/20261112-183738_testspeed001_mark-repo-scan-tests.md` is related and not blocking (no new marker is needed here, because `integration` already exists in `pyproject.toml`; if a test is reclassified, follow the marker conventions there). `issues/20261112-183922_testspeed004_adopt-parallel-test-execution.md` is related and not blocking (these fixes raise the benefit of parallel execution because the longest single test sets the floor).

## Background
Measured on 2026-11-12 (8-way parallel run of the non-integration suite) and re-measured on 2026-11-13 for these tests (4 workers): `test_restart_clears_stderr_file` 30.3 s; `test_setup_services_connection_failure_aborts` 18.9 s, `test_setup_services_healthy_start_passes` 9.6 s, `test_setup_services_process_exit_aborts` 7.0 s; `test_raises_on_timeout` 8.1 s; `test_multi_batch_replay_no_duplicates` 17.2 s and `test_overflow_disconnects_subscriber` 11.5 s (slower than the 2026-11-12 values because of CPU contention). Only three tests in `tests/agent/test_lifecycle.py` carry `@pytest.mark.integration`.

## Problem
Tests that only need to see that a timeout or retry limit produces the right error wait for the real timeout, or for a real script to exhaust its retries, and two eventbus tests publish about a thousand events each through the HTTP client and SQLite. Each is a fixed cost in every run and, being a single test, limits how much parallel execution can help. Causes found:
- `test_restart_clears_stderr_file`: the wait loop is `while time.monotonic() < deadline` in `scripts/agent/http_lifecycle_health_checker.py`; with `asyncio.sleep` patched out it busy-spins until the 30 s deadline from `_make_cfg(startup_timeout_sec=30)`.
- `test_raises_on_timeout`: `timeout=1` plus `HEALTH_POLL_INTERVAL_SEC` (0.5) plus `TERMINATE_TIMEOUT_SEC` (5.0) from `scripts/agent/http_lifecycle.py`, because a mocked process never terminates (derived; the exact split is measured in Phase 1).
- `tests/deploy/test_setup_services_eventbus.py`: `_run_setup` fixes `LLM_HEALTH_RETRIES=15` and `LLM_HEALTH_INTERVAL=1`, so a failure path waits all 15 attempts.
- The two eventbus tests do not wait on a clock: `test_multi_batch_replay_no_duplicates` publishes `replay_batch_size + 5` events (the default is 1000) and `test_overflow_disconnects_subscriber` publishes 1001 events to fill a queue of the default `subscriber_queue_maxsize` of 1000. Their cost is publish throughput.

## Reason for Change
These waits add nothing to what the tests assert. Removing them lowers every test run and is a precondition for a useful result from parallel execution.

## Implementation Intent
For each test, make the duration a test-controlled value: a short `startup_timeout_sec` for the busy-loop test, patched module constants for the terminate wait, script retry values passed per call for the deploy tests (the interval stays an integer), and smaller event counts through `replay_batch_size` and `subscriber_queue_maxsize` for the eventbus tests. Keep every asserted outcome. Where a test must exercise the real script and a real eventbus process, keep it with the shortest values that still exercise the path, or mark it `integration` and say so.

## Requirements
- `REQ-001`: Record, for each test named in the Background, why it takes its time, and record the duration profile (`--durations=25`) before and after the change in the change record (commit message).
- `REQ-002`: Make `test_restart_clears_stderr_file` finish in about 2 s or less by shortening the startup timeout used by its config, keeping the `HttpStartupError` assertion and the stderr-file and log-path assertions.
- `REQ-003`: Make `test_raises_on_timeout` finish in about 2 s or less by shortening the terminate and poll waits from the test side, keeping the `did not become healthy` assertion.
- `REQ-004`: Make the failure-path tests of `tests/deploy/test_setup_services_eventbus.py` wait only a few attempts by passing small integer retry values per call, keep a retry margin for the healthy-start tests, keep every assertion on the failure, process-exit, and READY paths, and for each test that stays above the threshold state in the test file or the change record whether it is kept (with the reason) or marked `integration`.
- `REQ-005`: Make `test_multi_batch_replay_no_duplicates` and `test_overflow_disconnects_subscriber` finish in about 2 s or less by reducing the event counts through the existing configuration fields from the test side, keeping the assertions on exactly-once replay and on the overflow disconnect.
- `REQ-006`: Show the changed tests are not timing-flaky: run the touched files serially and with `-n auto` several times, run the full suite once, and run `-m integration` once if any test was reclassified.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| tests/agent/test_http_lifecycle_integration.py | HTTP lifecycle manager tests with a mocked subprocess | `test_restart_clears_stderr_file` uses `_make_cfg()` with `startup_timeout_sec=30` and patches only `asyncio.sleep`; shorten the config (REQ-001, REQ-002) | REQ-001, REQ-002 / AC-001, AC-002 | `_make_cfg` sets `startup_timeout_sec=30` and accepts overrides; the test patches `asyncio.sleep` only; measured 30.3 s; the loop `while time.monotonic() < deadline` is in `http_lifecycle_health_checker.py` (checked in Step 3) | tests/agent/test_http_lifecycle_integration.py | Verified |
| tests/agent/test_lifecycle.py | Lifecycle manager unit tests with mocked process and client | `test_raises_on_timeout` waits `timeout=1` plus the real poll interval and terminate timeout; patch the two module constants from the test (REQ-001, REQ-003) | REQ-001, REQ-003 / AC-001, AC-003 | `test_raises_on_timeout` builds `_http_subprocess_cfg(timeout=1)` with a mocked `Popen` and client and measured 8.1 s; `HEALTH_POLL_INTERVAL_SEC` and `TERMINATE_TIMEOUT_SEC` are module constants of `agent.http_lifecycle` (checked in Step 3) | tests/agent/test_lifecycle.py | Verified |
| tests/deploy/test_setup_services_eventbus.py | Runs the real `deploy/setup_services.sh` in a sandbox | `_run_setup` hard-codes `LLM_HEALTH_RETRIES=15` and `LLM_HEALTH_INTERVAL=1`; make retries a per-call argument (REQ-001, REQ-004) | REQ-001, REQ-004 / AC-001, AC-004 | `_run_setup` env sets 15 and 1; `connection_failure` measured 18.9 s, `healthy_start_passes` 9.6 s, `process_exit_aborts` 7.0 s; the script reads both variables and uses them in bash arithmetic under `set -euo pipefail`, so the interval must be an integer (checked in Step 3) | tests/deploy/test_setup_services_eventbus.py | Verified |
| tests/eventbus/test_eventbus_subscribe.py | Event Bus subscribe and replay tests | `test_multi_batch_replay_no_duplicates` publishes `replay_batch_size + 5` events with the default 1000; reduce through the configuration field (REQ-001, REQ-005) | REQ-001, REQ-005 / AC-001, AC-005 | The test reads `cfg.replay_batch_size` to size the publish count and pages `/replay` with `limit=100`; measured 17.2 s with 4 workers; `eventbus_test_config` builds a frozen dataclass that tests adjust with `object.__setattr__` (checked in Step 3) | tests/eventbus/test_eventbus_subscribe.py | Verified |
| tests/eventbus/test_eventbus_slow_consumer.py | Event Bus slow-consumer and overflow tests | `test_overflow_disconnects_subscriber` publishes 1001 events to fill a queue of 1000; use a fixture with a smaller `subscriber_queue_maxsize` and consistent thresholds (REQ-001, REQ-005) | REQ-001, REQ-005 / AC-001, AC-005 | The test fills `sub.queue` to the default `maxsize` of 1000 then asserts the disconnect; measured 11.5 s with 4 workers; `scripts/eventbus/config.py` requires `slow_consumer_threshold < subscriber_queue_maxsize` and `backlog_health_threshold <= subscriber_queue_maxsize` (checked in Step 3) | tests/eventbus/test_eventbus_slow_consumer.py | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file
  group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT
  appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as
  its own row when it requires modification — do not fold it into the row for the
  source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be
  `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/agent/http_lifecycle_health_checker.py | Holds the deadline wait loop and the terminate-on-timeout call | tests/agent/test_http_lifecycle_integration.py / REQ-002 |
| scripts/agent/http_lifecycle.py | Defines `HEALTH_POLL_INTERVAL_SEC` and `TERMINATE_TIMEOUT_SEC` and computes the deadline | tests/agent/test_lifecycle.py / REQ-003 |
| deploy/setup_services.sh | Reads `LLM_HEALTH_RETRIES` and `LLM_HEALTH_INTERVAL`; the interval is used in integer arithmetic | tests/deploy/test_setup_services_eventbus.py / REQ-004 |
| scripts/eventbus/config.py | Defines `replay_batch_size`, `subscriber_queue_maxsize`, and the threshold rules between them | tests/eventbus/test_eventbus_slow_consumer.py / REQ-005 |
| tests/eventbus/eventbus_helpers.py | `eventbus_test_config` and `make_eventbus_client` build the config the eventbus tests adjust | tests/eventbus/test_eventbus_subscribe.py / REQ-005 |

## Acceptance Criteria
- `AC-001` (REQ-001): The change record states the cause for each named test and lists the `--durations=25` profile before and after.
- `AC-002` (REQ-002): `test_restart_clears_stderr_file` finishes in about 2 s or less in an 8-way parallel run and still asserts `HttpStartupError`, the cleared stderr file, and the cleared log path.
- `AC-003` (REQ-003): `test_raises_on_timeout` finishes in about 2 s or less in an 8-way parallel run and still asserts the `did not become healthy` error.
- `AC-004` (REQ-004): Each test of the deploy file finishes in about 2 s or less, or is recorded as kept with a stated reason, or is marked `integration` with a stated reason; the assertions on the connection-failure, process-exit, status-not-ok, READY, and malformed-body paths still exist and pass.
- `AC-005` (REQ-005): Both eventbus tests finish in about 2 s or less and still assert exactly-once replay across pages and the overflow disconnect (`sub.queue.full()`, the overflow count, and `sub.disconnect.is_set()`).
- `AC-006` (REQ-006): Repeated serial and `-n auto` runs of the touched files show no failure; a fresh `--durations=25` profile no longer lists the named tests among the slowest, except tests recorded under AC-004; no file under `scripts/`, `config/`, or `deploy/` changed.

## Tests
- The seven named tests themselves, changed in place (REQ-002, REQ-003, REQ-004, REQ-005): the asserted outcomes stay; only durations and counts change.
- Flakiness check (REQ-006): the five touched test files, serially and with `-n auto`, repeated several times.
- Full suite once and `uv run pytest -m integration` once if a test is reclassified (REQ-006).

## Documentation Impact
N/A: no `docs/` change; the `integration` marker is already described in `pyproject.toml`, and no behavior documented in `docs/` changes.

## Assumptions
- A shorter `startup_timeout_sec` in `_make_cfg` still drives the deadline-timeout path of `HealthChecker`; falsifier: the test no longer raises `HttpStartupError` after the change.
- Patching `TERMINATE_TIMEOUT_SEC` and `HEALTH_POLL_INTERVAL_SEC` from the test (module constants) is enough to bring `test_raises_on_timeout` under about 2 s; falsifier: the Phase 1 measurement shows another wait.
- Reducing `replay_batch_size`, `subscriber_queue_maxsize`, and the two thresholds through `object.__setattr__` on the test config keeps the meaning of the two eventbus tests (several pages replayed exactly once; an overflowing queue disconnects its subscriber).
- The 2 s threshold is the Issue's proposal and is kept as a target, not a hard gate for tests that start a real eventbus process.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether other eventbus tests (for example `test_reconnect_after_overflow_disconnect_resumes_from_offset`, which publishes 1000 events, and `tests/eventbus/test_eventbus_subscribe_transition.py`) exceed the threshold | Only two eventbus tests were measured | Take a fresh `--durations=25` profile in Phase 1; handle a slow test already in a target file in this Plan, and add any other file through `tools/amend_plan.py` as a scope amendment | False |
| UNK-02 | Whether the script-driven deploy tests can reach the 2 s threshold | `LLM_HEALTH_INTERVAL` must be an integer, so a failure path waits at least retries x 1 s plus the script start; healthy-start tests start a real eventbus process | Measure in Phase 2, then decide per test among shortened, kept with a stated reason, or marked `integration` | False |
| UNK-03 | The measured split of the 8 s in `test_raises_on_timeout` | The 8 s is derived from constants, not measured | Measure in Phase 1 before editing | False |
| UNK-04 | Open dependency named by the Issue: `issues/20261112-183738_testspeed001_mark-repo-scan-tests.md` (Plan `plans/20261113-093307_testspeed001_mark-repo-scan-tests.md`, rows not `Completed`) | The Plan is `Pending` | Not needed first: this Plan adds no marker; it only reuses the `integration` marker conventions if a test is reclassified | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| tests/agent/test_http_lifecycle_integration.py | Modify | Low | 3 | N/A | not applicable (rsynced) |
| tests/agent/test_lifecycle.py | Modify | Low | 9 | N/A | not applicable (rsynced) |
| tests/deploy/test_setup_services_eventbus.py | Modify | Low | 8 | N/A | not applicable (rsynced) |
| tests/eventbus/test_eventbus_subscribe.py | Modify | Low | 7 | N/A | not applicable (rsynced) |
| tests/eventbus/test_eventbus_slow_consumer.py | Modify | Low | 4 | N/A | not applicable (rsynced) |

## Design
- Path B because five test files are targets. Architecture analysis: tests only; no import or layer change, so `lint-imports` is unaffected. Dependency graphing: each target is a test module with no importer. Historical analysis: 30-day commit counts are in `Affected areas` (30-day count of `git log` commits per file); `tests/agent/test_lifecycle.py` is the busiest, so keep its diff to the one test. Operational inspection: the deploy test runs the real script against a sandbox directory with a free port (its env sets `DEPLOY_DB`, `DEPLOY_LOGS`, and `LLMAGENT_CONFIG_DIR` under the sandbox), so it does not touch `/opt/llm`; no MCP server or production database is involved, so no port or lock check applies.
- Validation quality baseline: `N/A: no Python target` under `scripts/` or `tools/`.
- Mechanism per test (see Problem). For the busy-loop test, other tests in the same file already shorten the same loop by patching `time.monotonic`; a shorter `startup_timeout_sec` is chosen instead because a global clock patch also affects the event loop's own timers.
- Deploy tests: pass retries per call and keep the interval at 1, because `deploy/setup_services.sh` uses the interval in bash arithmetic (`$((LLM_HEALTH_RETRIES * LLM_HEALTH_INTERVAL))`) under `set -euo pipefail`, and a decimal value breaks the FATAL message path. The healthy-start tests keep a retry margin because the real eventbus process needs time to become healthy.
- Eventbus tests: the configuration is a frozen dataclass; tests already set fields with `object.__setattr__`. For the overflow test, `subscriber_queue_maxsize` is lowered together with `slow_consumer_threshold` and `backlog_health_threshold` so the validation rule between them still holds. For the replay test, `replay_batch_size` is lowered and the `/replay` page `limit` is aligned so that more than one page is still read.
- Compatibility: no public interface changes; no production source changes. Marker: `integration` already exists; no new marker.

## Implementation steps
Each step cites the rows of `Implementation Target Files` above.

1. **Phase 1: Agent lifecycle tests**
   - [ ] Take the fresh `--durations=25` profile and measure the split of the 8 s in `test_raises_on_timeout` before editing (REQ-001; tests/agent/test_lifecycle.py)
   - [ ] Shorten the config of `test_restart_clears_stderr_file` and keep its assertions (REQ-002; tests/agent/test_http_lifecycle_integration.py)
   - [ ] Patch `TERMINATE_TIMEOUT_SEC` and `HEALTH_POLL_INTERVAL_SEC` in `test_raises_on_timeout` and keep its assertion (REQ-003; tests/agent/test_lifecycle.py)
2. **Phase 2: Deploy script tests**
   - [ ] Make retries a per-call argument of `_run_setup`; use small integer retries for failure-path tests and a margin for healthy-start tests (REQ-004; tests/deploy/test_setup_services_eventbus.py)
   - [ ] Measure each test and record it as shortened, kept with a reason, or marked `integration` (REQ-004; tests/deploy/test_setup_services_eventbus.py)
3. **Phase 3: Eventbus tests**
   - [ ] Reduce the publish count and align the page limit in `test_multi_batch_replay_no_duplicates` (REQ-005; tests/eventbus/test_eventbus_subscribe.py)
   - [ ] Add a small-queue fixture and use it in `test_overflow_disconnects_subscriber` (REQ-005; tests/eventbus/test_eventbus_slow_consumer.py)
4. **Phase 4: Verification**
   - [ ] Re-run the profile, repeat the touched files serially and with `-n auto`, run the full suite once and `-m integration` once if any test was reclassified, and write the causes and before and after timings in the commit message (REQ-001, REQ-006; all five target files)
   - [ ] No deploy step: only files under `tests/` change, so `skills/deploy/SKILL.md` is not needed (REQ-006)

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tests/agent/test_http_lifecycle_integration.py, tests/agent/test_lifecycle.py | Unit | `uv run pytest tests/agent/test_http_lifecycle_integration.py tests/agent/test_lifecycle.py -m "not integration and not production_paths_allowed" --durations=10` | All pass; the two tests no longer among the slowest |
| tests/deploy/test_setup_services_eventbus.py | Integration-like (real script in a sandbox) | `uv run pytest tests/deploy/test_setup_services_eventbus.py --durations=10` | All pass; durations recorded per test |
| tests/eventbus/test_eventbus_subscribe.py, tests/eventbus/test_eventbus_slow_consumer.py | Unit | `uv run pytest tests/eventbus/test_eventbus_subscribe.py tests/eventbus/test_eventbus_slow_consumer.py --durations=10` | All pass; the two tests under about 2 s |
| All five files | Flakiness | the five files serially and with `-n auto`, repeated several times | No failure in any run |
| All five files | Static checks | `uv run ruff format <files>`, `uv run ruff check <files>`, `uv run mypy --no-namespace-packages <files>` (tests outside `tests/eventbus` are type-checked only when passed explicitly) | Clean |
| Suite | Full | `uv run pytest -m "not integration and not production_paths_allowed" --durations=25`, and `uv run pytest -m integration` once if a test was reclassified | No new failures (three mdq failures are pre-existing); fresh profile without the named tests |

## Risks
- **Risk**: A shortened value is too tight under parallel load and the test becomes flaky → **Mitigation**: keep a margin above the measured minimum, repeat the files serially and with `-n auto`, and keep the retry margin for healthy-start tests.
- **Risk**: Lowering a timeout stops the failure path from being exercised → **Mitigation**: keep every assertion on the failure message or state; the deadline test still needs the loop to expire, only sooner.
- **Risk**: Reducing event counts changes what an eventbus test proves → **Mitigation**: keep the thresholds consistent with `scripts/eventbus/config.py`, keep the page limit below the event count, and keep the exactly-once and disconnect assertions.
- **Risk**: Marking a test `integration` removes it from the default selection → **Mitigation**: mark only a test that must start a real eventbus process, state the reason, and run `-m integration` once.
- **Risk**: A global patch of `time.monotonic` disturbs the event loop → **Mitigation**: do not patch the clock globally for the busy-loop test; use the shorter timeout.
- **Risk**: A slow test outside the five files is found later → **Mitigation**: UNK-01; add it by `tools/amend_plan.py` as a scope amendment with approval.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: agent lifecycle tests (tests/agent/test_http_lifecycle_integration.py, tests/agent/test_lifecycle.py) | In Progress | — | — |  |
| 2 | Phase 2: deploy script tests (tests/deploy/test_setup_services_eventbus.py) | In Progress | — | — |  |
| 3 | Phase 3: eventbus tests (tests/eventbus/test_eventbus_subscribe.py, tests/eventbus/test_eventbus_slow_consumer.py) | In Progress | — | — |  |
| 4 | Phase 4: verification and change record (all five target files) | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261113-101644_01_tests_agent_test_http_lifecycle_integration.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261113-101644_02_tests_agent_test_lifecycle.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261113-101644_03_tests_deploy_test_setup_services_eventbus.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261113-101644_04_tests_eventbus_test_eventbus_subscribe.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261113-101644_05_tests_eventbus_test_eventbus_slow_consumer.py.md | 3 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261112-183849_testspeed003_cut-timeout-test-waits.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261113-092136
- **Related target files**: tests/agent/test_http_lifecycle_integration.py, tests/agent/test_lifecycle.py, tests/deploy/test_setup_services_eventbus.py, tests/eventbus/test_eventbus_subscribe.py, tests/eventbus/test_eventbus_slow_consumer.py

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Required Changes (record cause; re-run profile) | tests/agent/test_http_lifecycle_integration.py | Phase 1, Phase 4 | AC-001 | Validation plan: suite row | Confirmed by repository evidence |
| REQ-001 | Issue Required Changes (record cause; re-run profile) | tests/agent/test_lifecycle.py | Phase 1, Phase 4 | AC-001 | Validation plan: suite row | Confirmed by repository evidence |
| REQ-001 | Issue Required Changes (record cause; re-run profile) | tests/deploy/test_setup_services_eventbus.py | Phase 2, Phase 4 | AC-001 | Validation plan: suite row | Confirmed by repository evidence |
| REQ-001 | Issue Required Changes (record cause; re-run profile); eventbus cost is publish volume (checked in Step 3) | tests/eventbus/test_eventbus_subscribe.py | Phase 3, Phase 4 | AC-001 | Validation plan: suite row | Derived from confirmed evidence |
| REQ-001 | Issue Required Changes (record cause; re-run profile); eventbus cost is publish volume (checked in Step 3) | tests/eventbus/test_eventbus_slow_consumer.py | Phase 3, Phase 4 | AC-001 | Validation plan: suite row | Derived from confirmed evidence |
| REQ-002 | Issue Background (30 s test); deadline loop in `http_lifecycle_health_checker.py` | tests/agent/test_http_lifecycle_integration.py | Phase 1 | AC-002 | Validation plan: first row | Confirmed by repository evidence |
| REQ-003 | Issue Background (`test_raises_on_timeout` 8 s); module constants of `http_lifecycle.py` | tests/agent/test_lifecycle.py | Phase 1 | AC-003 | Validation plan: first row | Derived from confirmed evidence |
| REQ-004 | Issue Background (deploy tests); script variables and integer arithmetic | tests/deploy/test_setup_services_eventbus.py | Phase 2 | AC-004 | Validation plan: deploy row | Confirmed by repository evidence |
| REQ-005 | Issue Target Files (eventbus tests, inspect first); publish counts and config fields | tests/eventbus/test_eventbus_subscribe.py | Phase 3 | AC-005 | Validation plan: eventbus row | Derived from confirmed evidence |
| REQ-005 | Issue Target Files (eventbus tests, inspect first); publish counts and config fields | tests/eventbus/test_eventbus_slow_consumer.py | Phase 3 | AC-005 | Validation plan: eventbus row | Derived from confirmed evidence |
| REQ-006 | Issue Testing Expectations; Constraints (no timing flakiness) | tests/agent/test_http_lifecycle_integration.py | Phase 4 | AC-006 | Validation plan: flakiness and suite rows | Explicit in issue |
| REQ-006 | Issue Testing Expectations; Constraints (no timing flakiness) | tests/agent/test_lifecycle.py | Phase 4 | AC-006 | Validation plan: flakiness and suite rows | Explicit in issue |
| REQ-006 | Issue Testing Expectations; Constraints (no timing flakiness) | tests/deploy/test_setup_services_eventbus.py | Phase 4 | AC-006 | Validation plan: flakiness and suite rows | Explicit in issue |
| REQ-006 | Issue Testing Expectations; Constraints (no timing flakiness) | tests/eventbus/test_eventbus_subscribe.py | Phase 4 | AC-006 | Validation plan: flakiness and suite rows | Explicit in issue |
| REQ-006 | Issue Testing Expectations; Constraints (no timing flakiness) | tests/eventbus/test_eventbus_slow_consumer.py | Phase 4 | AC-006 | Validation plan: flakiness and suite rows | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261113-101644 -->