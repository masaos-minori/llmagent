# Plan: Make workflow task and attempt persistence a validated, transactional state machine

**Task Classification:** Path B (more than 3 files; changes the `workflow.sqlite` schema; changes the `StateStore` / engine / audit interfaces; adds a module). Path B analysis applied (`skills/issue-to-plan/workflow-path-b.md`); design choices recorded in `Design` per `workflow.md` Step 5 (decisions applied narrowly).

## Goal
- Replace the unconstrained task-status writes, the per-call attempt counter, and the started-event `processed_events` marker with one validated, transactional persistence contract: typed statuses and transitions, persisted monotonic attempt numbers, a completed-stage ledger that is the only thing allowed to suppress a stage, and atomic, idempotent stale recovery.

## Priority
High

## Scope
- **In-Scope**: `TaskStatus` / `AttemptStatus` and a transition matrix; typed errors; conditional task transitions and a task claim/resume contract; persisted `attempt_number` allocated in the same write transaction; completed-event ledger linked to attempts; `finish_attempt` limited to terminal statuses; removal of the bypass `start_attempt`; atomic idempotent recovery; engine use of persisted attempt numbers and budget; attempt number in the `stage_completed` audit event; `CHECK` constraints and new columns with a registered migration; startup column check; ADR-001 INV-07 / INV-08 amendment and two agent documents; regression, concurrency, and migration tests.
- **Out-of-Scope**: stale detection by timestamp, owner, or lease (`issues/20261030-105723_wflease001_stale-attempt-lease.md`); timeout retry policy and failure propagation (`issues/20261030-105723_wfretry001_timeout-retry-failure-propagation.md`); task-key rename and `StateStore` / `task_ops` consolidation (`plans/20261030-113553_wftaskapi001_consolidate-task-persistence.md`); MCP tool-call idempotency; adding a user-facing resume feature.
- **Dependencies**: (1) Phase 2 (schema and migration) depends on `plans/20261029-214108_dbmig001_forward-only-db-migrations.md` Phase 3 (workflow domain wiring); Phases 1, 3 (after Phase 2), 4, and 5 are ordered behind it as listed. (2) Should follow `plans/20261030-113553_wftaskapi001_consolidate-task-persistence.md` Phase 2 (task CRUD in `task_ops`); if it has not landed, Phase 1 puts the transitions in `task_ops` and adds no new `StateStore` task SQL. (3) Shared files with Frozen Plans: see Assumptions (`schema_sql.py`, `state_store.py`, `test_workflow_engine.py`, `agent_04_03_...md`). (4) Sibling issues `wflease001` and `wfretry001` follow this Plan: they reuse its attempt and status contract.

## Background
- `begin_stage_if_new()` (`scripts/agent/workflow/idempotency_ops.py:18`) inserts the attempt and the `processed_events` row in one `begin_immediate()` transaction and returns `None` when the event ID exists; its comment says the table holds started events and that recovery removes their IDs, but `recover_stale_attempts()` (`state_store.py:246`) only flips `running` attempts to `failed` (checked in Step 3).
- `WorkflowEngine._run_stage_with_retry()` (`workflow_engine.py:134-148`) starts `attempt = 0` in memory per call; the event ID is `{task_id}:{stage_id}:{attempt}` (`:208`). A re-run of the same task reuses `...:1` and the stage is skipped.
- `WorkflowEngine.run()` (`:108-132`) writes `running` unconditionally and `completed` after the stages; `update_task_status` takes any string and ignores the row count (`task_ops.py:66`, `state_store.py:61`).
- `workflow.sqlite` DDL (`schema_sql.py:172-214`) has no status `CHECK`, no `attempt_number` on `attempts`, and no link from `processed_events` to an attempt; `artifacts.attempt_number` exists.
- No production caller uses `start_attempt` (`attempt_ops.py:12`, `state_store.py:126`) or passes `existing_task_id` (`workflow_engine_adapter.py` is the only reference; `Orchestrator._execute_turn` calls `execute_turn(line, turn_started_at, "")`), so the skipped-stage chain is reachable only through that unused parameter (checked in Step 3).
- Current code uses transitions a strict matrix must allow or replace: `pending -> halted` on turn-entry preparation failure (`workflow_engine_adapter.py:204`) and `completed -> failed` when the execute stage returns an `error_kind` (`_status_for_exit`, `:49-59`; written after the engine's `completed`).
- The `stage_completed` audit event (`scripts/agent/tool_audit.py:124-147`) has no attempt number; the `attempt_id` given to the LLM runner is `ctx.turn.current_turn_id` (`llm_turn_runner.py:72`), not `attempts.attempt_id`.
- ADR-001 INV-07 / INV-08 (`docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md:171-172`) and `agent_03_03_...md` "Workflow State Semantics" (`:31-33`, started not completed) describe the semantics being changed.

## Problem
A stale attempt is failed while its marker remains, so a re-run reusing attempt 1 is skipped and the task can end `completed`; the retry budget and attempt numbers reset per call; statuses and transitions are unvalidated and zero-row updates are silent; two attempt-start paths exist.

## Reason for Change
Correctness and durability defect in the persistence contract. The unconditional status writes and free-form strings are reachable now; the skipped-stage chain becomes reachable when any caller supplies `existing_task_id` or a retry/resume feature is added. The sibling lease and retry issues build on this contract.

## Implementation Intent
- One vocabulary and transition matrix shared by Python and SQL; every transition is a conditional update on the expected state with a typed error on zero rows.
- Persist `attempt_number`, allocate it with the insert inside `begin_immediate()`, and derive retry budget and event ID from the persisted value.
- `processed_events` becomes a completed-stage ledger written with the attempt's completion; only a completed attempt suppresses a stage.
- Recovery fails the stale attempt and its owning task atomically and is idempotent.
- The resume contract lives in the task-transition API, not in the adapter alone.
- Preserve artifact and audit behavior, extending both with the persisted attempt number.

## Requirements
- `REQ-001`: Define `TaskStatus` (`pending`, `running`, `completed`, `failed`, `halted`) and `AttemptStatus` (`running`, `completed`, `failed`) and an explicit transition matrix: `pending -> running | halted`; `running -> completed | failed | halted`; `failed -> running`; `completed -> failed` (transitional, removed by the retry issue); `halted` and `completed` otherwise terminal. A test proves the SQL `CHECK` vocabulary equals the enums.
- `REQ-002`: Task status changes are conditional updates on the expected current status that require exactly one updated row; zero rows raise `TaskNotFoundError` or `TaskTransitionError` (new `scripts/agent/workflow/errors.py`; `TaskTransitionError` subclasses `RuntimeError` to keep the adapter's existing `RuntimeError` behavior, and its message names the task's current status because `tests/agent/test_orchestrator.py:2116` matches on `halted`).
- `REQ-003`: Add a persisted `attempt_number`, unique per task-stage pair and allocated as `MAX + 1` inside the same `begin_immediate()` transaction as the attempt insert; one canonical attempt-start function serves the engine; the bypass `start_attempt` is removed from `attempt_ops.py` and `StateStore`.
- `REQ-004`: `processed_events` is a completed-stage ledger: a row (with `attempt_id` and `attempt_number`) is written in the transaction that marks the attempt `completed`; a stage is skipped only when a ledger row exists for the task-stage pair; starting a stage while another attempt for it is `running` raises `StageAlreadyRunningError`.
- `REQ-005`: `finish_attempt` accepts only terminal statuses, is a conditional update from `running`, and requires one updated row; its docstring is corrected.
- `REQ-006`: `recover_stale_attempts` marks each stale `running` attempt `failed` (with an error kind naming stale recovery) and moves its owning `running` task to `failed` in one transaction per attempt; repeating recovery changes nothing further.
- `REQ-007`: `WorkflowEngine.run()` claims the task through the transition API (`pending` or `failed` may be claimed; `running`, `completed`, and `halted` are rejected) and the retry loop starts from the persisted attempt number and enforces `max_attempts` across restarts; the adapter's resume guard delegates to the same contract.
- `REQ-008`: Add `CHECK` constraints for both status columns, `attempt_number NOT NULL` with a unique index on (`task_id`, `stage_id`, `attempt_number`), and `attempt_id` / `attempt_number` on `processed_events`, by table-rebuild migration steps registered in the dbmig001 workflow registry with a precondition that rejects rows with unknown statuses, a backfill of `attempt_number`, and a documented rollback; bump `WORKFLOW_SCHEMA_VERSION` and extend `REQUIRED_WORKFLOW_TABLES`.
- `REQ-009`: Task, stage, and persisted attempt number correlate across attempt rows, ledger rows, artifact rows, and the `stage_completed` audit event: the engine exposes the current persisted attempt number, the adapter passes it, and `audit_stage_completed` records `attempt_number`.
- `REQ-010`: Amend ADR-001 INV-07 / INV-08 (ADR change protocol), rewrite `agent_03_03` "Workflow State Semantics", "Resuming Existing Tasks", and "Startup Recovery", and update `agent_04_03` StateStore scope and the `begin_stage_if_new` bullet; correct the stale comments in `idempotency_ops.py` and `state_store.py`.
- `REQ-011`: Regression tests, each failing before the change: crash after the attempt row is written; crash after a side effect before the attempt is finished; repeated restart and recovery; resume of a failed task after one or more attempts; resume of completed, halted, and running tasks; two-connection concurrency on task claim and attempt-number allocation; invalid-status and zero-row writes at API and raw-SQL level; migration of databases with valid and with invalid rows.
- `REQ-012`: No production or test caller uses an attempt-start path that bypasses the canonical transaction.

## Implementation Target Files
**Freeze status**: Frozen (Amended 2026-10-30 (user-approved) after dbmig001 Phase 3 landed: row `scripts/db/migrations_workflow.py` appended after the last row (UNK-04 resolved); re-validated: file exists, concrete change, evidence checkable, linked to REQ-008, not in Reference Files. Original validation: Step 8 Implementation Target Files Validation passed on 2026-10-30: every row exists, or is a new file in an existing directory with "New file" stated, requires modification, cites checkable evidence, and links to a Requirement; existing paths confirmed on branch `docs/issues-workflow-persistence`).

This table is the canonical, frozen source of implementation scope for this Plan. Once `Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream `plan-to-implementation-procedure` document MUST reference file paths only from this table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/workflow/models.py` | Enums and transition matrix | Free-text status comments at `:20,34` | REQ-001 / AC-1 | `models.py:13-34` `TaskRecord`, `AttemptRecord` (checked in Step 3) | `tests/agent/workflow/test_workflow_models.py` | Verified |
| `scripts/agent/workflow/errors.py` | Typed workflow state errors | New file: not-found, transition, stage-already-running errors; directory `scripts/agent/workflow/` exists | REQ-002, REQ-004 / AC-2, AC-4 | No such module (`ls scripts/agent/workflow`); errors today are `RuntimeError` in the adapter (checked in Step 3) | `tests/agent/workflow/test_workflow_state_store.py` | Verified |
| `scripts/agent/workflow/task_ops.py` | Conditional transitions, claim, row-count checks | `update_task_status` is unconditional and ignores row count | REQ-002, REQ-007 / AC-2, AC-6 | `task_ops.py:66-73` (checked in Step 3) | `tests/agent/workflow/test_workflow_state_store.py` | Verified |
| `scripts/agent/workflow/attempt_ops.py` | Canonical attempt start (numbering) and finish; remove bypass | `start_attempt` inserts without marker or number; `finish_attempt` takes any status | REQ-003, REQ-005, REQ-012 / AC-3, AC-5, AC-9 | `attempt_ops.py:12,34,50` (checked in Step 3) | `tests/agent/workflow/test_workflow_stage_persistence.py` | Verified |
| `scripts/agent/workflow/idempotency_ops.py` | Completed-stage ledger and single attempt-start entry | `begin_stage_if_new` writes started markers | REQ-003, REQ-004 / AC-3, AC-4 | `idempotency_ops.py:12-67` incl. started-event comment (checked in Step 3) | `tests/agent/workflow/test_workflow_stage_persistence.py` | Verified |
| `scripts/agent/workflow/state_store.py` | Remove attempt duplicates; atomic idempotent recovery; correct comments | `start_attempt` / `finish_attempt` copies, recovery without task or marker handling | REQ-003, REQ-005, REQ-006, REQ-010, REQ-012 / AC-3, AC-5, AC-7 | `state_store.py:126,147,246-282` (checked in Step 3) | `tests/agent/workflow/test_state_store.py`, `tests/agent/workflow/test_workflow_state_store.py` | Verified |
| `scripts/agent/workflow/workflow_engine.py` | Claim, persisted attempt numbers, budget, expose attempt number | In-memory `attempt = 0` and unconditional status writes | REQ-007, REQ-009 / AC-6, AC-8 | `workflow_engine.py:108-132,148,208` (checked in Step 3) | `tests/agent/workflow/test_workflow_engine.py` | Verified |
| `scripts/agent/workflow_engine_adapter.py` | Resume guard via the transition API; typed errors; pass attempt number to audit | Local `halted` guard and `pending -> halted` / `completed -> failed` writes | REQ-007, REQ-009 / AC-6, AC-8 | `workflow_engine_adapter.py:49-59,204,235,273-283` (checked in Step 3) | `tests/agent/test_orchestrator.py` | Verified |
| `scripts/agent/tool_audit.py` | Add `attempt_number` to `stage_completed` | Event has no attempt number | REQ-009 / AC-8 | `tool_audit.py:124-147` (checked in Step 3) | `tests/agent/test_tool_audit.py` | Verified |
| `scripts/db/schema_sql.py` | `CHECK` constraints, `attempt_number`, ledger columns, version | DDL without constraints or numbering | REQ-008 / AC-10 | `schema_sql.py:172-203`, `:25` (checked in Step 3) | `tests/db/test_create_schema.py` | Verified |
| `scripts/agent/services/workflow_schema.py` | Required columns for the startup check | Required columns omit the new ones | REQ-008 / AC-10 | `workflow_schema.py:44-50`; version compare `:114` (checked in Step 3) | `tests/agent/test_repl_health.py` | Verified |
| `tests/agent/workflow/test_workflow_state_store.py` | Update attempt and recovery tests; add transition, error, and raw-SQL tests | Uses `start_attempt` (`:139,146-148,152,161,231-233`), recovery (`:285-535`), raw INSERTs (`:105,264,268,416,430`) | REQ-002, REQ-003, REQ-005, REQ-006, REQ-011 / AC-2, AC-3, AC-5, AC-7 | `rg start_attempt tests` (checked in Step 3) | itself | Verified |
| `tests/agent/workflow/test_state_store.py` | Update recovery tests for the atomic task transition | Mocks `find_stale_running_attempts`, asserts recovery counts (`:14-231`) | REQ-006, REQ-011 / AC-7 | `test_state_store.py:14-231` (checked in Step 3) | itself | Verified |
| `tests/agent/workflow/test_workflow_engine.py` | Persisted-attempt, claim, and budget tests | Existing idempotency and retry classes (`:161-230`) assume in-memory numbering | REQ-007, REQ-009, REQ-011 / AC-6, AC-8 | `test_workflow_engine.py:161-185` (checked in Step 3) | itself | Verified |
| `tests/agent/workflow/test_workflow_stage_persistence.py` | Replace `start_attempt` use; ledger tests | `start_attempt` at `:42,61,73`; raw task INSERT `:29` | REQ-003, REQ-004, REQ-011, REQ-012 / AC-3, AC-4, AC-9 | `test_workflow_stage_persistence.py:29-73` (checked in Step 3) | itself | Verified |
| `tests/agent/workflow/test_workflow_models.py` | Enum and matrix tests | Status literals `:24,39,50` | REQ-001 / AC-1 | `test_workflow_models.py:24-50` (checked in Step 3) | itself | Verified |
| `tests/agent/workflow/test_workflow_recovery.py` | New crash, resume, and repeated-recovery regression tests | New file: no recovery-scenario tests exist; directory exists | REQ-006, REQ-007, REQ-011 / AC-6, AC-7 | `ls tests/agent/workflow` (checked in Step 3) | itself | Verified |
| `tests/agent/workflow/test_workflow_concurrency.py` | New two-connection claim and numbering tests | New file: no multi-connection workflow test exists; directory exists | REQ-002, REQ-003, REQ-011 / AC-5b | `ls tests/agent/workflow` (checked in Step 3) | itself | Verified |
| `tests/agent/test_orchestrator.py` | Status-write and resume assertions; audit attempt number | Mocked `update_task_status` (`:2627-2765`), halted-resume test (`:2095-2118`) | REQ-007, REQ-009, REQ-011 / AC-6, AC-8 | `test_orchestrator.py:2095-2118,2627-2765,2953-2962,3219` (checked in Step 3) | itself | Verified |
| `tests/agent/test_repl_health.py` | Update workflow-table fixtures for new required columns | Minimal `CREATE TABLE` fixtures (`:540-590`) | REQ-008 / AC-10 | `test_repl_health.py:540-590` (checked in Step 3) | itself | Verified |
| `tests/agent/test_tool_audit.py` | Test `attempt_number` in `stage_completed` | No `stage_completed` test exists | REQ-009 / AC-8 | `rg stage_completed tests/agent/test_tool_audit.py` empty (checked in Step 3) | itself | Verified |
| `tests/db/test_create_schema.py` | Schema constraint and migration tests; DDL copy | DDL copy of `tasks` at `:359` | REQ-008, REQ-011 / AC-10 | `test_create_schema.py:359` (checked in Step 3) | itself | Verified |
| `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` | Amend INV-07 / INV-08 and test-citation rows | Invariants fix the old event key and recovery | REQ-010 / AC-11 | `adr_02_02_001_...md:171-172,187-188` (checked in Step 3) | `tools/check_adr_preservation.py` | Verified |
| `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` | Rewrite state semantics, resume, recovery sections | States "started (not completed)" and halted-only guard | REQ-010 / AC-11 | `agent_03_03_...md:31-33,35-42,143-146` (checked in Step 3) | docs checkers | Verified |
| `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md` | StateStore scope and `begin_stage_if_new` bullet | Describes the single-transaction started-event check | REQ-010 / AC-11 | `agent_04_03_...md:71,87` (checked in Step 3) | docs checkers | Verified |
| `scripts/db/migrations_workflow.py` | Register the migration spec(s) that rebuild `tasks` and `attempts` with the status `CHECK` constraints and `attempt_number`, and add the `processed_events` link columns; bump the version | The registry exists (dbmig001 Phase 3 landed: `MIGRATIONS = ()`, `WORKFLOW_DOMAIN`); a DDL change without a registered forward path is refused at the version check, so the schema row cannot ship without it | REQ-008 / AC-10 | `scripts/db/migrations_workflow.py` (`MIGRATIONS`), `scripts/shared/db_migrations.py` (`MigrationSpec`, `run_migrations`) | `tests/db/test_create_schema.py` (migration test with existing rows) | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze) for the full validation procedure):
- One row per file. No directory, glob, component name, file group, or vague phrase appears as a row.
- A test, configuration, schema, migration, deployment, or documentation file is its own row when it requires modification.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be `Verified` before this section is `Frozen`.

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/db/helper.py` | `begin_immediate()` (`:264`) is the writer-serialization primitive; `execute` returns the cursor used for `rowcount` | REQ-002, REQ-003 |
| `scripts/agent/workflow/artifact_ops.py` | `record_artifact(..., attempt_number=)` already accepts the number; no change needed | REQ-009 |
| `scripts/agent/session_persister.py` | Uses `get_execute_attempt_count` for `retry_count` (`:88-105`); semantics must hold | REQ-003 |
| `scripts/db/create_schema.py` | Version guard (`:54-77`) that makes the schema change migration-gated | REQ-008 |
| `config/workflows/default.json` | Execute stage `retryable`, `max_attempts` source for the budget | REQ-007 |
| `deploy/init_db.sh` | Required-table presence check; columns are not checked | REQ-008 |
| `tools/check_db_separation.py` | Table-ownership inventory; run after DDL changes | REQ-008 |
| `plans/20261029-214108_dbmig001_forward-only-db-migrations.md` | Migration registry, preconditions, ledger, backup gate | REQ-008 |
| `plans/20261030-113553_wftaskapi001_consolidate-task-persistence.md` | Task CRUD ownership | REQ-002 |
| `docs/00_governance/governance_01_documentation-policy.md` | ADR change protocol | REQ-010 |

## Acceptance Criteria
- AC-1 (REQ-001): `TaskStatus` and `AttemptStatus` exist with the matrix; a test fails if the `CHECK` vocabulary and the enums differ; `rg "status: str  # " scripts/agent/workflow/models.py` is empty.
- AC-2 (REQ-002): an invalid status string and an invalid transition each raise a typed error; a zero-row update raises `TaskNotFoundError` or `TaskTransitionError`; both are also rejected by the database when written with raw SQL after migration.
- AC-3 (REQ-003): attempt numbers per task-stage pair are strictly increasing across restarts (new `StateStore` / engine over the same file); `rg start_attempt scripts tests` finds no bypass.
- AC-4 (REQ-004): after a crash that leaves a `running` attempt (no ledger row) and recovery, re-running the stage executes it; a `completed` attempt with a ledger row is skipped; a second start while one is `running` raises `StageAlreadyRunningError`.
- AC-5 (REQ-005): `finish_attempt` rejects non-terminal statuses and a non-`running` source row. AC-5b (REQ-002, REQ-003): two connections claiming one task, or numbering one task-stage pair concurrently, yield exactly one winner and no duplicate number.
- AC-6 (REQ-007): resume of `completed`, `running`, and `halted` tasks is rejected; `failed` and `pending` are claimable; the retry budget counts persisted attempts and is not reset by a restart.
- AC-7 (REQ-006): after recovery a stale attempt is `failed` and its task is `failed`; recovery run three times leaves identical rows.
- AC-8 (REQ-009): attempt, ledger, artifact rows and the `stage_completed` event for one execution share (task, stage, attempt number).
- AC-9 (REQ-012): no production or test caller bypasses the canonical attempt start.
- AC-10 (REQ-008): a database at the previous version with valid rows migrates with rows preserved and numbers backfilled; one with an unknown status is refused by the precondition with the offending rows reported; `check_workflow_schema` fails when a required new column is missing.
- AC-11 (REQ-010): ADR-001 INV-07 / INV-08 and the two agent documents describe the implemented semantics; docs and ADR checkers pass with each reported ADR change explained.

## Tests
- `REQ-001`..`REQ-002`: `tests/agent/workflow/test_workflow_models.py`, `test_workflow_state_store.py` (enums, matrix, transitions, zero-row, raw-SQL).
- `REQ-003`..`REQ-005`, `REQ-012`: `test_workflow_stage_persistence.py`, `test_workflow_state_store.py`, `test_workflow_concurrency.py` (numbering, ledger, finish, two connections).
- `REQ-006`, `REQ-007`, `REQ-011`: `test_workflow_recovery.py`, `test_state_store.py`, `test_workflow_engine.py`, `tests/agent/test_orchestrator.py` (crash, resume, repeated recovery, budget).
- `REQ-008`: `tests/db/test_create_schema.py`, `tests/agent/test_repl_health.py`, and the dbmig001 migration harness (valid and invalid databases).
- `REQ-009`: `tests/agent/test_tool_audit.py`, `test_workflow_engine.py`.
- `REQ-010`: docs and ADR checkers.

## Documentation Impact
Yes: `REQ-010`. Targets (located through `docs/00_index.md` "Document References by Task"): ADR-001 INV-07 / INV-08 under the ADR change protocol, and two agent documents; intent, boundaries, and failure behavior only, no code or DDL restatement. `docs/41_db/db_02_architecture_and_schema-schema-reference.md` and `docs/90_deployment/deployment_01_deployment.md` name tables only and are not targets; the "recreate the database" sentence in db_02 belongs to the dbmig001 plan. The resume contract is settled by the owner (UNK-01), so it is documented as a decision, not a Needs Confirmation item.

## Assumptions
- Owner decisions recorded 2026-10-30: resume contract per REQ-007 (UNK-01) and recovery fails the owning task (UNK-03). The completed-event ledger (UNK-02) stays a default the owner may still change.
- Concurrent writers on one `workflow.sqlite` are possible (no process lock or single-instance guard found); the design relies on `BEGIN IMMEDIATE` plus a unique index, not on a deployment assumption.
- Step 8b overlap judgments (`tools/check_plan_target_overlaps.py`, 2026-10-30), listed in Step 8b output for this Plan: `scripts/db/schema_sql.py` with dbmig001 (ledger DDL), toolexec001 (new tables), ragcorpus001 (rag DDL), wftaskapi001 (one column rename): sequencing dependency, all register through the dbmig001 workflow registry and edit different DDL regions, so they are compatible if landed in registry order and whichever lands first the others rebase. `scripts/agent/workflow/state_store.py` and `tests/agent/workflow/test_workflow_engine.py` with toolexec001 (adds tool-call state helpers and pending-detection tests) and wftaskapi001 (delegation): compatible. `agent_04_03_...md` with toolexec001 and wftaskapi001: sequencing dependency (same StateStore-scope paragraph; this Plan changes the `begin_stage_if_new` bullet and scope wording; the later change reconciles). `tests/db/test_create_schema.py` with dbmig001 and wftaskapi001: compatible (additive tests).
- Further Step 8b judgments for rows added by the overlap check: `scripts/agent/tool_audit.py` with toolexec001: compatible (toolexec001 changes the `execution_snapshot` fields of `audit_tool_exec`, `tool_audit.py:159,188`; this Plan changes `audit_stage_completed`, `:124-147`). `scripts/agent/workflow/workflow_engine.py` with toolexec001: sequencing dependency (toolexec001 REQ-008 adds pending-tool-call detection and replay injection at turn entry in the same file; this Plan changes the status claim and attempt numbering in `run()` and the retry loop; the designs do not contradict, and the later change rebases). `tests/agent/test_orchestrator.py` with turnadr001: compatible (turnadr001 extends the guard test near `:2933`; this Plan edits the status-write and resume tests at `:2095-2118,2627-2765`). `scripts/agent/workflow/models.py`, `task_ops.py`, and the workflow test files with wftaskapi001: sequencing dependency (it renames the task key and consolidates CRUD; this Plan adds statuses and transitions; both preserve behavior and rebase in landing order).
- Schema version numbering (second-pass verification, 2026-10-30): this Plan, wfrecovery001, wflease001, wftaskapi001, and toolexec001 each bump `WORKFLOW_SCHEMA_VERSION` from `1.1.0`. Version numbers are not fixed in the Plans; they are assigned in landing order when the migration steps are registered, and each step's source version equals the previous step's target version (the dbmig001 registry records source and target versions per migration). Two Plans must not target the same version.
- Ordering note (second-pass verification): atomic recovery that fails the owning task (REQ-006) is safe in either landing order relative to wflease001, because today's recovery never fires on production timestamps and wflease001 Phase 1 replaces the 30-second rule with a conservative age before any attempt is recovered; wflease001 Phase 1 should still land no later than this Plan's Phase 3.
- Verification record (second pass, 2026-10-30): no Implementation Target Files row changed on `origin/master` since the merge base; every `path:line` citation lies within its file; no non-vocabulary status seeds in tests (UNK-06); `begin_immediate()` and `execute()` cursor `rowcount` exist in `scripts/db/helper.py` as assumed.
- Execution order (found while generating implementation procedures, 2026-10-30): the `Implementation steps` phases govern, not the `Implementation Target Files` row order. Row 10 (`scripts/db/schema_sql.py`, Phase 2) and its migration step must land before rows 03-07 (Phases 3 and 4) are executed, although they have a smaller table position; each generated procedure states this. Row 10 itself needs the dbmig001 registry module (`scripts/db/migrations_workflow.py`), which is not a row of this table, so its procedure is `Blocked: additional target file discovered` until dbmig001 is implemented and this Plan is amended with that file as a new row appended after the last row.
- The migration registration module `scripts/db/migrations_workflow.py` exists (dbmig001 Phase 3 landed, 2026-10-30) and is a target row (amended 2026-10-30). Registry contract for the spec(s): `MigrationSpec(migration_id, from_version, to_version, apply, precondition, postcondition)` in `scripts/shared/db_migrations.py`; versions are the semver text of `workflow_schema_version` (`WORKFLOW_SCHEMA_VERSION`); `apply` must use `conn.execute` only (never `executescript`) inside the runner's single write transaction; the runner re-checks the fingerprint against `build_workflow_schema_sql()` at the current version. A table rebuild must keep `attempts` rows when `tasks` is replaced: `foreign_keys=ON` makes `DROP TABLE tasks` cascade-delete them, so the spec sets `PRAGMA defer_foreign_keys=ON` first or rebuilds in an order that never drops a referenced parent. Version chain coordination with `plans/20261030-113553_wftaskapi001_consolidate-task-persistence.md`: the registry needs one linear chain, so whichever Plan lands second sets its spec's `from_version` to the first one's `to_version` (read `MIGRATIONS` at implementation time).
- `config/adr_authority.toml` (adrauth001) does not exist yet, so no authority-registry entry needs changing now.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | (Decided by the owner on 2026-10-30) Resume contract: `pending` and `failed` tasks may be claimed; `running`, `completed`, and `halted` are rejected | Resolved: the owner chose the recommended contract; no caller passes `existing_task_id`, and the docs keep describing resume | Implement per REQ-007; no Needs Confirmation item is needed for it | False |
| UNK-02 | Ledger choice: completed-event ledger vs. status-bearing attempt ledger | No owner decision | Default: completed-event ledger (keeps `processed_events`, which startup check, deploy check, and ADR name); alternative recorded in Design | False |
| UNK-03 | (Decided by the owner on 2026-10-30) Recovery also fails the owning `running` task | Resolved: the owner chose yes; `agent_03_03` states recovery never changes task status, so that sentence is rewritten | Implement per REQ-006; rewrite the docs sentence in Phase 5 | False |
| UNK-04 | dbmig001 registry API and registration module | `scripts/db/migrations_workflow.py` is planned, absent | Open dependency `plans/20261029-214108_dbmig001_forward-only-db-migrations.md` Phase 3; Phase 2 starts only after it; amend target files at procedure generation Resolved 2026-10-30: the registry landed (`scripts/db/migrations_workflow.py`, `scripts/shared/db_migrations.py`); the module is now a target row. | False |
| UNK-05 | Whether wftaskapi001 Phase 2 lands first | Plan exists, rows Pending | Open dependency `plans/20261030-113553_wftaskapi001_consolidate-task-persistence.md`; Phase 1 works in `task_ops` either way | False |
| UNK-06 | (Resolved, second-pass verification 2026-10-30) Whether tests that insert raw status rows use only the five-status vocabulary | Resolved: raw INSERT seeds use `'running'` (attempts) and `pending` (tasks); no non-vocabulary status literal (`done`, `success`, `error`, `cancelled`, `stale`, `active`, `waiting`, `timeout`, `aborted`) exists in `tests/agent/workflow`, `tests/db`, or `tests/agent/test_orchestrator.py`; `?`-parameter seeds are re-checked in Phase 1 | Re-check parameter values with the new constraints in Phase 1 | False |
| UNK-07 | Handling of retained rows that violate the new constraints (stale `running` attempts, markers without a completed attempt) | Production database not inspected (`rules/ai-execution.md` Repository Tool Usage item 7) | Precondition fails closed with the offending rows listed; owner decides on automatic mapping; backup gate from dbmig001 | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/workflow/models.py` | Modify | Medium | 1 | High (single contributor) | not applicable (rsynced) |
| `scripts/agent/workflow/errors.py` | Create | Low | N/A: new file | N/A: new file | not applicable (rsynced) |
| `scripts/agent/workflow/task_ops.py` | Modify | Medium | 1 | High (single contributor) | not applicable (rsynced) |
| `scripts/agent/workflow/attempt_ops.py` | Modify | Medium | 0 | High (single contributor) | not applicable (rsynced) |
| `scripts/agent/workflow/idempotency_ops.py` | Modify | Medium | 0 | High (single contributor) | not applicable (rsynced) |
| `scripts/agent/workflow/state_store.py` | Modify | High: 84 test references in 7 files | 2 | High (single contributor) | not applicable (rsynced) |
| `scripts/agent/workflow/workflow_engine.py` | Modify | High: 54 test references in 3 files | 1 | High (single contributor) | not applicable (rsynced) |
| `scripts/agent/workflow_engine_adapter.py` | Modify | Medium | 7 | High (single contributor) | not applicable (rsynced) |
| `scripts/agent/tool_audit.py` | Modify | Low | 2 | High (single contributor) | not applicable (rsynced) |
| `scripts/db/schema_sql.py` | Modify | High: version guards, sibling plans | 12 | High (single contributor) | not applicable (rsynced) |
| `scripts/agent/services/workflow_schema.py` | Modify | Medium: startup check, `check_workflow_schema` is grade C (12) | 3 | High (single contributor) | not applicable (rsynced) |
| `tests/agent/workflow/test_workflow_state_store.py` | Modify | Low | 4 | High (single contributor) | not applicable (rsynced) |
| `tests/agent/workflow/test_state_store.py` | Modify | Low | 0 | High (single contributor) | not applicable (rsynced) |
| `tests/agent/workflow/test_workflow_engine.py` | Modify | Low | 2 | High (single contributor) | not applicable (rsynced) |
| `tests/agent/workflow/test_workflow_stage_persistence.py` | Modify | Low | 2 | High (single contributor) | not applicable (rsynced) |
| `tests/agent/workflow/test_workflow_models.py` | Modify | Low | 0 | High (single contributor) | not applicable (rsynced) |
| `tests/agent/workflow/test_workflow_recovery.py` | Create | Low | N/A: new file | N/A: new file | not applicable (rsynced) |
| `tests/agent/workflow/test_workflow_concurrency.py` | Create | Low | N/A: new file | N/A: new file | not applicable (rsynced) |
| `tests/agent/test_orchestrator.py` | Modify | Medium | 14 | High (single contributor) | not applicable (rsynced) |
| `tests/agent/test_repl_health.py` | Modify | Low | 6 | High (single contributor) | not applicable (rsynced) |
| `tests/agent/test_tool_audit.py` | Modify | Low | 3 | High (single contributor) | not applicable (rsynced) |
| `tests/db/test_create_schema.py` | Modify | Low | 15 | High (single contributor) | not applicable (rsynced) |
| `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` | Modify | Medium: Accepted ADR | 5 | High (single contributor) | not applicable (rsynced) |
| `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` | Modify | Low | 23 | High (single contributor) | not applicable (rsynced) |
| `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md` | Modify | Low | 14 | High (single contributor) | not applicable (rsynced) |

## Design
- **Matrix.** Chosen edges include `pending -> halted` and a transitional `completed -> failed` because the adapter writes them today; removing the second edge is the retry issue's work. Alternative (strict matrix without them) would make current adapter writes fail. Compatibility: `TaskTransitionError` subclasses `RuntimeError`, so the existing adapter and test expectation of `RuntimeError` for a halted resume holds.
- **Ledger.** Alternatives: (a) completed-event ledger: `processed_events` rows written only with the `completed` finish, skip iff a row exists for the task-stage pair; (b) status-bearing attempt ledger: drop `processed_events`, use `attempts` alone. Chosen (a): the table is named by the startup check (`workflow_schema.py:44-50`), `deploy/init_db.sh`, `tools/check_db_separation.py`, and ADR-001 decision 9, so keeping it has the smaller blast radius; (b) is a later simplification. ADR-001 INV-08 is amended either way. A `running` attempt has no ledger row, so a crash leaves nothing that suppresses a re-run.
- **Numbering and concurrency.** `MAX(attempt_number)+1` and the insert run in one `begin_immediate()` transaction (`BEGIN IMMEDIATE`, default busy timeout 30000 ms), serializing writers; the unique index is a backstop. The engine reads the persisted maximum for the budget.
- **Recovery.** One transaction per attempt: conditional `running -> failed` on the attempt, then conditional `running -> failed` on the owning task when no other attempt for it is `running`; a repeat finds no `running` rows and changes nothing.
- **Migration.** SQLite cannot add `CHECK` or `NOT NULL` to an existing column, so `tasks`, `attempts`, and `processed_events` are rebuilt (create, copy with `attempt_number` backfilled by `ROW_NUMBER() OVER (PARTITION BY task_id, stage_id ORDER BY started_at, rowid)`, drop, rename). The step registers in the dbmig001 registry with a precondition that rejects unknown statuses and a documented rollback (restore from the pre-migration backup the gate creates). The wftaskapi001 column rename is a separate registered step.
- **Audit correlation.** The engine exposes the current persisted attempt number; the adapter reads it from the engine it already holds and passes it to `audit_stage_completed`, whose new `attempt_number` has a default so existing callers stay valid. The existing `attempt_id` passed to the LLM runner (a turn ID) is left unchanged.
- **Layering.** `errors.py` imports nothing from the workflow package; `lint-imports` baseline 6 kept, 0 broken (2026-10-30).

## Implementation steps
1. **Phase 1: Vocabulary, errors, and task transitions (no schema change)**
   - [ ] Add enums, matrix, and the typed errors (REQ-001, REQ-002; `scripts/agent/workflow/models.py`, `scripts/agent/workflow/errors.py`).
   - [ ] Add conditional transition and claim functions with row-count checks (REQ-002, REQ-007; `scripts/agent/workflow/task_ops.py`); resolve UNK-06 by checking test seeds.
   - [ ] Tests for enums, matrix, errors, zero-row, and invalid statuses (REQ-001, REQ-002; `tests/agent/workflow/test_workflow_models.py`, `tests/agent/workflow/test_workflow_state_store.py`).
2. **Phase 2: Schema and migration (starts after dbmig001 Phase 3)**
   - [ ] Update DDL, version, and required columns (REQ-008; `scripts/db/schema_sql.py`, `scripts/agent/services/workflow_schema.py`); register the rebuild migration steps with precondition and rollback (REQ-008; `scripts/db/migrations_workflow.py`).
   - [ ] Migration, constraint, and startup-check tests (REQ-008, REQ-011; `tests/db/test_create_schema.py`, `tests/agent/test_repl_health.py`).
3. **Phase 3: Attempt lifecycle, ledger, and recovery**
   - [ ] Canonical attempt start with numbering, ledger-on-complete, terminal-only finish, bypass removal (REQ-003, REQ-004, REQ-005, REQ-012; `scripts/agent/workflow/attempt_ops.py`, `scripts/agent/workflow/idempotency_ops.py`, `scripts/agent/workflow/state_store.py`).
   - [ ] Atomic idempotent recovery and comment corrections (REQ-006, REQ-010; `scripts/agent/workflow/state_store.py`).
   - [ ] Tests: numbering across restarts, ledger, recovery, repeated recovery, two connections (REQ-003..REQ-006, REQ-011; `tests/agent/workflow/test_workflow_stage_persistence.py`, `tests/agent/workflow/test_workflow_state_store.py`, `tests/agent/workflow/test_state_store.py`, `tests/agent/workflow/test_workflow_recovery.py`, `tests/agent/workflow/test_workflow_concurrency.py`).
4. **Phase 4: Engine, adapter, and audit correlation**
   - [ ] Engine claims through the transition API, uses persisted numbers and budget, exposes the attempt number (REQ-007, REQ-009; `scripts/agent/workflow/workflow_engine.py`).
   - [ ] Adapter resume guard delegates to the contract, handles typed errors, passes the attempt number; audit event gains `attempt_number` (REQ-007, REQ-009; `scripts/agent/workflow_engine_adapter.py`, `scripts/agent/tool_audit.py`).
   - [ ] Tests (REQ-007, REQ-009, REQ-011; `tests/agent/workflow/test_workflow_engine.py`, `tests/agent/test_orchestrator.py`, `tests/agent/test_tool_audit.py`).
5. **Phase 5: Documentation and ADR**
   - [ ] Amend ADR-001 INV-07 / INV-08 under the ADR change protocol and rewrite the agent document sections (REQ-010; `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`, `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`, `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md`); run the docs and ADR checkers.
6. **Phase 6: Deployment & Verification**
   - [ ] Hand off to `skills/deploy/SKILL.md` after the change is committed and pushed; deploying is the user's decision (approval gate). Prerequisite: the dbmig001 migration for the retained `/opt/llm/db/workflow.sqlite` has run with its backup gate; verify with the startup schema check and `uv run python tools/check_db_separation.py` (REQ-008; `scripts/db/schema_sql.py`).

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/workflow/` | Unit + crash / resume / concurrency | `uv run pytest tests/agent/workflow/ -v` | All pass; new tests fail on the pre-change code |
| Engine / adapter / audit | Integration | `uv run pytest tests/agent/test_orchestrator.py tests/agent/test_tool_audit.py tests/agent/test_repl_health.py -v` | All pass |
| Schema and migration | Unit + migration on valid and invalid databases | `uv run pytest tests/db/ -v` | Rows preserved; invalid rows refused |
| Schema ownership | Static | `uv run python tools/check_db_separation.py` | Pass |
| Source quality | Static | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `uv run python tools/check_module_size.py` | Clean; 6 contracts kept; `state_store.py` (11164 B) and `workflow_engine.py` (9644 B) stay under 20480 B |
| Changed-line coverage | Coverage | `uv run coverage run -m pytest tests/`, `uv run coverage xml`, `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | at least 90% (baseline without threshold: no covered lines in the current diff, which contains only documents) |
| Generated reference | Static | `uv run python tools/generate_reference_table.py --check` | `No drift found` |
| `docs/` and ADR | Static | `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_consistency.py --domain agent`, `check_docs_japanese.py`, `check_adr_preservation.py` | Pass; each ADR change reported and explained |

Baselines recorded 2026-10-30: radon (grade C or worse in the scanned set): `workflow_schema.check_workflow_schema` C (12), `workflow_engine_adapter._run_execute_stage` C (11); the workflow package modules otherwise none. vulture: 16 findings, none in these files. bandit: 0 medium or high repository-wide (51 low). Operational check: production database locks (`fuser`) not run; planning does not touch `/opt/llm/` (`rules/ai-execution.md` Repository Tool Usage item 7); `pip-audit` not applicable (no dependency change).

## Risks
- **Risk**: `StateStore` (84 references in 7 test files), `processed_events` (12 in 5), `recover_stale_attempts` (18 in 2), `update_task_status` (17 in 2), and `WorkflowHaltError` (28 in 3) exceed the `rules/toolchain.md` Impact-radius threshold; the blast radius is recorded here and the test updates are part of the same unit of work → **Mitigation**: tests are updated in the phase that changes their subject; each phase leaves the suite green.
- **Risk**: table-rebuild migration on a retained `workflow.sqlite` could lose rows or fail on rows that violate the constraints → **Mitigation**: dbmig001 backup gate and precondition, fail-closed on unknown statuses with the rows listed, rollback by restoring the backup, migration tests on valid and invalid databases (AC-10).
- **Risk**: `schema_sql.py` has 12 commits in 30 days and four Frozen Plans target it → **Mitigation**: all register through the dbmig001 registry, edit separate regions, and rebase in registry order.
- **Risk**: strict transitions break existing adapter writes (`pending -> halted`, `completed -> failed`) → **Mitigation**: both edges are in the matrix; the second is marked transitional for the retry issue.
- **Risk**: a crash-left `running` task becomes unresumable → **Mitigation**: recovery fails the owning task in the same transaction (UNK-03).
- **Risk**: amending an Accepted ADR changes an invariant other documents cite → **Mitigation**: ADR change protocol, `check_adr_preservation.py`, and updated test-citation rows; ADR-008 is edited by the dbmig001 plan, not here.
- **Risk**: another plan's migration step claims the same target version → **Mitigation**: version numbers assigned in landing order (Assumptions).
- **Risk**: single-contributor files (bus factor High) → **Mitigation**: small phases, each testable and revertable.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Vocabulary, errors, and task transitions | Completed | — | 20261030-144830 |  |
| 2 | Phase 2: Schema and migration | In Progress | — | — | Starts after dbmig001 Phase 3 |
| 3 | Phase 3: Attempt lifecycle, ledger, and recovery | Pending | — | — |  |
| 4 | Phase 4: Engine, adapter, and audit correlation | Pending | — | — |  |
| 5 | Phase 5: Documentation and ADR | Pending | — | — |  |
| 6 | Phase 6: Deployment & Verification | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |
| implementations/20261030-125334_10_scripts_db_schema_sql.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261030-125334_22_tests_db_test_create_schema.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261030-125334_26_scripts_db_migrations_workflow.py.md | 2 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261030-105639_wfrecovery001_workflow-recovery-state-machine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261030-114041
- **Related target files**: `scripts/agent/workflow/models.py`, `scripts/agent/workflow/errors.py`, `scripts/agent/workflow/task_ops.py`, `scripts/agent/workflow/attempt_ops.py`, `scripts/agent/workflow/idempotency_ops.py`, `scripts/agent/workflow/state_store.py`, `scripts/agent/workflow/workflow_engine.py`, `scripts/agent/workflow_engine_adapter.py`, `scripts/agent/tool_audit.py`, `scripts/db/schema_sql.py`, `scripts/agent/services/workflow_schema.py`, `tests/agent/workflow/test_workflow_state_store.py`, `tests/agent/workflow/test_state_store.py`, `tests/agent/workflow/test_workflow_engine.py`, `tests/agent/workflow/test_workflow_stage_persistence.py`, `tests/agent/workflow/test_workflow_models.py`, `tests/agent/workflow/test_workflow_recovery.py`, `tests/agent/workflow/test_workflow_concurrency.py`, `tests/agent/test_orchestrator.py`, `tests/agent/test_repl_health.py`, `tests/agent/test_tool_audit.py`, `tests/db/test_create_schema.py`, `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md`, `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md`, `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md`, `scripts/db/migrations_workflow.py`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Implementation Intent 1; Required Changes 1 | `scripts/agent/workflow/models.py` | Phase 1 | AC-1 | `tests/agent/workflow/test_workflow_models.py` | Confirmed by repository evidence |
| REQ-001 | Implementation Intent 1 | `tests/agent/workflow/test_workflow_models.py` | Phase 1 | AC-1 | `uv run pytest tests/agent/workflow/` | Confirmed by repository evidence |
| REQ-002 | Implementation Intent 2; Required Changes 9 | `scripts/agent/workflow/errors.py` | Phase 1 | AC-2 | `tests/agent/workflow/test_workflow_state_store.py` | Derived from confirmed evidence |
| REQ-002 | Required Changes 9 | `scripts/agent/workflow/task_ops.py` | Phase 1 | AC-2 | `tests/agent/workflow/test_workflow_state_store.py` | Confirmed by repository evidence |
| REQ-002 | Testing Expectations 2-3 | `tests/agent/workflow/test_workflow_concurrency.py` | Phase 3 | AC-5b | `uv run pytest tests/agent/workflow/` | Explicit in issue |
| REQ-003 | Required Changes 4-5 | `scripts/agent/workflow/attempt_ops.py` | Phase 3 | AC-3, AC-9 | `tests/agent/workflow/test_workflow_stage_persistence.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes 5 | `scripts/agent/workflow/idempotency_ops.py` | Phase 3 | AC-3 | `tests/agent/workflow/test_workflow_stage_persistence.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes 5 | `scripts/agent/workflow/state_store.py` | Phase 3 | AC-3, AC-9 | `tests/agent/workflow/test_workflow_state_store.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes 3; Implementation Intent 4 | `scripts/agent/workflow/idempotency_ops.py` | Phase 3 | AC-4 | `tests/agent/workflow/test_workflow_stage_persistence.py` | Derived from confirmed evidence |
| REQ-004 | Required Changes 3 | `scripts/agent/workflow/errors.py` | Phase 1 | AC-4 | `tests/agent/workflow/test_workflow_stage_persistence.py` | Derived from confirmed evidence |
| REQ-005 | Required Changes 6 | `scripts/agent/workflow/attempt_ops.py` | Phase 3 | AC-5 | `tests/agent/workflow/test_workflow_state_store.py` | Confirmed by repository evidence |
| REQ-005 | Required Changes 6 | `scripts/agent/workflow/state_store.py` | Phase 3 | AC-5 | `tests/agent/workflow/test_workflow_state_store.py` | Confirmed by repository evidence |
| REQ-006 | Required Changes 7; Background (crash-left tasks) | `scripts/agent/workflow/state_store.py` | Phase 3 | AC-7 | `tests/agent/workflow/test_workflow_recovery.py` | Derived from confirmed evidence |
| REQ-006 | Testing Expectations 1 | `tests/agent/workflow/test_workflow_recovery.py` | Phase 3 | AC-7 | `uv run pytest tests/agent/workflow/` | Explicit in issue |
| REQ-006 | Testing Expectations 1 | `tests/agent/workflow/test_state_store.py` | Phase 3 | AC-7 | `uv run pytest tests/agent/workflow/` | Confirmed by repository evidence |
| REQ-007 | Required Changes 8; Implementation Intent 6 | `scripts/agent/workflow/workflow_engine.py` | Phase 4 | AC-6 | `tests/agent/workflow/test_workflow_engine.py` | Confirmed by repository evidence |
| REQ-007 | Required Changes 8 | `scripts/agent/workflow_engine_adapter.py` | Phase 4 | AC-6 | `tests/agent/test_orchestrator.py` | Confirmed by repository evidence |
| REQ-007 | Required Changes 8 | `scripts/agent/workflow/task_ops.py` | Phase 1 | AC-6 | `tests/agent/workflow/test_workflow_state_store.py` | Confirmed by repository evidence |
| REQ-008 | Required Changes 2; Constraints | `scripts/db/schema_sql.py` | Phase 2 | AC-10 | `tests/db/test_create_schema.py` | Confirmed by repository evidence |
| REQ-008 | Required Changes 2; Constraints | `scripts/db/migrations_workflow.py` | Phase 2 | AC-10 | `tests/db/test_create_schema.py` | Confirmed by repository evidence |
| REQ-008 | Background (startup check) | `scripts/agent/services/workflow_schema.py` | Phase 2 | AC-10 | `tests/agent/test_repl_health.py` | Confirmed by repository evidence |
| REQ-008 | Testing Expectations 4 | `tests/db/test_create_schema.py` | Phase 2 | AC-10 | `uv run pytest tests/db/` | Explicit in issue |
| REQ-008 | Background (second finding) | `tests/agent/test_repl_health.py` | Phase 2 | AC-10 | `uv run pytest tests/agent/test_repl_health.py` | Confirmed by repository evidence |
| REQ-009 | Required Changes (correlation); Acceptance Criteria 8 | `scripts/agent/tool_audit.py` | Phase 4 | AC-8 | `tests/agent/test_tool_audit.py` | Derived from confirmed evidence |
| REQ-009 | Acceptance Criteria 8 | `scripts/agent/workflow/workflow_engine.py` | Phase 4 | AC-8 | `tests/agent/workflow/test_workflow_engine.py` | Derived from confirmed evidence |
| REQ-009 | Acceptance Criteria 8 | `scripts/agent/workflow_engine_adapter.py` | Phase 4 | AC-8 | `tests/agent/test_orchestrator.py` | Derived from confirmed evidence |
| REQ-009 | Acceptance Criteria 8 | `tests/agent/test_tool_audit.py` | Phase 4 | AC-8 | `uv run pytest tests/agent/test_tool_audit.py` | Derived from confirmed evidence |
| REQ-010 | Documentation Impact | `docs/10_adr/adr_02_02_001_agent-workflow-engine-mandatory.md` | Phase 5 | AC-11 | `check_adr_preservation.py`, docs checkers | Confirmed by repository evidence |
| REQ-010 | Documentation Impact | `docs/23_agent/agent_03_03_turn-processing-flow-workflow-engine.md` | Phase 5 | AC-11 | docs checkers | Confirmed by repository evidence |
| REQ-010 | Documentation Impact | `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md` | Phase 5 | AC-11 | docs checkers | Confirmed by repository evidence |
| REQ-011 | Testing Expectations | `tests/agent/workflow/test_workflow_state_store.py` | Phases 1, 3 | AC-2, AC-5 | `uv run pytest tests/agent/workflow/` | Explicit in issue |
| REQ-011 | Testing Expectations | `tests/agent/workflow/test_workflow_engine.py` | Phase 4 | AC-6 | `uv run pytest tests/agent/workflow/` | Explicit in issue |
| REQ-011 | Testing Expectations | `tests/agent/test_orchestrator.py` | Phase 4 | AC-6 | `uv run pytest tests/agent/test_orchestrator.py` | Explicit in issue |
| REQ-012 | Acceptance Criteria 9 | `scripts/agent/workflow/attempt_ops.py` | Phase 3 | AC-9 | `rg start_attempt scripts tests` | Explicit in issue |
| REQ-012 | Acceptance Criteria 9 | `tests/agent/workflow/test_workflow_stage_persistence.py` | Phase 3 | AC-9 | `rg start_attempt scripts tests` | Explicit in issue |