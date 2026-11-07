## Goal

- Delete `scripts/db/migrations_workflow.py` — the Workflow migration registry, baseline verify, backup gate, and `verify_backup_by_path` — per the current-schema-only policy (REQ-001: delete the migration framework modules).

## Scope
**Release unit**: current-schema-only-cutover

- Whole-file deletion of the workflow domain registry module. Its own test module is row 14 (own document, seq 14) because the Plan cites this test path in two rows.

## Assumptions

- `verify_backup_by_path` has no external caller at HEAD (Plan row evidence), so no re-pointing is needed.
- Deployed workflow databases keep their marker tables until the operator archives and recreates them (Plan Assumptions); this deletion touches no database.

## Design decisions

- No replacement workflow version mechanism: the workflow gate switches to shape-only acceptance in sibling document 10 (Plan Design).
- Deletion lands in the Phase 2 commit together with sibling importer edits (documents 05, 06).

## Alternatives considered

- Keeping `verify_backup_by_path` as a generic backup helper: rejected — backup/recovery validation lives in `scripts/db/recovery.py`, which is ledger-free (Plan Reference Files).

## Implementation
### Target file
`scripts/db/migrations_workflow.py`

### Procedure
1. `git rm scripts/db/migrations_workflow.py` in the Phase 2 commit (Plan Phase 2).

### Method
- The module carries the workflow registry steps and helpers: `_REQUIRED_TABLE` (line 76), `_LEDGER_CREATE_SQL` (line 80), `_BOOTSTRAP_MUTATION_SQL` (line 92), `_latest_workflow_string` (line 157), `_precondition_baseline` (line 174), `_precommit_fingerprint` (line 204), plus `ensure_baseline`, `verify_backup`, `verify_backup_by_path`, and `REGISTRY` (REQ-001 symbol list).
- Importers at HEAD: `scripts/db/create_schema.py` (document 06) and `scripts/db/migrate_db.py` (document 05) — both handled by siblings.

### Details
- No database file is read, written, archived, or deleted by this procedure.

## Compatibility considerations

- Existing workflow databases retain their `schema_migrations` / `workflow_schema_version` tables untouched until operator recreation (REQ-004).

## Security considerations

- N/A: pure deletion.

## Rollback considerations

- Revert the commit restores the module (single-commit deletion).

## Validation plan

- `grep -rn "migrations_workflow" scripts/ tests/ deploy/` — no remaining importer after siblings land (row 14 test document deletes the test module).
- `uv run pytest tests/` — collection succeeds after Phases 2-3 land.
- Whole-unit gates run in Plan Phase 5 per `rules/toolchain.md`.

## Completion criteria

- The module is absent and no file imports `ensure_baseline`, `verify_backup`, `verify_backup_by_path`, or `REGISTRY` from it (AC-001, AC-003).

## Out of Scope

- Deleting `tests/db/test_migrations_workflow.py` — own document (seq 14).
- Removing the marker-table DDL — sibling document 08.
- Workflow startup gate rework — sibling document 10.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | `git rm scripts/db/migrations_workflow.py` (Plan Phase 2) | Pending | — | — | Release unit "current-schema-only-cutover" |
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
- **Related target files**: `scripts/db/migrations_workflow.py`
