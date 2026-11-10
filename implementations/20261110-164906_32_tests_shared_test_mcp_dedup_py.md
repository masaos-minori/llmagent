## Goal

Replace the mcp_dedup stamp expectations with a fingerprint-refusal case (`REQ-003`,
`REQ-004`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `scripts/shared/mcp_dedup.py` now creates the table when absent and validates an
  existing store by the generalized fingerprint instead of stamping `user_version` (its
  row).
- The `_SNAP` snapshot metadata is read by the named `execution_snapshot` observability
  exception, so its `user_version` key stays.

## Design decisions
- Keep the `_SNAP` fixture; add one case that opens a drifted dedup store and asserts the
  archive-and-recreate refusal.

## Alternatives considered
N/A: test-only row; the wording follows the Plan's settled behavior.

## Implementation
### Target file
`tests/shared/test_mcp_dedup.py`

### Procedure
1. Keep the `_SNAP` fixture (lines 25-31); the `user_version` key at line 30 is snapshot
   metadata consumed by the named `execution_snapshot` exception, not a stamp assertion.
2. Add a case that opens a `DedupStore` against a pre-populated store whose table shape
   drifts (e.g. an extra column) and asserts the generalized fingerprint refuses with the
   archive-and-recreate error.
3. Remove any assertion that a `user_version` stamp is written on open.

### Method
- Locate the store-open path and snapshot usage with
  `rg -n 'DedupStore|open_dedup_store|_SNAP|user_version' tests/shared/test_mcp_dedup.py`
  before editing.

### Details
- Build the drifted store in a temp file and open it through the real `DedupStore` so the
  actual gate is exercised.

## Compatibility considerations
The imports at line 15 (`DedupStore`, `open_dedup_store`) stay.

## Security considerations
None.

## Rollback considerations
N/A: revert the commit.

## Validation plan
`uv run pytest tests/shared/test_mcp_dedup.py -v` — the drift case fails with the explicit
error; other cases pass.

## Completion criteria
A drifted mcp_dedup store is refused with the archive-and-recreate error; the snapshot
metadata fixture is retained.

## Out of Scope
Changing `mcp_dedup.py` itself (its row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the fingerprint-refusal case; drop stamp expectations | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-003` / `REQ-004` — mcp_dedup fingerprint-refusal case
- **Source issue**: issues/20261109-112715_adrrev005_schema-fingerprint-unify.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-095137_adrrev005_schema-fingerprint-unify.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-164906
- **Related target files**: `tests/shared/test_mcp_dedup.py`
