## Goal
- Replace the recreate-on-schema-change policy for `workflow.sqlite` and `eventbus.sqlite` with an ordered, forward-only migration framework gated on a verified recovery point, and add recovery drills for all four SQLite domains that produce measured restore-time and data-loss-window evidence.

## Priority
High

## Scope
- **In-Scope**:
  - Forward-only migration framework (registry entry: ID, source/target version, preconditions, postconditions, transaction boundary, schema fingerprint).
  - Pre-migration gate: WAL checkpoint + backup + independent integrity verification of the backup.
  - Downgrade and unknown-path rejection; original database preserved on failure/interruption.
  - Dry-run mode with byte-identical databases.
  - Migration ledger table per canonical database.
  - Startup validation of schema version and fingerprint before ready (fail-closed preserved).
  - Recovery drills for `rag.sqlite`, `session.sqlite`, `workflow.sqlite`, `eventbus.sqlite` with retained audit artifacts.
  - ADR-008 decision-record update for the recreate-only policy change.
- **Out-of-Scope**:
  - Migrations for `rag.sqlite` and `session.sqlite` (drills only).
  - Cross-database transactions, replicated storage, multi-host deployment.
  - Automatic restore on corruption beyond the existing `recover_corruption` policy.
  - Unrelated refactoring or formatting-only changes.
- **Dependencies**:
  - Blocks `issues/20261029-104503_toolexec001_idempotent-tool-call-snapshot.md` (new workflow tables must land through migrations) and `issues/20261029-104501_dlqbox001_dlq-sqlite-outbox.md` (outbox adds a table to `eventbus.sqlite`); this plan lands first.
  - Issue text called `ebdlqrecon002` procedures and the `ebaudit005` plan "in flight"; adversarial verification on 2026-10-29 confirmed both are archived (`implementations/done/20261029-085348_*`, `plans/done/`, publish-order procedures `implementations/done/20261029-101422_*`). No ordering constraint remains from them; they changed EventBus code but not the schema, as the issue states.
  - Shared target with `plans/20261029-214650_adrauth001_adr-authority-model.md`: `docs/10_adr/adr_01_index.md` (flagged by `check_plan_target_overlaps.py` 2026-10-29). Fix order: adrauth001 lands before this Plan's Phase 6; the ADR List table stays hand-maintained in both designs (adrauth001 generates only the graph sections), and the ADR-008 primary claim in `config/adr_authority.toml` is unchanged by this amendment (only the decision text changes), so the designs do not contradict.

## Background
ADR-008 records that the four databases "have no migration mechanism and are recreated on a schema change" and that backups are "periodic file copies (`rotate_all_dbs()`), not continuously verified Snapshots" (`docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`). Verified in current source: `scripts/eventbus/schema.py::_init_schema` refuses a database stamped with a different `PRAGMA user_version` ("recreate the database", never migrated); `scripts/db/create_schema.py` records `WORKFLOW_SCHEMA_VERSION` on a new database and refuses a different one; `scripts/db/schema_sql.py` defers the migrate-vs-recreate decision for `session`/`rag`. Partial recovery building blocks exist: `scripts/db/recovery.py` runs `PRAGMA integrity_check`, verifies backup domain identity (rag/session/workflow/eventbus targets supported), restores, and re-verifies; `scripts/db/rotation.py::rotate_all_dbs()` archives all four databases. No drill tooling, schedule, or RPO/RTO measurement exists (absence search under `scripts/`, `tools/`, `docs/`, `deploy/` finds nothing, re-verified 2026-10-29).

## Problem
`workflow.sqlite` and `eventbus.sqlite` hold canonical recovery state (tasks, attempts, events, delivery state, offsets, DLQ state). A schema change today discards that state via recreation. Backups are copied but never exercised end to end, so restore time and data loss are unknown and unproven.

## Reason for Change
Every later schema change to a canonical domain — the workflow tables planned in `toolexec001` and the EventBus outbox table decided in `dlqbox001` (owner confirmed outbox adoption on 2026-10-29) — is forced into destructive recreation until a migration path exists. Severity High: data integrity of canonical state.

## Implementation Intent
Treat migration and recovery as one lifecycle: no migration runs without a verified backup and a deterministic failure path. Keep `PRAGMA user_version` plus the schema fingerprint as the compatibility contract between binary and database. Reuse the existing integrity-check and domain-identity helpers in `scripts/db/recovery.py` rather than writing parallel ones. Framework core lives in `shared/` because the `.importlinter` contract forbids `eventbus` from importing `db`; domain-specific migration registries stay in their own layers (`scripts/db/`, `scripts/eventbus/`). `session.sqlite` and `rag.sqlite` keep their recreate policy; drills cover them.

## Requirements
- `REQ-001`: Ordered forward-only migration framework: per-migration ID, source and target version, preconditions, postconditions, explicit transaction boundary, and schema-fingerprint validation after apply.
- `REQ-002`: Pre-migration gate: WAL checkpoint, backup, and independent integrity verification of the backup; a migration is refused without a verified backup.
- `REQ-003`: Reject downgrades and unknown migration paths; a failed or interrupted migration leaves the original database intact and diagnosable.
- `REQ-004`: Dry-run mode performs no database mutation; target databases remain byte-identical.
- `REQ-005`: Fail-closed startup preserved: schema version and fingerprint are validated before a binary reports ready; an unsupported or malformed schema stops startup.
- `REQ-006`: Migration ledger: each canonical database records applied migration IDs and versions; ledger and fingerprint together prove the applied state.
- `REQ-007`: Recovery drills for all four SQLite domains: measure restore time and data-loss window, retain results as audit artifacts.
- `REQ-008`: ADR-008's recreate-only decision change is recorded as a new approval record in the ADR set, not a silent edit.
- `REQ-009`: `workflow.sqlite` and `eventbus.sqlite` schema upgrades on registered paths preserve canonical rows; unregistered paths keep today's refusal.

## Implementation Target Files
**Freeze status**: Frozen (Amended 2026-10-30: row `tools/check_db_separation.py` appended after the last row during `code-implementation` of the `scripts/db/schema_sql.py` row — an additional target file discovery; re-validated: file exists, concrete change, evidence reproduced, linked to REQ-001/REQ-006, no path overlap with Reference Files, `check_workitem_structure.py` re-run. Original validation: Step 8 Implementation Target Files Validation passed on 2026-10-29: every row exists-or-is-new-with-evidence, is linked to a Plan requirement, and is `Verified`; `check_workitem_structure.py` and `check_plan_target_overlaps.py` report no findings. Re-verified 2026-10-29 against `HEAD c5a8285dd` after a tree reorganization landed during planning (`f7f7616f3 refactor: reorganize scripts/ into domain-based packages`): every existing target path and evidence anchor re-confirmed against the reorganized tree; untracked pre-reorganization copies (`scripts/shared/{dlq,session_db,wiki_db,memory,user_profiles,terminal_lock_db,agent_token_store,skill_tools}.py`, `scripts/asset_service.py`, `configs/`) were cleaned from the working tree and never existed in git history — the plan never depended on them.)

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/shared/db_migrations.py` | New: domain-neutral migration framework (registry entry dataclass, runner, pre-migration checkpoint/backup/integrity gate, ledger write, dry-run, refusal semantics) | `.importlinter` forbids `eventbus` → `db`; both layers need one framework; `shared` (`scripts/shared/`) is the only layer both may import | REQ-001, REQ-002, REQ-003, REQ-004, REQ-006 | `.importlinter` contracts `db-only-uses-shared`, `eventbus-is-isolated`; precedent `shared/eventbus_schema_fingerprint.py`, `shared/db_maintenance.py` | `tests/shared/test_db_migrations.py` | Verified |
| `scripts/eventbus/migrations.py` | New: `eventbus.sqlite` migration registry (future version steps register here) | Domain-specific migrations must live in the `eventbus` layer | REQ-001, REQ-009 | `scripts/eventbus/schema.py:68-96` (version refusal today); `scripts/eventbus/schema.sql` stamps `PRAGMA user_version` | `tests/eventbus/test_eventbus_migrations.py` | Verified |
| `scripts/eventbus/schema.py` | Replace recreate-refusal with framework lookup: registered forward path migrates (gate-gated), unknown/downgrade still refuses | Today `_init_schema` raises on version mismatch; must accept only registered paths | REQ-003, REQ-005, REQ-009 | `scripts/eventbus/schema.py::_init_schema` refusal text "recreate the database" | `tests/eventbus/test_eventbus_schema_version.py`, `tests/eventbus/test_eventbus_migrations.py` | Verified |
| `scripts/eventbus/schema.sql` | Version-stamp baseline remains the post-migration fingerprint source; add ledger table DDL | Ledger table must exist for `eventbus.sqlite` | REQ-001, REQ-006 | `scripts/eventbus/schema.sql` read by `_SCHEMA_PATH` in `schema.py` | `tests/eventbus/test_eventbus_migrations.py`, `tests/db/test_eventbus_schema_equivalence.py` | Verified |
| `scripts/eventbus/migrate.py` | New: migration CLI for `eventbus.sqlite` (dry-run, apply, ledger status) using the shared framework and the eventbus registry | Operators need an explicit, testable entry point separate from startup | REQ-001, REQ-002, REQ-004, REQ-006 | `scripts/eventbus/` already ships per-concern modules (`schema.py`, `dlq.py`) | `tests/eventbus/test_eventbus_migrations.py` | Verified |
| `scripts/db/migrations_workflow.py` | New: `workflow.sqlite` migration registry (future version steps register here) | Domain-specific migrations live in the `db` layer | REQ-001, REQ-009 | `scripts/db/schema_sql.py:25` `WORKFLOW_SCHEMA_VERSION = "1.1.0"`; `scripts/db/create_schema.py` refuses other versions | `tests/db/test_migrations_workflow.py` | Verified |
| `scripts/db/migrate_db.py` | New: migration CLI for `workflow.sqlite` (dry-run, apply, ledger status) using the shared framework and the workflow registry | Operator entry point; also the drill-adjacent migration status command | REQ-001, REQ-002, REQ-004, REQ-006 | `scripts/db/create_schema.py` is today's only schema entry point | `tests/db/test_migrations_workflow.py` | Verified |
| `scripts/db/create_schema.py` | New-database path additionally creates the migration ledger and stamps the baseline version | Baseline databases must be ledger-compatible from creation | REQ-001, REQ-006 | `scripts/db/create_schema.py` records version on new DB and refuses a different one | `tests/db/test_create_schema.py` | Verified |
| `scripts/db/schema_sql.py` | Add `schema_migrations` ledger DDL to the workflow DDL set | Ledger table must exist for `workflow.sqlite` | REQ-001, REQ-006 | `scripts/db/schema_sql.py` holds the workflow DDL and `WORKFLOW_SCHEMA_VERSION` | `tests/db/test_create_schema.py`, `tests/db/test_migrations_workflow.py` | Verified |
| `scripts/db/recovery.py` | Expose integrity-check and domain-identity helpers for reuse by drills (no behavior change) | Issue instruction: reuse existing helpers instead of parallel ones | REQ-002, REQ-007 | `scripts/db/recovery.py` `_run_integrity_check`, `_verify_domain_identity`, `_backup_is_usable`; supports targets rag/session/workflow/eventbus | `tests/db/test_db_recovery.py` (regression: unchanged behavior) | Verified |
| `scripts/db/recovery_drill.py` | New: drill harness for all four domains — rotate a recovery point, restore into an isolated copy, measure restore time and data-loss window, write audit artifacts | No drill tooling exists (absence search) | REQ-007 | Absence search across `scripts/`, `tools/`, `docs/`, `deploy/` for "recovery drill"/"restore drill"/RPO/RTO | `tests/db/test_recovery_drill.py` | Verified |
| `scripts/db/rotation.py` | Post-archive integrity check on each archived file (archived copy becomes a verified recovery point) | Today archives are unverified file copies; the framework requires verified recovery points | REQ-002, REQ-007 | `scripts/db/rotation.py::rotate_all_dbs()` archives without verification | `tests/db/test_db_maintenance.py` | Verified |
| `deploy/init_db.sh` | Create ledger-compatible baselines; document/enable drill invocation on deployed databases | Deployed databases must be migration-compatible | REQ-006, REQ-007 | `deploy/init_db.sh` creates current databases via `create_schema` paths | `tests/deploy/` suite | Verified |
| `tests/shared/test_db_migrations.py` | New: framework regression tests (migration success, mid-migration failure, interrupted migration, downgrade rejection, unknown-path rejection, dry-run byte preservation, backup-gate refusal) | Issue Testing Expectations | REQ-001–REQ-004 | New test module; no existing migration tests (`tests/eventbus/test_eventbus_db_migration.py` covers only pragmas) | — | Verified |
| `tests/eventbus/test_eventbus_migrations.py` | New: eventbus migration registry + CLI tests incl. fault injection between backup and migration | Issue Testing Expectations | REQ-002, REQ-003, REQ-009 | New test module | — | Verified |
| `tests/eventbus/test_eventbus_schema_version.py` | Extend: registered-path migration now succeeds; unknown/downgrade still refused | Startup validation contract changes for registered paths | REQ-003, REQ-005, REQ-009 | Existing file tests version refusal | — | Verified |
| `tests/db/test_migrations_workflow.py` | New: workflow migration registry + CLI tests incl. fault injection | Issue Testing Expectations | REQ-002, REQ-003, REQ-009 | New test module | — | Verified |
| `tests/db/test_create_schema.py` | Extend: ledger creation and version stamping on new databases; fingerprint tests extended to migrated schemas | Issue Testing Expectations | REQ-001, REQ-006 | Existing file tests schema version behavior | — | Verified |
| `tests/db/test_recovery_drill.py` | New: drill harness tests (four domains, artifact emission, measurement fields) | Issue Testing Expectations | REQ-007 | New test module | — | Verified |
| `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | Update decision text: migration contract for `workflow`/`eventbus`, backup/recovery-point gate, failure behavior; recreate policy kept for `rag`/`session` | ADR-008 currently states no migration mechanism | REQ-008, REQ-009 | ADR-008 lines quoted in issue Background (verified present) | docs checkers | Verified |
| `docs/10_adr/adr_01_index.md` | Record the ADR-008 amendment/approval row in the index | Approval record must be discoverable, not a silent edit | REQ-008 | Index lists ADR status/date rows including ADR-008 | docs checkers | Verified |
| `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` | State the migration contract, pre-migration backup requirement, and failure behavior | Doc currently states recreate-only for `workflow.sqlite` | REQ-009 | Doc quoted in issue Background (verified present) | docs checkers | Verified |
| `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` | Drill runbook: procedure, frequency placeholder, artifact retention location | Issue asks which runbook carries the procedure; this is the DB recovery/reference doc | REQ-007 | `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` is the DB recovery doc | docs checkers | Verified |
| `tools/check_db_separation.py` | Register the `schema_migrations` ledger table in `TABLE_OWNERSHIP` for `workflow` and `eventbus` | The table-ownership check fails with `workflow.sqlite creates table 'schema_migrations', which is not in the inventory` as soon as the ledger DDL lands (reproduced 2026-10-30 while executing the `scripts/db/schema_sql.py` row); the file's own comment says to update the inventory when a table is added | REQ-001, REQ-006 | `tools/check_db_separation.py:55-77` (`TABLE_OWNERSHIP`); `uv run python tools/check_db_separation.py` output | `tests/tools/test_check_db_separation.py::test_live_repository_has_no_violations` (existing, unmodified) | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | Issue instruction: read ADR-008 before editing; decision text is the amendment base | REQ-008 |
| `scripts/shared/eventbus_schema_fingerprint.py` | Shared fingerprint contract that migration postconditions must reuse, not duplicate | REQ-001 (`scripts/shared/db_migrations.py`) |
| `scripts/db/config.py` | `DbConfig` resolves all four database paths; drills and CLIs consume it | REQ-007 (`scripts/db/recovery_drill.py`) |
| `scripts/db/recovery_restore.py` | Existing restore path drills must not duplicate | REQ-007 |
| `scripts/db/recovery_verification.py` | Existing restore-verification path to reuse | REQ-007 |
| `scripts/agent/services/workflow_schema.py` | Existing startup schema check for `workflow.sqlite`; REQ-005 must remain satisfied through it | REQ-005 |
| `scripts/eventbus/schema.sql` | Current baseline DDL and version stamp; migration postcondition source | `scripts/eventbus/schema.sql` row |
| `rules/env.md` | Production DB locations and service layout for drill/deploy steps | REQ-007 |
| `.importlinter` | Layer contract that fixes the framework's home in `shared` | REQ-001 |

## Acceptance Criteria
- AC-1 (REQ-009): Canonical rows survive every supported schema upgrade on registered paths for `workflow.sqlite` and `eventbus.sqlite`.
- AC-2 (REQ-003): A failed or interrupted migration leaves the original database intact and diagnosable (ledger unchanged, refusal logged with migration ID).
- AC-3 (REQ-005): A binary cannot start against an unsupported or malformed schema; registered-but-failed versions still refuse startup.
- AC-4 (REQ-002): Every applied migration has a verified backup recorded before mutation; without one the runner refuses.
- AC-5 (REQ-004): Dry-run leaves the target databases byte-identical (hash-compare test).
- AC-6 (REQ-007): Drill artifacts exist for all four domains with restore-time and data-loss-window measurements; results are retained and reviewed.
- AC-7 (REQ-008): ADR-008 and `adr_01_index.md` carry the approval record; no silent edit.

## Tests
- Framework regression tests (REQ-001–REQ-004): migration success, failure mid-migration, interrupted migration, downgrade rejection, unknown-path rejection, dry-run byte preservation — each written to fail before the change and pass after.
- Fault injection (REQ-002): failure between backup and migration, and during migration; assert original DB intact.
- Schema-version/fingerprint tests extended to migrated schemas (REQ-005, REQ-009) in `tests/eventbus/test_eventbus_schema_version.py` and `tests/db/test_create_schema.py`.
- Drill harness tests (REQ-007): all four domains produce artifacts with the required measurement fields.
- Suite commands: `uv run pytest tests/db tests/eventbus tests/shared`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `uv run python tools/check_db_separation.py`, `lint-imports`, and the docs checkers named in `routing.md` for the doc rows.

## Documentation Impact
Yes. `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` + `docs/10_adr/adr_01_index.md` (REQ-008 approval record), `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` (REQ-009 migration contract), and `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` (REQ-007 drill runbook) are target rows. Task mapping follows `docs/00_index.md` "DB layer spec (schema, ops, known issues)" and the ADR index. Docs state intent, boundaries, constraints, and failure behavior only, per `skills/DESIGN.md` Docs content policy.

## Assumptions
- Step 3a correction (2026-10-30): the Plan wrote `shared/db_migrations.py`; the importable package root is `scripts/` (`.importlinter` `root_packages`, `scripts/shared/` exists, `shared/` at the repository root does not), so the file is `scripts/shared/db_migrations.py`. `workflow.sqlite` migrations run through the CLI (`scripts/db/migrate_db.py`) only; `scripts/agent/services/workflow_schema.py` (a Reference File, not a target) keeps refusing a mismatched version at startup, and the migration records the new `workflow_schema_version` row so the check passes afterwards.
- Framework home is `shared/` because `eventbus` cannot import `db` (`.importlinter` contract `eventbus-is-isolated`); `shared` holds DB-adjacent helpers already (`eventbus_schema_fingerprint.py`, `db_maintenance.py`).
- Migration ledger is a new `schema_migrations` table in each canonical DB; the existing `workflow_schema_version` table stays as the baseline marker (issue's ledger-reuse question resolved this way; owner can veto).
- `rag.sqlite` and `session.sqlite` receive drills only, no migrations (issue Out-of-Scope; owner has not extended scope).
- RPO/RTO numeric targets and drill scheduling/retention ownership remain open (user decision 2026-10-29: proceed with them as open Unknowns; drills are built to *measure* them, not to a preset target).
- Step 3a correction (2026-10-30): one migration is registered at landing. Adding the `schema_migrations` ledger table to `scripts/eventbus/schema.sql` changes the canonical fingerprint, so the stamp moves from `PRAGMA user_version = 3` to 4 and the eventbus registry carries a `ledger-baseline` spec (3 to 4); without it every existing version 3 database would be refused (REQ-009). The workflow ledger is created idempotently by `ensure_ledger` and `WORKFLOW_SCHEMA_VERSION` is not bumped. The first other consumers are `toolexec001` (workflow tables) and `dlqbox001` (eventbus outbox table).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | RPO/RTO target values and drill scheduling/artifact-retention owner | No RPO/RTO definition exists anywhere in repo | Owner decision before drill scheduling goes live; framework/drill code does not depend on the numbers (user confirmed open-Unknown handling 2026-10-29) | False |
| UNK-02 | Whether `workflow_schema_version` should be reused instead of a new `schema_migrations` ledger | No decision record | Recorded as a Design decision; owner veto handled in procedure review | False |
| UNK-03 | Whether `rag.sqlite`/`session.sqlite` later gain migrations | Owner intent unknown | Assumption: drills only; revisit if owner extends scope | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/shared/db_migrations.py` | New module | Used by `db` and `eventbus` migration paths; shared-layer additions affect all layers | N/A (new) | High (single author) | Covered by `deploy.sh` whole-`scripts/`+shared sync; no `deploy.sh` edit |
| `scripts/eventbus/schema.py` | Startup path change | EventBus startup/health; running service holds `eventbus.sqlite` (confirmed via `ss`/`fuser` 2026-10-29, port 8015) | 10 | High (single author) | Synced by `rsync scripts/`; needs service restart |
| `scripts/eventbus/schema.sql` | Ledger DDL addition | Fingerprint baseline changes | 8 | High (single author) | Synced by `rsync scripts/` |
| `scripts/db/schema_sql.py` | Ledger DDL addition | Workflow/session/rag DDL consumers | 11 | High (single author) | Synced by `rsync scripts/` |
| `scripts/db/create_schema.py` | Ledger bootstrap | All DB creation paths incl. `deploy/init_db.sh` | 7 | High (single author) | Synced by `rsync scripts/` |
| `scripts/db/recovery.py` | Helper exposure only | Recovery path used by maintenance | 6 | High (single author) | Synced by `rsync scripts/` |
| `scripts/db/rotation.py` | Backup verification added | All rotation/maintenance callers | 0 | High (single author) | Synced by `rsync scripts/` |
| `deploy/init_db.sh` | Baseline/ledger + drill hook | Deployment init on production DBs | 4 | High (single author) | Direct deploy-time change; `init_db.sh` re-run required |
| `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | Decision text + approval | Governance reference used across plans | 4 | High (single author) | N/A: docs only |
| `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` | Contract text | DB spec reference | 26 | High (single author) | N/A: docs only |
| `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` | Runbook text | Ops reference | 23 | High (single author) | N/A: docs only |
| Other target rows (new CLIs, registries, tests) | New/extended | Scoped to their own test suites | N/A (new) or 3–15 | High (single author) | New scripts synced by `rsync scripts/` |

## Design
- Framework in `scripts/shared/db_migrations.py`: a `MigrationSpec` (id, from_version, to_version, precondition SQL/checks, mutation SQL, postcondition fingerprint check) plus a runner that (1) reads the current version and fingerprint through a per-domain version accessor (`PRAGMA user_version` for `eventbus.sqlite`; the latest `workflow_schema_version` row for `workflow.sqlite` — Step 3a correction 2026-10-30) and the existing `build_fingerprint` helper of `scripts/shared/eventbus_schema_fingerprint.py` (connection-based, reusable against DDL applied to an in-memory database), (2) resolves a unique ordered forward path, (3) checkpoints WAL, takes a SQLite backup-API copy, and runs `PRAGMA integrity_check` + domain-identity on the copy, (4) applies the path inside one transaction per migration step, (5) writes the ledger row and re-verifies the fingerprint, (6) on any error rolls back the step and leaves the DB at the last ledger-recorded version. Downgrade, cycle, and unknown targets are refusals, never repairs.
- Domain registries: `scripts/eventbus/migrations.py` and `scripts/db/migrations_workflow.py` register specs; startup code (`scripts/eventbus/schema.py`, workflow validation via `scripts/agent/services/workflow_schema.py`) consults the framework: registered path → migrate (with the gate); anything else → today's fail-closed refusal.
- CLIs (`scripts/eventbus/migrate.py`, `scripts/db/migrate_db.py`): `--dry-run` (runner executes resolution + gate against a throwaway copy and mutates nothing), `--apply`, `--status` (ledger print). Exit codes distinguish refusal classes.
- Ledger: `schema_migrations(id TEXT PRIMARY KEY, applied_at TEXT, from_version TEXT, to_version TEXT)` (Step 3a correction 2026-10-30: versions are TEXT because `workflow.sqlite` records the semver string `WORKFLOW_SCHEMA_VERSION = "1.1.0"` in `workflow_schema_version`, not `PRAGMA user_version`; `eventbus.sqlite` stores its integer `user_version` as text) in each canonical DB; created at DB creation and at framework introduction on existing DBs (a version-0 stamping step, mirroring the existing unstamped-database stamping logic in `scripts/eventbus/schema.py`).
- Drills (`scripts/db/recovery_drill.py`): for each domain — rotate to a timestamped archive, verify with the `recovery.py` helpers, restore into an isolated temp copy (never the live file), run domain identity + fingerprint checks, record elapsed restore time and the data-loss window (archive timestamp vs drill time) into a JSON artifact under the archive directory. RPO/RTO are the measured outputs (UNK-01).
- Failure-path invariant: original database files are only ever replaced by restore from a verified backup; migration failure paths never touch them beyond SQLite transaction rollback.

## Implementation steps
1. **Phase 1: Framework core**
   - [ ] Implement `scripts/shared/db_migrations.py` runner, spec, gate, ledger primitives (REQ-001, REQ-002, REQ-003, REQ-004, REQ-006; `scripts/shared/db_migrations.py`)
   - [ ] Write framework regression + fault-injection tests (REQ-001–REQ-004; `tests/shared/test_db_migrations.py`)
2. **Phase 2: eventbus domain wiring**
   - [ ] Add ledger DDL to `scripts/eventbus/schema.sql`; registry in `scripts/eventbus/migrations.py` (REQ-001, REQ-006; those rows)
   - [ ] Rework `_init_schema` in `scripts/eventbus/schema.py` to registered-path migration with unchanged fail-closed refusal (REQ-003, REQ-005, REQ-009; `scripts/eventbus/schema.py`)
   - [ ] Add `scripts/eventbus/migrate.py` CLI (REQ-001, REQ-002, REQ-004, REQ-006; `scripts/eventbus/migrate.py`)
   - [ ] Extend/new eventbus tests incl. fault injection (REQ-002, REQ-003, REQ-005, REQ-009; `tests/eventbus/test_eventbus_migrations.py`, `tests/eventbus/test_eventbus_schema_version.py`)
3. **Phase 3: workflow domain wiring**
   - [ ] Register the `schema_migrations` ledger in the table-ownership inventory (REQ-001, REQ-006; `tools/check_db_separation.py`), before the DDL rows of Phases 2 and 3
   - [ ] Add ledger DDL in `scripts/db/schema_sql.py` and bootstrap in `scripts/db/create_schema.py` (REQ-001, REQ-006; those rows)
   - [ ] Registry `scripts/db/migrations_workflow.py` + CLI `scripts/db/migrate_db.py` (REQ-001, REQ-002, REQ-004, REQ-006; those rows)
   - [ ] Tests incl. fault injection and migrated-schema fingerprint (REQ-002, REQ-003, REQ-009; `tests/db/test_migrations_workflow.py`, `tests/db/test_create_schema.py`)
4. **Phase 4: Verified recovery points and drills**
   - [ ] Add post-archive integrity verification to `scripts/db/rotation.py`; expose reusable helpers from `scripts/db/recovery.py` without behavior change (REQ-002, REQ-007; those rows)
   - [ ] Implement `scripts/db/recovery_drill.py` with JSON artifacts (REQ-007; `scripts/db/recovery_drill.py`)
   - [ ] Drill tests for all four domains (REQ-007; `tests/db/test_recovery_drill.py`)
5. **Phase 5: Deployment & Verification**
   - [ ] Update `deploy/init_db.sh` for ledger-compatible baselines and drill invocation; verify deployed-file freshness via the deploy checklist and confirm the running EventBus service (port 8015) is restarted after schema-touching deploys (deployment validation; REQ-006, REQ-007; `deploy/init_db.sh`)
   - [ ] Run full validation sequence: `uv run pytest`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `uv run python tools/check_db_separation.py`, `lint-imports`, docs checkers from `routing.md` (all REQ)
6. **Phase 6: Documentation & approval record**
   - [ ] Amend ADR-008 text and `adr_01_index.md` approval row (REQ-008; `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`, `docs/10_adr/adr_01_index.md`)
   - [ ] Update DB migration doc and recovery runbook (REQ-007, REQ-009; `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`, `docs/41_db/db_07_api_and_operations-recovery-and-reference.md`)

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/shared/db_migrations.py` | Unit: success/failure/interruption/downgrade/unknown-path/dry-run | `uv run pytest tests/shared/test_db_migrations.py` | All pass; dry-run hash-identical |
| `scripts/eventbus/schema.py`, `scripts/eventbus/migrations.py`, `scripts/eventbus/migrate.py` | Unit + integration (file-based SQLite) | `uv run pytest tests/eventbus` | Registered path migrates; unknown/downgrade refused; startup stays fail-closed |
| `scripts/db/create_schema.py`, `scripts/db/schema_sql.py`, `scripts/db/migrations_workflow.py`, `scripts/db/migrate_db.py` | Unit + integration | `uv run pytest tests/db` | Ledger created at bootstrap; migration preserves rows |
| `scripts/db/rotation.py`, `scripts/db/recovery.py`, `scripts/db/recovery_drill.py` | Integration + fault injection | `uv run pytest tests/db/test_recovery_drill.py tests/db/test_db_maintenance.py tests/db/test_db_recovery.py` | Archives verified; drill artifacts for four domains |
| Cross-cutting | Architecture + separation checks | `lint-imports`; `uv run python tools/check_db_separation.py` | No `eventbus`→`db` import; DB separation contract holds |
| Docs rows | Structure/reference checks | `uv run python tools/check_docs_structure.py` (+ reference checker named in `routing.md`) | Docs pass; ADR approval row discoverable |
| Type/quality | Static | `uv run mypy --no-namespace-packages scripts/ tests/eventbus` | Clean |

## Risks
- **Risk**: `eventbus.sqlite` is held by the running EventBus service (confirmed: listener on port 8015 holds the DB file, 2026-10-29). **Mitigation**: migration CLI requires the service stopped (check via `ss -ltnpH 'sport = :<PORT>'`); Phase 5 sequences restart after deploy.
- **Risk**: Startup migration changes EventBus fail-closed behavior. **Mitigation**: refusal semantics preserved for every unresolved case; `tests/eventbus/test_eventbus_schema_version.py` extended before wiring changes land (fail-first tests).
- **Risk**: Concurrent edits on the ADR set (ADR-008 churn 4 commits/30d, re-verified 2026-10-29) and DB docs — edit conflicts with other work in flight. **Mitigation**: land doc phase after code phases; rebase against current `HEAD` before editing; `check_plan_target_overlaps.py` gate already run at plan stage.
- **Risk**: Ledger stamping of existing production databases is itself a schema mutation. **Mitigation**: it runs through the same backup-gated runner and is covered by dry-run tests first.
- **Risk**: Restore-drill data-loss-window measurement depends on backup cadence, not only code. **Mitigation**: drill artifact records archive timestamps from `rotation.py` output so measurement reflects real cadence.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Framework core | Completed | — | 20261030-162056 |  |
| 2 | Phase 2: eventbus domain wiring | In Progress | — | — |  |
| 3 | Phase 3: workflow domain wiring | In Progress | — | — |  |
| 4 | Phase 4: Verified recovery points and drills | In Progress | — | — |  |
| 5 | Phase 5: Deployment & Verification | In Progress | — | — |  |
| 6 | Phase 6: Documentation & approval record | In Progress | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 5 | RPO/RTO targets and drill ownership undecided (UNK-01) | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261030-151746_01_scripts_shared_db_migrations.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261030-151746_02_scripts_eventbus_migrations.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261030-151746_03_scripts_eventbus_schema.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261030-151746_04_scripts_eventbus_schema.sql.md | 2 | Procedure | Pending | — | — |
| implementations/20261030-151746_05_scripts_eventbus_migrate.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261030-151746_06_scripts_db_migrations_workflow.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261030-151746_07_scripts_db_migrate_db.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261030-151746_08_scripts_db_create_schema.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261030-151746_09_scripts_db_schema_sql.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261030-151746_10_scripts_db_recovery.py.md | 4 | Procedure | Pending | — | — |
| implementations/20261030-151746_11_scripts_db_recovery_drill.py.md | 4 | Procedure | Pending | — | — |
| implementations/20261030-151746_12_scripts_db_rotation.py.md | 4 | Procedure | Pending | — | — |
| implementations/20261030-151746_13_deploy_init_db.sh.md | 5 | Procedure | Pending | — | — |
| implementations/20261030-151746_14_tests_shared_test_db_migrations.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261030-151746_15_tests_eventbus_test_eventbus_migrations.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261030-151746_16_tests_eventbus_test_eventbus_schema_version.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261030-151746_17_tests_db_test_migrations_workflow.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261030-151746_18_tests_db_test_create_schema.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261030-151746_19_tests_db_test_recovery_drill.py.md | 4 | Procedure | Pending | — | — |
| implementations/20261030-151746_20_docs_10_adr_adr_02_05_008_db-sqlite-4db-separation.md.md | 6 | Procedure | Pending | — | — |
| implementations/20261030-151746_21_docs_10_adr_adr_01_index.md.md | 6 | Procedure | Pending | — | — |
| implementations/20261030-151746_22_docs_41_db_db_03_architecture_and_schema-migration-and-scaling.md.md | 6 | Procedure | Pending | — | — |
| implementations/20261030-151746_23_docs_41_db_db_07_api_and_operations-recovery-and-reference.md.md | 6 | Procedure | Pending | — | — |
| implementations/20261030-151746_24_tools_check_db_separation.py.md | 3 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261029-104500_dbmig001_forward-only-db-migrations.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261029-214108
- **Related target files**: `scripts/shared/db_migrations.py`, `scripts/eventbus/migrations.py`, `scripts/eventbus/schema.py`, `scripts/eventbus/schema.sql`, `scripts/eventbus/migrate.py`, `scripts/db/migrations_workflow.py`, `scripts/db/migrate_db.py`, `scripts/db/create_schema.py`, `scripts/db/schema_sql.py`, `scripts/db/recovery.py`, `scripts/db/recovery_drill.py`, `scripts/db/rotation.py`, `deploy/init_db.sh`, `tests/shared/test_db_migrations.py`, `tests/eventbus/test_eventbus_migrations.py`, `tests/eventbus/test_eventbus_schema_version.py`, `tests/db/test_migrations_workflow.py`, `tests/db/test_create_schema.py`, `tests/db/test_recovery_drill.py`, `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`, `docs/10_adr/adr_01_index.md`, `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`, `docs/41_db/db_07_api_and_operations-recovery-and-reference.md`, `tools/check_db_separation.py`, `tools/check_db_separation.py`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes (migration framework) | `scripts/shared/db_migrations.py` | Phase 1 | AC-4 | Framework regression tests | Explicit in issue |
| REQ-001 | Required Changes | `scripts/eventbus/migrations.py` | Phase 2 | AC-1 | `tests/eventbus/test_eventbus_migrations.py` | Explicit in issue |
| REQ-001 | Required Changes | `scripts/eventbus/schema.sql` | Phase 2 | AC-1 | `tests/eventbus/test_eventbus_migrations.py` | Derived from confirmed evidence |
| REQ-001 | Required Changes | `scripts/db/migrations_workflow.py` | Phase 3 | AC-1 | `tests/db/test_migrations_workflow.py` | Explicit in issue |
| REQ-001 | Required Changes | `scripts/db/schema_sql.py` | Phase 3 | AC-1 | `tests/db/test_create_schema.py` | Derived from confirmed evidence |
| REQ-002 | Required Changes (backup gate) | `scripts/shared/db_migrations.py` | Phase 1 | AC-4 | Fault-injection tests | Explicit in issue |
| REQ-002 | Required Changes | `scripts/eventbus/migrate.py` | Phase 2 | AC-4 | `tests/eventbus/test_eventbus_migrations.py` | Derived from confirmed evidence |
| REQ-002 | Required Changes | `scripts/db/migrate_db.py` | Phase 3 | AC-4 | `tests/db/test_migrations_workflow.py` | Derived from confirmed evidence |
| REQ-002 | Required Changes | `scripts/db/rotation.py` | Phase 4 | AC-6 | `tests/db/test_db_maintenance.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes (refusals) | `scripts/eventbus/schema.py` | Phase 2 | AC-2, AC-3 | `tests/eventbus/test_eventbus_schema_version.py` | Explicit in issue |
| REQ-003 | Required Changes | `scripts/shared/db_migrations.py` | Phase 1 | AC-2 | Framework regression tests | Explicit in issue |
| REQ-004 | Required Changes (dry-run) | `scripts/shared/db_migrations.py` | Phase 1 | AC-5 | Dry-run hash-compare test | Explicit in issue |
| REQ-004 | Required Changes | `scripts/eventbus/migrate.py` | Phase 2 | AC-5 | `tests/eventbus/test_eventbus_migrations.py` | Derived from confirmed evidence |
| REQ-004 | Required Changes | `scripts/db/migrate_db.py` | Phase 3 | AC-5 | `tests/db/test_migrations_workflow.py` | Derived from confirmed evidence |
| REQ-005 | Constraints (fail-closed startup) | `scripts/eventbus/schema.py` | Phase 2 | AC-3 | `tests/eventbus/test_eventbus_schema_version.py` | Confirmed by repository evidence |
| REQ-006 | Required Changes; issue UNK re: ledger | `scripts/eventbus/schema.sql` | Phase 2 | AC-1 | `tests/eventbus/test_eventbus_migrations.py` | Derived from confirmed evidence |
| REQ-006 | Required Changes | `scripts/db/create_schema.py` | Phase 3 | AC-1 | `tests/db/test_create_schema.py` | Derived from confirmed evidence |
| REQ-006 | Required Changes | `deploy/init_db.sh` | Phase 5 | AC-1 | `tests/deploy/` suite | Confirmed by repository evidence |
| REQ-007 | Required Changes (drills) | `scripts/db/recovery_drill.py` | Phase 4 | AC-6 | `tests/db/test_recovery_drill.py` | Explicit in issue |
| REQ-007 | Required Changes | `scripts/db/recovery.py` | Phase 4 | AC-6 | `tests/db/test_db_recovery.py` regression | Confirmed by repository evidence |
| REQ-007 | Required Changes; Documentation Impact | `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` | Phase 6 | AC-6 | Docs checkers | Explicit in issue |
| REQ-008 | Required Changes (approval record) | `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | Phase 6 | AC-7 | Docs checkers | Explicit in issue |
| REQ-008 | Required Changes | `docs/10_adr/adr_01_index.md` | Phase 6 | AC-7 | Docs checkers | Derived from confirmed evidence |
| REQ-009 | Acceptance Criteria (rows survive) | `scripts/eventbus/migrations.py` | Phase 2 | AC-1 | `tests/eventbus/test_eventbus_migrations.py` | Explicit in issue |
| REQ-009 | Acceptance Criteria | `scripts/db/migrations_workflow.py` | Phase 3 | AC-1 | `tests/db/test_migrations_workflow.py` | Explicit in issue |
| REQ-009 | Documentation Impact | `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` | Phase 6 | AC-1 | Docs checkers | Explicit in issue |
| REQ-006 | Required Changes (ledger table) | `tools/check_db_separation.py` | Phase 3 | AC-1 | `tests/tools/test_check_db_separation.py` live-repository test | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261030-151746 -->