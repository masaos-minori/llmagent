## Goal

Declare `attempts.owner_id` and `attempts.lease_expires_at` `NOT NULL` with `CHECK(length(owner_id) > 0)` in the canonical workflow DDL, making the null-lease an invalid state the database rejects as the last backstop (`REQ-005`, Decision 2).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The fingerprint gate (`shared.schema_fingerprint.assert_matches`) derives shape dynamically from canonical DDL (`expected_fingerprint` applies DDL to a fresh in-memory DB and reads `PRAGMA table_info`, including the `notnull` flag), so adding `NOT NULL`/`CHECK` changes the derived shape with no per-object expectation to maintain. Confirmed by reading `schema_fingerprint.py`.
- `create_schema.py` applies `build_workflow_schema_sql()` then gates; `deploy/init_db.sh` re-runs the gate. Both need no change (reference files).
- An old nullable database is refused by the existing fingerprint gate and left byte-for-byte unchanged (AC8) — no migration/null-fill shim (AC9).

## Design decisions
- **`NOT NULL` + `CHECK(length(owner_id) > 0)` (Decision 2).** `get_owner_id()` never yields an empty string, so the `CHECK` excludes only rows the writer cannot produce (manually corrupted / externally inserted). It is the last backstop, matching the Issue's "database rejects null lease metadata as the last backstop".
- **Column-level placement.** Place both clauses inline on each column in the `attempts` table definition, preserving the existing comment style.

## Alternatives considered
- **`NOT NULL` only (no CHECK):** would permit an empty-string owner to slip through recovery ownership checks. Rejected (Decision 2 rationale).

## Implementation
### Target file
`scripts/db/schema_sql.py`
### Procedure
1. Make `owner_id` `NOT NULL` with `CHECK(length(owner_id) > 0)`.
2. Make `lease_expires_at` `NOT NULL`.
### Method
Two column-definition edits inside `_WORKFLOW_SCHEMA`.
### Details
- In `_WORKFLOW_SCHEMA`, the `attempts` table (lines 181-194), replace:
  ```sql
       owner_id         TEXT,
       lease_expires_at TEXT
  ```
  with:
  ```sql
       owner_id         TEXT NOT NULL CHECK (length(owner_id) > 0),
       lease_expires_at TEXT NOT NULL
  ```
  Keep the surrounding column alignment/comments intact. No other table changes.
- No change to `build_workflow_schema_sql()` (it returns `_WORKFLOW_SCHEMA` unchanged).

## Compatibility considerations
The `NOT NULL` makes a lease-less `attempts` row physically impossible in a fresh database (AC7). A fresh database rejects a null-lease raw insert with `sqlite3.IntegrityError`. An old nullable database is refused by the fingerprint gate and recreated (AC8); no migration is added (AC9). The writer (seq 01) always stamps both columns, so shipped writes are unaffected.

## Security considerations
N/A: no auth/permission changes. The `CHECK` is a data-integrity backstop against manually corrupted/externally-inserted rows, not a trust boundary.

## Rollback considerations
Revert the commit; the change is two column definitions. Note: applying this to a live production database without recreation triggers the fingerprint gate refusal (by design).

## Validation plan
- Unit: build the workflow DDL in a fresh connection; assert both lease columns are `not null` via `PRAGMA table_info(attempts)`.
- Unit: raw insert with a null lease → expect `sqlite3.IntegrityError`; FK-cascade and vocabulary inserts (which supply the columns) succeed.
- Manual: open an old-shape database and confirm refusal without modification.
- Command: `uv run pytest tests/db/test_create_schema.py` (seq 10).

## Completion criteria
- `attempts.owner_id` and `attempts.lease_expires_at` are `NOT NULL`; `owner_id` also carries `CHECK(length(owner_id) > 0)`.
- A fresh database defines both columns `NOT NULL`; a null-lease raw insert fails with `sqlite3.IntegrityError`.

## Out of Scope
The writer's stamping (seq 01); the facade (seq 02); the model (seq 03); raw-`INSERT` test updates (seq 10); migration/null-fill shims.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261117-130127 | 20261117-130127 | Part of release unit "schema-before-write" (spans Steps 1-2) |
| 2 | Add or update tests per Validation plan | Completed | 20261117-130127 | 20261117-130127 | Covered by `test_create_schema.py` (seq 10). |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261117-130127 | 20261117-130127 |  |

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
- **Requirement ID**: `REQ-005` (NOT NULL + CHECK on both lease columns)
- **Source issue**: `issues/20261116-114834_compat002_mandatory-attempt-leases.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261116-221315_compat002_mandatory-attempt-leases.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261117-011632
- **Related target files**: `scripts/db/schema_sql.py`