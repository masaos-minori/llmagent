## Goal

Make `scripts/agent/workflow/task_ops.py` the single owner of workflow task persistence (row mapping, lookup, status update, aggregates) and rename the task key `idempotency_key` to `task_nonce` (new) (Plan REQ-001, REQ-002, REQ-003).

## Scope

- Canonical task SQL: keep `create_task`, `update_task_status`, `get_task_by_id`, `_row_to_task`; add `get_task_count` and `get_workflow_count` moved from `StateStore` (REQ-001).
- Delete `get_task_by_idempotency_key`, `get_task_by_session`, `get_latest_task`, `list_tasks` after the Phase 1 zero-caller re-check (REQ-002).
- Rename the `idempotency_key` field/parameter/row-mapping use to `task_nonce` (new) (REQ-003).

## Assumptions

- Canonical owner = `task_ops` (Plan UNK-01 default; production already imports it at `scripts/agent/workflow_engine_adapter.py`).
- Plan overlap judgments (`tools/check_plan_target_overlaps.py`, re-read 2026-11-01): `state_store.py` and `test_workflow_engine.py` with toolexec001 are compatible; `schema_sql.py` with ragcorpus001 compatible; the `agent_04_03` paragraph is a sequencing dependency (docs row 11). wfrecovery001/wflease001 land after this Plan per its recommended order; their `migrations_workflow.py` rows land in registry order.
- Phase 1 caller search must return no non-test caller before the deletions land; stop and report otherwise (REQ-007).
- Migration ledger: `WORKFLOW_SCHEMA_VERSION` is `1.2.0`; this row only renames code-side uses; the version bump is rows 04/12 in landing order (next ledger code `3`).

## Design decisions

- `task_ops` functions stay module-level functions over `SQLiteHelper`; `StateStore` delegates (Plan Design: alternative (b) rejected as changing more call sites for no gain).
- Aggregate counts become module functions (`get_task_count(db, session_id)`, `get_workflow_count(db, session_id)`) mirroring the `StateStore` semantics at `state_store.py:210-223`.
- Renamed value keeps the same contract: UUID4, unique, never caller-derived; parameter/field name `task_nonce` (new) (Plan REQ-003).

## Alternatives considered

- Keeping `idempotency_key` name with a clarifying docstring: rejected by Plan REQ-003 (name states a guarantee it never gave).

## Implementation
### Target file
`scripts/agent/workflow/task_ops.py`

### Procedure
1. Rename the local key variable, INSERT column/value positions, `TaskRecord(...)` kwargs, and `_row_to_task` mapping from `idempotency_key` to `task_nonce` (new) (`:30,38,47,59,84`).
2. Delete `get_task_by_idempotency_key` (`:99-104`), `get_task_by_session` (`:107-114`), `get_latest_task` (`:116-125`), `list_tasks` (`:127-133`).
3. Add `get_task_count` and `get_workflow_count` module functions ported from `state_store.py:210-223` (same SQL, same return semantics).

### Method
Direct edit; no signature changes for surviving functions (`create_task`, `update_task_status`, `get_task_by_id` keep their parameters; only the docstring at `:21-28` is reworded to the nonce contract).

### Details
- `create_task` docstring must state: unique opaque nonce, not request deduplication; task identity remains `task_id`.
- Surviving callers today: `workflow_engine_adapter.py` (`create_task`, `get_task_by_id`), `state_store.py` (delegates `create_task` at `:51`), engine via `StateStore.update_task_status` (`workflow_engine.py:172-181`); aggregates' caller is `scripts/agent/session_persister.py` via `StateStore`.
- The cross-table diagnostics (`get_execute_attempt_count`, `get_artifact_uris`, `state_store.py:225,239`) stay in `StateStore` — do not move them.

## Compatibility considerations

- Deleted APIs have no production caller (Plan Background, re-verified 2026-11-01); tests referencing them are updated in rows 05/06.
- `TaskRecord` field rename pairs with the DDL rename in row 04 and the migration in row 12: rows 01-04 and 12 must land in one release unit (version guards in `create_schema.py` / `workflow_schema.py` reject a half-renamed database).

## Security considerations

- No new attack surface; the UNIQUE constraint stays a backstop against key-derivation regressions (unchanged contract).

## Rollback considerations

- Phase 2 (canonicalization) and Phase 3 (rename) are separate commits, independently revertable per Plan phases; a rename revert needs the paired DDL/migration revert (rows 04/12), which is why they ship as one release unit.

## Validation plan

- `uv run pytest tests/agent/workflow/ -v` and `uv run pytest tests/agent/test_orchestrator.py -v` (after rows 05-06 test updates).
- `rg "get_task_by_idempotency_key|get_task_by_session|get_latest_task|list_tasks" scripts tests tools docs deploy` → no definition or caller (AC-2).
- `rg "FROM tasks|UPDATE tasks|INSERT INTO tasks" scripts/agent/workflow` → only `task_ops.py` plus the two documented subselects (AC-1).
- Full sequence: `rules/toolchain.md` (ruff, mypy, lint-imports, bandit).

## Completion criteria

- `task_ops.py` is the only module with task CRUD/aggregate SQL; the four lookup APIs are gone; `rg` over `scripts/agent/workflow` shows only `task_nonce` (new) for the task key; behavior of `create_task`/`get_task_by_id`/`update_task_status` is unchanged for adapter and engine callers (AC-1, AC-2, AC-3).

## Out of Scope

- Attempt-operation dedup (`start_attempt`, `finish_attempt`, `count_attempts`) — Plan Out-of-Scope.
- `tool_call_state.idempotency_key` (toolexec001 transport key) — untouched.
- DDL, version bump, migration registration (rows 04/12); docs (rows 10/11).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-01 | 2026-11-01 | cycle 1 done (lookup APIs deleted, count functions added); rename sites deferred to cycle 2 cycle 2 rename applied (task_nonce contract in task_ops) |
| 2 | Add or update tests per Validation plan | Completed | 2026-11-01 | 2026-11-01 | cycle 1 test updates landed (rows 05/06) cycle 1+2 test updates landed (rows 05/06/09/12) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-01 | 2026-11-01 | cycle 1 validation passed; cycle 2 pending cycle 2 landed: full pytest suite 10869 passed, ruff/mypy/lint-imports/bandit/check_db_separation pass |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-11-01 | 2026-11-01 | out of scope: docs handled by rows 10/11/12 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Verification Notes (2026-11-01)
- Passed. Cites confirmed against `task_ops.py` (133 lines): rename sites
  `:30,38,47,59,84`, four lookup APIs `:99-133`, docstring `:1-9`.
- Correction: the schema-shape guards are
  `scripts/agent/services/workflow_schema.py:100-119` and
  `scripts/db/create_schema.py:54-77`; no `scripts/db/workflow_schema.py`
  exists. Count functions port from `state_store.py:210-223`.
- Cycle split (shared row plan 01/02/05/06): lookup-API deletion and count
  additions run in cycle 1 (no schema contact); the `idempotency_key` →
  `task_nonce` rename in this file (all five sites plus the docstring) runs
  in cycle 2 as one commit with rows 03/04/12 and row 06's engine kwarg.

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-001` (canonical task persistence), `REQ-002` (delete zero-caller lookups), `REQ-003` (rename to `task_nonce` (new))
- **Source issue**: issues/20261030-105723_wftaskapi001_consolidate-task-persistence.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-113553_wftaskapi001_consolidate-task-persistence.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261101-140834
- **Related target files**: scripts/agent/workflow/task_ops.py