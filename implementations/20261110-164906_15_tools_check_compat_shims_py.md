## Goal

Update the marker-table exception comments in `tools/check_compat_shims.py` now that the
marker-table detectors are removed (`REQ-004`, `REQ-007`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The file documents an exception for marker-table detectors at lines 128-132 and 443-449; the
  detectors (`LEGACY_MARKER_TABLES` in `workflow_schema.py`/`recovery_drill.py`) are removed by
  this Plan, so those comments no longer match live code.

## Design decisions
- Reword the two comment blocks to reflect that marker-table detection is gone and fingerprint matching is the single mechanism; do not change the checker's logic.

## Alternatives considered
- Deleting the exception blocks: rejected; they may gate a legitimate named exception — reword, don't delete.

## Implementation
### Target file
`tools/check_compat_shims.py`

### Procedure
1. Read lines 128-132 and 443-449; reword each comment to reference fingerprint matching instead of a marker-table detector that no longer exists.
2. Re-run the checker to confirm it still passes.

### Method
- Keep any functional exception the comments describe; only correct the now-stale prose referencing removed detectors.

### Details
- `uv run python tools/check_compat_shims.py` must exit 0 after the edit.

## Compatibility considerations
Documentation-comment only; no behavior change.

## Security considerations
None.

## Rollback considerations
Revert the commit.

## Validation plan
`uv run python tools/check_compat_shims.py` exits 0.

## Completion criteria
The marker-table comment references in `tools/check_compat_shims.py` no longer describe a live detector; checker passes.

## Out of Scope
Changing the checker's logic.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261111-135643 | both comment blocks reworded: LEGACY_MARKER_TABLES detectors named as deleted by adrrev005, fingerprint matching stated as the single mechanism; no logic change |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261111-135643 | uv run python tools/check_compat_shims.py exits 0; pre-commit green |

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
- **Requirement ID**: `REQ-004` — update stale marker-table exception comments
- **Source issue**: issues/20261109-112715_adrrev005_schema-fingerprint-unify.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-095137_adrrev005_schema-fingerprint-unify.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-164906
- **Related target files**: `tools/check_compat_shims.py`