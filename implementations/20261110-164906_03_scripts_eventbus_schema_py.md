## Goal

Switch `scripts/eventbus/schema.py` to validate an existing database with the generalized
fingerprint only: drop the `PRAGMA user_version` read/stamp comparison (`REQ-003`, `REQ-004`).

## Scope
**Release unit**: fingerprint-cutover (Phase 2)

## Assumptions
- `schema.sql` no longer stamps `user_version` (this Phase deletes the stamp; see the
  `schema.sql` row), so `_expected_schema_version()` is unused and removed.
- Callers import from the new module: `from shared.schema_fingerprint import assert_matches`.

## Design decisions
- `_init_schema()` compares shape only: apply the canonical `schema.sql` text to an in-memory DB via the generalized `assert_matches(conn, canonical_ddl, label="eventbus.sqlite")`; remove the `found == expected` version branch and `_expected_schema_version()`.
- Keep the fail-closed refusal message telling the operator to archive and recreate.

## Alternatives considered
- Keeping a `user_version` pre-check: rejected as a second mechanism (REQ-004).

## Implementation
### Target file
`scripts/eventbus/schema.py`

### Procedure
1. Change the import to `from shared.schema_fingerprint import assert_matches`.
2. In `_init_schema()`: when the `events` table is absent, execute the canonical DDL (unchanged); when present, read the DDL text and call `assert_matches(conn, sql, label="eventbus.sqlite")`, then return.
3. Delete `_VERSION_RE` and `_expected_schema_version()`.
4. Rewrite the docstring to describe fingerprint-only validation and remove the `user_version 0` refusal wording.

### Method
- The fresh-file path is unchanged (create when absent). The existing-file path now always fingerprints; any shape difference raises the archive-and-recreate error. No version branch remains.

### Details
- Pass the canonical DDL via `build_eventbus_schema_sql()` if one exists, else read `_SCHEMA_PATH.read_text()` and strip nothing (the normalizer handles comments). Keep the refusal text identical to `LEGACY_MARKER_REFUSAL_MESSAGE` semantics.

## Compatibility considerations
Existing eventbus databases keep their (now-ignored) `user_version`; matching databases behave identically, mismatched ones are now refused on shape.

## Security considerations
Read-only fingerprint of an existing database; no mutation on refusal.

## Rollback considerations
Revert the commit (Phase 2 release unit).

## Validation plan
`uv run pytest tests/eventbus/test_eventbus_startup.py -v` (stamp assertions replaced with fingerprint assertions by that row); `uv run pytest tests/eventbus -v` passes.

## Completion criteria
`scripts/eventbus/schema.py` imports `schema_fingerprint.assert_matches`, has no `user_version` read, and refuses shape drift with the archive-and-recreate error.

## Out of Scope
Deleting `eventbus_schema_fingerprint.py` (its row) and the `schema.sql` stamp (its row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261111-083915 | _init_schema is fingerprint-only (assert_matches with label eventbus.sqlite); _VERSION_RE/_expected_schema_version deleted |
| 2 | Add or update tests per Validation plan | Completed | — | 20261111-084928 | test file rewrite owned and executed by member 23 (same target file); fingerprint cases verified passing |
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
- **Requirement ID**: `REQ-003` / `REQ-004` — validate eventbus by fingerprint only
- **Source issue**: issues/20261109-112715_adrrev005_schema-fingerprint-unify.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-095137_adrrev005_schema-fingerprint-unify.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-164906
- **Related target files**: `scripts/eventbus/schema.py`