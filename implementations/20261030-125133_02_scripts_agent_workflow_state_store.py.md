## Goal

Remove the duplicated task SQL from `StateStore` so `task_ops` is the only owner (`REQ-001`, single task-SQL owner), and delete the lookup methods that have no caller (`REQ-002`, zero-caller removal), keeping thin delegates only where a production or test caller exists.

## Scope

- Modify only `scripts/agent/workflow/state_store.py`.
- Attempt methods (`start_attempt`, `finish_attempt`, `count_attempts`) and recovery are out of scope here.

## Assumptions

- Plan Dependencies (`plans/20261030-113553_wftaskapi001_consolidate-task-persistence.md` Scope): this row has no schema dependency and may run before the rename gate; it requires the `task_ops` count functions from row 01 (`get_task_count` (new) and `get_workflow_count` (new) in `task_ops`, created by that document's Step 1; they exist when `code-implementation` executes the rows in `seq` order).
- Plan overlap judgments (Step 8b): `state_store.py` is also a target of `plans/20261029-233524_toolexec001_idempotent-tool-call-snapshot.md` (adds tool-call state helpers) and `plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md` (attempt methods, recovery): compatible / sequencing, different methods; whichever lands first, the others rebase.
- Caller facts (checked in this cycle): production callers of `StateStore` task methods are `update_task_status` (`workflow_engine.py:121-132`, `workflow_engine_adapter.py:204,235`), `get_task_count` and `get_workflow_count` (`session_persister.py:92-93`); tests call `create_task` and the two counts. `get_task_by_id`, `get_task_by_idempotency_key`, `get_task_by_session`, `get_latest_task`, `list_tasks`, and `_row_to_task` on `StateStore` have no caller.

## Design decisions

- Keep delegates for exactly `create_task`, `update_task_status`, `get_task_count`, and `get_workflow_count`; delete the rest (Plan Implementation Intent: delegates only for methods a caller needs).
- The cross-table diagnostics `get_execute_attempt_count` and `get_artifact_uris` stay as they are; their `tasks` subselects (`:201`, `:209` region) are the allowed exception in the Plan's AC-1.

## Alternatives considered

- Delete every `StateStore` task method: rejected, the engine, adapter, `session_persister`, and tests call four of them.

## Implementation

### Target file

`scripts/agent/workflow/state_store.py`

### Procedure

1. Replace the bodies of `update_task_status` (`:61`), `get_task_count` (`:177`), and `get_workflow_count` (`:184`) with calls to the corresponding `task_ops` functions, passing `self._db`.
2. Delete `_row_to_task` (`:69`), `get_task_by_id` (`:84`), `get_task_by_idempotency_key` (`:91`), `get_task_by_session` (`:98`), `get_latest_task` (`:106`), and `list_tasks` (`:116`).
3. Extend the existing import of `create_task` from `agent.workflow.task_ops` with the functions now used, and remove imports that become unused (`sqlite3`, and `TaskRecord` only if no remaining annotation needs it).
4. Check that `_scalar_count` is still used by the attempt and artifact diagnostics; if the two count methods were its only users, keep it only if `get_execute_attempt_count` still calls it (it does).

### Method

- Each delegate keeps its current public signature and return type, so `session_persister` and the tests need no change.
- Re-run `rg "FROM tasks|UPDATE tasks|INSERT INTO tasks" scripts/agent/workflow`: the only `state_store.py` matches left are the two documented cross-table subselects.

### Details

- `create_task` already delegates (`:49`); leave it.
- Do not touch `start_attempt`, `finish_attempt`, `count_attempts`, `find_stale_running_attempts`, or `recover_stale_attempts`.
- Keep the class docstring accurate: it describes a facade over `workflow.sqlite`.

## Compatibility considerations

- Public surface shrinks by six methods with no caller; the four kept methods behave identically.
- `StateStore` has 84 references in 7 test files (Plan blast radius), but those calls target kept methods or attempt and diagnostic methods; run the whole `tests/agent/workflow/` suite.

## Security considerations

- N/A: no new input boundary; SQL moves to parameterized `task_ops` functions.

## Rollback considerations

- N/A: revert the commit (no schema or persisted-data change).

## Validation plan

- `uv run pytest tests/agent/workflow/ tests/agent/test_orchestrator.py -v`
- `rg "FROM tasks|UPDATE tasks|INSERT INTO tasks" scripts/agent/workflow` (only `task_ops.py` and the two documented subselects)
- `uv run ruff format scripts/agent/workflow/state_store.py`, `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports`
- `uv run python tools/check_module_size.py`

## Completion criteria

- `StateStore` defines the four kept delegates and none of the six removed methods.
- `state_store.py` contains no task row mapping, lookup, update, or count SQL.
- The `tests/agent/workflow/` and `tests/agent/test_orchestrator.py` suites pass.

## Out of Scope

- `task_ops.py`, `models.py`, DDL, tests, docs rows.
- Attempt, recovery, and ledger changes (wfrecovery001 and wflease001 Plans).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delegate the four kept methods; delete the six unused methods; fix imports | Pending | — | — | After row 01 Step 1 |
| 2 | Update tests per the test rows' documents | Pending | — | — | Covered by rows 05-11 documents |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-001 (single task-SQL owner), REQ-002 (remove zero-caller lookups)
- **Source issue**: issues/20261030-105723_wftaskapi001_consolidate-task-persistence.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-113553_wftaskapi001_consolidate-task-persistence.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-125133
- **Related target files**: scripts/agent/workflow/state_store.py
