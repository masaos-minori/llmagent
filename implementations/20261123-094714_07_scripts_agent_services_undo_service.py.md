## Goal

Make a failed memory reload after the undo DB delete an explicit error instead of a silent divergence (REQ-008 undo reload explicitness; AC-4).

## Scope
**Release unit**: N/A: not part of a release unit

Single-file change; row 26 is covered as this document's companion.

## Assumptions
- Current code verified: `undo_service.py:88-110` calls `ctx.session.undo_last_turn()` first and the later `fetch_messages` path (ambiguous tail match) is unguarded (plan evidence, checked against source).
- The DB rows are already deleted when the reload fails; the requirement is an explicit error, not a compensating restore (plan Assumptions: persisted rows are the recovery source).

## Design decisions
- Define `UndoReloadError` (new) in this module carrying the deleted row count; raise it when the post-delete reload fails so `/undo` cannot leave DB and in-memory history diverged silently (REQ-008).
- The command layer turns it into the recovery-hint message (seq 13), not this module.

## Alternatives considered
- Re-inserting the deleted rows on reload failure: rejected — the plan's recovery path is /session load re-reading the intact persisted rows.

## Implementation
### Target file
`scripts/agent/services/undo_service.py`
### Procedure
1. Wrap the post-delete reload in try/except and raise `UndoReloadError` (new) with the deleted-row count.
2. Keep the existing blocked-by-boundary and no-op paths unchanged.
### Method
Exception wrapping at the existing reload call site; no control-flow change for success paths.
### Details
N/A: none beyond the plan text.

### Companion test files
- `tests/agent/test_undo_db_memory_parity.py`
  - Procedure: extend `TestUndoReloadFallback` (`test_undo_db_memory_parity.py:245`) to assert `UndoReloadError` (new) is raised with the row count when the reload fails after the delete.
  - Validation: `uv run pytest tests/agent/test_undo_db_memory_parity.py -q`.

## Compatibility considerations
- New exception type exported from `agent.services.undo_service`; seq 13 catches it. Existing callers that never saw this path keep working.

## Security considerations
N/A: no new surface; the error message carries a count, not raw SQL details.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_undo_db_memory_parity.py -q`.

## Completion criteria
A failed reload after the DB delete raises `UndoReloadError` (new) and no code path leaves history and DB divergent without reporting it (AC-4).

## Out of Scope
Command message and recovery hint (seq 13), docs (seq 15).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan (companion row 26) | Pending | — | — | Tests written first per plan Phase 5 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Docs via seq 15 |

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
- **Requirement ID**: `REQ-008` (explicit undo reload failure)
- **Source issue**: `issues/20261119-145300_cliplc002_session-transition-generation.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261122-232757_cliplc002_session-transition-generation.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-094714
- **Related target files**: `scripts/agent/services/undo_service.py`, `tests/agent/test_undo_db_memory_parity.py`
