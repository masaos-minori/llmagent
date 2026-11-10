## Goal

Add unit tests for the generalized fingerprint in `tests/shared/test_schema_fingerprint.py`
(`REQ-002`, `REQ-005`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The new module exposes `assert_matches(conn, canonical_ddl, label=...)` (its row); tests pass
  canonical DDL text and an in-memory or temp connection.

## Design decisions
- Cover each drift kind against a known-good canonical DDL: missing CHECK constraint, extra legacy table, extra column, missing index, trigger difference; a matching database passes; a vec virtual table is satisfied by name.

## Alternatives considered
- Testing via the eventbus module: rejected; this tests the generalized module directly.

## Implementation
### Target file
`tests/shared/test_schema_fingerprint.py` (new)

### Procedure
1. Define a small canonical DDL fixture (e.g. a table with a CHECK, an index, a trigger).
2. For each drift case, apply a modified DDL to a fresh in-memory DB and assert `assert_matches(...)` raises `RuntimeError` with an archive-and-recreate message.
3. Assert a byte-identical canonical DDL passes.
4. Add a case where a vec virtual table is present-by-name and does not break the comparison.

### Method
- Use `sqlite3.connect(":memory:")` + `executescript(ddl)` per case; reuse one canonical DDL string and derive variants by string edits.

### Details
- Keep stdlib-only; no fixtures beyond tempfile/temp connections.

## Compatibility considerations
New file; no existing test affected.

## Security considerations
None.

## Rollback considerations
Revert the commit.

## Validation plan
`uv run pytest tests/shared/test_schema_fingerprint.py -v` passes for all drift kinds.

## Completion criteria
All drift kinds fail with the explicit error; a matching database passes; vec-by-name case passes.

## Out of Scope
Per-database drift tests (`tests/db/test_schema_validation_per_database.py`, its row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-002` / `REQ-005` — fingerprint unit tests
- **Source issue**: issues/20261109-112715_adrrev005_schema-fingerprint-unify.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-095137_adrrev005_schema-fingerprint-unify.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-164906
- **Related target files**: `tests/shared/test_schema_fingerprint.py`
