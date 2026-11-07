## Goal

- Delete `scripts/eventbus/migrate.py` — the operator-facing EventBus migration CLI (187 lines) — so no automatic migration entry point exists (REQ-001: delete the migration framework modules).

## Scope
**Release unit**: current-schema-only-cutover

- Whole-file deletion of the CLI. Operator guidance replaces it: archive-and-recreate via `deploy/init_db.sh` (sibling document 12).

## Assumptions

- UNK-01: whether any external runbook/crontab/systemd unit invokes this CLI is resolved in Plan Phase 5 before deploy; the deletion itself is not blocked.
- `deploy/init_db.sh` currently prints guidance naming this CLI (lines 100-123 block); sibling document 12 removes those lines in Phase 3, so the deletion lands consistently within the release unit.

## Design decisions

- No deprecated stub or "command removed" wrapper: REQ-001 leaves zero shim behind (`tools/check_compat_shims.py` gate).

## Alternatives considered

- Keeping a status-only CLI: rejected — REQ-001 deletes the ledger status surface; `tools/check_db_separation.py` and startup gates cover diagnostics.

## Implementation
### Target file
`scripts/eventbus/migrate.py`

### Procedure
1. `git rm scripts/eventbus/migrate.py` in the Phase 2 commit (Plan Phase 2).

### Method
- The module's docstring header is `"""scripts/eventbus/migrate.py — EventBus forward-only migration CLI.`; it imports `shared.db_migrations` (`MigrationRunner` path) and `eventbus.migrations.REGISTRY` — both deleted by siblings (documents 01, 03).
- Its service-listener guard (socket listener refusal) has no replacement need: after the cutover the EventBus gate runs in `eventbus.schema._init_schema` only (document 07).

### Details
- No database file is read, written, archived, or deleted by this procedure.

## Compatibility considerations

- Operators must stop using `eventbus/migrate.py --apply`; the refusal/recreate guidance text (REQ-004) replaces it in the startup gate and deploy gate messages.

## Security considerations

- N/A: pure deletion; removes an operator write surface.

## Rollback considerations

- Revert the commit restores the CLI (single-commit deletion).

## Validation plan

- `grep -rn "eventbus/migrate.py\|eventbus.migrate" scripts/ tests/ deploy/ docs/` — no remaining executable reference after siblings land (docs references are handled by documents 25-29).
- `uv run pytest tests/` — collection succeeds (document 15 deletes the test module that covered this CLI).
- Whole-unit gates run in Plan Phase 5 per `rules/toolchain.md`.

## Completion criteria

- The CLI file is absent, no deploy script or code references it, and `check_compat_shims.py` is clean (AC-001).

## Out of Scope

- Removing the `migrate.py` guidance lines from `deploy/init_db.sh` — sibling document 12.
- UNK-01 external-reference sweep — Plan Phase 5 operator step.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | `git rm scripts/eventbus/migrate.py` (Plan Phase 2) | Completed | 20261107-115200 | 20261107-115200 | Release unit "current-schema-only-cutover" git rm clean; importers owned by sibling docs |
| 2 | Verify no remaining reference (grep + full-suite collection) | Completed | — | 20261107-134716 | UNK-01 sweep is the Phase 5 step targeted tests green; full suite green |
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
- **Related target files**: `scripts/eventbus/migrate.py`