## Goal

Replace the existence-only `required_tables` checks in `scripts/db/session_consistency.py`
with the fingerprint check for `session.sqlite` (`REQ-003`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Current `_check_required_tables_exist()` and `_check_read_smoke_test()` only verify table
  names exist (lines 54-96); they do not compare columns, indexes, constraints, or triggers.
- Canonical session DDL comes from `db.schema_sql.build_session_schema_sql()`.

## Design decisions
- On the read path used for startup validation, call `assert_matches(conn, canonical_ddl, label="session.sqlite")` so a schema mismatch raises the archive-and-recreate error instead of passing existence-only.
- Keep the diagnostic/report functions (orphan detection, smoke reads) that are not schema-shape checks.

## Alternatives considered
- Extending the existence check to compare shapes inline: rejected; reuse the one mechanism.

## Implementation
### Target file
`scripts/db/session_consistency.py`

### Procedure
1. Import `assert_matches` from `shared.schema_fingerprint` and the session accessor from `db.schema_sql`.
2. In the consistency entry point, when validating an existing database, assert the fingerprint before returning a "consistent" report.
3. Leave orphan/diagnostic queries unchanged.

### Method
- Insert the fingerprint assertion where the current code currently returns success after the existence/smoke checks; on mismatch raise `RuntimeError` (archive-and-recreate).

### Details
- Vec tables (`memories_vec`, `memories_fts`) are required by name only (UNK-01); the fingerprint excludes their shape.

## Compatibility considerations
A matching session database behaves the same; a mismatched one now fails startup.

## Security considerations
Read-only fingerprint.

## Rollback considerations
Revert the commit.

## Validation plan
`uv run pytest tests/db/test_create_schema.py -v` (that row covers session); `uv run pytest tests/db -v` passes.

## Completion criteria
`scripts/db/session_consistency.py` validates `session.sqlite` by fingerprint; existence-only is gone.

## Out of Scope
Changing session diagnostic/orphan logic.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261111-111429 | existence-only check replaced by assert_matches(label session.sqlite); drill/verification callers record RuntimeError fail-closed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261111-111429 | tests/db 363 pass; drill+recovery+init_db gate 94 pass; lint/mypy/imports clean |

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
- **Requirement ID**: `REQ-003` — validate session by fingerprint
- **Source issue**: issues/20261109-112715_adrrev005_schema-fingerprint-unify.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-095137_adrrev005_schema-fingerprint-unify.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-164906
- **Related target files**: `scripts/db/session_consistency.py`