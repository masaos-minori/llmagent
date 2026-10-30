## Goal

Add the migration ledger table to `scripts/eventbus/schema.sql` (`REQ-001`, registry state; `REQ-006`, applied-state ledger) while keeping the version stamp as the fingerprint source.

## Scope

- Modify only `scripts/eventbus/schema.sql`.

## Assumptions

- Verified (Step 3a): `schema.sql` ends with the comment and `PRAGMA user_version = 3;`, and is read by `_SCHEMA_PATH` in `scripts/eventbus/schema.py`, by `eventbus_schema_version` in `scripts/db/schema_sql.py`, and by `scripts/shared/eventbus_schema_fingerprint.py`; adding a table changes the fingerprint.
- The ledger table is part of the canonical shape, so the stamp must change: bump `user_version` to 4 (the existing comment says to bump it when the schema changes). This is a real eventbus schema change shipped with the registry: version 3 databases need a registered spec from 3 to 4 (created by the row 02 document) or a refusal; see Details.
- Plan overlap judgment: `plans/20261029-221254_dlqbox001_dlq-sqlite-outbox.md` also targets this file; sequencing dependency, this Plan lands first.
- Names that `tools/stale_detector.py` flags in this document are created by other rows of this Plan (the framework row 01 and the domain, drill, and schema rows it names) and exist when `code-implementation` executes the rows in Plan phase order.

## Design decisions

- Add `CREATE TABLE IF NOT EXISTS schema_migrations (id TEXT PRIMARY KEY, applied_at TEXT NOT NULL, from_version TEXT NOT NULL, to_version TEXT NOT NULL);` before the stamp.
- The `to_version` (new) of the baseline equals the stamped version.

## Alternatives considered

- Keep the ledger out of the DDL and create it lazily: rejected, the Plan requires the ledger to be part of the canonical shape (REQ-006) so ledger and fingerprint prove the state together.

## Implementation

### Target file

`scripts/eventbus/schema.sql`

### Procedure

1. Add the ledger DDL above the `PRAGMA user_version` stamp, with a short comment.
2. Bump the stamp from 3 to 4 and extend the comment: version 4 adds `schema_migrations` (new).

### Method

- Match the existing DDL style (uppercase keywords, aligned columns).
- Step 3a: only `tests/eventbus/test_eventbus_schema_version.py:74-75` (`assert eventbus_schema_version() == 3`) pins the stamp (a target row, row 16 document); `tests/db/test_create_schema.py` reads it dynamically through `eventbus_schema_version()`; no other file pins 3.

### Details

- A stamp bump makes version 3 databases fail the version check until the registry carries a 3 to 4 spec: row 02's registry therefore registers a `ledger-baseline` spec (3 to 4, applies only the `CREATE TABLE`), shipped in the same release. Recreation instead would discard canonical rows, contradicting REQ-009.
- Needs confirmation (non-blocking): which migration id and wording to use for the 3 to 4 baseline spec; the Plan assumes a version-0 stamping step but `eventbus.sqlite` is already stamped at 3.

## Compatibility considerations

- N/A: no further compat beyond the other sections.

## Security considerations

- N/A: DDL only.

## Rollback considerations

- Revert the commit together with row 02's spec; a database already migrated to 4 is restored from its pre-migration backup (forward-only).

## Validation plan

- `uv run pytest tests/eventbus tests/db/test_eventbus_schema_equivalence.py -v`
- `uv run python tools/check_db_separation.py`
- `uv run python tools/generate_reference_table.py --check`

## Completion criteria

- `schema.sql` defines `schema_migrations` (new) and stamps the new version; `build_eventbus_schema_sql()` and the fingerprint tests agree with it.

## Out of Scope

- Outbox or any other table (`dlqbox001`).
- Migration code (rows 01-03).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the ledger DDL and bump the stamp | Pending | — | — | Plan Phase 2; with row 02's baseline spec |
| 2 | Add or update tests per Validation plan | Pending | — | — | Covered by the row 15 and 16 documents |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — |  |

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
- **Related target files**: scripts/eventbus/schema.sql
