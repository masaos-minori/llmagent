## Goal
- Initialize the sweep cycle state in the lifespan, make shutdown tolerate a background task that already ended with an exception (REQ-002), and remove the unused `_ENVELOPE_SCHEMA_PATH` (REQ-003).

## Scope
**Release unit**: eventbus-supervision-and-cleanup

- In scope: `lifespan`, `_shutdown_lifespan`, and the `_ENVELOPE_SCHEMA_PATH` constant in `scripts/eventbus/app.py`, plus the seven companion test files that patch the constant.
- `tests/eventbus/test_eventbus_auth.py` also references the constant but keeps its own document (seq 23).

## Assumptions
- `_ENVELOPE_SCHEMA_PATH` has no reader under `scripts`; the lifespan reads the schema through `get_schema_path()`, which the tests also patch (verified in Step 3a).
- `monkeypatch.setattr` raises on a missing attribute, so every companion patch MUST be removed in the same change as the constant.
- `_shutdown_lifespan` awaits each task catching only `CancelledError`, so a task that ended with an exception re-raises there and aborts shutdown before the broker and database are closed (verified in Step 3a).
- `test_eventbus_shutdown.py` builds an app state with `dlq_task=None` and no `authz_sweep_task`; the new helper MUST accept `None`, and the sweep task is read with `getattr`.

## Design decisions
- Add one private async helper `_stop_task` (new) used for both the DLQ task and the sweep task: cancel, await, treat `asyncio.CancelledError` as normal, log any other exception and continue.
- Keep the shutdown order unchanged: shutdown flag, tasks, broker, then the database lock and close.

## Alternatives considered
- Catch `Exception` around the whole shutdown: rejected, it would hide a real failure to close the database.

## Implementation
### Target file
`scripts/eventbus/app.py`

### Procedure
1. Remove the `_ENVELOPE_SCHEMA_PATH` patches from the seven companion files (below); the constant still exists, so nothing breaks yet.
2. In `lifespan`, next to the DLQ cycle state, set `app.state.last_authz_sweep_result` to `"not_run"` and `app.state.last_authz_sweep_time` to `None` before the sweep task is created.
3. Add `_stop_task` (new) and replace the two cancel-and-await blocks of `_shutdown_lifespan` with calls to it (DLQ task first, then the sweep task read through `getattr`).
4. Delete the `_ENVELOPE_SCHEMA_PATH` constant; `Path` stays imported because the lifespan still uses it.

### Method
- In `_stop_task` (new), the broad `except Exception` carries a `# noqa: BLE001 — ...` justification stating that it logs and continues so the broker and database still close; log with the task name.
- Do not change `_dlq_loop` or the lock-timeout error path.

### Details
- Run `rg "_ENVELOPE_SCHEMA_PATH" scripts tests`; after this document and the seq 23 document it MUST find nothing.

### Companion test files
- `tests/eventbus/eventbus_helpers.py`
  - Procedure: drop the two `monkeypatch.setattr(eb_app, "_ENVELOPE_SCHEMA_PATH", schema_path)` lines.
  - Validation: `uv run pytest tests/eventbus/test_eventbus_startup.py -q`.
- `tests/eventbus/test_admin_topics_authorization.py`
  - Procedure: drop the one patch line.
  - Validation: `uv run pytest tests/eventbus/test_admin_topics_authorization.py -q`.
- `tests/eventbus/test_eventbus_app_isolation.py`
  - Procedure: drop the one patch line.
  - Validation: `uv run pytest tests/eventbus/test_eventbus_app_isolation.py -q`.
- `tests/eventbus/test_eventbus_replay_pagination.py`
  - Procedure: drop the one patch line.
  - Validation: `uv run pytest tests/eventbus/test_eventbus_replay_pagination.py -q`.
- `tests/eventbus/test_eventbus_route_helpers_metrics.py`
  - Procedure: drop the one patch line.
  - Validation: `uv run pytest tests/eventbus/test_eventbus_route_helpers_metrics.py -q`.
- `tests/eventbus/test_eventbus_offsets.py`
  - Procedure: drop the one patch line.
  - Validation: `uv run pytest tests/eventbus/test_eventbus_offsets.py -q`.
- `tests/eventbus/test_eventbus_restart_resume.py`
  - Procedure: drop the two patch lines.
  - Validation: `uv run pytest tests/eventbus/test_eventbus_restart_resume.py -q`.

## Compatibility considerations
- `_ENVELOPE_SCHEMA_PATH` is a module-private name; the only users are the tests listed here and in the seq 01, 02, and 23 documents.
- Shutdown behavior for a healthy task is unchanged.

## Security considerations
- Shutdown still closes the database only after the lock is acquired; a failed background task no longer prevents that.

## Rollback considerations
- Revert with the release unit.

## Validation plan
- `uv run ruff format --check` and `uv run ruff check` on the changed files; `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`; `uv run bandit scripts/eventbus/app.py -c pyproject.toml -ll`; `uv run python tools/check_suppression_justification.py`.
- `uv run pytest tests/eventbus -q` (including `test_eventbus_shutdown.py`).

## Completion criteria
- The lifespan initializes the sweep state, shutdown completes when a task ended with an exception, `_ENVELOPE_SCHEMA_PATH` is gone from `scripts`, and the companion suites pass.

## Out of Scope
- Changes to `_dlq_loop`, the lock-timeout behavior, and the health contract.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit `lifespan`, add `_stop_task` (new), and remove the constant | Completed | 20261119-121159 | 20261119-121159 | Changed: scripts/eventbus/app.py (lifespan state init, _stop_task, shutdown through the helper, _ENVELOPE_SCHEMA_PATH removed); recorded together with the companion edits in row 2 |
| 2 | Drop the patches in the seven companion files | Completed | 20261119-115853 | 20261119-120025 | Do this before deleting the constant Step 2 stale check clean; Step 3a: constant has no reader in scripts; test_eventbus_shutdown uses dlq_task=None and no authz_sweep_task; seven companion files clean at baseline Changed: scripts/eventbus/app.py (lifespan state init, _stop_task, shutdown via helper, constant removed); tests/eventbus/{eventbus_helpers,test_admin_topics_authorization,test_eventbus_app_isolation,test_eventbus_replay_pagination,test_eventbus_route_helpers_metrics,test_eventbus_offsets,test_eventbus_restart_resume}.py (9 patch lines removed, diff verified deletion-only). Eventbus suite 536 passed; the two seq 02 red tests are now green |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261119-120025 | 20261119-121150 | ruff, bandit, suppression pass; mypy: 1 allowed red (tests/eventbus/test_eventbus_auth.py references the removed constant) attributed to seq 23 After seq 23: mypy clean (571 files); the allowed red is resolved End of unit: full suite 12918 passed 7 skipped 0 failed (not integration/production_paths_allowed/repo_scan); diff-cover 100% (37 lines); ADR-cited tests 52 passed; validation gates pass; ruff, mypy (571 files), lint-imports (6 kept), bandit, radon, vulture, suppression, compat shims, db separation clean |

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
- **Requirement ID**: `REQ-002` (lifespan state and shutdown tolerance), `REQ-003` (remove the envelope-path constant)
- **Source issue**: issues/20261117-123017_adrchk017_eventbus-task-supervision.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261119-113711_adrchk017_eventbus-task-supervision.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-114620
- **Related target files**: `scripts/eventbus/app.py`, `tests/eventbus/eventbus_helpers.py`, `tests/eventbus/test_admin_topics_authorization.py`, `tests/eventbus/test_eventbus_app_isolation.py`, `tests/eventbus/test_eventbus_replay_pagination.py`, `tests/eventbus/test_eventbus_route_helpers_metrics.py`, `tests/eventbus/test_eventbus_offsets.py`, `tests/eventbus/test_eventbus_restart_resume.py`