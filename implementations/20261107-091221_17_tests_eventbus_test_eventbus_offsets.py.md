## Goal

- tests/eventbus/test_eventbus_offsets.py — migrate 7 facade import sites by layer (AC-002, REQ-002)

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
`tests/eventbus/test_eventbus_offsets.py`
### Procedure
1. Split each facade import into per-module imports:
   ```python
   from eventbus.delivery_repo import ack_event_for_consumer
   from eventbus.delivery_repo import get_consumer_offset
   from eventbus.event_repo import insert_event
   from eventbus.db_conn import open_db
   ```
   keeping the deferred (in-function) placement and the existing `# noqa: PLC0415`
   markers on the two multi-line blocks.
2. Change nothing else: offset assertions and fixtures are unchanged.
### Method
REQ-002 / AC-002. Seven facade import sites mix three layers:
- lines 122-124: deferred block `ack_event_for_consumer, insert_event`
- lines 176, 195: `get_consumer_offset`
- lines 225-227: deferred block `ack_event_for_consumer, insert_event`
- line 267: `get_consumer_offset, open_db`
- lines 276 and 307: `ack_event_for_consumer, get_consumer_offset, open_db`

Mapping: `ack_event_for_consumer` and `get_consumer_offset` → `delivery_repo`;
`insert_event` → `event_repo`; `open_db` → `db_conn`.
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

- Command: `grep -c "from eventbus.db import" tests/eventbus/test_eventbus_offsets.py`
  Expected: 0.
- Command: `uv run pytest tests/eventbus/test_eventbus_offsets.py -q`
  Expected: pass.

## Completion criteria

- every name imported from its owning layer module. (AC-002, REQ-002)

## Out of Scope

- Every other file in the Plan's Implementation Target Files table is covered by a sibling document of this set; see Compatibility considerations for the ordering this document depends on.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Migrate facade imports in this file — Plan Phase 2 | Pending | — | — | facade-cutover unit: suite green only with all unit documents landed |
| 2 | Run this document's Validation plan commands | Pending | — | — | |
| 3 | Full validation sequence (`rules/toolchain.md`) in the Plan Phase 4 pass | Pending | — | — | |

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
- **Related target files**: `tests/eventbus/test_eventbus_offsets.py`
