## Goal

- tests/eventbus/test_eventbus_concurrent.py — migrate the facade open_db import (AC-002, REQ-002)

## Scope
**Release unit**: facade-cutover

- The Plan declares one unit covering Phases 1-2: the NACK signature tightening, every import migration, both facade deletions, and the checker patterns land in one commit; any remaining facade import would break suite collection before release (Plan Release unit row, 2026-11-07).

## Assumptions

- All line anchors re-verified 2026-11-07 at HEAD `1a13653e8` (no target-file changes since the Plan freeze at `1b2dded66`).

## Design decisions

- Mechanical import-path rewrite only: zero behavior, assertion, or fixture edits.

## Alternatives considered

- A single multi-file commit without per-file validation: rejected — per-file sibling documents keep each file's grep gate and test run auditable.

## Implementation
### Target file
`tests/eventbus/test_eventbus_concurrent.py`
### Procedure
1. Replace the import at line 74 with:
   ```python
   from eventbus.db_conn import open_db
   ```
2. Change nothing else.
### Method
REQ-002 / AC-002. `tests/eventbus/test_eventbus_concurrent.py` has one facade import:
line 74 imports `open_db`, which lives in `eventbus.db_conn`.
### Details
Import lines only; assertions and fixtures unchanged.

## Compatibility considerations

- Sibling document ordering (Plan phase sequence):
  - Depends on: nothing (Phase 2 of the `facade-cutover` unit).
  - Blocks: sibling documents 02, 26.

## Security considerations

N/A: import-boundary change.

## Rollback considerations

- Reverting the single facade-cutover commit restores this file with every sibling change together; no persisted state is involved.

## Validation plan

- Command: `grep -c "from eventbus.db import" tests/eventbus/test_eventbus_concurrent.py`
  Expected: 0.
- Command: `uv run pytest tests/eventbus/test_eventbus_concurrent.py -q`
  Expected: pass.

## Completion criteria

- no facade import remains. (AC-002, REQ-002)

## Out of Scope

- Every other file in the Plan's Implementation Target Files table is covered by a sibling document of this set; see Compatibility considerations for the ordering this document depends on.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Migrate facade imports in this file — Plan Phase 2 | Completed | 20261107-164122 | 20261107-164122 | facade-cutover unit: suite green only with all unit documents landed |
| 2 | Run this document's Validation plan commands | Completed | 20261107-164122 | 20261107-164122 |  |
| 3 | Full validation sequence (`rules/toolchain.md`) in the Plan Phase 4 pass | Completed | 20261107-164122 | 20261107-164122 |  |

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
- **Requirement ID**: REQ-002 / AC-002
- **Source issue**: issues/20261106-125144_compatrm003_remove-db-store-and-eventbus-db-facades-and-optional-nack-consumer-id.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261107-063921_compatrm003_remove-db-store-and-eventbus-db-facades-and-optional-nack-consumer-id.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261107-091221
- **Related target files**: `tests/eventbus/test_eventbus_concurrent.py`