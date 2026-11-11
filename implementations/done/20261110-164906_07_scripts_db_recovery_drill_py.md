## Goal

Replace the legacy marker-table detector in `scripts/db/recovery_drill.py` with the
generalized fingerprint check for each domain (`REQ-003`, `REQ-004`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Current code defines `LEGACY_MARKER_TABLES = ("schema_migrations", "workflow_schema_version")`
  and `_legacy_marker_tables()`; the drill reports their presence as a finding (lines 50-71).
- Canonical DDL is available via `db.schema_sql` accessors and `eventbus/schema.sql`.

## Design decisions
- Replace the marker-table presence check with a per-domain `assert_matches(conn, canonical_ddl, label=...)` call in the drill's per-domain verification; a shape difference is the finding instead of a marker-table name list.
- Remove `LEGACY_MARKER_TABLES` and `_legacy_marker_tables()` once unused.

## Alternatives considered
- Keeping marker-table detection as a separate check: rejected; one mechanism (REQ-004).

## Implementation
### Target file
`scripts/db/recovery_drill.py`

### Procedure
1. In the per-domain verification path, open the archived/isolated database and call the generalized fingerprint with the domain's canonical DDL.
2. Replace the marker-table finding message with the fingerprint diff / archive-and-recreate error.
3. Delete `LEGACY_MARKER_TABLES`, `LEGACY_MARKER_REFUSAL_MESSAGE` (if unused elsewhere), and `_legacy_marker_tables()`.

### Method
- Locate the caller of `_legacy_marker_tables` / the drill finding (around line 238 area) and substitute a fingerprint assertion; keep the drill's read-only contract.

### Details
- The drill must still report a missing table, extra legacy table, extra column, and missing index as failures (the four drift cases) via the fingerprint diff.

## Compatibility considerations
The drill's external output (a JSON artifact) keeps its shape; only the finding source changes.

## Security considerations
Read-only inspection of archived copies.

## Rollback considerations
Revert the commit.

## Validation plan
`uv run pytest tests/db/test_recovery_drill.py -v` (that row replaces the marker-table finding with the fingerprint finding); `uv run pytest tests/db -v` passes.

## Completion criteria
`scripts/db/recovery_drill.py` reports drift via fingerprint matching; no marker-table detector remains.

## Out of Scope
Changing the drill's artifact schema.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261111-110544 | marker scan removed; fingerprint gate via read-only conn |
| 2 | Add or update tests per Validation plan | Completed | — | 20261111-110544 | verification key schema_matches; artifact error = refusal text |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261111-110544 | tests/db/test_recovery_drill.py 13 tests pass; ruff/mypy clean |

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
- **Requirement ID**: `REQ-003` / `REQ-004` — fingerprint check replaces marker-table detector
- **Source issue**: issues/20261109-112715_adrrev005_schema-fingerprint-unify.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-095137_adrrev005_schema-fingerprint-unify.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-164906
- **Related target files**: `scripts/db/recovery_drill.py`