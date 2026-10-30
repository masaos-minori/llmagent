## Goal

Create the framework regression tests in `tests/shared/test_db_migrations.py` (`REQ-001` to `REQ-004`, ordered migration, verified-backup gate, refusals, dry-run).

## Scope

- Create only `tests/shared/test_db_migrations.py`.

## Assumptions

- Depends on row 01. Each test is written to fail before the framework exists and pass after (Plan Tests). `tests/shared/` exists; use file-based SQLite under `tmp_path` (the framework opens its own connections).
- `tests/eventbus/test_eventbus_db_migration.py` covers only pragmas; there is no existing migration test to extend.
- Names that `tools/stale_detector.py` flags in this document are created by other rows of this Plan (the framework row 01 and the domain, drill, and schema rows it names) and exist when `code-implementation` executes the rows in Plan phase order.

## Design decisions

- Build a small throwaway domain in the test (table `t`, version stored in `PRAGMA user_version`) so the framework is tested without EventBus or workflow code.

## Alternatives considered

- Parametrize over both version stores: rejected, one throwaway domain proves the accessor seam; row 17 covers the table-based store.

## Implementation

### Target file

`tests/shared/test_db_migrations.py` (new)

### Procedure

1. Add tests for: successful chain of two specs with ledger rows and a backup; mid-migration failure leaves the original intact and the ledger unchanged; interrupted migration (a step that kills before commit) leaves the original intact; downgrade refusal; unknown path refusal; ambiguous path refusal; dry-run leaves the file byte-identical (hash compare, AC-5); refusal when the backup copy fails integrity (fault injection between backup and migration, AC-4); no-op path creates no backup.

### Method

- Hash with `hashlib.sha256` over the database file bytes before and after dry-run (checkpoint first so WAL state does not differ).
- Inject the integrity failure by patching the framework's integrity helper at the framework's own module name.

### Details

- Follow the repository test style (`from __future__ import annotations`, pytest, `tmp_path`); mark none as integration.

## Compatibility considerations

- New test module.

## Security considerations

- N/A: tests only.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/shared/test_db_migrations.py -v`
- `uv run ruff format tests/shared/test_db_migrations.py`, `uv run ruff check tests/shared/test_db_migrations.py`

## Completion criteria

- All listed behaviors are asserted and the tests fail when the corresponding framework behavior is removed.

## Out of Scope

- Domain-specific registries and CLIs.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write the tests per Procedure | Completed | 20261030-162046 | 20261030-162046 | Plan Phase 1; written before or with row 01 15 tests; 20 incl. boundary guard pass |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261030-162046 | 20261030-162046 | same validation and full-suite run as row 01 (no change in between) |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004
- **Source issue**: issues/20261029-104500_dbmig001_forward-only-db-migrations.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261029-214108_dbmig001_forward-only-db-migrations.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-151746
- **Related target files**: tests/shared/test_db_migrations.py