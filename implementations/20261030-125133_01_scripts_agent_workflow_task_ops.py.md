## Goal

Make `scripts/agent/workflow/task_ops.py` the single owner of task persistence: move the task aggregate counts into it (`REQ-001`, single task-SQL owner), delete the four task lookup APIs that have no production caller (`REQ-002`, zero-caller removal), and rename the task key column and field to `task_nonce` (new) (`REQ-003`, accurate key name). The rename step is gated behind the schema row (see Assumptions).

## Scope

- Modify only `scripts/agent/workflow/task_ops.py`.
- Phase 2 part (executable now): counts move in, lookups removed.
- Phase 3 part (gated): column rename in `create_task` and `_row_to_task`.

## Assumptions

- Plan Dependencies (`plans/20261030-113553_wftaskapi001_consolidate-task-persistence.md` Scope): the rename depends on the dbmig001 workflow migration registry (`plans/20261029-214108_dbmig001_forward-only-db-migrations.md` Phase 3). Steps 3-4 below MUST NOT run before the plan's schema row (`scripts/db/schema_sql.py`) and its migration step land in the same release; Steps 1-2 do not depend on it.
- Plan overlap judgments (Plan Assumptions, Step 8b): `task_ops.py` is also a target of `plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md` (transition API in the same file): sequencing dependency, this Plan lands first and the transition work rebases.
- `models.py` row 03 renames `TaskRecord.idempotency_key` to `task_nonce` (new) (`task_nonce` (new) on the dataclass); this document's rename step runs after that row in the same release.
- Caller evidence (Plan Background): `get_task_by_idempotency_key`, `get_task_by_session`, `get_latest_task`, and `list_tasks` have no caller in `scripts/`; only `tests/agent/workflow/test_workflow_engine.py` and `test_workflow_state_store.py` call the key lookup.

## Design decisions

- `task_ops` is the canonical owner (Plan Design): production already imports `create_task` and `get_task_by_id` from it (`scripts/agent/workflow_engine_adapter.py:38`).
- The two task aggregates (`get_task_count`, `get_workflow_count`) move here because they query only `tasks`; the cross-table attempt and artifact diagnostics stay in `StateStore` (Plan REQ-001).

## Alternatives considered

- Keep `StateStore` as owner: rejected, more call sites change for no behavior gain (Plan Design).
- Drop the unique key column: rejected, needs a table rebuild on SQLite 3.46.1 (Plan UNK-03).

## Implementation

### Target file

`scripts/agent/workflow/task_ops.py`

### Procedure

1. Re-run the caller search for the four removable names and for task `idempotency_key` across `scripts/`, `tests/`, `tools/`, `docs/`, `deploy/` (REQ-007 record); stop and report if a caller outside `tests/` appears.
2. Add `get_task_count(db, session_id)` (new) and `get_workflow_count(db, session_id)` (new) with the same SQL as the `StateStore` methods of the same names.
3. Delete `get_task_by_idempotency_key`, `get_task_by_session`, `get_latest_task`, and `list_tasks`.
4. (Gated) Rename the key in `create_task`, `_row_to_task`, and the module docstring text to `task_nonce` (new), keeping the UUID4 generation and the never-caller-derived contract.

### Method

- Count functions take a `SQLiteHelper` and a session id, run one parameterized `SELECT COUNT(*)` (and `COUNT(DISTINCT workflow_id)` for workflows, with the `workflow_id IS NOT NULL` filter), and return `int`; model the row access on the existing `StateStore` versions so the result types stay identical.
- Deletions remove the four function definitions and any imports that become unused (`sqlite3` stays: `_row_to_task` uses it).
- Rename touches the INSERT column list and values, the keyword argument in `TaskRecord(...)` construction at both construction sites, and the row key read in `_row_to_task`.

### Details

- Current layout: `create_task` at `:13`, `update_task_status` at `:66`, `_row_to_task` at `:75`, `get_task_by_id` at `:91`, `get_task_by_idempotency_key` at `:99`, `get_task_by_session` at `:107`, `get_latest_task` at `:116`, `list_tasks` at `:127`.
- Keep `create_task`, `update_task_status`, and `get_task_by_id` signatures unchanged (the adapter and engine depend on them).
- Mypy: new functions fully annotated, return `int`.

## Compatibility considerations

- `StateStore` keeps `get_task_count` and `get_workflow_count` as delegates (row 02) so `session_persister` is unaffected.
- The rename is a persisted-schema change: it ships only with the migration; a retained `workflow.sqlite` at the old version is refused at startup otherwise.

## Security considerations

- N/A: no new input boundary; SQL stays parameterized.

## Rollback considerations

- Steps 1-3: revert the commit.
- Step 4 is not reversible after the forward-only migration has run; hence the gate and the release-unit rule.

## Validation plan

- `uv run pytest tests/agent/workflow/ -v`
- `rg "get_task_by_idempotency_key|get_task_by_session|get_latest_task|list_tasks" scripts tests tools docs deploy` (empty after all rows)
- `uv run ruff format scripts/agent/workflow/task_ops.py`, `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll`
- `uv run python tools/check_module_size.py`

## Completion criteria

- `task_ops.py` defines the count functions and none of the four removed lookups.
- After the gated step, `rg idempotency_key scripts/agent/workflow/task_ops.py` is empty and `create_task` writes `task_nonce` (new).
- All tests in `tests/agent/workflow/` pass.

## Out of Scope

- `StateStore` delegation (row 02), `TaskRecord` field (row 03), DDL and migration (row 04), tests and docs rows.
- Status transitions and attempt logic (wfrecovery001 Plan).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Caller search and record; add count functions; delete the four lookups | Pending | — | — | Not gated |
| 2 | Rename the key to `task_nonce` (new) | Pending | — | — | Gated: only with row 03 and the schema row and migration, after dbmig001 Phase 3 |
| 3 | Update tests per the test rows' documents | Pending | — | — | Covered by rows 05-11 documents |
| 4 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-001 (single task-SQL owner), REQ-002 (remove zero-caller lookups), REQ-003 (rename key)
- **Source issue**: issues/20261030-105723_wftaskapi001_consolidate-task-persistence.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-113553_wftaskapi001_consolidate-task-persistence.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-125133
- **Related target files**: scripts/agent/workflow/task_ops.py
