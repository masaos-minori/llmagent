## Goal

- scripts/eventbus/dlq_route.py — import DLQ operations from their repositories (AC-002, REQ-002)

## Scope
**Release unit**: facade-cutover

- The Plan declares one unit covering Phases 1-2: the NACK signature tightening, every import migration, both facade deletions, and the checker patterns land in one commit; any remaining facade import would break suite collection before release (Plan Release unit row, 2026-11-07).

## Assumptions

- All line anchors re-verified 2026-11-07 at HEAD `1a13653e8` (no target-file changes since the Plan freeze at `1b2dded66`).

## Design decisions

- Only the import line moves: `redeliver_event` already matches the call-site usage, so no call-site edits and no aliases.

## Alternatives considered

- A single multi-file commit without per-file validation: rejected — per-file sibling documents keep each file's grep gate and test run auditable.

## Implementation
### Target file
`scripts/eventbus/dlq_route.py`
### Procedure
1. Replace line 11:
   ```python
   from eventbus.event_repo import count_dlq, fetch_dlq
   from eventbus.dlq_repo import redeliver_event
   ```
2. Touch nothing else in the file; call sites and the `run_with_db_lock` helper usage
   stay identical.
### Method
REQ-002 / AC-002. Line 11 imports `count_dlq, fetch_dlq, redeliver_event` from the
`eventbus.db` facade. `count_dlq` and `fetch_dlq` live in `eventbus.event_repo`;
`redeliver_event` lives in `eventbus.dlq_repo` (its signature takes
`conn, event_id, now` — it is not consumer-scoped, so no call-site change is needed).
Call sites: lines 33 (`count_dlq(db)`), 34 (`fetch_dlq(db, ...)`), 65
(`redeliver_event(db, event_id)`) — names are unchanged, so only the import line moves.
### Details
Import lines only; assertions and fixtures unchanged.

## Compatibility considerations

- Sibling document ordering (Plan phase sequence):
  - Depends on: nothing (can land any time in Phase 2 of the `facade-cutover` unit).
  - Blocks: sibling documents 02 (dlq_route is one of the importers that must be migrated before the
  facade is deleted).

## Security considerations

N/A: import-boundary change.

## Rollback considerations

- Reverting the single facade-cutover commit restores this file with every sibling change together; no persisted state is involved.

## Validation plan

- Command: `grep -n "eventbus.db\b" scripts/eventbus/dlq_route.py`
  Expected: no matches.
- Command: `uv run pytest tests/eventbus/test_eventbus_dlq.py tests/eventbus/test_eventbus_dlq_outbox.py -q`
  Expected: pass (with doc 14/16 migrations landed).

## Completion criteria

- dlq_route imports each operation from its owning repository module. (AC-002, REQ-002)

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
- **Related target files**: `scripts/eventbus/dlq_route.py`
