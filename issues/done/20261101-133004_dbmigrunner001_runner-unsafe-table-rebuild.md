# Migration runner cannot apply a table rebuild safely and its head-version step is fragile

## Priority
High

## Summary
The forward-only migration runner (`MigrationRunner` in `shared/db_migrations.py`) documents that each step is all-or-nothing, but it runs a step with `executescript`, which is not atomic, and the operator CLI opens the workflow database with foreign keys enforced, so dropping a parent table deletes its child rows. The registered tool_call_state step also writes whatever `WORKFLOW_SCHEMA_VERSION` is at import time instead of its own version. Nothing breaks today because the two registered steps are idempotent DDL, but the next schema change either corrupts data (a table rebuild) or leaves the version marker wrong (any version bump). Fix the runner contract before any step that rebuilds a table or bumps the schema version is added.

## Background
Found while analysing how to integrate the unmerged workflow-recovery work (`wfrecovery001`, `wftaskapi001`, `wflease001`) with the migration framework that landed on master (`dbmig001`). Those plans need steps that rebuild `tasks`, `attempts` and `processed_events` with new constraints and rename a column.
- `MigrationRunner._apply_step` runs each step's preconditions and then `conn.executescript(spec.mutation_sql)` followed by `commit`; on `sqlite3.Error` it calls `rollback`. Its docstring says `executescript` runs every statement "inside a single implicit transaction" so a step "is all-or-nothing".
- `MigrationRunner.apply` records the ledger row (`record_applied`) and re-checks the postcondition only after the step's commit, in separate transactions.
- `scripts/db/migrate_db.py` opens the workflow database with `SQLiteHelper("workflow").open(write_mode=True)`; the helper enables `PRAGMA foreign_keys=ON` for write mode. The CLI resolves the database path from configuration and has no option to point it at a copy.
- `scripts/db/migrations_workflow.py` builds `_TOOL_STATE_MUTATION_SQL` as an f-string that inserts `WORKFLOW_SCHEMA_VERSION` (currently `1.2.0`) into `workflow_schema_version` when the module is imported.
- `docs/41_db/db_04_api_and_operations-module-boundaries-and-helper.md` already states that `executescript()` commits pending transactions before execution, which contradicts the runner docstring.
- Archived background: `issues/done/20261029-104500_dbmig001_forward-only-db-migrations.md` and `plans/done/20261029-214108_dbmig001_forward-only-db-migrations.md`.

## Problem
Evidence (`Explicit in code` plus a throwaway script on temporary SQLite files; no real database or service was touched):
1. A script whose second statement fails leaves the first statement applied after the runner's `rollback`: `CREATE TABLE x(a); CREATE TABLE x(a);` raises "table x already exists" and table `x` still exists. A multi-statement step is therefore not all-or-nothing.
2. With `foreign_keys=ON`, `DROP TABLE` of a parent table removes the rows of a child declared `ON DELETE CASCADE` (one child row before, zero after). A step that rebuilds `tasks` (create new, copy, drop old, rename) would delete every `attempts` and `processed_events` row.
3. `PRAGMA foreign_keys=OFF` inside an open transaction is a no-op, so the step cannot switch enforcement off itself unless it controls the transaction.
4. The ledger row and the postcondition run after the step's commit, so a crash between them leaves a step applied but unrecorded; the next run then refuses it on its own precondition (for example a rename whose source column no longer exists).
5. `_TOOL_STATE_MUTATION_SQL` embeds the live `WORKFLOW_SCHEMA_VERSION` (`1.2.0` today, confirmed). Raising that constant for a later schema change makes the tool_call_state step write the new version, so a migrated database would carry the wrong marker and pass or fail the startup check for the wrong reason.

Effects:
- The planned recovery schema step would silently destroy attempt and ledger history on an existing database, or leave it half-rebuilt.
- Any schema change that bumps the version constant breaks the earlier step's meaning.

## Reason for Change
The runner is the safety layer for forward-only migrations of retained databases. Its documented guarantee (atomic step, verified backup, recorded ledger) does not hold for the kind of step the next planned changes need, and the defects are invisible until such a step runs against real data. Fixing it first keeps those plans from being the first test of the runner.

## Implementation Intent
Give a step an explicit transaction contract: the runner (not the step's SQL) begins one write transaction per step, optionally with foreign-key enforcement switched off before it begins, runs the statements one by one, writes the ledger row and the version stamp inside the same transaction, runs an optional pre-commit verification (including `PRAGMA foreign_key_check` when enforcement was off), commits, and always restores the foreign-key setting. Existing steps must behave exactly as before. Pin the tool_call_state step to its own literal version. Let the CLI operate on a database copy so a migration can be rehearsed without touching the configured database. Correct the runner docstring.

## Target Files or Areas
- `scripts/shared/db_migrations.py` (`MigrationSpec`, `MigrationRunner._apply_step`, `MigrationRunner.apply`, `record_applied`)
- `scripts/db/migrations_workflow.py` (`_TOOL_STATE_MUTATION_SQL`)
- `scripts/db/migrate_db.py` (database path option)
- `tests/shared/test_db_migrations.py`, `tests/db/test_migrations_workflow.py`
- `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`, `docs/41_db/db_07_api_and_operations-recovery-and-reference.md`, `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` (confirm which state the transaction contract; `Needs confirmation`)

## Required Changes
- Run each step in one explicit transaction: statements executed individually, ledger row and version stamp written in the same transaction, rollback leaves no partial step.
- Add an opt-in step attribute for foreign-key enforcement off during the step, restored in a `finally`, with `PRAGMA foreign_key_check` run before commit and a failing check rolling the step back.
- Add an optional pre-commit verification callback to a step; keep the existing post-commit postcondition semantics for current steps or document the change.
- Replace the f-string version in `_TOOL_STATE_MUTATION_SQL` with the literal `1.2.0` (the tool_call_state step's own version).
- Add a way to run `migrate_db.py` against a given database file (for example `--db <path>`), refusing nothing else about its modes.
- Correct the `_apply_step` docstring and align the database documentation with the actual guarantee.
- Add tests: a multi-statement step that fails midway leaves the database unchanged; a table-rebuild step on a database with child rows keeps every child row and fails closed on a dangling reference; the foreign-key setting is restored after success and after failure; the ledger row and the version stamp are committed together; raising the head-version constant does not change what the tool_call_state step writes; the CLI works on a copy.

## Constraints
- Existing steps (ledger bootstrap and tool_call_state) must produce byte-identical results to today on a legacy database.
- Keep the backup gate (checkpoint, backup, integrity check, injected verifier) and its refusal semantics.
- Do not add steps or change schema versions in this issue.
- Tests use temporary database files only; nothing may open the configured workflow database or any path under `/opt/llm`.
- `shared` must not import `db` (import-linter contracts stay kept).

## Acceptance Criteria
- A step that fails at any statement leaves no partial change, and neither the ledger nor the version stamp advances.
- A rebuild step with foreign-key enforcement off keeps all child rows, and a dangling reference makes the step fail before commit.
- The foreign-key pragma is restored after every step, including failures.
- The tool_call_state step writes `1.2.0` regardless of the current head constant.
- `migrate_db.py` can be pointed at a database copy for `--status`, `--dry-run` and `--apply`.
- The runner docstring and the database documentation describe the actual transaction behavior.
- The new tests fail on the current code and pass after the change.

## Testing Expectations
- Unit tests for the runner with temporary SQLite files and toy steps (a failing multi-statement step, a rebuild step with child rows, a dangling-reference step).
- Regression: `tests/shared/test_db_migrations.py`, `tests/db/test_migrations_workflow.py`, the eventbus migration tests; run `ruff`, `mypy --no-namespace-packages` and `PYTHONPATH=scripts uv run lint-imports` on touched files; run the documentation checks for changed docs.

## Documentation Impact
State the per-step transaction contract (what is atomic, when the ledger row is written, how foreign-key enforcement is handled for a rebuild), the new CLI option, and that the step's postcondition now runs before or after commit (whichever is decided). Describe intent and failure behavior only.

## Out of Scope
- The workflow recovery schema, the `task_nonce` rename and any new migration step (`wfrecovery001`, `wftaskapi001`, `wflease001`).
- The eventbus migration registry's own steps.
- Changing the backup gate or the ledger table layout.

## Dependencies
- Blocks `issues/20261030-105639_wfrecovery001_workflow-recovery-state-machine.md` Phase 2 and `issues/20261030-105723_wftaskapi001_consolidate-task-persistence.md` Phase 3 (their plans are `plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md` and `plans/20261030-113553_wftaskapi001_consolidate-task-persistence.md`): both need a safe table rebuild and a version bump.
- Related archived work: `issues/done/20261029-104500_dbmig001_forward-only-db-migrations.md`.

## Unresolved Questions
- Whether the postcondition should run before commit (rolling the step back on failure) or stay after the ledger write: a design choice for the owner; running it before commit is safer but changes the documented order.
- Whether a rolled-back `BEGIN` left open by a failed script can occur once statements are executed individually: `Needs confirmation`; to be settled by the failure-injection test.
- Whether any workflow or eventbus database is already at a version the current head constants would misinterpret: `Needs confirmation` (the configured databases were not inspected).

## AI Implementation Instruction
Write the failing tests first (partial-step, child-row loss, foreign-key restore, version literal). Change only the runner's step execution, the tool_call_state step's version literal, the CLI path option, the docstring and the documentation. Do not add migration steps. Use temporary databases only. Stop and report if making a step atomic requires changing the ledger layout or the backup gate.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261101-133004
- **Related target files**: scripts/shared/db_migrations.py, scripts/db/migrations_workflow.py, scripts/db/migrate_db.py, tests/shared/test_db_migrations.py, tests/db/test_migrations_workflow.py, docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md, docs/41_db/db_07_api_and_operations-recovery-and-reference.md, docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md
