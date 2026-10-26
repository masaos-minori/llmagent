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

- **Run the real `setup_services.sh` in a sandboxed copy, driven entirely by the Doc 05 env overrides.** Verified 20261026: the harness copies `deploy/setup_services.sh` + `deploy/load_env.sh` into a `tmp_path` sandbox (so `REPO_ROOT` resolves to the sandbox) and runs it with `cwd = repo root` (the repo's synced `.venv`; no per-test uv project build — a copied `pyproject.toml` fails to build because the sandbox lacks the `scripts/` package dir). All state is redirected via the overrides added in procedure 20261025-155039_05: `DEPLOY_SCRIPTS=<repo>/scripts`, `DEPLOY_DB`/`DEPLOY_LOGS`/`WORKFLOW_JSON` → sandbox paths, `EVENTBUS_HEALTH_URL` → the per-test free port, plus `LLMAGENT_CONFIG_DIR` → the sandbox config (mandatory: without it the app reads the production `/opt/llm/config/eventbus.toml`). The Workflow pre-flight passes against a sandbox `workflow.sqlite` seeded with the four required tables + a `workflow_schema_version` row equal to `db.schema_sql.WORKFLOW_SCHEMA_VERSION`, and the LLM gate passes against local canned-200 mock servers referenced from the sandbox `config/agent.toml`. No production path is written to (mirrors the procedure 20261025-155039_09 sandbox decision).
- **Vary the gate signal per case; only the process-exit case uses real app state.** The process-exit case pre-seeds the sandbox EventBus DB as stamped-but-malformed so the real `eventbus.app` lifespan fails and the child exits. The other cases keep the real app (canonical sandbox DB) but steer `EVENTBUS_HEALTH_URL`: to an unbound port (connection-failure: the only deterministic way to exercise the retried `000`/retry-budget branch — occupying the app's own bind port instead makes uvicorn exit and surfaces as the crash path, which is also fatal), or to a canned-body server (status-not-ok: `db == unavailable` 503 while the child is alive; and capacity-only 503 pass-tolerance in the healthy test). The gate's contract is the `/health` body it reads, so canned bodies with the exact `health_route.py` field shape test the predicate faithfully.
- **Reap the child via the printed PID.** On a READY start the gate leaves `EB_PID` running; the harness parses the `Event Bus PID: <n>` line from stdout and terminates/waits/SIGKILLs that PID in teardown (same shape as `terminate`, `wait`, `kill` on timeout). On every abort path the script's own `eb_gate_fail` already killed the child; the harness confirms no child survives.

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

- The harness builds the sandbox under `tmp_path`: `deploy/` (copies of the two shell files), `config/` (sandbox `agent.toml` pointing `embed_url`/`llm_url` at canned-200 mock servers, sandbox `eventbus.toml` with `port = <per-test free port>`, `db_path`/`storage_dir`/`deadletter_dir` inside the sandbox, `auth_token = "${ENV:EVENTBUS_AUTH_TOKEN}"`), `config/workflows/default.json` (copy of the repo definition), `db/`, `logs/`. `_run` invokes `bash <sandbox>/deploy/setup_services.sh` with `cwd=_REPO_ROOT`, `capture_output=True`, `text=True`, `check=False`, a bounded `timeout`, and the env described above (`LLM_HEALTH_RETRIES`/`LLM_HEALTH_INTERVAL` shrunk to keep runs fast).
- Case drives:
  - Process-exit: seed the sandbox EventBus DB as canonical + `PRAGMA user_version = 1` + `ALTER TABLE events ADD COLUMN malformed_extra TEXT` (the Doc 03/09 unrepairable deviation; `CREATE ... IF NOT EXISTS` re-apply cannot heal it) so the real lifespan fails and the child exits.
  - Connection-failure: canonical DB, `EVENTBUS_HEALTH_URL` pointed at a bound-then-closed free port; every poll gets write-out `000` and the gate fails once the retry budget is exhausted (child still alive until `eb_gate_fail` kills it).
  - Status-not-ok: canonical DB (child alive and listening on its own port), `EVENTBUS_HEALTH_URL` pointed at a canned 503 body `{"status":"degraded","db":"unavailable","dlq_task":"running","degraded_reasons":["db_unavailable"]}`.
  - Healthy-start: canonical DB, real `/health` → 200 READY. The same test re-runs with `EVENTBUS_HEALTH_URL` pointed at a canned capacity-only 503 body (`db == ok`, `dlq_task == running`, `degraded_reasons: ["lock_wait_high","subscribers_at_capacity"]`) and asserts READY (pass-tolerance).
- In the abort cases assert a non-zero exit, `[FATAL] Event Bus` on stderr, and no READY banner; in the healthy-start case assert the READY banner and exit 0. Teardown: parse `Event Bus PID: <n>` and terminate/wait/SIGKILL.

### Details

- The readiness predicate reads the two JSON fields the shared readiness definition depends on: `db` must equal `ok` and `dlq_task` must equal `running`, both from `scripts/eventbus/health_route.py`.
- Capacity-only degradation does not fail the gate. The `degraded_reasons` array in `scripts/eventbus/health_route.py` includes the transient capacity signals `lock_wait_high`, `slow_consumers_detected`, `query_duration_high`, `broker_queue_backlog_high`, and `subscribers_at_capacity`; none change `db` or `dlq_task`, so a body carrying only them still satisfies the readiness predicate.
- The process-exit case is caught indirectly: `_init_schema()` rejects the malformed database at runtime, the uvicorn lifespan fails, and the process exits; the gate's `kill -0` check then fires the fatal path before any response is seen.
- No new shell function is introduced beyond the gate already added to `setup_services.sh`; the poll reuses the `uv run` flags already used at lines 36-68 via the shared `UV_PROD_FLAGS` list.

## Compatibility considerations

- The new module is a standalone test file appended under `tests/deploy/`; it shares no imports with `test_load_env_gate.py` beyond the mirrored harness shape, so neither suite affects the other.

## Security considerations

- Fail-closed: a crashed, unreachable, or unavailable process aborts `setup_services.sh` instead of reporting success. The test uses throwaway sandbox databases/logs and per-test free ports; production `/opt/llm` paths are never written to (all paths redirected via the Doc 05 overrides + `LLMAGENT_CONFIG_DIR`).

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
| 1 | Create `tests/deploy/test_setup_services_eventbus.py` (new) mirroring the subprocess harness | Completed | — | — | REQ-004 Sandbox harness: copied setup_services.sh+load_env.sh, cwd=repo root, DEPLOY_*/WORKFLOW_JSON/EVENTBUS_CONFIG_PATH/EVENTBUS_HEALTH_URL overrides; no production path touched |
| 2 | Add `test_setup_services_process_exit_aborts` (new) asserting abort on process crash | Completed | — | — | REQ-004 Malformed stamped DB -> child crash; exit 1, [FATAL] Event Bus, no READY banner, child reaped |
| 3 | Add `test_setup_services_connection_failure_aborts` (new) asserting abort when the process cannot bind | Completed | — | — | REQ-004 EVENTBUS_HEALTH_URL -> bound-then-released port; 000 retried branch, exit 1 after budget, child reaped |
| 4 | Add `test_setup_services_status_not_ok_aborts` (new) asserting abort on a non-capacity `status != ok` body | Completed | — | — | REQ-004 Canned 503 db=unavailable -> readiness predicate fail, exit 1 |
| 5 | Add `test_setup_services_healthy_start_passes` (new) asserting READY on a healthy start | Completed | — | — | REQ-004 Real app canonical DB -> READY exit 0; canned capacity-only 503 -> READY exit 0. Surfaced missing EVENTBUS_CONFIG_PATH export; fixed in setup_services.sh (doc 05 design decision added) |
| 6 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | 4 passed; fast gates Pass; bandit High/Medium 0; lint-imports 6 KEPT; pre-commit Passed; full suite 10135 passed, 9 skipped |
| 7 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — | N/A: test-only N/A: test-only |

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