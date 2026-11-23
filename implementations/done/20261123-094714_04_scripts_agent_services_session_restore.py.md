## Goal

Turn `restore_session` into a state builder that constructs the restored state without mutating the context and reports fetched, synthesized, dropped, and restored counts (REQ-002 transactional restore, REQ-009 separate counts; AC-1, AC-5).

## Scope
**Release unit**: N/A: not part of a release unit

Single-file change; the builder result is committed by the transition service (seq 02). Its test row (row 23) has its own procedure document (seq 23).

## Assumptions
- Current code verified: `session_restore.py:155-223` mutates history, undo floor, session id, correlation, and stats in sequence; `n_messages` is the fetched count (comment at 219-222); orphan repair runs before the boundary computation.
- `SessionRestoreResult` counts (seq 05) exist before this row is executed (plan Phase 3 order).

## Design decisions
- `restore_session` keeps its name and error contract (`SessionNotFoundError`, `SessionNoMessagesError`) but returns the built state (restored history, undo floor, counts) instead of writing into the context; the transition service performs the commit (plan Design).
- Existing internal order is preserved: orphan tool_call repair before boundary computation, boundary computed before any state change (already true at 169-186).

## Alternatives considered
- Keeping the mutation and adding compensating undo: rejected — partial mutations during failure are the defect AC-1 targets.

## Implementation
### Target file
`scripts/agent/services/session_restore.py`
### Procedure
1. Remove the `replace_history`, `undo_floor`, session id assignment, `refresh_session_correlation`, and `reset_session_stats` calls from the restore path.
2. Return the built state plus the four counts (`fetched` (new), `synthesized` (new), `dropped` (new), `restored` (new) fields on `SessionRestoreResult`, defined in seq 05).
3. Keep the raises and the boundary/floor computation semantics identical.
### Method
Pure-builder conversion; all context writes move to the seq 02 commit step.
### Details
- `cmd_session.py` currently calls `restore_session` directly (`cmd_session.py:250-269`); until seq 12 rewires it, seq 12 must apply the returned state — coordinate commit order (this row lands with seq 02 in the same plan step, not standalone-deployable).

## Compatibility considerations
- Behavior change for any direct caller during the transition window; the only caller is `cmd_session.py`, a target row (seq 12). Plan consumer scan lists `restore_session` consumers.

## Security considerations
N/A: no new input or logging surface.

## Rollback considerations
N/A: revert the commit together with seq 02 (the builder is only callable through the service after seq 12 rewires commands).

## Validation plan
- `uv run pytest tests/agent/test_session_restore.py tests/agent/services -q` (row 23 document covers the tests).
- `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`.

## Completion criteria
A failed restore leaves history, session id, undo floor, correlation, and stats exactly as they were (the builder never writes them), and the result reports the four counts separately (AC-1, AC-5).

## Out of Scope
`SessionRestoreResult` field definitions (seq 05), commit/rollback (seq 02), test changes (seq 23).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-23 | 2026-11-23 | Land with seq 02/05 pure builder returns RestoredSessionState; no ctx mutation; 4 counts with undo-floor clamp |
| 2 | Add or update tests per Validation plan | Completed | 2026-11-23 | 2026-11-23 | Row 23 has its own document (seq 23) covered by seq 23 tests (41 pass) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-23 | 2026-11-23 | ruff, mypy, lint-imports pass |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-11-23 | 2026-11-23 | Generated docs via seq 18 Docs updated via seq 15-20 (2026-11-23) |

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
- **Requirement ID**: `REQ-002` (non-mutating restore build), `REQ-009` (separate load counts)
- **Source issue**: `issues/20261119-145300_cliplc002_session-transition-generation.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261122-232757_cliplc002_session-transition-generation.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-094714
- **Related target files**: `scripts/agent/services/session_restore.py`