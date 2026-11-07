## Goal

- scripts/eventbus/app.py — import connection operations from db_conn (AC-002, REQ-002)

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
`scripts/eventbus/app.py`
### Procedure
1. Replace line 42:
   ```python
   from eventbus.db_conn import get_db_lock, open_db
   ```
2. Leave every other import and call unchanged.

Companion file (`tests/eventbus/test_eventbus_shutdown.py`) procedure: see Companion test files.
### Method
REQ-002 / AC-002. `scripts/eventbus/app.py` imports the two connection names from the
facade at line 42 (`from eventbus.db import get_db_lock, open_db`). Both live in
`eventbus.db_conn`.
### Details
Import lines only; assertions and fixtures unchanged.

### Companion test files
- `tests/eventbus/test_eventbus_shutdown.py`
  - Procedure: Migrate the module-object import at line 163 to `from eventbus import db_conn as eb_db`
    (keeping the `eb_db` name so the monkeypatch at line 180 only changes its target module;
    `route_helpers.run_with_db_lock` resolves the attribute from `db_conn` at call time) and the
    facade `open_db` imports at lines 311 and 397 to `from eventbus.db_conn import open_db`.
  - Validation: `grep -n "eventbus\.db\b" tests/eventbus/test_eventbus_shutdown.py` returns no matches;
    `uv run pytest tests/eventbus/test_eventbus_shutdown.py -q` passes.

## Compatibility considerations

- Sibling document ordering (Plan phase sequence):
  - Depends on: nothing (Phase 2 of the `facade-cutover` unit; disjoint from
compatrm002's auth edits at lines 26, 84 — re-verify line positions after 002 lands).
  - Blocks: sibling documents 02 (app.py is an importer that must be migrated before the facade is
  deleted).

## Security considerations

N/A: import-boundary change.

## Rollback considerations

- Reverting the single facade-cutover commit restores this file with every sibling change together; no persisted state is involved.

## Validation plan

- Command: `grep -n "eventbus.db\b" scripts/eventbus/app.py`
  Expected: no matches.
- Command: `uv run pytest tests/eventbus/test_eventbus_startup.py tests/eventbus/test_eventbus_shutdown.py -q`
  Expected: pass; the shutdown test's lock monkeypatch still takes effect (proving the
  patch target moved correctly).
- Command: `uv run python -c "import eventbus.app"`
  Expected: import succeeds; `from eventbus import db` is no longer referenced by app code (AC-002).

## Completion criteria

- app startup wiring uses `db_conn` directly and the facade is no longer referenced by app code (AC-002, REQ-002)

## Out of Scope

- Every other file in the Plan's Implementation Target Files table is covered by a sibling document of this set; see Compatibility considerations for the ordering this document depends on.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Migrate `scripts/eventbus/app.py` line 42 and the companion test file — Plan Phase 2 | Completed | 20261107-164122 | 20261107-164122 | facade-cutover unit: suite green only with all unit documents landed |
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
- **Related target files**: `scripts/eventbus/app.py`, `tests/eventbus/test_eventbus_shutdown.py`