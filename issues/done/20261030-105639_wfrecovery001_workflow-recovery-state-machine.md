# Make workflow task and attempt persistence a validated, transactional state machine

## Priority
High

## Summary
Replace the unconstrained task-status writes, the per-process attempt counter, and the ambiguous `processed_events` marker with one transactional persistence contract. Task and attempt transitions are validated, attempt numbers are persisted and monotonic per task-stage pair, and only a completed attempt may suppress a stage.

## Background
Source: `memo-issue.md` entry H-01 (consolidating H-01..H-04, L-01, L-02, L-04; the memo contains this entry twice, verbatim; it is treated as one). Claims were re-checked against current source on 2026-10-30 (evidence labels per `skills/DESIGN.md`):

- Confirmed: `begin_stage_if_new()` in `scripts/agent/workflow/idempotency_ops.py` inserts the attempt row and the `processed_events` row in one `begin_immediate()` transaction and returns `None` when the event ID exists. Its docstring says the table holds events that were started, not completed.
- Confirmed: `StateStore.recover_stale_attempts()` in `scripts/agent/workflow/state_store.py` only runs `UPDATE attempts SET status='failed' ... AND status='running'`. It never touches `processed_events`, although the `begin_stage_if_new()` comment says recovery "removes their event IDs". The comment and the code disagree.
- Confirmed: `WorkflowEngine._run_stage_with_retry()` in `scripts/agent/workflow/workflow_engine.py` starts `attempt = 0` in memory on every call. The event ID is `{task_id}:{stage_id}:{attempt}`, so a re-run of the same task reuses `...:1`, and `_run_stage()` returns without running the stage when that marker exists.
- Confirmed: `WorkflowEngine.run()` calls `update_task_status(task_id, "running")` unconditionally and `"completed"` after the three stages return, with no check of the prior status. `update_task_status()` (in `task_ops.py` and `StateStore`) takes any string and ignores the row count.
- Confirmed: `attempts` and `processed_events` in `scripts/db/schema_sql.py` (`_WORKFLOW_SCHEMA`) have no `CHECK` on status, no `attempt_number` column, and no link from `processed_events` to `attempt_id`. `artifacts` already has `attempt_number`.
- Confirmed: `start_attempt()` (`attempt_ops.py` and `StateStore`) inserts a `running` attempt without any event marker. Production code does not call it (`rg start_attempt scripts` finds only the definitions); only tests in `tests/agent/workflow/` call it. `finish_attempt()` accepts any status string.
- Corrected against the memo: the only resume entry is the `existing_task_id` parameter of `WorkflowEngineAdapter.execute_turn()` / `_init_workflow_task()` in `scripts/agent/workflow_engine_adapter.py`, and `Orchestrator._execute_turn()` calls `execute_turn(line, turn_started_at, "")` without it. No production caller passes `existing_task_id` (`rg existing_task_id scripts` outside the adapter: no hits). So the crash-then-resume chain described in the memo is reachable only through that parameter, which is currently unused. The adapter's own resume guard only rejects `halted`; a `completed` or `running` task is accepted.
- Confirmed (docs, read 2026-10-30): the current documents state the semantics this issue changes. `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` "Workflow State Semantics" says workflow state means "started" (not "completed"). Accepted ADR `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` INV-08 fixes the key `{task_id}:{stage_id}:{attempt}` with the attempt number incremented per retry, and INV-07 fixes startup recovery of interrupted attempts as `failed`. The same agent_03_03 "Resuming Existing Tasks" section documents `existing_task_id` and a guard that rejects only `halted`, so the document treats resume as an existing feature even though no production caller uses it.
- Corrected against the memo: the engine counts attempts in memory only for retryable stages (`execute`). `plan` and `verify` (`config/workflows/default.json`: `retryable: false`) call `_run_stage(..., attempt=1)` and always use `...:1`.

- Adversarial verification (issue-to-plan Step 2, 2026-10-30): the status vocabulary matches production use. Code under `scripts/agent/` writes only `pending` (at creation), `running`, `completed`, `failed`, and `halted` to `tasks`; `cancelled` is an adapter exit reason that is stored as `halted`; no `pending_approval` status exists in `scripts/`. Blast radius in `tests/` (`rules/toolchain.md` Impact-radius check): `StateStore` 84 references in 7 files, `processed_events` 12 in 5 files, `update_task_status` 17 in 2, `recover_stale_attempts` 18 in 2, `WorkflowHaltError` 28 in 3; this exceeds the rule-of-thumb threshold, so test updates are budgeted as part of the same unit of work.
- Adversarial verification: SQLite cannot add a `CHECK` constraint to an existing table with `ALTER TABLE`, so the constraint needs a table rebuild inside the migration; `ADD COLUMN` for `attempt_number` is possible but cannot carry a `NOT NULL` without a default, and existing rows need a backfill. `SQLiteHelper.begin_immediate()` (`BEGIN IMMEDIATE ... COMMIT`, default `busy_timeout` 30000 ms) is the existing writer-serialization primitive. `deploy/init_db.sh` checks table presence only (`REQUIRED_WORKFLOW_TABLES`), so adding columns does not affect it.
- Adversarial verification, transition matrix (Step 2, second finding): today's code uses edges a strict matrix must either allow or replace. `WorkflowEngineAdapter.execute_turn` writes `halted` while the task is still `pending` (turn-entry preparation failure, `workflow_engine_adapter.py:204`, before `engine.run` writes `running`), and `_record_exit_status` writes `failed` after the engine already wrote `completed` when the execute stage returned an `error_kind` (`_status_for_exit`, `workflow_engine_adapter.py:49-59`). The matrix therefore needs `pending -> halted` and, until `issues/20261030-105723_wfretry001_timeout-retry-failure-propagation.md` removes the overwrite, a transitional `completed -> failed` edge.
- Adversarial verification, crash-left tasks: if `running` tasks are rejected by the resume path, a task left `running` by a crashed process can never be claimed again, because `recover_stale_attempts` changes attempts only and `agent_03_03` states it never changes task status. Recovery must either also move the owning task `running -> failed` in the same transaction, or the contract must name another way back; this is an owner decision recorded under Unresolved Questions.
- Adversarial verification, correlation: the `stage_completed` audit event (`scripts/agent/tool_audit.py:124-147`) carries `task_id`, `stage_id`, and `workflow_id` but no attempt number, and the `attempt_id` that the adapter passes to the LLM runner is `ctx.turn.current_turn_id` (a turn ID, not `attempts.attempt_id`; required non-empty at `llm_turn_runner.py:72`). The acceptance criterion on correlating audit records by attempt number therefore needs `tool_audit.py` and the adapter in scope. `tests/agent/test_repl_health.py:540-590` builds minimal workflow tables and asserts the required-table check, so changing `REQUIRED_WORKFLOW_TABLES` columns changes that fixture; `tests/deploy/test_setup_services_eventbus.py:126` only needs the `processed_events` table to exist.

## Problem
The persisted state cannot express or enforce the intended lifecycle:

- A stale `running` attempt becomes `failed` but its `processed_events` row stays, so any later run of the same task and stage that reaches attempt number 1 is skipped as "already processed" with no completed attempt behind it, and the task can still end as `completed`.
- The retry budget (`max_attempts`) and attempt numbering live only in a local variable, so they reset on every call.
- Status values and transitions are not validated by code or by the database; a zero-row update is silent.
- Two public attempt-start paths exist, only one of which is idempotent.

## Reason for Change
This is a correctness and durability defect in the persistence contract, independent of whether the resume entry is used today. The unconditional `running`/`completed` writes and the free-form status strings are reachable in the normal path now; the skipped-stage chain becomes reachable as soon as any caller supplies `existing_task_id` (or any future retry/resume feature is added). Fixing the contract before a resume caller exists is cheaper than discovering the gap after one does. Timing is not otherwise urgent.

## Implementation Intent
- Define one vocabulary and transition matrix for task status (`pending`, `running`, `completed`, `failed`, `halted`) and attempt status (`running`, `completed`, `failed`), shared by application code and database `CHECK` constraints.
- Keep one canonical persistence API for task transitions and attempt lifecycle. Every transition is a conditional update on the expected current state and raises a typed error when zero rows change.
- Persist `attempt_number`, allocate it inside the same write transaction as the attempt insert, and derive both the retry budget and the event ID from the persisted maximum.
- Make `processed_events` mean "completed" (a completed-stage ledger), or fold it into the attempt row; choose one and remove the started-event meaning. Only a completed attempt may suppress a stage.
- Recover a stale attempt and any marker it owns in one transaction.
- Decide the resume contract for `pending`, `running`, `failed`, `halted`, and `completed` tasks in one place, and enforce it in that place rather than in the adapter alone.
- Preserve the existing audit and artifact behavior; `artifacts.attempt_number` already exists and is the correlation key to extend.

## Target Files or Areas
- `scripts/agent/workflow/models.py`
- `scripts/agent/workflow/attempt_ops.py`
- `scripts/agent/workflow/idempotency_ops.py`
- `scripts/agent/workflow/task_ops.py`
- `scripts/agent/workflow/state_store.py`
- `scripts/agent/workflow/workflow_engine.py`
- `scripts/agent/workflow/artifact_ops.py`
- `scripts/agent/workflow_engine_adapter.py` (resume guard only)
- `scripts/db/schema_sql.py` (`_WORKFLOW_SCHEMA`, `WORKFLOW_SCHEMA_VERSION`)
- `scripts/agent/tool_audit.py` (`audit_stage_completed`: add the attempt number)
- `scripts/agent/services/workflow_schema.py` (`REQUIRED_WORKFLOW_TABLES`, the startup schema check that must stay consistent with the new columns)
- `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` (INV-07, INV-08, and the INV-07 test-citation row)
- `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` ("Workflow State Semantics", "Resuming Existing Tasks", "Startup Recovery")
- `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md` (StateStore scope; `begin_stage_if_new` description)
- `tests/agent/workflow/`, `tests/agent/test_orchestrator.py` (status-write and audit assertions), `tests/agent/test_repl_health.py` (workflow-table fixtures)

## Required Changes
- Add `TaskStatus` and `AttemptStatus` enums and a transition table; replace the free-text status comments in `models.py`.
- Add `CHECK` constraints for both status columns and an `attempt_number` column (unique per task-stage pair) to the workflow schema, through the migration path chosen in Dependencies.
- Link each event marker to its attempt (attempt ID and number), and redefine `processed_events` semantics as chosen above.
- Allocate `attempt_number` transactionally; make the engine start from the persisted maximum and enforce `max_attempts` against it.
- Route `begin_stage_if_new()`, `start_attempt()`, and recovery through one attempt-start / attempt-finish implementation; remove or privatize the bypass `start_attempt()`.
- Restrict `finish_attempt()` to terminal statuses and fix its docstring ("Mark an attempt as completed" is inaccurate).
- Make stale recovery update the attempt and its marker in one transaction, and keep it idempotent on repeat.
- Replace the unconditional `running`/`completed` writes in `WorkflowEngine.run()` with expected-state transitions; reject resume of `completed` and `running` tasks and of `halted` tasks per the decided contract.
- Raise explicit not-found and transition-conflict errors for zero-row updates.
- Expose the persisted attempt number to the adapter and add it to the `stage_completed` audit event so audit, attempt, marker, and artifact rows share (task, stage, attempt number).
- Correct the comments in `idempotency_ops.py` and `state_store.py` to match the implemented semantics.
- Amend ADR-001 INV-08 (event key and "started" versus "completed" meaning) and, if the recovery semantics change, INV-07, following the ADR change protocol (`docs/00_governance/governance_01_documentation-policy.md`, `governance_05_change-impact-and-dependency-graphs.md`); keep the INV-07 test-citation row accurate.
- Rewrite the three documentation sections listed under Documentation Impact so none still describes started-event semantics or an unconditional resume guard.

## Constraints
- Fail-closed and audit behavior must not weaken.
- `workflow.sqlite` schema changes must use the forward-only migration mechanism, not ad-hoc DDL and not silent recreation (see Dependencies).
- Retained databases may contain rows that violate the new constraints (for example attempts left `running`, or markers without a completed attempt); the migration must define their handling and have a rollback procedure.
- Import-layer contract in `skills/DESIGN.md` Shared Vocabulary applies; `db/helper.py` transaction behavior (`begin_immediate`) is the locking primitive in use.

## Acceptance Criteria
- A task-stage whose latest attempt is not `completed` is never skipped, including after stale recovery, verified by a test that creates a `running` attempt with its marker, runs recovery, and re-runs the stage.
- Attempt numbers per task-stage pair are strictly increasing across engine restarts, and the retry budget counts persisted attempts.
- An invalid task or attempt status, and an invalid transition, is rejected by the application API and, when written with raw SQL, by the database.
- A zero-row task or attempt update raises a typed error instead of returning silently.
- Two concurrent claims of the same task, or of the same task-stage attempt number, result in exactly one winner.
- Repeating stale recovery any number of times yields the same final state.
- `completed` and `running` tasks are rejected by the resume path; `failed` tasks resume with a new attempt number; the `halted` and `pending` behavior matches the documented contract.
- Attempt, event marker, and artifact rows for one execution can be joined by task, stage, and attempt number.
- No production or test caller uses an attempt-start path that bypasses the canonical transaction.

## Testing Expectations
- Regression tests, each failing before the change: crash after the attempt row and marker are written; crash after a side effect but before the attempt is finished; repeated restart and recovery; resume after one or more failed attempts; resume of completed, halted, and running tasks.
- A two-connection concurrency test for task claim and attempt-number allocation (separate `SQLiteHelper` connections to one file).
- Invalid-status and zero-row-update tests at both the API and raw-SQL level.
- Migration tests against a database with valid rows and one with rows that violate the new constraints.
- Update `tests/agent/workflow/test_workflow_state_store.py` and `tests/agent/test_orchestrator.py` where they assume the free-form status writes.
- Run the sequence in `rules/toolchain.md`, plus `uv run python tools/check_db_separation.py` (schema DDL changes).
- Docs checkers per `routing.md` Tools: `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_consistency.py --domain agent`, and `check_docs_japanese.py`; `check_needs_confirmation_inventory.py` if a Needs Confirmation marker is added.
- `uv run python tools/check_adr_preservation.py`: ERROR on INV-07/INV-08 text is expected for the intended amendment; the PR must explain each reported change and no other decision may change.

## Documentation Impact
Yes. Intent, boundaries, and failure behavior only; no code or DDL restatement (`skills/DESIGN.md` "Avoid implementation-reference duplication", "Docs content policy — remove").

- `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`: amend INV-08 and, if needed, INV-07 (Accepted ADR; change protocol applies).
- `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`: replace "Workflow State Semantics" (currently "started", not "completed"); update "Resuming Existing Tasks" to the decided resume contract per task status; update "Startup Recovery" if recovery now also resolves event markers.
- `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md`: update the `StateStore` scope paragraph and the `begin_stage_if_new` bullet if the attempt-start path or its guarantee changes.
- Checked and not affected unless a table is added or renamed: `docs/41_db/db_02_architecture_and_schema-schema-reference.md` section 7 names the tables only (no status or attempt columns); `docs/90_deployment/deployment_01_deployment.md` lists table names only. The "recreate the database" recovery sentence in db_02 is owned by `plans/20261029-214108_dbmig001_forward-only-db-migrations.md`.
- Record the resume contract as a Needs Confirmation item if the owner has not settled it (register per `routing.md` Tools).

## Out of Scope
- Stale-attempt detection by timestamp, worker identity, or lease (separate issue, see Dependencies).
- Timeout retry policy and failure propagation to the turn result (separate issue).
- Consolidating the duplicated `StateStore` / `task_ops` implementations and the `idempotency_key` naming (separate issue), beyond what this change must touch.
- MCP tool-call idempotency.
- Adding a user-facing resume feature.

## Dependencies
- Depends on `plans/20261029-214108_dbmig001_forward-only-db-migrations.md` (migration framework and ledger for `workflow.sqlite`); this issue's schema changes must be registered there. That plan is in flight and no migration module exists under `scripts/db/` yet, so the schema part cannot land first.
- Shares `scripts/db/schema_sql.py` with `plans/20261029-233524_toolexec001_idempotent-tool-call-snapshot.md` (new workflow tables); both register steps through dbmig001, so order them by migration step.
- Should follow `plans/20261030-113553_wftaskapi001_consolidate-task-persistence.md` (its issue is archived as `issues/done/20261030-105723_wftaskapi001_consolidate-task-persistence.md`), which makes `task_ops` the single owner of task CRUD; otherwise the transition validation is written twice. Related, not blocking: `issues/20261030-105723_wflease001_stale-attempt-lease.md` (lease fields on the same attempt rows) and `issues/20261030-105723_wfretry001_timeout-retry-failure-propagation.md` (retry budget and failure kinds use this issue's status and attempt contract).
- Shares `docs/10_adr/` editing with `plans/20261029-214108_dbmig001_forward-only-db-migrations.md` (ADR-008) and `plans/20261029-214650_adrauth001_adr-authority-model.md` (`docs/10_adr/adr_01_index.md`); this issue edits ADR-001 only and does not touch the index table. Re-check the adrauth001 plan for any primary-claim registration of ADR-001 invariants before editing (not verified).
- Related closed work that must not regress: `issues/done/20261021-093421_turn003_task-status-overwritten-after-failure.md` (adapter must not overwrite the engine's status).

## Unresolved Questions
- 不明: whether resuming an existing task is a supported feature. No production caller passes `existing_task_id`. If it is not planned, the owner may prefer removing the parameter and narrowing this issue to the validation, atomicity, and attempt-number parts.
- 不明: whether stale recovery should also move the owning `running` task to `failed` so it becomes resumable (see the crash-left tasks finding); default assumed in the plan: yes.
- 不明: whether `failed` tasks are meant to be resumable at all, and whether `halted` tasks are terminal (the adapter treats `halted` as non-resumable; the memo lists `halted` as a resume case).
- 不明: choice between a completed-event ledger and a status-bearing attempt ledger for `processed_events`. Either choice changes the meaning fixed by ADR-001 INV-08, so the choice is recorded with its compatibility impact in the plan.
- 不明: whether the raw-SQL status seeds in `tests/agent/workflow/test_workflow_state_store.py` (INSERT statements around lines 105, 264, 268, 416, 430) all use the five-status vocabulary; they must satisfy the new `CHECK` constraints.
- Resolved by verification (2026-10-30): `config/adr_authority.toml` does not exist yet (it is created by the adrauth001 plan), so no registry entry needs changing now; re-check when that plan lands.
- Assumption: concurrent workers on one `workflow.sqlite` are possible (the memo requires it); the deployment model for multiple agent processes is not confirmed from the files read.

## AI Implementation Instruction
- Read all affected source, schema, migration, and test files before editing; do not invent behavior the owner has not decided (see Unresolved Questions) — stop and report the missing decision.
- Keep one source of truth for statuses and transitions; do not duplicate the matrix between Python and SQL by hand without a test that keeps them equal.
- Keep the change limited to the files in Target Files or Areas; do not refactor unrelated code.
- Write regression tests first and confirm they fail before the implementation change.
- Do not close with documentation-only changes while a listed defect remains.
- Report changed files, migration effects, commands run, and test results.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261030-105639
- **Related target files**: `scripts/agent/workflow/models.py`, `scripts/agent/workflow/attempt_ops.py`, `scripts/agent/workflow/idempotency_ops.py`, `scripts/agent/workflow/task_ops.py`, `scripts/agent/workflow/state_store.py`, `scripts/agent/workflow/workflow_engine.py`, `scripts/agent/workflow/artifact_ops.py`, `scripts/agent/workflow_engine_adapter.py`, `scripts/db/schema_sql.py`, `scripts/agent/services/workflow_schema.py`, `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`, `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`, `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md`
