## Goal

- Delete `scripts/eventbus/migrations.py` — the EventBus migration registry (`REGISTRY`) and baseline verify (`verify_backup`) — per the current-schema-only policy (REQ-001: delete the migration framework modules).

## Scope
**Release unit**: current-schema-only-cutover

- Whole-file deletion of the EventBus registry module. Its own test module is row 15 (own document, seq 15) because the Plan cites this test path in two rows (3 and 4).

## Assumptions

- The eventbus current-schema identifier after the cutover is `PRAGMA user_version = 6` plus the canonical fingerprint only; the registry chain `3 -> 4 -> 5 -> 6` and `_BASELINE_VERSION = 3` disappear with this file (Plan row evidence).
- Deployed eventbus databases keep their `schema_migrations` table until operator recreation (Plan Assumptions).

## Design decisions

- No replacement for `verify_backup`: after REQ-001 the only EventBus refusal source is `shared.eventbus_schema_fingerprint` (plain `RuntimeError`), per the Plan Design correction re-verified 2026-11-07.

## Alternatives considered

- Keeping the registry read-only for status reporting: rejected — REQ-001 names the module and its symbols for deletion and `check_compat_shims.py` must stay clean.

## Implementation
### Target file
`scripts/eventbus/migrations.py`

### Procedure
1. `git rm scripts/eventbus/migrations.py` in the Phase 2 commit (Plan Phase 2).

### Method
- The module carries `_REQUIRED_TABLES` (line 28), `_BASELINE_VERSION = 3` (line 32), `_LEDGER_VERSION = 4` (line 35), `_OUTBOX_VERSION = 5` (line 41), `_FK_DEDUP_VERSION = 6` (line 46), `_LEDGER_CREATE_SQL` (line 48), `_BOOTSTRAP_MUTATION_SQL` (line 58), `_DLQ_OUTBOX_SQL` (line 67), `_OUTBOX_MUTATION_SQL` (line 81), `_FK_DEDUP_CREATE_SQL` (line 88), plus `REGISTRY` and `verify_backup` (REQ-001 symbol list).
- Importers at HEAD: `scripts/eventbus/schema.py` (document 07) and `scripts/eventbus/migrate.py` (document 04) — both handled by siblings.

### Details
- No database file is read, written, archived, or deleted by this procedure.

## Compatibility considerations

- Existing eventbus databases retain their ledger table untouched until operator recreation (REQ-004).

## Security considerations

- N/A: pure deletion.

## Rollback considerations

- Revert the commit restores the module (single-commit deletion).

## Validation plan

- `grep -rn "eventbus.migrations" scripts/ tests/ deploy/` — no remaining importer after siblings land (document 15 deletes the test module; document 16 deletes the equivalence test that imports `REGISTRY`).
- `uv run pytest tests/` — collection succeeds after Phases 2-3 land.
- Whole-unit gates run in Plan Phase 5 per `rules/toolchain.md`.

## Completion criteria

- The module is absent and no file imports `REGISTRY` or `verify_backup` from `eventbus.migrations` (AC-001, AC-003).

## Out of Scope

- Removing `MigrationRunner`/`read_ledger` wiring from `scripts/eventbus/schema.py` — sibling document 07.
- Deleting `scripts/eventbus/migrate.py` — sibling document 04.
- Removing the `schema_migrations` CREATE from `scripts/eventbus/schema.sql` — sibling document 09.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | `git rm scripts/eventbus/migrations.py` (Plan Phase 2) | Pending | — | — | Release unit "current-schema-only-cutover" |
| 2 | Verify no remaining importer (grep + full-suite collection) | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) in the Phase 5 unit pass | Pending | — | — | |

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
- **Requirement ID**: REQ-001 (delete the migration framework and every symbol it exports)
- **Source issue**: issues/20261106-125142_compatrm001_remove-db-migration-and-enforce-current-schema-startup.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261107-061846_compatrm001_remove-db-migration-and-enforce-current-schema-startup.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261107-081028
- **Related target files**: `scripts/eventbus/migrations.py`
