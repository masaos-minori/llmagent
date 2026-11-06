# Plan: Remove database migration compatibility and enforce current-schema-only startup

## Goal
- Remove every Workflow and EventBus database-migration mechanism (framework, registries, CLIs, ledger, automatic migration and stamping) and replace it with one current-schema-only lifecycle: create a database only when none exists; accept an existing database only when its version and full schema match the current specification; reject every other existing database before any mutation; require the operator to archive and recreate manually.

## Priority
High

## Scope
- **In-Scope**: Delete the migration framework modules, registries, CLIs, ledger DDL, baseline stamping, and migration tests; remove `schema_migrations` and `workflow_schema_version` from canonical DDL; enforce current-schema-only startup and pre-flight gates (`scripts/eventbus/schema.py`, `scripts/agent/services/workflow_schema.py`, `deploy/init_db.sh`); replace migration-success tests with legacy-rejection tests; update the DB schema docs and runbook for the manual archive-and-recreate procedure.
- **Out-of-Scope**: Automatic data export/import, down migrations, a compatibility converter, automatic deletion of an incompatible database, rotation/archive-validation removal (operational data protection is preserved), and the repository-wide compatibility-policy sweep (docs, CI, `dbmig001` text in ADRs and remaining references) owned by `issues/20261106-125145_compatrm004_finalize-no-compatibility-policy-across-ci-tests-docs.md`.
- **Dependencies**: Must complete before `issues/20261106-125145_compatrm004_finalize-no-compatibility-policy-across-ci-tests-docs.md`, whose checker targets the final deleted-symbol set. May run in parallel with `issues/20261106-125143_compatrm002_remove-eventbus-auth-compat-state-authzgeneration-only.md` (disjoint files: `eventbus/auth.py` and route state vs the migration/schema layer).
  - **Depends on**: issues/20261106-125145_compatrm004_finalize-no-compatibility-policy-across-ci-tests-docs.md | phase all | 004's compat-shim checker must target the final set of deleted migration modules and symbols; 001 defines that set.

## Background
- Initiative issue H-1 of `memo-issue.md` ("Backward Compatibility Removal"), implemented first. Verified 2026-11-07 against current source:
  - All named modules exist: `scripts/shared/db_migrations.py` (`MigrationRefusalReason`, `MigrationRefusalError`, `MigrationSpec`, `LedgerRow`, `ensure_ledger`, `read_ledger`, `record_applied`, `MigrationRunner`), `scripts/db/migrations_workflow.py` (workflow `REGISTRY` steps 0→1, 1→2, 2→3, 3→4, `verify_backup`, `verify_backup_by_path`, `ensure_baseline`), `scripts/eventbus/migrations.py` (eventbus `REGISTRY` steps 3→4, 4→5, 5→6, `_BASELINE_VERSION=3`), `scripts/eventbus/migrate.py`, `scripts/db/migrate_db.py` (workflow CLI), `tests/eventbus/test_eventbus_migrations.py`, `tests/shared/test_db_migrations.py`, `tests/db/test_migrations_workflow.py`, `tests/db/test_create_schema.py`.
  - Reference counts are larger than the Issue's figures: `schema_migrations` appears in 35 files and `dbmig001` in 26 files under `scripts/`, `tests/`, `tools/`, `docs/`, `deploy/` (excluding `__pycache__` and `done/`). The Issue's "about 20 / about 16" was accurate for its narrower path set; the counts below include `deploy/init_db.sh` and the docs/ADR files.
  - `verify_backup_by_path` has no caller outside `scripts/db/migrations_workflow.py` (repository-wide search) — the Issue's Unresolved Question 2 is resolved: delete it with the module.
  - `workflow_schema_version` is migration history, not one current schema: rows are inserted by each registry step (`INSERT INTO workflow_schema_version (version) VALUES ('1.2.0' / '1.3.0' / '1.4.0')`) and `docs/41_db/db_02` documents it as "an append-only log whose current version is the latest row". The Issue's Unresolved Question 1 is resolved per the Issue's own condition (keep version metadata only if it represents one current schema): delete it.
- Operational state (inspected 2026-11-07): deployed DBs under `/opt/llm/db/` are `workflow.sqlite` at marker `1.4.0` with a `schema_migrations` ledger, and `eventbus.sqlite` at `PRAGMA user_version = 6` with a ledger and `dlq_outbox`; `eventbus.sqlite` is held open by the running eventbus service (PID 3104771). No `sqlite`-named systemd unit matched the grep filter, but the open handle proves a live writer. The acceptance criterion "current valid databases open normally" therefore holds only for freshly created current-shape databases; the deployed databases carry legacy markers and will be rejected after this change until the operator archives and recreates them. This is an intended deploy-time operator action, not a defect (see Risks).

## Problem
- Two schema-management paths (migrate vs recreate) coexist: startup auto-migrates registered lower versions, auto-stamps `user_version = 0` databases, and a ledger gate in `deploy/init_db.sh` forces operators to bootstrap a ledger before starting. Tests, docs, and CLIs encode contradictory guidance about whether an incompatible database should be migrated or recreated.

## Reason for Change
- One unambiguous database lifecycle is easier to operate and test than a migration framework, and it matches the repository's current-only policy.

## Implementation Intent
- One lifecycle: create the current schema only when the database file is absent; accept an existing database only after an exact version check followed by a full schema fingerprint/shape check; reject every other existing database before mutation with a fixed operator-facing message; preserve rotation, archive validation, and supported corruption recovery; delete the migration path entirely.

## Requirements
- `REQ-001`: Delete `scripts/shared/db_migrations.py`, `scripts/db/migrations_workflow.py`, `scripts/eventbus/migrations.py`, `scripts/eventbus/migrate.py`, `scripts/db/migrate_db.py` and every symbol they export (`MigrationRunner`, `MigrationSpec`, `MigrationRefusalReason`, `LedgerRow`, `ensure_ledger`, `read_ledger`, `record_applied`, `Registry`, `REGISTRY`, `verify_backup`, `verify_backup_by_path`, `ensure_baseline`). No remaining import may reference them.
- `REQ-002`: Remove the `schema_migrations` DDL from the workflow template and the `workflow_schema_version` table from the workflow DDL in `scripts/db/schema_sql.py`, remove `schema_migrations` from `scripts/eventbus/schema.sql` (keeping `PRAGMA user_version = 6` as the EventBus current-schema identifier), remove the `WORKFLOW_SCHEMA_VERSION` constant and all ledger/baseline stamping and `dbmig001` comments from the schema layer.
- `REQ-003`: Current-schema-only startup and connection validation: EventBus accepts only `user_version == 6` plus a fingerprint match; Workflow accepts only the exact current table/column shape and treats the presence of `schema_migrations` or `workflow_schema_version` as a legacy marker rejection; `user_version = 0` existing databases are rejected and not stamped; a missing database is created with the current schema.
- `REQ-004`: Rejection performs no write, version update, table change, archive, or deletion; the error message follows the Issue's fixed text (database path, expected and detected versions, manual recreate guidance) and exposes no credentials.
- `REQ-005`: `deploy/init_db.sh` gates invert: it fails when `schema_migrations` or `workflow_schema_version` is present in `workflow.sqlite` / `eventbus.sqlite` and directs the operator to archive and recreate; the current-shape/fingerprint checks remain.
- `REQ-006`: Preserve rotation, archive validation, and supported recovery: `scripts/db/rotation.py` and backup code keep working unchanged (verified: neither references the ledger); `scripts/db/recovery_drill.py` replaces ledger-state audit with current-shape audit and flags legacy marker tables as findings.
- `REQ-007`: Replace migration-success tests with legacy-rejection tests; delete migration test modules; keep version-pin and fingerprint tests aligned with the post-change DDL.
- `REQ-008`: Schema fingerprints are regenerated and verified: the EventBus fingerprint is derived from canonical `schema.sql` at runtime, so removing the ledger DDL re-derives it; fingerprint and schema-equivalence tests must pass against the new canonical shape.
- `REQ-009`: Update the DB schema docs and operations runbook to describe only the current-schema and manual archive-and-recreate policy. The repository-wide policy wording sweep (`dbmig001` text in ADRs, remaining documents) stays with compatrm004.

## Implementation Target Files
**Freeze status**: Frozen (Step 8 validation passed 2026-11-07: every row `Verified` against current
source; `tools/check_plan_target_overlaps.py` returned "No findings"; `tools/check_workitem_structure.py`
clean.)

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/shared/db_migrations.py | DELETE | Migration runner, ledger, refusal types, spec/registry types (REQ-001) | REQ-001 / AC-001, AC-003 | Exists; imported by `create_schema.py`, `migrate_db.py`, `recovery_drill.py`, `eventbus/schema.py`, `eventbus/migrate.py` | tests/shared/test_db_migrations.py (DELETE) | Verified |
| scripts/db/migrations_workflow.py | DELETE | Workflow registry, baseline, backup gate, `verify_backup_by_path` (no external caller) (REQ-001) | REQ-001 / AC-001, AC-003 | Exists; imported by `create_schema.py`, `migrate_db.py` | tests/db/test_migrations_workflow.py (DELETE) | Verified |
| scripts/eventbus/migrations.py | DELETE | EventBus registry, baseline verify (REQ-001) | REQ-001 / AC-001, AC-003 | Exists; imported by `eventbus/schema.py`, `eventbus/migrate.py` | tests/eventbus/test_eventbus_migrations.py (DELETE) | Verified |
| scripts/eventbus/migrate.py | DELETE | EventBus migration CLI (REQ-001) | REQ-001 / AC-001 | Exists | tests/eventbus/test_eventbus_migrations.py (DELETE) | Verified |
| scripts/db/migrate_db.py | DELETE | Workflow migration CLI (REQ-001) | REQ-001 / AC-001 | Exists | tests/db/test_migrations_workflow.py (DELETE) | Verified |
| scripts/db/create_schema.py | MODIFY | Remove `ensure_ledger` / `ensure_baseline` / version-row stamping; keep fail-closed rejection and fingerprint gate (REQ-002, REQ-003) | REQ-002 / AC-002 | Lines 25, 29, 71: ledger import, baseline import, version stamp | tests/db/test_create_schema.py (MODIFY) | Verified |
| scripts/eventbus/schema.py | MODIFY | Remove `MigrationRunner`/`REGISTRY`/`read_ledger` wiring and auto-migration/stamping branches; keep version==6 + fingerprint gate; reject `user_version = 0` without stamping; import `MigrationRefusalError` from `shared.eventbus_schema_fingerprint` (REQ-001, REQ-003, REQ-004) | REQ-003 / AC-004, AC-005, AC-006 | Lines 8–16 import deleted framework; `_init_schema` stamping branch used by `db_conn.py` | tests/eventbus/test_eventbus_schema_version.py, tests/eventbus/test_eventbus_startup.py (MODIFY) | Verified |
| scripts/db/schema_sql.py | MODIFY | Remove `schema_migrations` and `workflow_schema_version` DDL, `WORKFLOW_SCHEMA_VERSION` constant, `dbmig001` comments (REQ-002) | REQ-002 / AC-002 | Lines 25–27, 253–261 | tests/db/test_create_schema.py (MODIFY) | Verified |
| scripts/eventbus/schema.sql | MODIFY | Remove `schema_migrations` CREATE TABLE; keep `PRAGMA user_version = 6` (REQ-002) | REQ-002 / AC-002, AC-007 | Line 46 CREATE, line 74 PRAGMA | tests/deploy/test_init_db_eventbus_schema.py (no change needed: fingerprint is derived dynamically) | Verified |
| scripts/agent/services/workflow_schema.py | MODIFY | Startup/health gate: drop `workflow_schema_version` requirement and version-row comparison; reject legacy marker tables as incompatible (REQ-003, REQ-004) | REQ-003 / AC-004 | Lines 58, 78, 118–129 pin the marker table and constant | tests/agent/test_repl_health.py (MODIFY) | Verified |
| scripts/db/recovery_drill.py | MODIFY | Replace ledger-state audit with current-shape audit; flag legacy marker tables (REQ-006) | REQ-006 / AC-008 | Lines 29, 58–62 import `read_ledger`, `_has_ledger_table` | tests/db/test_recovery_drill.py (MODIFY) | Verified |
| deploy/init_db.sh | MODIFY | Invert ledger gate to marker-absence gate with archive-and-recreate guidance (REQ-005) | REQ-005 / AC-002 | Lines 100–123 require the ledger | tests/deploy/test_init_db_schema_gate.py (CREATE) | Verified |
| tests/shared/test_db_migrations.py | DELETE | Tests the deleted shared runner | REQ-007 / AC-003 | Exists | — | Verified |
| tests/db/test_migrations_workflow.py | DELETE | Tests the deleted workflow registry | REQ-007 / AC-003 | Exists | — | Verified |
| tests/eventbus/test_eventbus_migrations.py | DELETE | Tests the deleted eventbus registry | REQ-007 / AC-003 | Exists | — | Verified |
| tests/db/test_eventbus_schema_equivalence.py | DELETE | Tests runner/ledger equivalence against deleted framework | REQ-007 / AC-003 | Imports `eventbus.migrations.REGISTRY`, `shared.db_migrations` | — | Verified |
| tests/deploy/test_init_db_ledger_gate.py | DELETE | Tests the inverted (removed) ledger-presence gate | REQ-007 / AC-002 | Asserts "ledger present/missing" strings | tests/deploy/test_init_db_schema_gate.py (CREATE) | Verified |
| tests/deploy/test_init_db_schema_gate.py | CREATE | Replacement deploy-gate test: init_db.sh fails on legacy marker tables, passes on marker-free current-shape databases | REQ-005, REQ-007 / AC-002 | Replaces `test_init_db_ledger_gate.py` pattern | — | Verified |
| tests/db/test_create_schema.py | MODIFY | Replace ledger/baseline expectations with marker-absence and rejection expectations | REQ-007 / AC-002 | Asserts ledger rows and version stamp | — | Verified |
| tests/eventbus/test_eventbus_schema_version.py | MODIFY | Replace migration/stamping tests (`test_registered_v3_database_migrates_at_startup`, `test_unstamped_current_database_is_stamped`) with rejection tests | REQ-007 / AC-004 | Test list verified by grep | — | Verified |
| tests/eventbus/test_eventbus_startup.py | MODIFY | Startup fixtures currently stamp `user_version` manually; align with no-stamp rejection policy | REQ-007 / AC-004 | Lines 267, 281 | — | Verified |
| tests/agent/test_repl_health.py | MODIFY | Remove `WORKFLOW_SCHEMA_VERSION` import and version-row fixtures; add legacy-marker rejection cases | REQ-007 / AC-004 | Lines 27, 525, 607, 615 | — | Verified |
| tests/deploy/test_setup_services_eventbus.py | MODIFY | Fixture stamps a `workflow_schema_version` row and imports `WORKFLOW_SCHEMA_VERSION` | REQ-007 / AC-004 | Lines 25, 133 | — | Verified |
| tests/db/test_recovery_drill.py | MODIFY | Replace `test_missing_ledger_is_an_audited_finding` with legacy-marker and current-shape audit cases | REQ-007 / AC-008 | Line 652 | — | Verified |
| docs/41_db/db_01_architecture_and_schema-overview-and-config.md | MODIFY | Overview states new databases "receive the migration ledger and baseline row" — must describe the new lifecycle | REQ-009 / AC-009 | Lines 17–20 | — | Verified |
| docs/41_db/db_02_architecture_and_schema-schema-reference.md | MODIFY | Documents `workflow_schema_version` append-only log and version-comparison gate | REQ-009 / AC-009 | Line 46 | — | Verified |
| docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md | MODIFY | Core migration-policy document: rewrite as current-schema-only + manual archive-and-recreate runbook | REQ-009 / AC-009 | Exists, cites ledger and dbmig001 | — | Verified |
| docs/41_db/db_07_api_and_operations-recovery-and-reference.md | MODIFY | DB-recreation procedure (§11) must state the no-migration policy and archive-before-remove order | REQ-009 / AC-009 | §11 already exists; policy sentence must be added | — | Verified |
| docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md | MODIFY | EventBus schema document describing the ledger table and migration versions | REQ-009 / AC-009 | Cites `schema_migrations` | — | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/db/rotation.py | Rotation gate preserved; verified it contains no ledger/migration reference, so it must keep working unchanged | REQ-006 / rotation tests in AC-008 |
| scripts/db/backup.py | Generic backup/archive validation preserved as operational data protection | REQ-006 |
| scripts/shared/eventbus_schema_fingerprint.py | The single fingerprint validator (`validate_canonical`, `assert_matches`) and its own `MigrationRefusalError`; becomes the only refusal type after REQ-001 | REQ-003, REQ-008 |
| scripts/eventbus/db_conn.py | Calls `eventbus.schema._init_schema` on connection; startup gate behavior must hold here | REQ-003 |
| tools/check_db_separation.py | Allowed-table sets already include the marker tables permissively; kept unchanged so marker-free databases pass and legacy databases are caught by startup gates, not this checker | REQ-006, environment rule |
| tools/check_compat_shims.py + config/compat_exceptions.toml | Existing shim checker; 004 extends it to the deleted migration symbols — 001 must leave zero shim/facade behind | REQ-001 |
| rules/persisted-schema-change.md | Persisted-schema checklist the Plan must run (recorded in Design) | whole Plan |
| docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md (schema section) and scripts/eventbus/schema.sql | Current EventBus canonical shape for gate design | REQ-003 |

## Acceptance Criteria
- AC-001: All migration framework, registry, and CLI modules are deleted (REQ-001).
- AC-002: `schema_migrations` and `workflow_schema_version` are absent from newly created Workflow and EventBus databases, and no baseline record is created (REQ-002, REQ-005).
- AC-003: No source or test imports a deleted migration symbol (REQ-001, REQ-007); verified by grep and a full test-suite collection.
- AC-004: An existing `user_version = 0` database is rejected and not stamped; a lower or higher schema version is rejected; a current-version database with an altered schema is rejected (REQ-003).
- AC-005: Rejection performs no write, version update, table change, automatic archive, or deletion — database file hash unchanged before/after each rejection test (REQ-004).
- AC-006: A missing database is created with the current schema; current valid (marker-free, current-shape) databases open normally (REQ-003).
- AC-007: Schema fingerprints are regenerated and verified against the new canonical DDL (REQ-008).
- AC-008: Rotation, archive validation, and supported recovery tests continue to pass (REQ-006).
- AC-009: Active documentation describes only the current-schema and manual-recreation policy (REQ-009).

## Tests
- Fresh Workflow and EventBus databases: inspect `sqlite_master` — no `schema_migrations`, no `workflow_schema_version` (AC-002).
- Rejection matrix per domain: lower version, higher version, unversioned (`user_version = 0`), malformed/altered shape, and current databases; each rejection test compares the database file hash before and after (AC-004, AC-005).
- EventBus fingerprint tests and `tools/check_db_separation.py` against the regenerated canonical shape (AC-007).
- Database maintenance, rotation, archive, and recovery tests continue to pass; new legacy-marker drill findings (AC-008).
- Full suite plus `tools/check_compat_shims.py` (AC-001, AC-003).
- Deploy-gate integration test (`tests/deploy/test_init_db_schema_gate.py`): provisioned databases with and without marker tables against `deploy/init_db.sh` (AC-002).

## Documentation Impact
Yes: REQ-009 drives updates named in the `docs/00_index.md` "Document References by Task" DB rows: the DB architecture overview and schema reference, the migration/scaling document (rewritten as the current-schema + manual archive-and-recreate runbook), the recovery/reference document (§11), and the EventBus persistence/schema document. The cross-document policy sweep and `dbmig001` text removal in ADRs belong to compatrm004.

## Assumptions
- The deployed databases are treated as legacy under the new policy and will be archived and recreated by the operator at deploy time; no code path preserves them in place.
- `check_db_separation.py` allowed-table sets are left permissive (marker entries retained) so 001 stays minimal; compatrm004 owns checker policy.
- `tests/deploy/test_init_db_eventbus_schema.py` needs no edit because the expected fingerprint is derived from canonical `schema.sql` at runtime; verified during implementation.
- Companion files covered by other rows get no own procedure document (per this repository's procedure-generation convention).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether any external runbook/operator script outside the repository calls `migrate_db.py` / `eventbus/migrate.py` (e.g. in an operator shell history or cron) | Only repository paths are searchable; cron/systemd not fully enumerable (grep filter missed units) | Inspect `systemctl list-units` without grep filter and crontabs during the deploy phase; report findings before deploy | False |
| UNK-02 | Whether `dlq_outbox`-less but v6-stamped databases exist anywhere in operator backups | Backup archives under `/opt/llm/db/archive-20261106` were not opened | Rejection tests cover this shape; archives are never auto-restored | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/shared/db_migrations.py | DELETE | 5 importers removed | 6 | 1 (single migration-framework author set) | Yes — file sync + service restart |
| scripts/db/migrations_workflow.py | DELETE | 2 importers removed | 8 | 1 | Yes — file sync + service restart |
| scripts/eventbus/migrations.py | DELETE | 2 importers removed | 5 | 1 | Yes — file sync + service restart |
| scripts/eventbus/migrate.py | DELETE | CLI removal, operator-facing | 2 | 1 | Yes — file sync |
| scripts/db/migrate_db.py | DELETE | CLI removal, operator-facing | 5 | 1 | Yes — file sync |
| scripts/db/create_schema.py | MODIFY | schema creation path for all 4 DBs | 9 | 1 | Yes — used by deploy/init_db.sh |
| scripts/eventbus/schema.py | MODIFY | every eventbus connection path (`db_conn.py`) | 11 | 1 | Yes — service restart |
| scripts/db/schema_sql.py | MODIFY | canonical DDL SSOT | 16 | 1 | Yes — file sync |
| scripts/eventbus/schema.sql | MODIFY | canonical eventbus DDL | 10 | 1 | Yes — file sync |
| scripts/agent/services/workflow_schema.py | MODIFY | agent startup health gate | 5 | 1 | Yes — service restart |
| scripts/db/recovery_drill.py | MODIFY | drill verification semantics | 4 | 1 | Yes — script sync |
| deploy/init_db.sh | MODIFY | deploy pre-flight gate | 6 | 1 | Yes — deploy entry point |

## Design
- **One lifecycle, two domains.** Workflow and EventBus keep separate gates but identical policy: version/shape match → accept; anything else → raise before opening write access; never mutate, archive, or delete an incompatible database.
- **EventBus gate** (`scripts/eventbus/schema.py`): accept iff `PRAGMA user_version == eventbus_schema_version()` (6) AND `shared.eventbus_schema_fingerprint.assert_matches` passes. Delete the registered-lower-version auto-migration branch and the `user_version = 0` auto-stamp branch: an unversioned database is rejected and left unstamped. New databases get the stamp from canonical `schema.sql` DDL only (via `create_eventbus_schema`). `MigrationRefusalError` is imported from `shared.eventbus_schema_fingerprint` instead of `shared.db_migrations`, consolidating refusal types onto the single fingerprint validator (REQ-008).
- **Workflow gate** (`scripts/agent/services/workflow_schema.py`): `workflow_schema_version` is migration history (Background), so the health check switches to shape-only acceptance: required tables/columns exactly as `REQUIRED_WORKFLOW_TABLES` (minus the marker row) AND absence of `schema_migrations` and `workflow_schema_version`; either marker present → incompatible legacy → fail with the fixed message. No new workflow version mechanism is introduced (the Issue's "keep Workflow schema-version metadata only if it represents one current schema" resolves to removal; `PRAGMA user_version` stays an EventBus-only identifier per the Issue). `WORKFLOW_SCHEMA_VERSION` disappears with `scripts/db/schema_sql.py`.
- **DDL changes** (`scripts/db/schema_sql.py`, `scripts/eventbus/schema.sql`): delete both marker-table CREATEs, the baseline insert paths, ledger/version `dbmig001` comments, and the version constant. EventBus keeps `PRAGMA user_version = 6` (Issue line 34). EventBus fingerprint is computed from canonical `schema.sql` at runtime, so removing the ledger DDL regenerates it automatically (REQ-008).
- **Refusal message** (REQ-004): one shared text per domain — "The database does not match the current schema. Automatic migration and version stamping are not supported. Stop the service, archive the existing database if required, remove or rename it, and create a new database using the current schema." plus database path and expected/detected versions; no credentials.
- **Deploy gate inversion** (`deploy/init_db.sh`): the ledger-presence fatal check becomes a marker-absence fatal check (present → FATAL with archive-and-recreate guidance); existing fingerprint/version checks remain.
- **Recovery drill** (`scripts/db/recovery_drill.py`): `_has_ledger_table`/`_read_ledger_state` audit becomes a legacy-marker audit: marker tables present → audited finding; current-shape integrity checks unchanged. Rotation (`scripts/db/rotation.py`) and backup validation are verified ledger-free and untouched.
- **Persisted-schema checklist outcomes** (`rules/persisted-schema-change.md`, run 2026-11-07): item 1 (version stores move together) — applies: both workflow stores (string marker + ledger user_version) and the eventbus store (user_version) are enumerated; both workflow stores are deleted, eventbus keeps only `user_version = 6`; every writer/reader named in the target table. Item 2 (shape change moves the fingerprint) — applies deliberately: canonical DDL loses the ledger tables, so deployed databases with ledgers fail the gate by design and are recreated manually; no migration step or baseline is registered because migration support is being removed, which is the Issue's explicit intent. Item 3 (table rebuild/FK cascade) — N/A: no rebuild; tables are only absent from new DDL. Item 4 (NOT NULL/write path) — applies in its ordering form: ledger DDL and ledger write paths (`ensure_ledger`, `ensure_baseline` in `create_schema.py`) ship in one release unit so no intermediate state writes into removed tables. Item 5 (frozen migration text) — N/A: registered steps are deleted, not edited; convergence tests are deleted with the framework. Item 6 (registry-pinning tests) — applies: pinning tests named and updated (`test_eventbus_schema_version.py` keeps `test_schema_version_is_pinned_to_six`, replaces migration pins; `test_eventbus_schema_equivalence.py` and `test_migrations_workflow.py` deleted; `test_db_migrations.py` deleted). Item 7 (rows with an old meaning) — applies: deployed databases hold ledger rows/marker tables; owner decision (Issue common policy 3–5): fail closed, operator archives and recreates; rejection tests seed exactly these rows (scratch-database recipe used in Phase 1 test design; never run against `/opt/llm/`).

## Implementation steps
1. **Phase 1: Red policy tests (scratch-DB matrix)**
   - [ ] Rewrite `tests/db/test_create_schema.py` expectations: fresh DBs contain no `schema_migrations` / `workflow_schema_version`, no baseline row; rejection behavior preserved (REQ-002, REQ-007).
   - [ ] Rewrite `tests/eventbus/test_eventbus_schema_version.py`: replace migrate/stamp tests with rejection matrix (lower, higher, unversioned, altered-shape) incl. file-hash-unchanged assertions (REQ-003, REQ-004, REQ-007).
   - [ ] Update `tests/eventbus/test_eventbus_startup.py` fixtures for no-stamp policy (REQ-003).
   - [ ] Add legacy-marker rejection cases to `tests/agent/test_repl_health.py` (REQ-003).
   - [ ] Add `tests/deploy/test_init_db_schema_gate.py` (marker-absence gate) and delete `tests/deploy/test_init_db_ledger_gate.py` (REQ-005, REQ-007).
2. **Phase 2: Framework deletion and importer migration**
   - [ ] Delete `scripts/shared/db_migrations.py`, `scripts/db/migrations_workflow.py`, `scripts/eventbus/migrations.py`, `scripts/eventbus/migrate.py`, `scripts/db/migrate_db.py` (REQ-001).
   - [ ] Strip ledger/baseline/version stamping from `scripts/db/create_schema.py`; strip runner/registry/auto-migration/stamp branches from `scripts/eventbus/schema.py` and re-point `MigrationRefusalError` to `shared.eventbus_schema_fingerprint` (REQ-001, REQ-003).
   - [ ] Delete `tests/shared/test_db_migrations.py`, `tests/db/test_migrations_workflow.py`, `tests/eventbus/test_eventbus_migrations.py`, `tests/db/test_eventbus_schema_equivalence.py` (REQ-007).
3. **Phase 3: Canonical DDL, gates, drill, deploy**
   - [ ] Remove marker-table DDL, version constant, and ledger comments from `scripts/db/schema_sql.py`; remove `schema_migrations` from `scripts/eventbus/schema.sql` keeping `PRAGMA user_version = 6` (REQ-002, REQ-008).
   - [ ] Rework `scripts/agent/services/workflow_schema.py` to shape-only acceptance + marker rejection (REQ-003, REQ-004).
   - [ ] Invert the ledger gate in `deploy/init_db.sh` to marker-absence with archive-and-recreate guidance (REQ-005).
   - [ ] Rework `scripts/db/recovery_drill.py` ledger audit into legacy-marker audit; update `tests/db/test_recovery_drill.py` (REQ-006, REQ-007).
   - [ ] Align `tests/agent/test_repl_health.py` and `tests/deploy/test_setup_services_eventbus.py` fixtures with the removed constant/table (REQ-007).
4. **Phase 4: Documentation**
   - [ ] Update `docs/41_db/db_01_architecture_and_schema-overview-and-config.md`, `docs/41_db/db_02_architecture_and_schema-schema-reference.md`, `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` (current-schema-only + manual archive-and-recreate runbook), `docs/41_db/db_07_api_and_operations-recovery-and-reference.md` (§11 policy sentence), `docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md` (REQ-009).
5. **Phase 5: Full validation and deploy hand-off**
   - [ ] Run the full validation sequence (`rules/toolchain.md` §1–§8), `uv run pytest tests/`, `uv run python tools/check_db_separation.py`, `uv run python tools/check_compat_shims.py`, fingerprint tests (AC-001–AC-008).
   - [ ] Resolve UNK-01 (systemd units, crontabs referencing deleted CLIs) before deploy; deploy requires operator action: stop services, archive `/opt/llm/db/workflow.sqlite` and `eventbus.sqlite` (operator-confirmed), recreate via `deploy/init_db.sh`, restart services. No deploy without explicit user approval.

### Release units
**Unit**: current-schema-only-cutover | **Phases**: 1, 2, 3 | **Reason**: Phase 1 tests are RED against current auto-migration/stamping behavior, and Phase 2 deletion breaks `create_schema.py` / `eventbus/schema.py` imports until Phase 3 completes; the suite is only green with all three phases landed.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/eventbus/schema.py + schema.sql | Unit matrix (version 0/5/6/7, altered shape, fresh create) + file-hash check | `uv run pytest tests/eventbus/test_eventbus_schema_version.py tests/eventbus/test_eventbus_startup.py` | All rejection cases pass; hashes unchanged; fresh DB marker-free |
| scripts/db/create_schema.py + schema_sql.py | Unit: `sqlite_master` inspection of fresh 4-DB set | `uv run pytest tests/db/test_create_schema.py` | No marker tables, no baseline rows; fail-closed paths intact |
| scripts/agent/services/workflow_schema.py | Unit: legacy-marker and marker-free fixtures | `uv run pytest tests/agent/test_repl_health.py` | Marker present → invalid; marker-free current shape → valid |
| deploy/init_db.sh | Integration (provisioned temp DBs) | `uv run pytest tests/deploy/test_init_db_schema_gate.py` | Marker present → FATAL; marker-free → OK |
| scripts/db/recovery_drill.py | Integration drill on scratch domain DBs | `uv run pytest tests/db/test_recovery_drill.py` | Marker audit finding replaces ledger finding |
| tools/check_db_separation.py + fingerprint | Environment check | `uv run python tools/check_db_separation.py`; fingerprint tests | Clean; fingerprint matches regenerated DDL |
| Whole repository | Suite + gates | `uv run pytest tests/`; `uv run ruff check .`; `uv run mypy scripts/`; `uv run bandit -q -r scripts/ -c pyproject.toml`; `uv run radon cc scripts/ -s -n B`; `uv run vulture scripts/ --min-confidence 80`; `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90`; `uv run python tools/check_compat_shims.py`; pre-commit | Baselines preserved: radon no C+ in changed files, bandit clean, vulture pre-existing only, diff-cover ≥90%, shim check clean |

## Risks
- **Risk**: Deployed `workflow.sqlite` (marker 1.4.0 + ledger) and `eventbus.sqlite` (v6 + ledger) will be rejected by the new gates until recreated → **Mitigation**: Deploy phase is operator-gated: stop services, archive databases (archives already exist: `archive-20261106`, `bak-20261026`), recreate with `deploy/init_db.sh`, restart; the refusal message names the exact procedure. No automatic archive or deletion is ever performed.
- **Risk**: A live writer (eventbus service, PID 3104771 at inspection time) races the gate change at deploy → **Mitigation**: services are stopped before database replacement in the deploy runbook.
- **Risk**: Deleting five modules and six test files in one cutover can strand a hidden importer → **Mitigation**: REQ-001 AC is enforced by full-suite collection plus `check_compat_shims.py` plus grep for every deleted symbol listed in the Issue's Target Files line.
- **Risk**: Removing `workflow_schema_version` weakens workflow version mismatch detection for shape-compatible-but-legacy databases → **Mitigation**: The gate rejects any database carrying the marker tables, which is precisely the legacy population; fresh databases are pinned by exact table/column shape.
- **Risk**: Fingerprint regeneration invalidates old archives for restore → **Mitigation**: AC-008 tests continue to pass on current-shape archives; old-schema archives are explicitly not restorable ("Do not restore an old Workflow or EventBus archive into the current schema automatically").

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Red policy tests | Pending | — | — | |
| 2 | Phase 2: Framework deletion and importer migration | Pending | — | — | |
| 3 | Phase 3: Canonical DDL, gates, drill, deploy script | Pending | — | — | |
| 4 | Phase 4: Documentation | Pending | — | — | |
| 5 | Phase 5: Full validation and deploy hand-off | Pending | — | — | |

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
- **Source issue**: issues/20261106-125142_compatrm001_remove-db-migration-and-enforce-current-schema-startup.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261107-061846
- **Related target files**: scripts/shared/db_migrations.py, scripts/db/migrations_workflow.py, scripts/eventbus/migrations.py, scripts/eventbus/migrate.py, scripts/db/migrate_db.py, scripts/db/create_schema.py, scripts/eventbus/schema.py, scripts/db/schema_sql.py, scripts/eventbus/schema.sql, scripts/agent/services/workflow_schema.py, scripts/db/recovery_drill.py, deploy/init_db.sh, tests/shared/test_db_migrations.py, tests/db/test_migrations_workflow.py, tests/eventbus/test_eventbus_migrations.py, tests/db/test_eventbus_schema_equivalence.py, tests/deploy/test_init_db_ledger_gate.py, tests/deploy/test_init_db_schema_gate.py, tests/db/test_create_schema.py, tests/eventbus/test_eventbus_schema_version.py, tests/eventbus/test_eventbus_startup.py, tests/agent/test_repl_health.py, tests/deploy/test_setup_services_eventbus.py, tests/db/test_recovery_drill.py, docs/41_db/db_01_architecture_and_schema-overview-and-config.md, docs/41_db/db_02_architecture_and_schema-schema-reference.md, docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md, docs/41_db/db_07_api_and_operations-recovery-and-reference.md, docs/24_eventbus/eventbus_06_persistence_schema_and_replay.md

### Requirement Traceability
| Requirement ID | Source | Acceptance Criteria | Implementation Target Files | Procedure | Status |
|---|---|---|---|---|---|
| REQ-001 | issues/20261106-125142_compatrm001_remove-db-migration-and-enforce-current-schema-startup.md Required Changes | AC-001, AC-003 | scripts/shared/db_migrations.py, scripts/db/migrations_workflow.py, scripts/eventbus/migrations.py, scripts/eventbus/migrate.py, scripts/db/migrate_db.py | — | Planned |
| REQ-002 | same, Required Changes (schemas) | AC-002 | scripts/db/schema_sql.py, scripts/eventbus/schema.sql, scripts/db/create_schema.py | — | Planned |
| REQ-003 | same, Required Changes (startup) | AC-004, AC-006 | scripts/eventbus/schema.py, scripts/agent/services/workflow_schema.py | — | Planned |
| REQ-004 | same, Constraints | AC-005 | scripts/eventbus/schema.py, scripts/agent/services/workflow_schema.py | — | Planned |
| REQ-005 | same, Required Changes (deploy gate) | AC-002 | deploy/init_db.sh | — | Planned |
| REQ-006 | same, Implementation Intent (preserve operations) | AC-008 | scripts/db/recovery_drill.py | — | Planned |
| REQ-007 | same, Required Changes (tests) | AC-003 | test rows in Implementation Target Files | — | Planned |
| REQ-008 | same, Required Changes (fingerprints) | AC-007 | scripts/db/schema_sql.py, scripts/eventbus/schema.sql | — | Planned |
| REQ-009 | same, Documentation Impact | AC-009 | docs rows in Implementation Target Files | — | Planned |

## Freeze Decision Log

| Timestamp | Freeze status | Validation evidence |
|---|---|---|
| 2026-11-07 06:25 | Frozen | All `Implementation Target Files` rows `Verified` against rebased HEAD `1b2dded66`: the five migration modules, both marker tables (`schema_migrations`, `workflow_schema_version`), the ledger gate in `deploy/init_db.sh` lines 100-123, `workflow_schema.py` lines 58/78/118-129, `recovery_drill.py` lines 29/58-62, and every test-row citation spot-checked by grep in this cycle. No blocking Unknown: UNK-01, UNK-02 `Blocking? = False`. No open dependency (004 runs after this Plan, not a blocker for freezing). `tools/check_plan_target_overlaps.py` returned "No findings"; no other Frozen plan exists in `plans/` (ragfix001/002 are in `plans/done/` with zero file overlap against this Plan's rows). |
