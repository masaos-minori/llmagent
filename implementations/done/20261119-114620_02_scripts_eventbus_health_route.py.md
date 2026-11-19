## Goal
- Report the authorization sweep task in `/health`: its state, last cycle result and time, a stopped reason that sets liveness to false, and a failing reason that does not (REQ-001: the health contract covers every background task).

## Scope
**Release unit**: eventbus-supervision-and-cleanup

- In scope: `health_check` in `scripts/eventbus/health_route.py`, and the health tests in its companion file.
- Depends on the seq 01 document for the recorded cycle state; the shutdown test in the companion also needs the seq 03 document.

## Assumptions
- `health_check` derives `liveness` from `dlq_task_status == "running"` alone and has no sweep field (verified in Step 3a); `/health` is read by `deploy/setup_services.sh` through `liveness` and `readiness`.
- Existing tests compare `degraded_reasons` for exact equality in several cases (for example the capacity case), so a healthy sweep MUST add no reason; the real sweep loop runs in the `client` fixture and reports `ok` (verified in Step 3a).
- `health_check` is C(19) by radon; the new code uses a private helper to keep the complexity from growing.
- No public top-level symbol is added: `_task_running` (new) is private, so the generated manifest does not change from this document.

## Design decisions
- Read the sweep state with `getattr` defaults (`stopped` when the task is missing, `not_run` and `None` for the cycle), as the DLQ cycle state is read.
- Liveness becomes true only when both the DLQ task and the sweep task are running; `authz_sweep_failing` (new) is a 503-only reason like `dlq_sweep_failing`.

## Alternatives considered
- Add the sweep to readiness instead of liveness: rejected, the issue states a stopped task sets liveness to false as for the DLQ task.

## Implementation
### Target file
`scripts/eventbus/health_route.py`

### Procedure
1. Write the companion tests first and confirm they fail (no sweep field exists).
2. Add a private helper `_task_running` (new) that returns whether a task exists and is not done, and use it for the DLQ task and the sweep task.
3. Compute `authz_sweep_task` (`running` or `stopped`) from `getattr(request.app.state, "authz_sweep_task", None)`, and read `last_authz_sweep_result` and `last_authz_sweep_time` with the defaults above.
4. Add `authz_sweep_task_stopped` (new) to `degraded_reasons` when the sweep task is not running, and `authz_sweep_failing` (new) when the last result is `failed`.
5. Set `liveness` to the DLQ task running and the sweep task running; leave `readiness` as it is.
6. Add `authz_sweep_task` and `last_authz_sweep` (new) (`{"result": ..., "time": ...}`) to the response body beside the DLQ fields.

### Method
- Place the new reasons after the DLQ reasons so existing reason lists keep their order.
- Do not change the status code rule: any reason gives 503.

### Details
- Re-run `uv run radon cc scripts/eventbus/health_route.py -s -n C`; the grade of `health_check` MUST NOT get worse.

### Companion test files
- `tests/eventbus/test_eventbus_health.py`
  - Procedure: add `test_health_reports_sweep_task_running` (new) (fields present, status 200, liveness true on the `client` fixture); a fixture `sweep_stub_client` (new) that patches `eventbus.authz_ttl.sweep_expired_authorizations` before the lifespan starts, with `test_health_503_when_sweep_task_stopped` (new) (stub raises `RuntimeError`; wait until `app.state.authz_sweep_task.done()` through `client.portal`; expect 503, `authz_sweep_task_stopped` (new), `authz_sweep_task` `stopped`, `liveness` false) and `test_health_503_when_sweep_cycle_failed` (new) (stub raises `OSError`; wait for a non-`not_run` result; expect 503, `authz_sweep_failing` (new), liveness true); and `test_shutdown_completes_when_sweep_task_failed` (new) (start the app inside the test with the `RuntimeError` stub, leave the `with` block, assert no exception and `app.state.db` is `None`; expected red until the seq 03 document lands). Also drop the `monkeypatch.setattr(eb_app, "_ENVELOPE_SCHEMA_PATH", schema_path)` line of the `client` fixture (REQ-003).
  - Validation: `uv run pytest tests/eventbus/test_eventbus_health.py -q`.

## Compatibility considerations
- Adds two body fields and two reasons; no field is removed or renamed. A consumer reading only `db`, `dlq_task`, `liveness`, and `readiness` keeps working.
- `liveness` becomes stricter: a stopped sweep task now fails the deploy gate.

## Security considerations
- A stopped sweep leaves expired grants active; this change makes that visible and fails the gate, which is the purpose of the issue.

## Rollback considerations
- Revert with the release unit.

## Validation plan
- `uv run ruff format --check` and `uv run ruff check` on the changed files; `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`; `uv run bandit scripts/eventbus/health_route.py -c pyproject.toml -ll`; `uv run radon cc scripts/eventbus/health_route.py -s -n C`.
- `uv run pytest tests/eventbus -q` (the health, phase1, publish, subscribe, route-registry, slow-consumer, auth, and isolation suites call `/health`).

## Completion criteria
- `/health` reports the sweep fields and reasons as specified, liveness includes the sweep task, the existing health tests pass unchanged, and `health_check` complexity does not rise.

## Out of Scope
- Documentation (seq 07 to 10); the loop state (seq 01); lifespan state and shutdown (seq 03).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit `health_check` and add the private helper | Completed | 20261119-115656 | 20261119-115853 | Step 2 stale check clean; Step 3a: health_check, existing exact-equality reason tests, TestClient.portal, filterwarnings verified; files clean at baseline Changed: scripts/eventbus/health_route.py (private helpers _task_running, _sweep_state, _sweep_reasons; fields authz_sweep_task and last_authz_sweep; reasons; liveness). First attempt raised health_check from C(19) to D(22); moved the sweep branches into helpers: back to C(19), no public symbol added |
| 2 | Write the health tests (fail first) and drop the patch in the companion | Completed | 20261119-115853 | 20261119-120025 | The shutdown test is red until the seq 03 document lands Changed: tests/eventbus/test_eventbus_health.py (TestAuthzSweepHealth 4 tests + sweep_stub_client fixture, written first: all 4 failed; envelope patch dropped). Now 20 passed; 2 allowed red until seq 03 (stopped and shutdown tests fail at lifespan exit because _shutdown_lifespan re-raises the task exception) After seq 03: test_eventbus_health.py 22 passed; eventbus suite 536 passed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261119-115853 | 20261119-121150 | ruff, mypy, bandit pass; radon C(19) unchanged End of unit: full suite 12918 passed 7 skipped 0 failed (not integration/production_paths_allowed/repo_scan); diff-cover 100% (37 lines); ADR-cited tests 52 passed; validation gates pass; ruff, mypy (571 files), lint-imports (6 kept), bandit, radon, vulture, suppression, compat shims, db separation clean; radon health_check C(19) unchanged |

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
- **Requirement ID**: `REQ-001` (sweep task in `/health`), `REQ-002` (shutdown test), `REQ-003` (drop the envelope-path patch in the companion)
- **Source issue**: issues/20261117-123017_adrchk017_eventbus-task-supervision.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261119-113711_adrchk017_eventbus-task-supervision.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-114620
- **Related target files**: `scripts/eventbus/health_route.py`, `tests/eventbus/test_eventbus_health.py`