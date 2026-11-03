# Consolidate workflow task persistence behind one implementation and name the task key accurately

## Priority
Low

## Summary
Task row mapping, lookup, listing, and status update exist twice (`task_ops.py` and `StateStore`), and `tasks.idempotency_key` is a random UUID that does not deduplicate anything. Make one module own task CRUD and give the key a name that matches its guarantee.

## Background
Source: `memo-issue.md` entry L-01 (consolidating M-06 and L-03). Re-checked against current source on 2026-10-30:

- Confirmed: `scripts/agent/workflow/state_store.py` re-implements `update_task_status`, `_row_to_task`, `get_task_by_id`, `get_task_by_idempotency_key`, `get_task_by_session`, `get_latest_task`, and `list_tasks` with the same SQL as the module functions in `scripts/agent/workflow/task_ops.py`. Only `create_task` is delegated.
- Confirmed: `scripts/agent/workflow/task_ops.py` `create_task()` sets `idempotency_key = str(uuid.uuid4())`, independent of the caller; its docstring already states the key is an opaque generated identifier and that the UNIQUE constraint is inert.
- Confirmed: `get_task_by_idempotency_key`, `get_task_by_session`, `get_latest_task`, and `list_tasks` have no caller under `scripts/` (both the `task_ops` and `StateStore` versions); only `tests/agent/workflow/` calls the key lookup. Production uses `task_ops.create_task`, `task_ops.get_task_by_id`, and `StateStore.update_task_status`.
- Confirmed: the key column is documented in `docs/41_db/db_02_architecture_and_schema-schema-reference.md` and `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md` under the name `idempotency_key`. The EventBus `idempotency_key` (`scripts/eventbus/app.py`) is a separate concept and is not in scope.
- Related closed work: `issues/done/20261021-093421_turn001_task-idempotency-key-collides-across-restarts.md` removed the derived key (restart collision) and `issues/done/20261024-105743_workflow001_state-store-create-task-duplicates-the-composite-idempotency-key.md` removed the second derivation in `StateStore.create_task`. Neither renamed the field or removed the duplicated read/update methods.

- Adversarial verification (issue-to-plan Step 2, 2026-10-30): none of `get_task_by_session`, `get_latest_task`, `list_tasks`, or `get_task_by_idempotency_key` appears in `docs/`, so documentation impact is limited to the key paragraph and the `get_task_by_id` mention already listed. `TaskRecord` has 2 references in 1 test file; `StateStore` has 84 references in 7 test files, so the `StateStore` methods are kept as thin delegates where tests call them rather than removed.

- Adversarial verification (Step 2, second finding): raw `INSERT INTO tasks (... idempotency_key ...)` statements exist in `tests/agent/workflow/test_workflow_state_store.py` (lines 105, 264, 416, 466, 509) and `tests/agent/workflow/test_workflow_stage_persistence.py:29`; `tests/db/test_create_schema.py` holds a copy of the `tasks` DDL (line 359) and a test named `test_tasks_idempotency_key_unique` (line 495); `test_workflow_models.py:25` constructs `TaskRecord(idempotency_key=...)`. A rename therefore touches these files, not only the three the first draft listed. `scripts/db/create_schema.py` and `scripts/agent/services/workflow_schema.py:114` refuse a database whose recorded `WORKFLOW_SCHEMA_VERSION` differs, so bumping the version without a registered migration makes a retained database fail startup.

## Problem
- Any change to task validation, schema, or transition rules must be made in two places, and the two copies can diverge silently (the closed `workflow001` issue is an example of exactly that).
- The name `idempotency_key` implies caller-request deduplication that does not exist; the only protection is the docstring.
- Several lookup APIs have no production caller.

## Reason for Change
The state-machine work in `issues/20261030-105639_wfrecovery001_workflow-recovery-state-machine.md` adds transition validation to task updates. Doing that against two copies would write it twice. Timing: it should be settled before or together with that issue; independent of it the risk is maintenance only, hence Low.

## Implementation Intent
- Keep one task-persistence implementation (the `task_ops` module functions or a `StateStore`-owned repository; choose one) and make the other a thin delegate or remove it. Row-to-model conversion, validation, and error mapping live in that one place.
- Decide whether task creation needs caller-request deduplication. If no caller needs it (none exists today), rename the column and field to describe a unique nonce or row identity; if it is needed, accept a caller-stable key and define duplicate-creation behavior.
- Remove lookup APIs with no verified caller, or keep them only with a named caller.
- Preserve external behavior of `create_task`, `get_task_by_id`, and `update_task_status` as used by the adapter and engine.

## Target Files or Areas
- `scripts/agent/workflow/task_ops.py`
- `scripts/agent/workflow/state_store.py`
- `scripts/agent/workflow/models.py` (`TaskRecord.idempotency_key`)
- `scripts/db/schema_sql.py` (`tasks.idempotency_key`, `WORKFLOW_SCHEMA_VERSION`), only if the column is renamed
- `scripts/agent/workflow_engine_adapter.py`, `scripts/agent/workflow/workflow_engine.py` (call sites)
- `tests/agent/workflow/test_workflow_state_store.py`, `tests/agent/workflow/test_workflow_engine.py`, `tests/agent/workflow/test_workflow_stage_persistence.py`, `tests/agent/workflow/test_workflow_models.py`, `tests/db/test_create_schema.py` (corrected: `tests/agent/workflow/test_state_store.py` has no task-key reference and is not a target)
- `docs/41_db/db_02_architecture_and_schema-schema-reference.md` (section 7, task-key paragraph), `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md` ("StateStore Responsibility Scope" and the "fresh, unique task keys" bullet)

## Required Changes
- Run a repository-wide caller search (`scripts/`, `tests/`, `tools/`, `docs/`) for each duplicated method and for `idempotency_key` on tasks, and record the result in the PR.
- Make one implementation canonical; delegate or delete the duplicate methods and the duplicate `_row_to_task`.
- Record the decision on task-request deduplication, and either rename the key (schema, model, callers, tests, docs) or add validated caller-stable key handling with defined duplicate behavior.
- Delete the lookup APIs without a caller, and the tests that only exercise them, unless a caller is identified.
- Update the task-key paragraph in db_02 section 7 and the two agent_04_03 passages, which today describe `idempotency_key` as a UUID4 backstop and name `get_task_by_id`; they must follow the rename or the kept key, and state the difference between task identity, task-request deduplication, and stage-event idempotency.

## Constraints
- A column rename is a `workflow.sqlite` schema change and must go through the forward-only migration mechanism (see Dependencies); it must not be done by recreating the database.
- Do not change the task status vocabulary or transition rules here; that belongs to the state-machine issue.
- Deprecated symbols follow the deletion rule in `rules/coding.md` (Deprecation policy: zero-caller `rg` re-check).

## Acceptance Criteria
- Exactly one implementation of each task read/update operation exists under `scripts/agent/workflow/`; the other layer contains no SQL for tasks.
- A schema or transition change to tasks requires editing one module.
- The task key's name or documented contract matches its behavior, and the duplicate-creation behavior is stated and tested (either deduplicates by caller key or creates distinct rows).
- `rg` over `scripts/` finds no task lookup API without a caller.
- Existing adapter and engine tests pass unchanged except for renames.

## Testing Expectations
- Behavioral tests through the canonical API for create, get, update, session listing (if kept), and the chosen duplicate-creation behavior.
- If the column is renamed: migration test on a database containing existing rows.
- `uv run pytest tests/agent/workflow/ tests/agent/test_orchestrator.py`, then the sequence in `rules/toolchain.md`; `uv run python tools/check_db_separation.py` if DDL changes.
- Docs checkers per `routing.md` Tools: `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_consistency.py --domain agent`, and `check_docs_japanese.py`; `check_needs_confirmation_inventory.py` if a Needs Confirmation marker is added.
- `uv run python tools/generate_reference_table.py --check` (code under `scripts/agent/` changed; refresh with `--type agent` if it drifts).

## Documentation Impact
Yes, narrowly (intent and boundaries only; no code restatement per `skills/DESIGN.md`):

- `docs/41_db/db_02_architecture_and_schema-schema-reference.md` section 7 and `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md` (StateStore scope, task-key bullet): state the key's contract after the decision, and the identity / request-deduplication / stage-event idempotency distinction. Both currently describe the UUID4 key and `get_task_by_id` reuse.
- Checked, not affected (corrected from the first draft): `docs/23_agent/agent_13_reference-api-generated.md` mentions `idempotency_key` only as an `audit_tool_exec` parameter and lists none of the task APIs, so it is not a target; the generator drift check stays as a gate (baseline `No drift found`, 2026-10-30).
- `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` INV-08 uses the stage event key, not the task key, so it is unaffected.

## Out of Scope
- Transition validation, attempt numbering, recovery semantics (`issues/20261030-105639_wfrecovery001_workflow-recovery-state-machine.md`).
- The EventBus `idempotency_key` and the MCP tool-call `X-Idempotency-Key`.
- Attempt-operation duplication in `StateStore` (`start_attempt`, `finish_attempt`, `count_attempts`); that is handled by the state-machine issue.

## Dependencies
- Blocks (recommended order): `issues/20261030-105639_wfrecovery001_workflow-recovery-state-machine.md` should follow this issue, or take the canonical-module decision from it.
- If the column is renamed: depends on `plans/20261029-214108_dbmig001_forward-only-db-migrations.md` (migration framework).

## Unresolved Questions
- 不明: whether any external or planned caller needs caller-request deduplication for task creation; no such caller exists in `scripts/`. Default assumption if unanswered: no, so rename rather than add deduplication.
- 不明: which implementation the owner prefers as canonical (`task_ops` functions or `StateStore` methods).
- Assumption: the tests that call `get_task_by_idempotency_key` verify only the lookup and may be removed with it.

## AI Implementation Instruction
- Do the caller search first and stop to report if a caller outside `tests/` appears for an API proposed for removal.
- Do not decide the deduplication question silently; if it is still unresolved at implementation time, report it and use the rename path.
- Keep changes limited to task persistence; do not touch attempt, event, or status-transition logic.
- Report changed files, migration effects, commands run, and test results.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261030-105723
- **Related target files**: `scripts/agent/workflow/task_ops.py`, `scripts/agent/workflow/state_store.py`, `scripts/agent/workflow/models.py`, `scripts/db/schema_sql.py`, `scripts/agent/workflow_engine_adapter.py`, `scripts/agent/workflow/workflow_engine.py`, `tests/agent/workflow/test_workflow_state_store.py`, `tests/agent/workflow/test_workflow_engine.py`, `tests/agent/workflow/test_workflow_stage_persistence.py`, `tests/agent/workflow/test_workflow_models.py`, `tests/db/test_create_schema.py`, `docs/41_db/db_02_architecture_and_schema-schema-reference.md`, `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md`
