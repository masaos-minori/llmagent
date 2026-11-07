## Goal

- Delete `scripts/db/migrate_db.py` — the operator-facing Workflow migration CLI (220 lines) — so no automatic migration entry point exists (REQ-001: delete the migration framework modules).

## Scope
**Release unit**: current-schema-only-cutover

- Whole-file deletion of the CLI. Operator guidance replaces it: archive-and-recreate via `deploy/init_db.sh` (sibling document 12).

## Assumptions

- UNK-01: whether any external runbook/crontab/systemd unit invokes this CLI is resolved in Plan Phase 5 before deploy; the deletion itself is not blocked.
- `deploy/init_db.sh` guidance lines naming `db/migrate_db.py --apply` are removed by sibling document 12 in Phase 3.

## Design decisions

- No deprecated stub: REQ-001 leaves zero shim behind (`tools/check_compat_shims.py` gate).

## Alternatives considered

- Keeping `--status` (ledger read) as a diagnostic: rejected — the ledger itself is removed from the policy; the recovery-drill marker audit (document 11) is the diagnostic surface (REQ-006).

## Implementation
### Target file
`scripts/db/migrate_db.py`

### Procedure
1. `git rm scripts/db/migrate_db.py` in the Phase 2 commit (Plan Phase 2).

### Method
- The module's docstring header is `"""scripts/db/migrate_db.py — Workflow forward-only migration CLI.`; its import block includes `from shared.db_migrations import MigrationRefusalError, MigrationRefusalReason, read_ledger` and the workflow registry path `db.migrations_workflow` — both deleted by siblings (documents 01, 02).

### Details
- No database file is read, written, archived, or deleted by this procedure.

## Compatibility considerations

- Operators must stop using `db/migrate_db.py --apply`; the fixed refusal/recreate message (REQ-004) replaces it.

## Security considerations

- N/A: pure deletion; removes an operator write surface.

## Rollback considerations

- Revert the commit restores the CLI (single-commit deletion).

## Validation plan

- `grep -rn "migrate_db" scripts/ tests/ deploy/ docs/` — no remaining executable reference after siblings land.
- `uv run pytest tests/` — collection succeeds (document 14 deletes the test module that covered this CLI).
- Whole-unit gates run in Plan Phase 5 per `rules/toolchain.md`.

## Completion criteria

- The CLI file is absent and no deploy script, code, or test references it (AC-001).

## Out of Scope

- Removing the `migrate_db.py` guidance lines from `deploy/init_db.sh` — sibling document 12.
- UNK-01 external-reference sweep — Plan Phase 5 operator step.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | `git rm scripts/db/migrate_db.py` (Plan Phase 2) | Completed | 20261107-115200 | 20261107-115200 | Release unit "current-schema-only-cutover" git rm clean; importers owned by sibling docs |
| 2 | Verify no remaining reference (grep + full-suite collection) | Completed | — | 20261107-134716 | UNK-01 sweep is the Phase 5 step importer/reference verification: ast-grep binary absent locally; substituted with ruff, mypy, lint-imports, and the m5 dependency-direction tests, all green |
| 3 | Run the validation sequence (`rules/toolchain.md`) in the Phase 5 unit pass | Completed | — | 20261107-134815 | end-of-unit validation sequence green: ruff, mypy 558 files, lint-imports 6 kept, bandit -ll rc 0, full-suite coverage 11780 passed, diff-cover 100 pct |

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
- **Related target files**: `scripts/db/migrate_db.py`