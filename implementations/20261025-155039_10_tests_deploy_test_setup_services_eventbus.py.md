## Goal

Add deploy shell/integration tests for the `deploy/setup_services.sh` EventBus readiness gate (`REQ-004`): process exit, connection failure, non-200, `status != ok`, and healthy-start cases, so a crashed, unreachable, or genuinely-unavailable EventBus is never reported as `started`, while a healthy start on a transient capacity signal still passes.

## Scope

- Create `tests/deploy/test_setup_services_eventbus.py` only: a new deploy shell-test that runs `deploy/setup_services.sh` and asserts the EventBus gate behavior for each case.
- Do not modify `deploy/setup_services.sh`, `deploy/load_env.sh`, `scripts/eventbus/app.py`, `scripts/eventbus/health_route.py`, or any other target here — they are the deployment targets this test verifies (`REQ-004`).

## Assumptions

- The EventBus readiness gate lives in the `deploy/setup_services.sh` EventBus block (lines 157-198): the background launch at lines 180-183, the PID captured at line 183, and the bounded poll that treats a dead child, a persistent connection failure, a non-200, or a `status != ok` body as fatal with child cleanup, while tolerating capacity-only `degraded_reasons`.
- `setup_services.sh` runs the Workflow pre-flight (lines 24-75) and the LLM health gate (lines 80-155) before the EventBus block, so reaching the EventBus gate requires those earlier gates to have passed.
- `/health` in `scripts/eventbus/health_route.py` returns `db == ok`/`unavailable`, `dlq_task == running`/`stopped`, and HTTP 503 whenever any `degraded_reasons` entry exists; the readiness predicate is `db == ok` AND `dlq_task == running`.
- The env-overridable retry/interval pattern `LLM_HEALTH_RETRIES` / `LLM_HEALTH_INTERVAL` (lines 87-88) bounds the poll and is reused by the new gate.

## Design decisions

- **Run the real `setup_services.sh` in a controlled environment.** The test spawns `deploy/setup_services.sh` as a subprocess (mirroring the `subprocess` harness shape used in `tests/eventbus/test_eventbus_startup.py` lines 150-250) with an environment where the Workflow and LLM gates already pass, so execution reaches the EventBus gate. This tests the actual shipped script rather than a replicated predicate.
- **Vary the EventBus condition via real app state.** Each case controls what the gate observes through the EventBus database and process, exactly as the gate does: a malformed-stamped DB makes the lifespan fail and the process exit (process-exit case); occupying the bind port prevents binding (connection-failure case); a DB that exists but is unreachable makes `/health` report `db == unavailable` (non-200 / `status != ok` case); a canonical DB reaches `db == ok` AND `dlq_task == running` (healthy-start case).
- **Mirror the subprocess cleanup pattern.** Both the harness and the per-case teardown terminate the child identically to `test_main_failing_lifespan_exits_without_attributeerror` (lines 244-250), so no child leaks between cases.

## Alternatives considered

- **Extract the gate into a sourceable function and call it directly.** Rejected: the plan modifies `setup_services.sh` in place and the acceptance criterion is that the shipped script behaves correctly; a sourced-function test would not exercise the real script flow.
- **Require `status == ok` for the pass case.** Rejected: `/health` returns 503 on transient capacity degradation, so `status == ok` would fail a healthy start; the provisional `db == ok` AND `dlq_task == running` signal is the intended readiness predicate.

## Implementation

### Target file

`tests/deploy/test_setup_services_eventbus.py` (new)

### Procedure

1. Open `deploy/setup_services.sh` and confirm the EventBus launch block (lines 157-198): the `require_env_vars` call at line 176, the background launch at lines 180-183, the PID at line 183, and the summary banner at line 198.
2. Create `tests/deploy/test_setup_services_eventbus.py` with `_REPO_ROOT`, the `deploy/setup_services.sh` reference, a `_write_setup_services_driver` (new) helper, a `_run` helper matching the load-env gate, and the four tests below.
3. Write `test_setup_services_process_exit_aborts` (new): drive `setup_services.sh` with a malformed-stamped EventBus DB and assert the gate aborts with child cleanup.
4. Write `test_setup_services_connection_failure_aborts` (new): prevent the EventBus process from binding and assert the gate aborts after the retry budget.
5. Write `test_setup_services_status_not_ok_aborts` (new): make `/health` report `db == unavailable` and assert the gate aborts.
6. Write `test_setup_services_healthy_start_passes` (new): provide a canonical EventBus DB and assert the gate reports READY without failing on a capacity-only 503.

### Method

- `_write_setup_services_driver` (new) writes `driver.sh` containing `set -euo pipefail`, the absolute `deploy/setup_services.sh` path, and a single `bash "${SETUP}"` line that captures stdout/stderr for the caller.
- `_run` mirrors the load-env gate: minimal `PATH` env, `bash driver.sh` with `capture_output=True`, `text=True`, `timeout=30`, `check=False`, returning the `CompletedProcess`.
- Each case runs the driver with an environment in which the Workflow and LLM gates pass (a valid workflow definition and DB, and reachable mock LLM `/health` endpoints), then varies the EventBus condition:
  - Process-exit: pre-seed `/opt/llm/db/eventbus.sqlite` as stamped-but-malformed so the uvicorn lifespan fails and the process exits; the gate's `kill -0` liveness check fires the fatal path.
  - Connection-failure: occupy port 8015 with a bound socket before launching so the EventBus process cannot bind; every poll sees a connection failure and the gate fails once `LLM_HEALTH_RETRIES` is exhausted.
  - Status-not-ok: point the EventBus config at a database that exists but is unreachable so the process starts but `/health` returns `db == unavailable`; the gate reads `status != ok` and aborts.
  - Healthy-start: pre-seed a canonical EventBus DB so the process binds and `/health` reports `db == ok` AND `dlq_task == running`; assert the gate reports READY. A capacity-only 503 body still satisfies the predicate, so the pass case tolerates it.
- In the abort cases assert a non-zero exit, the missing `started` banner, and child cleanup; in the healthy-start case assert the READY banner and exit 0.
- Teardown terminates the child identically to lines 244-250 (`terminate`, `wait`, `kill` on timeout).

### Details

- The readiness predicate reads the two JSON fields the shared readiness definition depends on: `db` must equal `ok` and `dlq_task` must equal `running`, both from `scripts/eventbus/health_route.py`.
- Capacity-only degradation does not fail the gate. The `degraded_reasons` array in `scripts/eventbus/health_route.py` includes the transient capacity signals `lock_wait_high`, `slow_consumers_detected`, `query_duration_high`, `broker_queue_backlog_high`, and `subscribers_at_capacity`; none change `db` or `dlq_task`, so a body carrying only them still satisfies the readiness predicate.
- The process-exit case is caught indirectly: `_init_schema()` rejects the malformed database at runtime, the uvicorn lifespan fails, and the process exits; the gate's `kill -0` check then fires the fatal path before any response is seen.
- No new shell function is introduced beyond the gate already added to `setup_services.sh`; the poll reuses the `uv run` flags already used at lines 36-68 via the shared `UV_PROD_FLAGS` list.

## Compatibility considerations

- The new module is a standalone test file appended under `tests/deploy/`; it shares no imports with `test_load_env_gate.py` beyond the mirrored harness shape, so neither suite affects the other.

## Security considerations

- Fail-closed: a crashed, unreachable, or unavailable process aborts `setup_services.sh` instead of reporting success. The test uses throwaway databases and a per-test port; no real secrets or production paths are touched beyond the deployment DB directory.

## Rollback considerations

- Delete the new test file (or `git checkout` the parent commit); no existing file is modified.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `tests/deploy/test_setup_services_eventbus.py` | Integration: process-exit/connection-failure/non-200/status!=ok abort with cleanup; healthy start passes; capacity-only 503 does not fail | `uv run pytest tests/deploy/test_setup_services_eventbus.py` | each fatal case aborts with child cleanup and last-response logging; healthy start reports READY; capacity-only degradation does not abort |

## Completion criteria

- `test_setup_services_process_exit_aborts` (new) asserts the gate aborts when the EventBus process exits during startup.
- `test_setup_services_connection_failure_aborts` (new) asserts the gate aborts when the EventBus process cannot bind within the retry budget.
- `test_setup_services_status_not_ok_aborts` (new) asserts the gate aborts when `/health` reports `status != ok`.
- `test_setup_services_healthy_start_passes` (new) asserts a healthy start reports READY and tolerates a capacity-only 503.
- `shellcheck`, `ruff`, `mypy`, `bandit`, and `lint-imports` pass with all contracts KEPT.

## Out of Scope

- The `/health` contract and `degraded_reasons` taxonomy (`scripts/eventbus/health_route.py`), the runtime startup gate (`REQ-002`), the `init_db.sh` strict gate (`REQ-003`), and the config/token preflight (`REQ-005`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create `tests/deploy/test_setup_services_eventbus.py` (new) mirroring the subprocess harness | Pending | — | — | REQ-004 |
| 2 | Add `test_setup_services_process_exit_aborts` (new) asserting abort on process crash | Pending | — | — | REQ-004 |
| 3 | Add `test_setup_services_connection_failure_aborts` (new) asserting abort when the process cannot bind | Pending | — | — | REQ-004 |
| 4 | Add `test_setup_services_status_not_ok_aborts` (new) asserting abort on a non-capacity `status != ok` body | Pending | — | — | REQ-004 |
| 5 | Add `test_setup_services_healthy_start_passes` (new) asserting READY on a healthy start | Pending | — | — | REQ-004 |
| 6 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 7 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: test-only |

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
- **Source issue**: `issues/20261023-154326_eventbus003_startup-gate-schema-health.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-111552_eventbus003_startup-gate-schema-health.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261025-155039
- **Related target files**: `tests/deploy/test_setup_services_eventbus.py`
