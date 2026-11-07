## Goal

- tests/eventbus/test_eventbus_crash_ack.py — migrate 4 facade import sites by layer (AC-002, REQ-002)

## Scope
**Release unit**: facade-cutover

- The Plan declares one unit covering Phases 1-2: the NACK signature tightening, every import migration, both facade deletions, and the checker patterns land in one commit; any remaining facade import would break suite collection before release (Plan Release unit row, 2026-11-07).

## Assumptions

- All line anchors re-verified 2026-11-07 at HEAD `1a13653e8` (no target-file changes since the Plan freeze at `1b2dded66`).
- Overlap note (compatrm002): 002 edits this file's auth fixture regions; the sites
  listed here are facade-import lines — re-verify line positions after 002 lands.

## Design decisions

- Mechanical import-path rewrite only: zero behavior, assertion, or fixture edits.

## Alternatives considered

- A single multi-file commit without per-file validation: rejected — per-file sibling documents keep each file's grep gate and test run auditable.

## Implementation
### Target file
`tests/eventbus/test_eventbus_crash_ack.py`
### Procedure
1. Apply the mapping above, keeping deferred placement.
2. Change nothing else: crash/ack recovery assertions are unchanged.
### Method
REQ-002 / AC-002. `tests/eventbus/test_eventbus_crash_ack.py` has four facade import
sites:
- line 45: `open_db` → `db_conn`
- lines 120 and 145: `get_consumer_offset` → `delivery_repo`
- line 211: `ack_event_for_consumer, insert_event` → `delivery_repo` + `event_repo`
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

- Command: `grep -c "from eventbus.db import" tests/eventbus/test_eventbus_crash_ack.py`
  Expected: 0.
- Command: `uv run pytest tests/eventbus/test_eventbus_crash_ack.py -q`
  Expected: pass.

## Completion criteria

- every name imported from its owning layer module. (AC-002, REQ-002)

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
- **Related target files**: `tests/eventbus/test_eventbus_crash_ack.py`