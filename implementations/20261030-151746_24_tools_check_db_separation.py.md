## Goal

Register the `schema_migrations` ledger table in the table-ownership inventory of `tools/check_db_separation.py` for `workflow` and `eventbus` (`REQ-001`, registry state; `REQ-006`, applied-state ledger), so the ADR-008 separation check accepts the ledger DDL.

## Scope

- Modify only `tools/check_db_separation.py`.
- Plan amendment (user-approved 2026-10-30): this row was appended after row 23 as an additional target file discovery.

## Assumptions

- Verified (Step 3a): `TABLE_OWNERSHIP` at `:55-77` lists each database's tables; the check reports `workflow.sqlite creates table 'schema_migrations', which is not in the inventory` once the ledger DDL exists (reproduced while executing the `scripts/db/schema_sql.py` row). Its comment says to update the inventory together with the ADR when a table is added.
- `tests/tools/test_check_db_separation.py` has no pinned table sets; its live-repository test passes once the inventory matches the DDL, so no test change is needed.
- Execution order: before the `scripts/db/schema_sql.py` row (Phase 3) and the `scripts/eventbus/schema.sql` row (Phase 2); the Plan's Phase 3 lists it first. A new or modified `tools/*.py` follows `routing.md` Tools "Adding a new tool" (lighter validation).
- Names that `tools/stale_detector.py` flags in this document are created by other rows of this Plan (the framework row 01 and the domain, drill, and schema rows it names) and exist when `code-implementation` executes the rows in Plan phase order.

## Design decisions

- Add the ledger name to both the `workflow` and `eventbus` sets: both databases carry one `schema_migrations` table, and the check keys ownership by database, so the same name in two sets is the intended shape (see how the check resolves an owner at `:142-144` before editing).

## Alternatives considered

- Exempt the ledger from the inventory: rejected, it would hide a real table from the separation check.

## Implementation

### Target file

`tools/check_db_separation.py`

### Procedure

1. Add `"schema_migrations"` to the `workflow` frozenset and to the `eventbus` frozenset.

### Method

- Keep the sets' formatting (one name per line in the workflow set).

### Details

- Read `check_db_separation.py:136-160` first: the owner lookup `next((d for d, t in TABLE_OWNERSHIP.items() if name in t), None)` picks the first database whose set contains a name, so a name present in two sets may be attributed to the wrong database in the cross-database foreign-key and creation checks. If that makes the live check fail, stop and report instead of changing the lookup (that would be a second behavior change in this tool).

- Correction (Step 3a): the check also fails with `no longer creates inventory table` when an inventory entry has no DDL (`check_table_ownership`: `expected - tables`), so each inventory entry must land together with its DDL. This document therefore executes in two halves: step 1 (`workflow`) right before the `scripts/db/schema_sql.py` row, step 2 (`eventbus`) right before the `scripts/eventbus/schema.sql` row. The document is archived only after both halves and the validation ran.

## Compatibility considerations

- Additive inventory entries; no behavior change for existing tables.

## Security considerations

- N/A: static inventory.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run ruff format tools/check_db_separation.py`, `uv run ruff check tools/check_db_separation.py`, `uv run mypy tools/check_db_separation.py`, `uv run bandit tools/check_db_separation.py`
- `uv run python tools/check_db_separation.py` against the live repository (after the DDL rows land, no violation)
- `uv run pytest tests/tools/test_check_db_separation.py -v`
- `uv run python tools/check_tool_descriptions_sync.py`

## Completion criteria

- `TABLE_OWNERSHIP` lists `schema_migrations` for `workflow` and `eventbus`, the live check and its test pass once the DDL rows land, and the tool lints, type-checks, and passes bandit.

## Out of Scope

- The DDL rows, the ADR table-ownership text (row 20), and any change to the owner lookup.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `schema_migrations` to the `workflow` set | Completed | 20261030-165727 | 20261030-165727 | Plan Phase 3; immediately before row 09 workflow entry added |
| 2 | Add `schema_migrations` to the `eventbus` set | Pending | — | — | Gated: immediately before row 04 (Phase 2) |
| 3 | Run the tool validation (`routing.md` Adding a new tool) | Pending | — | — | No test row; `tests/tools/test_check_db_separation.py` unmodified; run after each of steps 1 and 2 |

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
- **Requirement ID**: REQ-001, REQ-006
- **Source issue**: issues/20261029-104500_dbmig001_forward-only-db-migrations.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261029-214108_dbmig001_forward-only-db-migrations.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-151746
- **Related target files**: tools/check_db_separation.py