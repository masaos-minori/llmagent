## Goal

- scripts/eventbus/route_helpers.py — import get_db_lock from db_conn (AC-002, REQ-002)

## Scope
**Release unit**: facade-cutover

- The Plan declares one unit covering Phases 1-2: the NACK signature tightening, every import migration, both facade deletions, and the checker patterns land in one commit; any remaining facade import would break suite collection before release (Plan Release unit row, 2026-11-07).

## Assumptions

- All line anchors re-verified 2026-11-07 at HEAD `1a13653e8` (no target-file changes since the Plan freeze at `1b2dded66`).

## Design decisions

- Keep the deferred-import placement (PLC0415 discipline); after the move, monkeypatches target the `db_conn` module attribute that `run_with_db_lock` resolves at call time.

## Alternatives considered

- A single multi-file commit without per-file validation: rejected — per-file sibling documents keep each file's grep gate and test run auditable.

## Implementation
### Target file
`scripts/eventbus/route_helpers.py`
### Procedure
1. Replace line 133 with `from eventbus.db_conn import get_db_lock` keeping its
   `# noqa: PLC0415` marker:
   ```python
   from eventbus.db_conn import get_db_lock
   ```
   (or merge `get_db_lock` into the existing `eventbus.db_conn` deferred import block at
   lines 134-138 — either form; keep the `# noqa: PLC0415` marker.)
2. Change nothing else: lines 134-138, `_locked()`, and line 147 stay as-is.
### Method
REQ-002 / AC-002. `run_with_db_lock()` carries a deferred facade import at line 133
(`from eventbus.db import get_db_lock  # noqa: PLC0415`), immediately before an existing
deferred import block from `eventbus.db_conn` (lines 134-138). The lock usage at line
147 (`with get_db_lock():`) stays unchanged. After the move, tests that monkeypatch
`get_db_lock` patch the `eventbus.db_conn` module attribute, which `run_with_db_lock`
resolves at call time (docs 06 companion and 24).
### Details
Import lines only; assertions and fixtures unchanged.

## Compatibility considerations

- Sibling document ordering (Plan phase sequence):
  - Depends on: nothing (Phase 2 of the `facade-cutover` unit).
  - Blocks: sibling documents 02 (an importer that must be migrated before the facade is deleted), and
  the monkeypatch targets in the companion of doc 06 and in doc 24 (this is where the
  patched attribute resolves from).

## Security considerations

N/A: import-boundary change.

## Rollback considerations

- Reverting the single facade-cutover commit restores this file with every sibling change together; no persisted state is involved.

## Validation plan

- Command: `grep -n "eventbus.db\b" scripts/eventbus/route_helpers.py`
  Expected: no matches.
- Command: `uv run pytest tests/eventbus/test_eventbus_route_helpers_metrics.py -q`
  Expected: pass after doc 24 lands (its monkeypatch target moves with this change).

## Completion criteria

- the only `get_db_lock` import in route_helpers is from `db_conn`. (AC-002, REQ-002)

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
- **Related target files**: `scripts/eventbus/route_helpers.py`
