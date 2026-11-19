## Goal
- Record the result and time of every authorization sweep cycle on `app.state`, so `/health` can report them (REQ-002: the sweep loop records its last cycle).

## Scope
**Release unit**: eventbus-supervision-and-cleanup

- In scope: `authz_sweep_loop` in `scripts/eventbus/authz_ttl.py`, and the loop-state tests in its companion file.
- The consumer of the new state is the seq 02 document (`health_route.py`); the state is initialized by the seq 03 document (`app.py`).

## Assumptions
- The loop catches only `OSError` and `ValueError`; that handler is not changed (Plan UNK-02: detection of other exceptions comes from the task state).
- `eventbus.json_utils.now_iso` is a leaf helper already imported by `app.py`, so importing it here adds no cycle (verified in Step 3a).
- The DLQ loop is the model: it sets `last_dlq_cycle_result` to `ok` or `failed` and `last_dlq_cycle_time` after each cycle (verified in Step 3a).
- The loop signature and the public symbol set of the module do not change, so the generated manifest is not affected by this document.

## Design decisions
- Name the state `last_authz_sweep_result` (new) and `last_authz_sweep_time` (new), mirroring the DLQ names.
- Write the time after both a successful and a failed cycle; write nothing when the task is cancelled.

## Alternatives considered
- A module-level variable instead of `app.state`: rejected, the DLQ state lives on `app.state` and tests build several apps.

## Implementation
### Target file
`scripts/eventbus/authz_ttl.py`

### Procedure
1. Write the loop-state tests in the companion file first and confirm they fail (the attributes are never set).
2. Import `now_iso` from `eventbus.json_utils`.
3. In `authz_sweep_loop`, set `app.state.last_authz_sweep_result` to `"ok"` after `sweep_expired_authorizations` returns, and to `"failed"` in the `(OSError, ValueError)` branch; set `app.state.last_authz_sweep_time` to `now_iso()` after either outcome, before the sleep.
4. Leave the `asyncio.CancelledError` branch re-raising untouched.

### Method
- Keep the structure of the existing `try` block; add the two assignments and nothing else.

### Details
- The first cycle runs immediately at startup, so a healthy start reads `ok` within moments; `not_run` is the lifespan's initial value (seq 03).

### Companion test files
- `tests/eventbus/test_authz_generation_ttl.py`
  - Procedure: add `test_sweep_loop_records_ok_result_and_time` (new) and `test_sweep_loop_records_failed_result_on_oserror` (new): drive `authz_sweep_loop` with a `SimpleNamespace` app whose `state.config` comes from `eventbus_test_config`, patch `eventbus.authz_ttl.sweep_expired_authorizations` (return `None`, then raise `OSError`) and `eventbus.authz_ttl.asyncio.sleep` (raise `asyncio.CancelledError` to end the loop after one cycle), then assert the recorded result and a time ending in `Z`. Also drop the two `monkeypatch.setattr(eb_app, "_ENVELOPE_SCHEMA_PATH", schema_path)` lines of the restart tests (REQ-003).
  - Validation: `uv run pytest tests/eventbus/test_authz_generation_ttl.py -q`; the two new tests fail before step 3 and pass after.

## Compatibility considerations
- Adds attributes to `app.state` only; no caller reads them before seq 02.

## Security considerations
- No authorization behavior changes; the recorded time is not a secret.

## Rollback considerations
- Revert with the release unit.

## Validation plan
- `uv run ruff format --check` and `uv run ruff check` on the changed files; `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`; `uv run bandit scripts/eventbus/authz_ttl.py -c pyproject.toml -ll`.
- `uv run pytest tests/eventbus/test_authz_generation_ttl.py -q`.

## Completion criteria
- The loop records the result and time after each cycle, the cancellation path writes nothing, and the new tests pass.

## Out of Scope
- Broadening the exception handler; `/health` changes (seq 02); lifespan initialization (seq 03).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit `authz_sweep_loop` to record the cycle state | Completed | — | 20261119-115656 | Changed: scripts/eventbus/authz_ttl.py (now_iso import; result ok/failed and time recorded per cycle) |
| 2 | Write the loop-state tests (fail first) and drop the patches in the companion | Completed | 20261119-115602 | 20261119-115656 | Step 2 stale check clean; Step 3a: loop, now_iso, app_get_config verified; files clean at baseline. Release unit order: 01 02 03 04 05 06 then docs 07-10, generated 11-13, 23 Changed: tests/eventbus/test_authz_generation_ttl.py (TestSweepLoopState 2 tests, written first: both failed with AttributeError before the change; two envelope patches dropped). 14 passed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261119-115656 | 20261119-121150 | ruff, mypy (571 files), bandit pass; full suite once at end of unit End of unit: full suite 12918 passed 7 skipped 0 failed (not integration/production_paths_allowed/repo_scan); diff-cover 100% (37 lines); ADR-cited tests 52 passed; validation gates pass; ruff, mypy (571 files), lint-imports (6 kept), bandit, radon, vulture, suppression, compat shims, db separation clean |

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
- **Requirement ID**: `REQ-002` (record the last sweep cycle), `REQ-003` (drop the envelope-path patches in the companion)
- **Source issue**: issues/20261117-123017_adrchk017_eventbus-task-supervision.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261119-113711_adrchk017_eventbus-task-supervision.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-114620
- **Related target files**: `scripts/eventbus/authz_ttl.py`, `tests/eventbus/test_authz_generation_ttl.py`