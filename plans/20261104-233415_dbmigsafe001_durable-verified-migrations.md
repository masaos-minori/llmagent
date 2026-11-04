## Goal
- Make the shared migration runner a fully auditable migration-safety workflow: a durable verified pre-migration archive, WAL-consistent dry-run, mutation-integrity checks that run before commit, distinguishable machine-readable refusal reasons, deterministic ledger ordering, and CLI version semantics documented for operators and automation.

## Priority
High

## Scope
- **In-Scope**:
  - Durable pre-migration archive created with the SQLite backup API, plus an audit artifact recording archive path, SHA-256, source version, creation time, and retention status.
  - Dry-run snapshots created with the SQLite backup API instead of `shutil.copyfile` (WAL content included; live database unchanged).
  - Move mutation-integrity assertions from `postcondition` to `pre_commit_verification` in both registries; postconditions become observational only.
  - New distinct `MigrationRefusalReason` values for checkpoint-busy, in-memory refusal, missing archive target, and archive failure; documentation of the `PRAGMA wal_checkpoint(FULL)` behavior.
  - Deterministic ledger ordering: `read_ledger` orders by the ledger row's append sequence (`rowid`), with a `seq` field on `LedgerRow`. No ledger DDL change.
  - Documented version semantics in `migrate_db.py --status` (integer migration code plus semantic `workflow_schema_version` marker) and updated migration docs, including the current `0 -> 1 -> 2 -> 3 -> 4` workflow chain and the two eventbus steps.
  - Restoration-validation tests for a run that fails after at least one earlier step committed, restoring from the durable archive.
- **Out-of-Scope**: Eventbus schema creation/validation redesign (issue `20261104-143443_ebschema001`), recovery from corruption (`scripts/db/recovery*.py`), new migration steps, archive retention/pruning policy implementation, any change to already-frozen `mutation_sql` text.
- **Dependencies**: The source issue lists `issues/20261104-143443_ebschema001_separate-eventbus-schema-create-validate-migrate.md`: both touch `scripts/eventbus/migrations.py` and the shared ledger; coordinate the ledger-ordering change with the eventbus migrations. This Plan lands first (memo cycle order 5 before 6); the ebschema001 Plan must re-verify its `scripts/eventbus/migrations.py` and eventbus CLI rows against this Plan's post-change state.

## Background
Adversarial verification against current source (2026-11-04) confirmed every mechanism the issue cites, with two corrections:

- `_run_pre_migration_gate` copies the database with `live_conn.backup()` into a `tempfile.mkstemp` file and always unlinks it in `finally`; no durable pre-run recovery point survives (`scripts/shared/db_migrations.py` L205-L260).
- `MigrationRunner.apply` runs `spec.postcondition(conn)` after `_apply_step` has committed the step and ledger row (`scripts/shared/db_migrations.py` L412-L415, L479); the workflow specs put their `user_version`/shape assertions in `_postcondition_*` functions (`scripts/db/migrations_workflow.py` L204, L268, L331, L392), and no workflow or eventbus spec sets `pre_commit_verification`, so a failed integrity assertion cannot roll back.
- Dry-run uses `shutil.copyfile(db_path, tmp_path)` (`scripts/shared/db_migrations.py` L383), which omits committed content still in the WAL.
- A non-zero `PRAGMA wal_checkpoint(FULL)` busy count raises `NO_VERIFIED_BACKUP` (L217-L221), the same reason as in-memory refusal (L225-L229), backup integrity failure (L237-L242), and verifier failure (L243-L253). No ADR documents the FULL-checkpoint choice.
- `read_ledger` orders by `applied_at, id` (L146-L149) while `applied_at` has one-second granularity (L49), so same-second steps order by id text. The eventbus test suite already flags this caveat (`tests/eventbus/test_eventbus_migrations.py` L161-L162 comment).
- Partially disconfirmed: `scripts/db/migrate_db.py` already prints both `user_version=` and `marker=` on `--status` (L74-L75). The remaining gap is that neither field's meaning is documented, and the docs still describe the outdated chain and step set.
- Doc staleness found during verification: `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` L44 says the workflow chain is `0 -> 1 -> 2 -> 3` while the registry head is 4 (`_ATTEMPT_LEASE_VERSION`, `scripts/db/migrations_workflow.py` L71), and L52 says eventbus has "one registered forward-only migration" while `REGISTRY` now has two steps (`eventbus_ledger_baseline`, `eventbus_dlq_outbox`, `scripts/eventbus/migrations.py` L153-L172).
- The issue's "runner tests (path: Unknown)" resolved to: `tests/shared/test_db_migrations.py` (runner), `tests/db/test_migrations_workflow.py` (workflow registry), `tests/eventbus/test_eventbus_migrations.py` (eventbus registry). No test calls `migrate_database`; no test covers WAL-visible dry-run content, distinct gate refusal reasons, or same-second ledger order.

## Problem
Whole-run recoverability, mutation rejection before commit, WAL-consistent dry-run, distinguishable refusal reasons, and deterministic audit order are not guaranteed. These concerns share one execution boundary (the shared runner), so archive, verification, and ledger changes must stay compatible across both domains.

## Reason for Change
Data-integrity and audit risk on a forward-only migration path executed against production databases: a mid-run failure currently has no durable restore point, post-commit integrity failures leave the database mutated, and the audit trail can misorder steps applied within one second.

## Implementation Intent
Keep the temporary gate copy and the durable archive as separate concepts in code and docs. The gate stays fail-closed and transient; a second, durable backup-API archive is written before the step loop with a machine-readable audit artifact. Every mutation-integrity assertion moves inside the step transaction (`pre_commit_verification`) so a failed check changes neither schema, `user_version`, nor ledger. Ledger order becomes the append sequence rather than a timestamp. CLI version semantics are documented rather than newly invented, because the fields already print.

## Requirements
- `REQ-001`: A durable pre-migration archive is created with the SQLite backup API before any step runs; its path, SHA-256, source `user_version`, creation time, and retention status are recorded in a machine-readable audit artifact; archive failure refuses the run (fail closed).
- `REQ-002`: Dry-run snapshots are produced with `sqlite3.Connection.backup()` (WAL content included) and leave the live database byte-unchanged.
- `REQ-003`: Mutation-integrity assertions in both registries run as `pre_commit_verification` inside the step transaction; `postcondition` is no longer used to assert mutation correctness.
- `REQ-004`: Checkpoint-busy, in-memory refusal, missing archive target, and archive failure each raise a distinct `MigrationRefusalReason` value; backup/integrity/verifier failures keep `NO_VERIFIED_BACKUP`; the refusal set and the FULL-checkpoint behavior are documented.
- `REQ-005`: `read_ledger` returns rows in actual application order (append sequence via `rowid`, exposed as `LedgerRow.seq`), independent of `applied_at` granularity; existing ledgers stay readable without DDL change.
- `REQ-006`: CLI `--status` semantics are documented: `user_version=` is the integer migration code and `marker=` is the semantic `workflow_schema_version` string; docs describe both and the current step chains.
- `REQ-007`: A migration that fails after at least one earlier step committed can be restored to the exact pre-run logical state from the durable archive; a test validates this end to end.

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/shared/db_migrations.py | Extend refusal reasons; add durable archive API and audit artifact; replace dry-run `shutil.copyfile` with backup-API snapshot; order `read_ledger` by append sequence and add `LedgerRow.seq` | Core runner: gate copy is transient (L231-L260), checkpoint-busy reuses `NO_VERIFIED_BACKUP` (L217-L221), dry-run misses WAL (L383), ledger order is `applied_at, id` (L146-L149) | REQ-001, REQ-002, REQ-004, REQ-005 / AC-001, AC-003, AC-004, AC-005, AC-006 | `scripts/shared/db_migrations.py` L49, L59-L73, L117-L158, L205-L261, L368-L396, L410-L431 | tests/shared/test_db_migrations.py, tests/db/test_migrations_workflow.py, tests/eventbus/test_eventbus_migrations.py | Verified |
| scripts/db/migrations_workflow.py | Move `user_version`/shape/fingerprint assertions from `_postcondition_*` to `pre_commit_verification` callbacks on all four registered specs; wire the archive API into `migrate_database` | Failed postcondition currently runs after commit (runner L412-L415) and cannot roll back the step | REQ-003, REQ-001 / AC-002 | `scripts/db/migrations_workflow.py` L204-L218, L268-L281, L331-L347, L392-L409, L411-L448, L450-L472 | tests/db/test_migrations_workflow.py | Verified |
| scripts/eventbus/migrations.py | Move baseline/outbox integrity checks from `_postcondition_*` to `pre_commit_verification`; wire the archive API into the eventbus apply path; ledger-ordering compatibility | Same post-commit gap as workflow; shares the runner and ledger with `read_ledger` | REQ-003, REQ-005, REQ-001 / AC-002, AC-006 | `scripts/eventbus/migrations.py` L122-L151, L153-L172, L176-L193 | tests/eventbus/test_eventbus_migrations.py | Verified |
| scripts/db/migrate_db.py | Require an explicit archive target for `--apply`; map new gate-family refusal reasons to `EXIT_GATE_FAILURE`; document the `--status` field semantics in help text | CLI must supply the operator-chosen archive location and stable exit mapping; `user_version=`/`marker=` already print (L74-L75) but are undocumented | REQ-001, REQ-004, REQ-006 / AC-001, AC-005, AC-007 | `scripts/db/migrate_db.py` L34-L38, L67-L81, L135-L160 | tests/db/test_migrations_workflow.py | Verified |
| scripts/eventbus/migrate.py | Same CLI changes as the workflow CLI: explicit archive target for `--apply`, refusal-reason exit mapping, documented `--status` semantics | Eventbus CLI mirrors the workflow CLI and maps only `NO_VERIFIED_BACKUP` today | REQ-001, REQ-004, REQ-006 / AC-001, AC-005, AC-007 | `scripts/eventbus/migrate.py` L35-L38, L61-L70, L137-L144 | tests/eventbus/test_eventbus_migrations.py | Verified |
| tests/shared/test_db_migrations.py | Add tests: distinct refusal reasons per gate branch, backup-API dry-run visibility of WAL content, durable archive creation/SHA-256/audit artifact, ledger `seq` ordering with identical `applied_at` values | Each runner branch changed by REQ-001/002/004/005 needs unit coverage | REQ-001, REQ-002, REQ-004, REQ-005 / AC-001, AC-003, AC-004, AC-006 | `tests/shared/test_db_migrations.py` L241-L296 (existing gate/dry-run tests share one reason today) | — | Verified |
| tests/db/test_migrations_workflow.py | Convert postcondition tests to pre-commit equivalents asserting schema/`user_version`/ledger unchanged; add archive + late-step-failure restore integration test in WAL mode; update `--status` semantics assertions | REQ-003 behavior change and REQ-007 restore validation are workflow-domain acceptance | REQ-003, REQ-007, REQ-006 / AC-002, AC-007 | `tests/db/test_migrations_workflow.py` L622-L648 (postcondition tests), L695-L727 (gate tests), L915-L958 (status tests) | — | Verified |
| tests/eventbus/test_eventbus_migrations.py | Add same-second ledger-order regression using `seq`; keep registry pinning green through the pre-commit move; cover new refusal reasons through the shared gate | Ledger change must remain compatible with the eventbus registry (issue constraint) | REQ-005, REQ-003, REQ-004 / AC-002, AC-006 | `tests/eventbus/test_eventbus_migrations.py` L114 (registry pin), L161-L162 (same-second ordering caveat) | — | Verified |
| docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md | Update migration contract section: refusal-reason table, durable archive and audit artifact, WAL dry-run semantics, ledger ordering key, version semantics (`user_version` integer vs `marker` string), workflow chain `0 -> 1 -> 2 -> 3 -> 4`, two eventbus steps | Existing text is stale (L44 chain stops at 3; L52 claims one eventbus step) and lacks the new contract | REQ-001..REQ-007 / AC-001..AC-007 | `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` L44, L52, L58, L76-L77 | — | Verified |

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
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/db/helper.py | `SQLiteHelper("workflow").open(write_mode=True)` is how `migrate_db.py` opens the database; dry-run/archive calls must not change its isolation or locking behavior | scripts/db/migrate_db.py, REQ-002 |
| scripts/db/schema_sql.py | Canonical workflow DDL and the `workflow_schema_version` marker constant the `marker=` field reports | scripts/db/migrations_workflow.py, REQ-006 |
| scripts/eventbus/schema.sql | Canonical eventbus DDL ending in `PRAGMA user_version = N;` that the outbox step must equal | scripts/eventbus/migrations.py, REQ-003 |
| scripts/shared/eventbus_schema_fingerprint.py | Fingerprint used by the eventbus baseline postcondition being moved to `pre_commit_verification` | scripts/eventbus/migrations.py, REQ-003 |
| scripts/db/create_schema.py | Writes the workflow string marker at creation; confirms the fresh-versus-migrated convergence assumption | scripts/db/migrations_workflow.py, REQ-006 |
| rules/persisted-schema-change.md | Planning checklist whose item outcomes are recorded in Design | All REQ |

## Acceptance Criteria
- `AC-001` (REQ-001): A verified pre-migration archive remains available after both success and failure of the run, and its audit artifact contains path, SHA-256, source version, creation time, and retention status.
- `AC-002` (REQ-003, REQ-007): A partial multi-step migration can be restored from the archive to the exact pre-run logical state (rows, `user_version`, ledger rows equal pre-run values).
- `AC-003` (REQ-003): A failed `pre_commit_verification` changes neither schema, `user_version`, nor ledger.
- `AC-004` (REQ-002): A dry-run sees rows committed in the WAL and leaves the live database byte-identical.
- `AC-005` (REQ-004): Checkpoint-busy refusal and backup-failure refusal carry different `MigrationRefusalReason` values observable at the CLI exit-code boundary.
- `AC-006` (REQ-005): Ledger output preserves actual application order when several steps finish within one second.
- `AC-007` (REQ-006): CLI `--status` output shows both the integer migration code and the semantic marker, and the docs define both fields.

## Tests
- `REQ-001` unit: gate refusal when the archive target is unwritable or missing (distinct `no_archive_target` reason); archive creation writes file + audit artifact with correct SHA-256 and source version; archive survives a later step failure.
- `REQ-002` integration: WAL-mode database with committed-but-uncheckpointed rows; dry-run gate observes those rows; live file and its sidecars unchanged byte-for-byte after dry-run.
- `REQ-003` unit: each workflow step and each eventbus step — a `pre_commit_verification` failure rolls back schema, `user_version`, and ledger together (existing postcondition tests converted, not deleted).
- `REQ-004` unit: checkpoint-busy, in-memory, backup-integrity, and verifier-failure branches each raise their own reason value; CLI maps gate-family reasons to `EXIT_GATE_FAILURE`.
- `REQ-005` unit: three ledger rows recorded with the same explicit `applied_at` are returned in insertion order via `seq`; the eventbus registry test's same-second caveat is replaced with a `seq`-based order assertion.
- `REQ-006` unit: `--status` prints `user_version=` and `marker=` with the documented field names (existing `test_status_reports_marker_and_empty_ledger` extended).
- `REQ-007` integration: apply a multi-step path with a fault injected into the last step (earlier steps committed), restore from the durable archive, and assert the restored database equals the pre-run snapshot (row counts, `user_version`, ledger, marker).
- Full sequence per `rules/toolchain.md`: targeted pytest runs, then full `uv run pytest`, ruff, mypy.

## Documentation Impact
Docs update required. `docs/00_index.md`'s task-scope mapping for migration/operations points at the `docs/41_db/` migration-and-scaling document: it must document the refusal-reason set (including the FULL-checkpoint behavior as implemented, pending the ADR decision), the durable archive concept separate from the gate copy, the audit artifact fields, the ledger ordering key, the version semantics of `user_version` vs `marker`, the corrected workflow chain `0 -> 1 -> 2 -> 3 -> 4`, and the two eventbus steps. All REQ-001..REQ-007 drive this document. The ADRs named as missing (FULL checkpoint, workflow schema version) are recorded as Unknowns — creating an ADR requires an owner decision this Plan cannot make.

## Assumptions
- Ledger tables are append-only today (`record_applied` is the only writer; no DELETE/UPDATE of ledger rows exists), so `rowid` order equals application order for existing databases; this is tested before relying on it (Phase 4).
- Changing a registered spec's verification callbacks (not its `mutation_sql` text) does not affect databases that already applied the step; frozen-text rule (`rules/persisted-schema-change.md` item 5) is satisfied because no step SQL changes.
- `migrate_db.py` and `scripts/eventbus/migrate.py` are the only production entry points that call `MigrationRunner.apply` with `dry_run=False`; no other caller needs the archive argument. Verified by repository grep for `MigrationRunner` usage during Phase 3.
- The workflow DB file and eventbus DB file are separate databases; each domain supplies its own archive directory and audit artifact (no cross-database archive).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Archive retention period, pruning policy, production storage location defaults, and file permissions | No retention config, owner policy, or ADR exists in the repository | Operator supplies `--archive-dir` per invocation (no location inferred in code); retention/pruning decision must come from the owner before any automated cleanup is ever built — record as open question per the issue's AI instruction | True for any retention automation; False for this Plan's scope (no pruning implemented) |
| UNK-02 | Whether `PRAGMA wal_checkpoint(FULL)` is a requirement or intentional conservatism (no ADR located; `grep wal_checkpoint docs/` finds none for the migration gate) | No ADR or design note states the mandate | Implementer documents current behavior only; the ADR decision must come from the owner before the requirement is asserted as mandated | True for the ADR artifact; False for the code change (behavior unchanged) |
| UNK-03 | Workflow schema-version ADR (semantic marker history) absent | No ADR file found for `workflow_schema_version` | Owner decision; docs record the mapping as implemented | False |
| UNK-04 | Operational runbooks/cron entries that invoke `--apply` without an archive target would start refusing | Production invocation inventory not inspectable from the repository | Confirm live invocation patterns with operations before deploying; docs update the runbook section | True for deployment enablement; False for implementation |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/shared/db_migrations.py | Feature + refactor | high (shared runner consumed by both domains; refusal enum is a public contract) | 4 commits | 1 | N/A: no deployment file change; CLIs gain a required flag |
| scripts/db/migrations_workflow.py | Refactor | medium (registry spec callbacks; called by migrate_db and create_schema convergence paths) | 7 commits | 1 | N/A |
| scripts/eventbus/migrations.py | Refactor | medium (shared by eventbus CLI and service startup paths) | 3 commits | 1 | N/A |
| scripts/db/migrate_db.py | Feature | medium (operator CLI contract: required flag for --apply) | 4 commits | 1 | N/A: not called by deploy.sh/init_db.sh (verify in Phase 8) |
| scripts/eventbus/migrate.py | Feature | medium (operator CLI contract) | 1 commits | 1 | N/A |
| tests/shared/test_db_migrations.py | Test | low | 3 commits | 1 | N/A |
| tests/db/test_migrations_workflow.py | Test | low | 5 commits | 1 | N/A |
| tests/eventbus/test_eventbus_migrations.py | Test | low | 3 commits | 1 | N/A |
| docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md | Docs | low | 22 commits | 1 | N/A |

## Design
Six decisions, grounded in Step 5 analysis of the runner boundary:

1. **Archive is a second, durable backup — the gate copy stays as is.** `scripts/shared/db_migrations.py` gains an `archive_pre_migration(live_conn, archive_dir)` step that: runs after the existing transient gate passes and before the step loop; writes `live_conn.backup()` to a new file named `<db-stem>-v<user_version>-<utc-stamp>.sqlite` under the caller-provided directory; runs `PRAGMA integrity_check` and hashes SHA-256 on the archive; writes a sidecar JSON audit artifact `{archive_path, sha256, source_db, source_version, created_at, retention_status}`; and refuses (`ARCHIVE_FAILURE` or `NO_ARCHIVE_TARGET`) on any problem. Retention status is the literal `"unset"` until UNK-01 is resolved; nothing ever prunes archives. The archive target comes only from the operator (`--archive-dir` on both CLIs, required for `--apply`); no location is inferred in code, per the issue's AI instruction. Dry-run does not create archives.
2. **Distinct refusal classes.** `MigrationRefusalReason` gains `CHECKPOINT_BUSY = "checkpoint_busy"`, `IN_MEMORY_DATABASE = "in_memory_database"`, `NO_ARCHIVE_TARGET = "no_archive_target"`, `ARCHIVE_FAILURE = "archive_failure"`; `NO_VERIFIED_BACKUP` stays for integrity/verifier failures. Both CLIs map the gate-family reasons to `EXIT_GATE_FAILURE` and keep `EXIT_REFUSAL` for path refusals. Enum values are additive; existing `NO_VERIFIED_BACKUP` behavior is unchanged.
3. **WAL-consistent dry-run.** The dry-run branch replaces `shutil.copyfile` with: create temp file, `live_conn.backup(backup_conn)` (the backup API reads through the WAL and takes only a shared lock), then run the gate against that snapshot connection. The live database is never written; the snapshot temp file is unlinked as today.
4. **Pre-commit integrity verification.** Each of the four workflow specs and both eventbus specs moves its `user_version`/shape/fingerprint assertions into a `pre_commit_verification` callback that runs inside the step transaction after `mutation_sql` and the ledger row (the runner already invokes it at L476-L477 before commit). The old `_postcondition_*` functions are removed from the specs (spec `postcondition` field stays supported by the runner for observational checks only, documented in the `MigrationSpec` docstring). Mutation SQL text is untouched — frozen-step rule respected (`rules/persisted-schema-change.md` item 5: SQL frozen, callbacks are code).
5. **Ledger order = append sequence.** `read_ledger` selects `rowid` as `seq` and orders by `rowid`; `LedgerRow` gains `seq: int = 0` (keyword-compatible addition). No ledger DDL change, no registered migration step, no `applied_at` format change (mixed second/`%f` formats would sort wrongly). The alternative — a registered `seq` column — was rejected under `rules/persisted-schema-change.md` items 2/4/6: it would add DDL and a version-stamped step to fix a read-ordering problem that `rowid` already solves for append-only ledgers; kept as an open question if a future Plan ever writes ledger rows out of order.
6. **Version semantics are documented, not re-invented.** `--status` already prints both `user_version=` (integer ledger code) and `marker=` (semantic `workflow_schema_version` string, workflow domain only); the change documents both semantics in CLI help and in the migration doc, and corrects the doc's stale chain/step facts.

`rules/persisted-schema-change.md` item outcomes: item 1 — applies read-only: this Plan changes no version store writers; it documents the two stores already identified (workflow integer + string marker; eventbus `user_version`). Item 2 — does not apply: no table/column/index change, so no fingerprint move and no new step. Item 3 — does not apply: no table rebuild. Item 4 — does not apply: no new persisted column. Item 5 — applies as constraint: no `mutation_sql` text may change in Phase 5; convergence tests must stay green. Item 6 — applies: registry-pinning tests (`tests/db/test_migrations_workflow.py` L125-L169, `tests/eventbus/test_eventbus_migrations.py` L114) are named as updated in the same change. Item 7 — does not apply: no existing values gain a new meaning; ledger rows are re-ordered only in read output.

## Implementation steps
1. **Phase 1: Refusal-reason classes (REQ-004)**
   - [ ] Add the four new `MigrationRefusalReason` values and default messages; route the checkpoint-busy and in-memory branches to their own reasons (scripts/shared/db_migrations.py)
   - [ ] Map new reasons to `EXIT_GATE_FAILURE` in both CLIs and extend their help text (scripts/db/migrate_db.py, scripts/eventbus/migrate.py)
   - [ ] Convert the two gate tests to assert distinct reason values per branch; add in-memory branch test (tests/shared/test_db_migrations.py, tests/db/test_migrations_workflow.py)
2. **Phase 2: Backup-API dry-run (REQ-002)**
   - [ ] Replace `shutil.copyfile` with a backup-API snapshot connection in the dry-run branch (scripts/shared/db_migrations.py)
   - [ ] Add a WAL-mode test: committed-uncheckpointed rows are visible to the dry-run gate; live file and sidecars byte-identical after dry-run (tests/shared/test_db_migrations.py)
3. **Phase 3: Durable archive + audit artifact (REQ-001)**
   - [ ] Add `archive_pre_migration` with integrity check, SHA-256, and JSON audit artifact; wire it into `apply` between gate and step loop (scripts/shared/db_migrations.py)
   - [ ] Add required `--archive-dir` to `--apply` in both CLIs and pass it to the runner; document refusal when the target is missing or unwritable (scripts/db/migrate_db.py, scripts/eventbus/migrate.py)
   - [ ] Wire the archive call points through the domain helpers (scripts/db/migrations_workflow.py, scripts/eventbus/migrations.py)
   - [ ] Unit tests: artifact fields correct, archive survives later failure, `no_archive_target` refusal (tests/shared/test_db_migrations.py)
4. **Phase 4: Ledger ordering (REQ-005)**
   - [ ] Select `rowid` as `seq` and order by `rowid` in `read_ledger`; add `LedgerRow.seq`; verify the append-only assumption by grepping all ledger writers first (scripts/shared/db_migrations.py)
   - [ ] Same-second ordering regression test with explicit identical `applied_at` values; replace the eventbus caveat comment with a `seq`-based assertion (tests/shared/test_db_migrations.py, tests/eventbus/test_eventbus_migrations.py)
5. **Phase 5: Pre-commit verification move (REQ-003)**
   - [ ] Convert `_postcondition_*` assertions into `pre_commit_verification` callbacks on all four workflow specs; remove the `postcondition=` arguments; keep `mutation_sql` byte-identical (scripts/db/migrations_workflow.py)
   - [ ] Same conversion for both eventbus specs, fingerprint check included (scripts/eventbus/migrations.py)
   - [ ] Update postcondition tests into pre-commit equivalents asserting schema/`user_version`/ledger unchanged (tests/db/test_migrations_workflow.py, tests/eventbus/test_eventbus_migrations.py)
6. **Phase 6: Version semantics documentation (REQ-006)**
   - [ ] Extend `--status` help/docstrings naming `user_version` as the integer migration code and `marker` as the semantic string version (scripts/db/migrate_db.py, scripts/eventbus/migrate.py)
   - [ ] Extend the status tests to pin both fields' meaning (tests/db/test_migrations_workflow.py)
7. **Phase 7: Restoration validation + docs (REQ-007, docs)**
   - [ ] Integration test in WAL mode with the production-equivalent workflow schema: late-step fault after earlier commits, restore from the durable archive, assert equality with the pre-run snapshot (tests/db/test_migrations_workflow.py)
   - [ ] Rewrite the migration-contract passages: refusal-reason table, archive + audit artifact, WAL dry-run, ledger ordering key, version semantics, chain `0 -> 1 -> 2 -> 3 -> 4`, two eventbus steps (docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md)
8. **Phase 8: Full verification and operational dependency check**
   - [ ] Run the full toolchain per `rules/toolchain.md` (all target tests, then full suite, ruff, mypy)
   - [ ] Confirm `deploy.sh`/`init_db.sh` never invoke `migrate_db.py` or `migrate.py --apply` (so the new required flag breaks no deployment path); record the result (scripts/db/migrate_db.py, scripts/eventbus/migrate.py — inspection only)

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/shared/db_migrations.py | Unit (reasons, dry-run WAL snapshot, archive, ledger seq) | `uv run pytest tests/shared/test_db_migrations.py` | All pass; distinct reasons observable on exception objects |
| scripts/db/migrations_workflow.py | Integration (WAL-mode real files, pre-commit rollback, restore-from-archive) | `uv run pytest tests/db/test_migrations_workflow.py` | Failed pre-commit check changes nothing; restore equals pre-run snapshot |
| scripts/eventbus/migrations.py | Unit + registry pinning | `uv run pytest tests/eventbus/test_eventbus_migrations.py` | Registry pins green; same-second order asserted via `seq` |
| scripts/db/migrate_db.py, scripts/eventbus/migrate.py | CLI-level (exit codes, required flag) | `uv run pytest tests/db/test_migrations_workflow.py tests/eventbus/test_eventbus_migrations.py` plus manual `--help` | `--apply` without `--archive-dir` refuses with `EXIT_REFUSAL`; gate-family reasons exit 1 |
| whole change | Static analysis + full suite | `uv run ruff check . && uv run mypy scripts/ && uv run pytest` | Clean |
| docs/41_db/db_03 | Doc checker | `uv run python tools/check_docs.py` (per `routing.md` Tools) | No findings |

## Risks
- **Risk**: `Connection.backup()` on a live database takes a shared lock; a busy source makes the dry-run or archive step raise `sqlite3.OperationalError` where `shutil.copyfile` would have silently copied a torn file. → **Mitigation**: fail closed with `ARCHIVE_FAILURE`/gate refusal (correct behavior: a torn copy was the bug), and cover a busy-source test.
- **Risk**: `rowid` ordering assumes append-only ledger writes; an out-of-band tool could insert ledger rows out of order. → **Mitigation**: Phase 4 greps every `INSERT INTO schema_migrations` writer before relying on it; the assumption is recorded in Assumptions and tested.
- **Risk**: Removing `postcondition=` from six registered specs could mask a regression the old checks caught post-commit. → **Mitigation**: equivalent `pre_commit_verification` callbacks assert the same conditions strictly before commit; converted tests keep the same names and coverage.
- **Risk**: Unbounded archive growth fills disk in production. → **Mitigation**: no archive automation ships in this Plan; UNK-01 blocks any pruning decision and the audit artifact is the inventory; docs state the operator's retention duty.
- **Risk**: Two Plans edit `scripts/eventbus/migrations.py` in adjacent cycles. → **Mitigation**: this Plan lands first; the ebschema001 Plan must re-verify its rows against the post-change file (Scope dependency note).

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Refusal-reason classes | Pending | — | — | |
| 2 | Phase 2: Backup-API dry-run | Pending | — | — | |
| 3 | Phase 3: Durable archive + audit artifact | Pending | — | — | |
| 4 | Phase 4: Ledger ordering | Pending | — | — | |
| 5 | Phase 5: Pre-commit verification move | Pending | — | — | |
| 6 | Phase 6: Version semantics documentation | Pending | — | — | |
| 7 | Phase 7: Restoration validation + docs | Pending | — | — | |
| 8 | Phase 8: Full verification and operational dependency check | Pending | — | — | |

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
- **Source issue**: issues/20261104-143443_dbmigsafe001_durable-verified-migrations.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261104-233415
- **Related target files**: scripts/shared/db_migrations.py, scripts/db/migrations_workflow.py, scripts/eventbus/migrations.py, scripts/db/migrate_db.py, scripts/eventbus/migrate.py, tests/shared/test_db_migrations.py, tests/db/test_migrations_workflow.py, tests/eventbus/test_eventbus_migrations.py, docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md

### Requirement Traceability
See `templates/requirement-traceability.md` for the canonical column format.

| REQ | Source issue line | Acceptance criteria | Implementation target file | Test | Phase |
|---|---|---|---|---|---|
| REQ-001 | Required Changes bullet 1 | AC-001 | scripts/shared/db_migrations.py, scripts/db/migrations_workflow.py, scripts/eventbus/migrations.py, scripts/db/migrate_db.py, scripts/eventbus/migrate.py | tests/shared/test_db_migrations.py | 3 |
| REQ-002 | Required Changes bullet 2 | AC-004 | scripts/shared/db_migrations.py | tests/shared/test_db_migrations.py | 2 |
| REQ-003 | Required Changes bullet 3 | AC-002, AC-003 | scripts/db/migrations_workflow.py, scripts/eventbus/migrations.py | tests/db/test_migrations_workflow.py, tests/eventbus/test_eventbus_migrations.py | 5 |
| REQ-004 | Required Changes bullet 4 | AC-005 | scripts/shared/db_migrations.py, scripts/db/migrate_db.py, scripts/eventbus/migrate.py | tests/shared/test_db_migrations.py, tests/db/test_migrations_workflow.py | 1 |
| REQ-005 | Required Changes bullet 5 | AC-006 | scripts/shared/db_migrations.py | tests/shared/test_db_migrations.py, tests/eventbus/test_eventbus_migrations.py | 4 |
| REQ-006 | Required Changes bullet 6 | AC-007 | scripts/db/migrate_db.py, scripts/eventbus/migrate.py | tests/db/test_migrations_workflow.py | 6 |
| REQ-007 | Required Changes bullet 7 | AC-002 | tests/db/test_migrations_workflow.py | tests/db/test_migrations_workflow.py | 7 |
