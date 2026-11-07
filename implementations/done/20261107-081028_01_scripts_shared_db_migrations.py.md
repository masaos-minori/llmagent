## Goal

- Delete `scripts/shared/db_migrations.py` — the shared forward-only migration framework (runner, ledger, refusal types, archive) — so no code path supports automatic migration or version stamping (REQ-001: delete the migration framework and every symbol it exports).

## Scope
**Release unit**: current-schema-only-cutover

- Whole-file deletion of the shared framework module plus its companion test module. The suite is only green with all Plan Phases 1-3 landed; importer re-pointing is done by sibling documents in the same release unit.

## Assumptions

- Deployed databases are legacy under the new policy and are archived and recreated by the operator at deploy time; this deletion itself touches no database (Plan Assumptions).
- UNK-01 (external runbook/operator script referencing the migration CLIs) is resolved in Plan Phase 5 before deploy; it does not block this deletion.
- An older procedure `implementations/done/20261105-170302_01_scripts_shared_db_migrations.py.md` created this file under a different plan (dbmig001); it does not cover this row (Source plan mismatch) — this document reverses that work per the Issue's policy change.

## Design decisions

- Full deletion, no facade or compatibility shim: `tools/check_compat_shims.py` must stay clean after the cutover (Plan Reference Files row).
- Deletion lands in Phase 2 together with importer edits (sibling documents 06, 07, 11) so no intermediate commit leaves a broken import unaddressed.

## Alternatives considered

- Keeping the module but disabling it: rejected — REQ-001 names the file and every exported symbol for deletion.

## Implementation
### Target file
`scripts/shared/db_migrations.py`

### Procedure
1. `git rm scripts/shared/db_migrations.py` in the Phase 2 commit (Plan Phase 2).
2. Confirm no tracked file still imports the module after the sibling Phase 2 edits land (sibling documents 02, 03, 04, 05, 06, 07, 11 handle their own importers).

### Method
- The module currently exports `MigrationRefusalReason` (line 63), `MigrationRefusalError` (line 92), `MigrationSpec` (line 109), `LedgerRow` (line 135), `ensure_ledger` (line 149), `read_ledger` (line 154), `record_applied` (line 184), `MigrationArchive` (line 288), `archive_pre_migration` (line 315), `MigrationRunner` (line 395), and ledger constants `_LEDGER_TABLE` (line 42), `_LEDGER_CREATE` (line 43).
- Importers at HEAD: `scripts/db/migrations_workflow.py`, `scripts/db/create_schema.py`, `scripts/db/migrate_db.py`, `scripts/db/recovery_drill.py`, `scripts/eventbus/migrations.py`, `scripts/eventbus/schema.py`, `scripts/eventbus/migrate.py` — every one is deleted or edited by another row of this Plan.

### Details
- No database file is read, written, archived, or deleted by this procedure (REQ-004 boundary).

### Companion test files
- `tests/shared/test_db_migrations.py`
  - Procedure: `git rm` the module in the same Phase 2 commit — it tests only the deleted runner, ledger, and refusal types (row 13).
  - Validation: file absent afterwards; `uv run pytest tests/` collection shows no reference to it.

## Compatibility considerations

- Any still-open database keeps its `schema_migrations` table untouched; the deletion changes code only (REQ-004).

## Security considerations

- N/A: pure deletion; removes an operator CLI surface (handled by rows 04-05 documents).

## Rollback considerations

- Revert the commit restores the module and its companion test (single-commit deletion).

## Validation plan

- `grep -rn "shared.db_migrations\|shared/db_migrations" scripts/ tests/ tools/ deploy/` — only historical records (done/ documents) remain.
- `uv run pytest tests/` — full collection succeeds after all Phase 2/3 sibling documents land.
- `uv run python tools/check_compat_shims.py` — clean.
- Completion gates per `rules/toolchain.md` run in Plan Phase 5 for the whole unit.

## Completion criteria

- The module and `tests/shared/test_db_migrations.py` are absent (AC-001, AC-003).
- No source, test, deploy, or tool file imports any deleted symbol (AC-003).

## Out of Scope

- Re-pointing importers (`create_schema.py`, `eventbus/schema.py`, `recovery_drill.py`) — sibling documents 06, 07, 11.
- Deleting the CLI entry points — sibling documents 04, 05.
- `tools/check_db_separation.py` allowed-table sets (left permissive per Plan Assumptions).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | `git rm scripts/shared/db_migrations.py` and `tests/shared/test_db_migrations.py` (Plan Phase 2) | Completed | 20261107-115031 | 20261107-115031 | Release unit "current-schema-only-cutover": suite green only after Phases 1-3 stale check clean; git rm both files; residual importer only tests/db/test_eventbus_schema_equivalence.py (deleted by sibling doc 16) |
| 2 | Verify no remaining import of the deleted symbols (grep + full-suite collection + `check_compat_shims.py`) | Completed | 20261107-115031 | 20261107-134715 | grep clean except doc16 target; full collection + check_compat_shims deferred to unit-end pass targeted tests green; full suite 11780 passed, diff-cover 100 pct |
| 3 | Run the validation sequence (`rules/toolchain.md`) in the Phase 5 unit pass | Completed | — | 20261107-134814 | end-of-unit validation sequence green: ruff, mypy 558 files, lint-imports 6 kept, bandit -ll rc 0, full-suite coverage 11780 passed, diff-cover 100 pct |

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
- **Related target files**: `scripts/shared/db_migrations.py`, `tests/shared/test_db_migrations.py`