## Goal

- scripts/eventbus/db.py — delete the layer-re-export facade (AC-001, REQ-001)

## Scope
**Release unit**: facade-cutover

- The Plan declares one unit covering Phases 1-2: the NACK signature tightening, every import migration, both facade deletions, and the checker patterns land in one commit; any remaining facade import would break suite collection before release (Plan Release unit row, 2026-11-07).

## Assumptions

- All line anchors re-verified 2026-11-07 at HEAD `1a13653e8` (no target-file changes since the Plan freeze at `1b2dded66`).

## Design decisions

- Delete the file rather than keep a deprecated shim: the Issue and REQ-001 explicitly forbid warnings or aliases.

## Alternatives considered

- Keep a deprecated shim with runtime warnings: rejected — REQ-001 and the Issue forbid deprecation paths.

## Implementation
### Target file
`scripts/eventbus/db.py`
### Procedure
1. Confirm every importer has been migrated (run before deleting):
   ```bash
   grep -rn "from eventbus\.db import\|import eventbus\.db\b\|from eventbus import db\b" scripts/ tests/ tools/
   ```
   Expected at this point: only the not-yet-migrated lines and the checker literals.
2. Land doc 26 so all four import-path patterns are checker-enforced from this commit.
3. Delete the file:
   ```bash
   git rm scripts/eventbus/db.py
   ```
4. Remove the stale bytecode artifact:
   ```bash
   rm -f scripts/eventbus/__pycache__/db.cpython-*.pyc
   ```
5. Do not add any of the 15 names to `scripts/eventbus/__init__.py` (it exports nothing
   today and must stay that way — REQ-001).
### Method
REQ-001 / AC-001. `scripts/eventbus/db.py` (42 lines) re-exports 15 symbols over four
layer modules: connection names from `db_conn` (`check_db`, `get_db_lock`, `open_db`),
event names from `event_repo` (`count_dlq`, `fetch_dlq`, `fetch_events_since`,
`get_seq`, `insert_event`), delivery names from `delivery_repo` (`NackResult`,
`ack_event_for_consumer`, `get_consumer_offset`, `get_resume_position`,
`nack_event`), and `redeliver_event` from `dlq_repo`. It preserves an entry point the
2026-10-27 boundary decision replaced with direct module imports. After docs 04-10,
13-22 and 24 land, nothing imports it; REQ-001 forbids recreating it.
### Details
File deletion plus stale `__pycache__` cleanup; the 15 re-exported names stay available from their owning modules.

## Compatibility considerations

- Sibling document ordering (Plan phase sequence):
  - Depends on: sibling documents 04-10 (all production importers), sibling documents 13-22 and 24 (all test
  importers, plus the companion in doc 06), doc 26 (checker patterns) — the deletion is
  the last step of the cutover and must land in the same commit as them.
  - Blocks: none (sibling documents 12, 27-30 are independent wording updates in Phase 3).
  - Release unit: facade-cutover (Phase 2).

## Security considerations

N/A: import-boundary change.

## Rollback considerations

- Reverting the single facade-cutover commit restores this file with every sibling change together; no persisted state is involved.

## Validation plan

- Command: re-run the step 1 grep after deletion.
  Expected: no matches outside the `tools/check_compat_shims.py` pattern literals.
- Command: `uv run python tools/check_compat_shims.py`
  Expected: clean across `scripts/ tests/ tools/ docs/`.
- Command: `PYTHONPATH=scripts uv run lint-imports`
  Expected: 6 contracts kept — the eventbus isolation contract is package-level.
- Command: `uv run pytest tests/eventbus/ -q`
  Expected: pass.
  recreates any of the 15 names).

## Completion criteria

- AC-001 (file gone, path unused), AC-002 (no package-level re-export (AC-001, REQ-001)

## Out of Scope

- Every other file in the Plan's Implementation Target Files table is covered by a sibling document of this set; see Compatibility considerations for the ordering this document depends on.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete `scripts/eventbus/db.py` — Plan Phase 2 | Completed | 20261107-164122 | 20261107-164122 | facade-cutover unit: suite green only with all unit documents landed |
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
- **Requirement ID**: REQ-001 / AC-001
- **Source issue**: issues/20261106-125144_compatrm003_remove-db-store-and-eventbus-db-facades-and-optional-nack-consumer-id.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261107-063921_compatrm003_remove-db-store-and-eventbus-db-facades-and-optional-nack-consumer-id.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261107-091221
- **Related target files**: `scripts/eventbus/db.py`