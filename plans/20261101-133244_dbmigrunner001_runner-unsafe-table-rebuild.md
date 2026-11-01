## Goal
- Make `MigrationRunner` run every migration step in one explicit, runner-controlled write transaction (statements executed individually, ledger row written in the same transaction, optional foreign-key enforcement switch and pre-commit verification), pin the `workflow_tool_call_state` step to its own literal version `1.2.0`, and let `migrate_db.py` operate on a given database file, so that a later table-rebuild or version-bump step can be added without data loss or a wrong version marker.

## Priority
High

## Scope
- **In-Scope**:
  - Per-step transaction contract in the shared runner: explicit `BEGIN` taken by the runner, statements run one by one (no `executescript`), `record_applied` written before the single `commit`, rollback leaves no partial step.
  - Opt-in `MigrationSpec` attribute for foreign-key enforcement off during a step (set before the transaction begins, restored in a `finally`), with `PRAGMA foreign_key_check` before commit and rollback on a violation.
  - Optional pre-commit verification callback on `MigrationSpec`; the existing `postcondition` keeps its current post-commit position (see UNK-01).
  - Replace the f-string in `_TOOL_STATE_MUTATION_SQL` with the literal `1.2.0`.
  - `migrate_db.py` option to run `--status`, `--dry-run` and `--apply` against a given database file.
  - Correct the `_apply_step` docstring and the database documentation of the per-step transaction behavior.
  - Failing-first tests for each acceptance criterion.
- **Out-of-Scope**:
  - The workflow recovery schema, the `task_nonce` rename, and any new migration step (`wfrecovery001`, `wftaskapi001`, `wflease001`).
  - The eventbus migration registry's own steps (they must keep working unchanged on the new runner).
  - Changing the backup gate, its refusal semantics, or the `schema_migrations` ledger layout.
  - Adding steps or changing `WORKFLOW_SCHEMA_VERSION` / `WORKFLOW_VERSION_CODES`.
- **Dependencies**: This work blocks the recovery-schema phases of `plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md` (Phase 2 of its Issue) and `plans/20261030-113553_wftaskapi001_consolidate-task-persistence.md` (Phase 3 of its Issue): both need a safe table rebuild and a version bump, so this Plan is implemented first; those Plans are not edited here. Related archived work: `plans/done/20261029-214108_dbmig001_forward-only-db-migrations.md` and `issues/done/20261029-104500_dbmig001_forward-only-db-migrations.md` (closed; no open ordering dependency).

## Background
`MigrationRunner` (`shared.db_migrations`) is the safety layer for forward-only migrations of retained `workflow.sqlite` and `eventbus.sqlite` databases (landed by dbmig001). Its documentation claims each step is all-or-nothing, but `_apply_step` runs the step with `executescript` and commits afterwards. The operator CLI `migrate_db.py` opens the workflow database through `SQLiteHelper("workflow").open(write_mode=True)`, which turns `PRAGMA foreign_keys=ON` on, and takes the path only from configuration. `apply` writes the ledger row and re-checks the postcondition after the step's commit. `_TOOL_STATE_MUTATION_SQL` embeds the live `WORKFLOW_SCHEMA_VERSION` constant (`1.2.0` today). The recovery plans need steps that rebuild `tasks`, `attempts` and `processed_events` and rename a column. Their own Plans still describe `scripts/db/migrations_workflow.py` as absent; that is stale, the module exists (checked in Step 3).

## Problem
Confirmed this cycle (checked in Step 2, with throwaway scripts on temporary SQLite files only):
1. A step whose second statement fails leaves the first statement applied after the runner's `rollback`, because `executescript` commits any open transaction and runs statements in autocommit mode.
2. With `foreign_keys=ON`, `DROP TABLE` of a parent deletes the rows of an `ON DELETE CASCADE` child (1 row before, 0 after), so a rebuild step on the CLI path would destroy child history.
3. `PRAGMA foreign_keys=OFF` is a no-op inside an open transaction (confirmed: setting it after `BEGIN` leaves it unchanged), so the setting must be switched before the runner begins the transaction. Set before `BEGIN`, it takes effect, and `DROP TABLE` then leaves the child row.
4. The ledger row and the postcondition are written and run after the step commit, in separate transactions; a crash between them leaves a step applied but unrecorded.
5. `_TOOL_STATE_MUTATION_SQL` embeds `WORKFLOW_SCHEMA_VERSION`; raising that constant later would make the earlier step write the new version.

Also confirmed: DDL and `PRAGMA user_version` writes are rolled back together with an explicit transaction when statements are executed individually, so one transaction can hold a whole step including its version stamp.

## Reason for Change
The documented guarantee (atomic step, verified backup, recorded ledger) does not hold for the kind of step the next planned changes need, and the defects are invisible until such a step runs against real data. Fixing the runner first keeps the recovery plans from being its first test.

## Implementation Intent
Give a step an explicit transaction contract owned by the runner. For each step: run the preconditions as today; if the step opts in, read the current foreign-key setting and switch enforcement off (outside any transaction); begin one write transaction; execute the statements of `mutation_sql` individually; write the ledger row in the same transaction; if enforcement was switched off, run `PRAGMA foreign_key_check` and fail on any violation; run the optional pre-commit verification; commit; and in a `finally` restore the foreign-key setting. A failure at any point rolls the whole step back (statements, ledger row, version stamp). Existing steps behave exactly as before. The step's `postcondition` is kept as the post-commit re-check. Pin the tool_call_state version literal. Add a database-file option to the CLI so a migration can be rehearsed on a copy. Correct the docstring and the database documentation.

## Requirements
- `REQ-001`: The runner runs each step in one explicit write transaction with statements executed individually (no `executescript`); a failure at any statement leaves no partial change and no ledger row.
- `REQ-002`: The ledger row (and the step's version stamp) is committed in the same transaction as the step's statements, never in a separate later transaction.
- `REQ-003`: A step may opt in to foreign-key enforcement being off during the step; the setting is switched before the transaction begins, `PRAGMA foreign_key_check` runs before commit and a violation rolls the step back, and the previous setting is restored after every step including failures.
- `REQ-004`: A step may supply an optional pre-commit verification callback whose failure rolls the step back; the existing post-commit `postcondition` semantics for current steps are kept and the final order is documented (UNK-01).
- `REQ-005`: `_TOOL_STATE_MUTATION_SQL` writes the literal `1.2.0` regardless of the current `WORKFLOW_SCHEMA_VERSION`.
- `REQ-006`: `migrate_db.py` accepts a database file option and runs `--status`, `--dry-run` and `--apply` against that file instead of the configured database; the other modes and exit codes are unchanged, and a path that does not exist is refused rather than created (Derived: `sqlite3.connect` creates an empty file for a missing path).
- `REQ-007`: The `_apply_step` docstring (and the `MigrationRunner.apply` docstring ordering text) and the database documentation describe the actual transaction behavior, the new CLI option, and the postcondition order.
- `REQ-008`: Compatibility: the two registered workflow steps and the two eventbus steps produce results identical to today on a legacy database; the backup gate and its refusals, and the ledger table layout, are unchanged; `shared` still imports nothing from `db`; no steps or schema versions are added.
- `REQ-009`: Tests, written first and failing on current code, cover: a multi-statement step failing midway leaves the database unchanged; a table-rebuild step with child rows keeps every child row and a dangling reference fails closed before commit; the foreign-key setting is restored after success and failure; the ledger row and version stamp commit together; raising the head-version constant does not change what the tool_call_state step writes; the CLI works on a database copy.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/shared/db_migrations.py` | Runner transaction contract and `MigrationSpec` attributes | `_apply_step` uses `executescript`; `apply` writes the ledger row and runs the postcondition after commit; `MigrationSpec` has no foreign-key or pre-commit field; docstring is inaccurate | REQ-001, REQ-002, REQ-003, REQ-004, REQ-007, REQ-008; AC-1, AC-2, AC-3, AC-4, AC-7 | `MigrationSpec`, `MigrationRunner._apply_step`, `MigrationRunner.apply`, `record_applied` read in full; 15651 B against the 20480 B module-size gate (checked in Step 3) | `tests/shared/test_db_migrations.py`, `tests/eventbus/test_eventbus_migrations.py` | Verified |
| `scripts/db/migrations_workflow.py` | tool_call_state version literal | `_TOOL_STATE_MUTATION_SQL` is an f-string over `WORKFLOW_SCHEMA_VERSION`; its import becomes unused once replaced | REQ-005; AC-5 | `_TOOL_STATE_MUTATION_SQL` and the only use of `WORKFLOW_SCHEMA_VERSION` in this module found with `rg` (checked in Step 3) | `tests/db/test_migrations_workflow.py` | Verified |
| `scripts/db/migrate_db.py` | Database-file option | `main` always opens `SQLiteHelper("workflow")` from configuration; no path option | REQ-006; AC-6 | `main`; `SQLiteHelper.__init__` already accepts `db_path` and bypasses configuration when given (checked in Step 3) | `tests/db/test_migrations_workflow.py` | Verified |
| `tests/shared/test_db_migrations.py` | Runner transaction tests | Add failing-first tests for partial step, child-row loss, foreign-key restore, ledger-in-transaction | REQ-001, REQ-002, REQ-003, REQ-004, REQ-009; AC-1, AC-2, AC-3, AC-8 | Existing `TestMigrationFramework` with `_toy_registry` and `_init_db` helpers; no foreign-key or rebuild test exists (checked in Step 3) | itself | Verified |
| `tests/db/test_migrations_workflow.py` | Version-literal and CLI-copy tests | Add tests for the pinned `1.2.0` marker and `migrate_db.py` on a copy | REQ-005, REQ-006, REQ-009; AC-5, AC-6, AC-8 | `TestWorkflowToolCallStateStep`, `TestWorkflowCli` and `_run_cli` (sandboxed config dir, temporary database) exist (checked in Step 3) | itself | Verified |
| `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` | Document the per-step contract and CLI option | Section 8 text says "per-step transactionality" without stating the mechanism, ledger timing, foreign-key handling, the CLI option or the postcondition order | REQ-007; AC-7 | Shared-contract paragraph in section 8b and the 8a text read; no mention of the CLI database option (checked in Step 3) | `tools/check_docs_*` gates (Validation plan) | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file
  group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT
  appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as
  its own row when it requires modification — do not fold it into the row for the
  source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be
  `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/db/helper.py` | `SQLiteHelper.__init__` `db_path` argument and `apply_connection_pragmas` (`foreign_keys=ON` in write mode) define the CLI connection | REQ-003, REQ-006 |
| `scripts/eventbus/migrations.py` | Registered eventbus steps run on the same runner and must stay byte-identical in effect | REQ-008 |
| `scripts/eventbus/migrate.py` | Eventbus CLI opens a plain `sqlite3.connect` (foreign keys off, default isolation): the runner must work on such a connection | REQ-001, REQ-008 |
| `scripts/eventbus/schema.py` | `open_db` path calls `apply` on its own connection | REQ-001, REQ-008 |
| `tests/eventbus/test_eventbus_migrations.py` | Regression tests for the eventbus steps | REQ-008 |
| `scripts/db/create_schema.py` | Imports `WORKFLOW_SCHEMA_VERSION` and `ensure_baseline`; its create path must be unaffected | REQ-005, REQ-008 |
| `scripts/db/schema_sql.py` | Defines `WORKFLOW_SCHEMA_VERSION` (the constant the literal must stop following) | REQ-005 |
| `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` | Confirmed not to describe the step transaction; its section 11 sentence that "a migration feature does not exist" predates dbmig001 and is outside this Plan (UNK-04) | REQ-007 |
| `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | Its migration sentence ("rolls back to the last good version on a failing step (never half-applies a migration)") is consistent with the corrected behavior, so no ADR edit is needed (Needs ADR owner confirmation only if wording is later tightened) | REQ-007 |
| `docs/41_db/db_04_api_and_operations-module-boundaries-and-helper.md` | Already states that `executescript()` commits pending transactions, the statement the old docstring contradicted | REQ-007 |
| `plans/done/20261029-214108_dbmig001_forward-only-db-migrations.md` | Original REQ/design of the migration framework | REQ-008 |
| `rules/toolchain.md` | Validation sequence and diff-cover threshold | Validation plan |

## Acceptance Criteria
- `AC-1` (REQ-001, REQ-002): a step that fails at any statement leaves no partial change, and neither the ledger nor the version stamp advances.
- `AC-2` (REQ-003): a rebuild step with foreign-key enforcement off keeps all child rows, and a dangling reference makes the step fail before commit with the database unchanged.
- `AC-3` (REQ-003): the foreign-key pragma holds its prior value after every step, including failures and a refused precondition.
- `AC-4` (REQ-002, REQ-004): the ledger row and the version stamp are committed together with the step's changes, and a failing pre-commit verification rolls all of them back.
- `AC-5` (REQ-005): the tool_call_state step writes `1.2.0` regardless of the current head constant.
- `AC-6` (REQ-006): `migrate_db.py` run against a database copy supports `--status`, `--dry-run` and `--apply` and never opens the configured database; a missing path is refused without creating a file.
- `AC-7` (REQ-007): the runner docstring and `docs/41_db` describe the actual transaction behavior and the CLI option; the documentation checks pass.
- `AC-8` (REQ-008, REQ-009): the new tests fail on the current code and pass after the change; the existing runner, workflow and eventbus migration tests still pass unchanged; `lint-imports` reports no broken contract and `tools/check_module_size.py` passes.

## Tests
- `REQ-009` / `REQ-001`: toy step with two statements whose second fails; assert schema, ledger and `user_version` unchanged (fails today because the first statement persists).
- `REQ-009` / `REQ-003`: toy parent/child database opened with `foreign_keys=ON`; rebuild step with the opt-in keeps the child rows; a step that leaves a dangling reference fails and rolls back; the pragma value is read back after success, failure and refusal.
- `REQ-009` / `REQ-002`, `REQ-004`: ledger row visible only after commit (failure injected via a failing pre-commit callback leaves no ledger row and no stamp).
- `REQ-009` / `REQ-005`: with the head constant changed (module reloaded under a patched constant), migrating a legacy fixture still writes `1.2.0` to `workflow_schema_version`.
- `REQ-009` / `REQ-006`: `_run_cli` with the database-file option on a copy for `--status`, `--dry-run` (file byte-identical) and `--apply`; a missing path exits non-zero and creates nothing.
- `REQ-008`: regression run of `tests/shared/test_db_migrations.py`, `tests/db/test_migrations_workflow.py`, `tests/eventbus/test_eventbus_migrations.py`, `tests/eventbus/test_eventbus_db_migration.py`, `tests/deploy/test_init_db_ledger_gate.py`.
- All tests use temporary database files only; nothing opens the configured workflow database or any path under `/opt/llm`.

## Documentation Impact
Yes. `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` (section 8, shared migration contract paragraph; REQ-007) must state, as intent and failure behavior only: what is atomic per step, when the ledger row is written, how foreign-key enforcement is handled for a rebuild, the new CLI database-file option, and the postcondition order. Confirmed via the db_03 text that no other doc owns this statement; `db_07` and ADR-008 need no edit (see Reference Files). Run the docs checks listed in the Validation plan.

## Assumptions
- Statements of `mutation_sql` can be split safely with `sqlite3.complete_statement` accumulation, which also handles trigger bodies (Derived: `complete_statement` returns true for a `CREATE TRIGGER ... BEGIN ...; END;` text; the registered steps contain only plain DDL, `DELETE`/`INSERT` and `PRAGMA user_version`). The procedure phase may choose the splitting mechanism.
- The runner may issue an explicit `BEGIN IMMEDIATE` on the caller's connection because `apply` has already committed the ledger creation, leaving no open transaction (Derived from `apply`); a connection opened in an always-in-transaction mode is not supported and is covered by RISK below.
- `PRAGMA user_version` and DDL are transactional, so the version stamp inside `mutation_sql` is rolled back with the step (Confirmed with a throwaway script on a temporary file, this cycle).
- Preconditions keep their current position (before the transaction begins), so the CLI's first-step preflight and the "refusal never touches the database" invariant are unchanged (judgment call).
- The foreign-key setting is restored to the value read before the step, not forced to ON.
- Overlap check (Step 8b, `tools/check_plan_target_overlaps.py` run after freeze): no finding names this Plan; none of its six target files is a target of another Frozen Plan (the wfrecovery001, wftaskapi001, wflease001 and wfretry001 Plans do not list `scripts/shared/db_migrations.py`, `scripts/db/migrations_workflow.py` or `scripts/db/migrate_db.py`), so no compatible/sequencing/conflict judgment is needed beyond the Scope Dependencies entry.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether `postcondition` should move before commit (rolling the step back on failure) or stay after the commit; this Plan keeps it after commit and adds the separate pre-commit callback | Owner decision (Issue Unresolved Question 1) | Owner confirms at plan review; if "before commit" is chosen, amend REQ-004 and the db_03 text before procedure generation. Current default is safe because the pre-commit callback gives the rollback path | False |
| UNK-02 | Whether a `BEGIN` can be left open after a failed individually executed statement | Needs confirmation (Issue Unresolved Question 2) | Settled by the failure-injection test in REQ-009 (assert `conn.in_transaction` is false after the failure) | False |
| UNK-03 | Whether any configured workflow or eventbus database is at a version the head constants would misinterpret, or already has dangling foreign-key rows that would make a future opt-in step fail its `foreign_key_check` | Configured databases were not inspected (forbidden here); Needs confirmation | Rehearse on a copy with the new `--db` option and `--status` before any real apply; belongs to the deploy hand-off | False |
| UNK-04 | `docs/41_db/db_07` section 11 still says "a migration feature does not exist", which contradicts ADR-008 and db_03 for workflow and eventbus; not touched by this Plan | Needs confirmation whether it should be corrected by a separate docs Issue | Owner decides; if wanted, file a separate docs Issue (not part of this Plan's frozen scope) | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/shared/db_migrations.py` | Modify | High: shared runner used by the workflow CLI, `db` registry, eventbus CLI, `eventbus.schema`, and tests | 3 commits | High (single author) | not applicable (rsynced) |
| `scripts/db/migrations_workflow.py` | Modify | Medium: workflow registry, imported by `migrate_db.py`, `create_schema.py` and tests | 4 commits | High (single author) | not applicable (rsynced) |
| `scripts/db/migrate_db.py` | Modify | Low: operator CLI only (`deploy/init_db.sh` only checks that the ledger table exists, it does not run the CLI) | 3 commits | High (single author) | not applicable (rsynced) |
| `tests/shared/test_db_migrations.py` | Modify | Low: test-only | 2 commits | High (single author) | not applicable (rsynced) |
| `tests/db/test_migrations_workflow.py` | Modify | Low: test-only | 2 commits | High (single author) | not applicable (rsynced) |
| `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` | Modify | Low: documentation, referenced by ADR-008 and db_03_07 | 27 commits | High (one author under two name spellings) | not applicable (rsynced) |

## Design
Path B (more than 3 files, shared runner, CLI and docs). Architecture: `shared` is a leaf; the runner stays stdlib-only and receives all domain behavior as injected callables or `MigrationSpec` fields, so `lint-imports` stays kept (checked: 6 contracts kept at baseline, Step 3). Callers are `db.migrate_db`, `db.migrations_workflow` (registry), `eventbus.migrate`, `eventbus.schema.open_db`, and `eventbus.migrations` (registry); the eventbus callers use plain `sqlite3.connect` connections with foreign keys off, so the new code must not assume `foreign_keys=ON` and must restore whatever value it found.

Design decisions (alternatives and compatibility impact):
1. Transaction owner. Chosen: the runner issues an explicit `BEGIN IMMEDIATE`, executes statements one by one, inserts the ledger row, commits once. Alternatives: keep `executescript` and embed `BEGIN`/`COMMIT` in step SQL (rejected: `executescript` commits first and runs in autocommit, which is the defect); `SAVEPOINT` per step (rejected: cannot switch foreign keys and adds nothing over a top-level transaction). Impact: existing steps are plain statements, so behavior is identical; `PRAGMA user_version` stays inside the transaction.
2. Statement splitting. Chosen: split by `sqlite3.complete_statement` accumulation, so trigger bodies survive. Alternative: split on `;` (rejected: breaks triggers). Impact: registered steps only contain simple statements.
3. Foreign-key control. Chosen: opt-in `MigrationSpec` boolean (default off, i.e. enforcement untouched); switch off before `BEGIN`, `foreign_key_check` before commit, restore in `finally`. Alternative: always disable (rejected: changes existing steps). Impact: default steps are unaffected.
4. Verification order. Chosen: new optional pre-commit callback plus unchanged post-commit `postcondition` (UNK-01 records the owner choice). Impact: the existing `_postcondition_fingerprint` and `_postcondition_tool_state` keep their meaning, since both run after commit and read the committed ledger and `user_version`.
5. Version pinning. The tool_call_state step writes its own literal; `WORKFLOW_VERSION_CODES` and `create_schema` stay as they are (no schema change in this Plan).
6. CLI database option. `SQLiteHelper("workflow", db_path=...)` already bypasses configuration, so no helper change is needed. A missing path is refused before opening.

Module-size note: `scripts/shared/db_migrations.py` is 15651 B against the 20480 B gate; the added transaction code is expected to fit, and `tools/check_module_size.py` is part of the validation (RISK below if it does not).

## Implementation steps
1. **Phase 1: Failing tests first**
   - [ ] Add runner tests for partial step, child-row loss, foreign-key restore, ledger-in-transaction and failing pre-commit verification (REQ-001, REQ-002, REQ-003, REQ-004, REQ-009; `tests/shared/test_db_migrations.py`).
   - [ ] Add the pinned-version test and the CLI-copy tests (REQ-005, REQ-006, REQ-009; `tests/db/test_migrations_workflow.py`). Confirm each new test fails on current code.
2. **Phase 2: Runner transaction contract**
   - [ ] Add the opt-in foreign-key attribute and the optional pre-commit verification field to `MigrationSpec` (REQ-003, REQ-004; `scripts/shared/db_migrations.py`).
   - [ ] Rework `_apply_step` and the ledger write in `apply` into one runner-owned transaction with `finally` restore of the foreign-key setting; keep preconditions and the post-commit `postcondition` order (REQ-001, REQ-002, REQ-003, REQ-008; `scripts/shared/db_migrations.py`).
   - [ ] Correct the `_apply_step` and `apply` docstrings (REQ-007; `scripts/shared/db_migrations.py`).
3. **Phase 3: Version literal**
   - [ ] Replace the f-string version with the literal `1.2.0` and drop the then-unused import (REQ-005; `scripts/db/migrations_workflow.py`).
4. **Phase 4: CLI database option**
   - [ ] Add the database-file option, refuse a missing path, keep modes and exit codes (REQ-006; `scripts/db/migrate_db.py`).
5. **Phase 5: Documentation**
   - [ ] Update the shared migration contract text and describe the CLI option and postcondition order (REQ-007; `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`).
6. **Phase 6: Validation and deployment hand-off**
   - [ ] Run the Validation plan commands (all REQ).
   - [ ] Deployment hand-off: `scripts/` changes are deployed through `skills/deploy/SKILL.md`; prerequisite is that the change is committed and pushed first, and deploying is the user's decision (approval gate). Rehearse `migrate_db.py --db <copy> --dry-run` before any real apply (REQ-006; `scripts/db/migrate_db.py`).

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/shared/db_migrations.py`, `tests/shared/test_db_migrations.py` | Unit, temporary SQLite files, toy steps | `uv run pytest tests/shared/test_db_migrations.py` | New tests fail before Phase 2 and pass after; old tests pass |
| `scripts/db/migrations_workflow.py`, `scripts/db/migrate_db.py`, `tests/db/test_migrations_workflow.py` | Unit and CLI subprocess on temporary files | `uv run pytest tests/db/test_migrations_workflow.py` | Pass, including pinned literal and CLI-on-copy |
| Eventbus callers of the runner | Regression | `uv run pytest tests/eventbus/test_eventbus_migrations.py tests/eventbus/test_eventbus_db_migration.py tests/deploy/test_init_db_ledger_gate.py` | Pass unchanged |
| Touched Python files | Format, lint, types, security | `uv run ruff format`, `uv run ruff check`, `uv run mypy --no-namespace-packages <files>`, `uv run bandit -r scripts/ -c pyproject.toml` | Clean on touched files (bandit baseline: 0 undefined, Medium 8, High 43 repo-wide before change, no findings in these three modules; checked in Step 5) |
| Import layering and size | Architecture | `PYTHONPATH=scripts uv run lint-imports`, `uv run python tools/check_module_size.py` | 6 contracts kept; `scripts/shared/db_migrations.py` under 20480 B |
| Complexity baseline | Static | `uv run radon cc <file> -s` per target | No function worse than before by more than one grade; baseline: `MigrationRunner.plan` C(14), `main` in `migrate_db.py` C(12), `apply` B(8), `_apply_step` A(4) |
| Diff coverage | Coverage | `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` (sequence in `rules/toolchain.md` section 7) | At least 90% on changed lines; current baseline number not recorded this cycle (needs the full-suite coverage run, not run here) |
| `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` | Docs gates | `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_consistency.py --domain db`, `uv run python tools/check_docs_japanese.py` | All pass |

## Risks
- **Risk**: The runner's explicit `BEGIN` fails on a caller connection that already has an open transaction or runs in an always-in-transaction mode (likelihood: low; the eventbus and workflow callers use default connections). → **Mitigation**: `apply` already commits the ledger creation before the loop; the runner checks `conn.in_transaction` at step start and raises a clear error; tests run toy steps on default-isolation and `isolation_level=None` connections and the eventbus regression tests run unchanged.
- **Risk**: Statement splitting differs from `executescript` for an existing step and changes its effect (likelihood: low). → **Mitigation**: REQ-008 regression asserts the schema, ledger and `user_version` of the four registered steps equal the pre-change results; registered SQL contains only plain statements.
- **Risk**: A crash between the step's statements and commit now rolls everything back, but SQLite WAL recovery is relied on (likelihood: low). → **Mitigation**: the backup gate is unchanged and still runs before any step; a rollback leaves the last ledger-recorded version.
- **Risk**: Foreign-key enforcement is left off if the restore is skipped (likelihood: low, high impact). → **Mitigation**: restore in `finally`, tested after success, failure and refused precondition (AC-3).
- **Risk**: Pre-existing dangling foreign-key rows in a real database make a future opt-in step fail its `foreign_key_check` (UNK-03). → **Mitigation**: fail-closed is intended; rehearse on a copy with `--db` first.
- **Risk**: `scripts/shared/db_migrations.py` grows past the 20480 B module-size gate (likelihood: low; 15651 B now). → **Mitigation**: `tools/check_module_size.py` in validation; if exceeded, extract the transaction helper with `module_nodes.py` rather than raising the baseline.
- **Risk**: A `--db` pointed at a live database used by a running agent while `--apply` runs (likelihood: low). → **Mitigation**: unchanged from today (SQLite busy handling and the backup gate); documentation states the option is for rehearsal on a copy.
- **Risk**: Blast radius of the shared runner reaches the eventbus startup path (`eventbus.schema.open_db`). → **Mitigation**: eventbus regression tests are in the validation plan; `deploy` hand-off follows `skills/deploy/SKILL.md` and is the user's decision.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Failing-first tests (`tests/shared/test_db_migrations.py`, `tests/db/test_migrations_workflow.py`) | Pending | — | — | |
| 2 | Runner transaction contract and docstrings (`scripts/shared/db_migrations.py`) | Pending | — | — | |
| 3 | tool_call_state version literal (`scripts/db/migrations_workflow.py`) | Pending | — | — | |
| 4 | CLI database-file option (`scripts/db/migrate_db.py`) | Pending | — | — | |
| 5 | Database documentation (`docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`) | Pending | — | — | |
| 6 | Validation and deployment hand-off (all target files) | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261101-133004_dbmigrunner001_runner-unsafe-table-rebuild.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261101-133244
- **Related target files**: scripts/shared/db_migrations.py, scripts/db/migrations_workflow.py, scripts/db/migrate_db.py, tests/shared/test_db_migrations.py, tests/db/test_migrations_workflow.py, docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Problem 1, Required Changes 1; `MigrationRunner._apply_step` uses `executescript` | `scripts/shared/db_migrations.py` | Step 2 | AC-1 | Tests: multi-statement failure; Validation plan row 1 | Confirmed by repository evidence |
| REQ-001 | Same | `tests/shared/test_db_migrations.py` | Step 1 | AC-1 | Partial-step test | Confirmed by repository evidence |
| REQ-002 | Issue Problem 4, Required Changes 1; `apply` writes the ledger after commit | `scripts/shared/db_migrations.py` | Step 2 | AC-1, AC-4 | Ledger-in-transaction test | Confirmed by repository evidence |
| REQ-002 | Same | `tests/shared/test_db_migrations.py` | Step 1 | AC-4 | Ledger-in-transaction test | Confirmed by repository evidence |
| REQ-003 | Issue Problem 2 and 3, Required Changes 2 | `scripts/shared/db_migrations.py` | Step 2 | AC-2, AC-3 | Child-row and foreign-key restore tests | Confirmed by repository evidence |
| REQ-003 | Same | `tests/shared/test_db_migrations.py` | Step 1 | AC-2, AC-3 | Child-row and restore tests | Confirmed by repository evidence |
| REQ-004 | Issue Required Changes 3, Unresolved Question 1 | `scripts/shared/db_migrations.py` | Step 2 | AC-4 | Failing pre-commit callback test | Derived from confirmed evidence |
| REQ-004 | Same | `tests/shared/test_db_migrations.py` | Step 1 | AC-4 | Failing pre-commit callback test | Derived from confirmed evidence |
| REQ-005 | Issue Problem 5, Required Changes 4; `_TOOL_STATE_MUTATION_SQL` f-string | `scripts/db/migrations_workflow.py` | Step 3 | AC-5 | Pinned-literal test | Confirmed by repository evidence |
| REQ-005 | Same | `tests/db/test_migrations_workflow.py` | Step 1 | AC-5 | Pinned-literal test | Confirmed by repository evidence |
| REQ-006 | Issue Required Changes 5; `main` has no path option; `SQLiteHelper` accepts `db_path` | `scripts/db/migrate_db.py` | Step 4 | AC-6 | CLI-copy tests | Confirmed by repository evidence |
| REQ-006 | Same | `tests/db/test_migrations_workflow.py` | Step 1 | AC-6 | CLI-copy tests | Confirmed by repository evidence |
| REQ-007 | Issue Required Changes 6, Documentation Impact; db_03 and `_apply_step` docstring | `scripts/shared/db_migrations.py` | Step 2 | AC-7 | Docs gates; review of docstring | Confirmed by repository evidence |
| REQ-007 | Same | `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` | Step 5 | AC-7 | Docs gates (Validation plan) | Confirmed by repository evidence |
| REQ-008 | Issue Constraints; eventbus steps share the runner | `scripts/shared/db_migrations.py` | Step 2 | AC-8 | Regression runs (Validation plan rows 2-3) | Explicit in issue |
| REQ-008 | Same | `scripts/db/migrations_workflow.py` | Step 3 | AC-8 | Workflow regression tests | Explicit in issue |
| REQ-009 | Issue Required Changes 7, Testing Expectations, AI Implementation Instruction | `tests/shared/test_db_migrations.py` | Step 1 | AC-8 | Failing-first runs | Explicit in issue |
| REQ-009 | Same | `tests/db/test_migrations_workflow.py` | Step 1 | AC-8 | Failing-first runs | Explicit in issue |
