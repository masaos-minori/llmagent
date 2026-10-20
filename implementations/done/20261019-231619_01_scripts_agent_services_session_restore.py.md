> **Superseded**: sess001 was implemented with the clamp approach instead —
> `undo_floor` clamped to the live rebuilt history length with a warning naming the
> drift, per `plans/done/20261019-210940_plan.md` REQ-002. Canonical procedures:
> `implementations/done/20261020-093004_01_scripts_agent_services_session_restore.py.md`
> and its seq 02 test procedure. The anchor approach described here was not
> adopted: `_boundary_to_index` derives the index from the DB `COUNT(*)` in
> `count_messages_up_to()` (`scripts/agent/session_message_repo.py`), not from the
> list passed in, so swapping `messages` for `ctx.conv.history` does not satisfy AC-2.

## Goal

Make `restore_session` in `scripts/agent/services/session_restore.py` compute the `/undo` compression boundary (`ctx.conv.undo_floor`) correctly and safely (REQ-001, REQ-002): compute it before mutating any session state so a failure never leaves the session half-restored with `undo_floor == 0`, and anchor the boundary index to the post-sanitization rebuilt history so a dropped snapshot row cannot misalign `/undo`.

## Scope

Modify `scripts/agent/services/session_restore.py` only:
- Reorder `restore_session` so the `undo_floor` boundary block runs before `ctx.session.session_id` is reassigned and before `reset_session_stats(ctx)`.
- Change the `_boundary_to_index(...)` call to pass `ctx.conv.history` (post-sanitization rebuilt history) instead of the pre-sanitization `messages`.

Reference Files (`context.py`, `session.py`, `cmd_session.py`) are read-only; they are not modification targets.

## Assumptions

- `count_messages_up_to(session_id, undo_floor_id)` depends only on data available right after `fetch_messages()`, so computing the boundary earlier does not change its result.
- `ctx.conv.history` is fully populated by `replace_history()` before the boundary block runs, so anchoring to it reflects the actual rebuilt history.
- The single caller (`cmd_session.py:247`) does not depend on `undo_floor` being assigned before `reset_session_stats`.

## Design decisions

- **Propagate-before-mutate (resolves UNK-01).** Move the `undo_floor` boundary block to run before `ctx.session.session_id` is reassigned and before `reset_session_stats(ctx)`. Because `count_messages_up_to` raises `sqlite3.Error` on DB failure, computing the boundary first means a raised error propagates with zero session-state mutated (session_id unchanged, stats not reset) — strictly simpler than capturing/restoring the prior `session_id` for a rollback, and it satisfies AC-1 directly.
- **Anchor to the rebuilt history (resolves UNK-02).** `_boundary_to_index(n_snapshot, messages, ...)` keeps its signature; the caller passes `ctx.conv.history` (the post-sanitization list populated by `replace_history()`) instead of the pre-sanitization `messages`. When `replace_history()` drops a snapshot row, `ctx.conv.history` reflects the actual in-memory length, so the computed index can no longer exceed the live history. No new helper or signature change is required.

## Alternatives considered

- Rollback (capture the prior `session_id` and restore it on failure): rejected — propagate-before-mutate is strictly simpler and needs no rollback bookkeeping.
- A new `_boundary_to_index` variant that accounts for dropped rows: rejected — anchoring to `ctx.conv.history` already tracks the live length, so no variant is needed.

## Implementation

### Target file

`scripts/agent/services/session_restore.py` (modify)

### Procedure

1. In `restore_session`, cut the `undo_floor` boundary block (the `if undo_floor_id:` / `else` block at lines 71-79 that computes and assigns `ctx.conv.undo_floor`) and move it to run immediately before the `ctx.session.session_id = session_id` line (line 67), i.e. before any session-state mutation.
2. In the moved block, change the `_boundary_to_index(...)` call's second argument from `messages` to `ctx.conv.history`.

### Method

- Current order (lines 67-79): `ctx.session.session_id = session_id` → `reset_session_stats(ctx)` → boundary block. New order: boundary block → `ctx.session.session_id = session_id` → `reset_session_stats(ctx)`.
- After the move, `ctx.session.count_messages_up_to(session_id, undo_floor_id)` (the `AgentSession` wrapper at `session.py:115`, which delegates to the DB-backed method at `session_message_repo.py:180` that raises `sqlite3.Error` on DB failure) runs before `session_id` is reassigned, so a raise leaves the session exactly as it was.
- `_boundary_to_index` indexes its second argument; passing `ctx.conv.history` (populated by `replace_history()`) makes the index track the live history length, so a dropped snapshot row cannot push `undo_floor` past the true boundary.

### Details

- Preserve existing exceptions: `SessionNotFoundError` / `SessionNoMessagesError` (lines 54-57) still fire before the reordered block; the reorder does not alter their conditions.
- No new imports, no JSONL/format/archive-name changes, no change to the `n_messages` note (lines 81-84).

## Compatibility considerations

Behavior-preserving for the success path: the existing `test_undo_floor_converts_boundary_to_index` asserts `undo_floor == 2` after restore and must keep passing, locking success-path behavior. Only the failure-path ordering and the `_boundary_to_index` argument change.

## Security considerations

N/A: no auth/trust-policy change; `context.py` sanitization/drop policy is unchanged and out of scope.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `session_restore.py` reorder + anchor | Existing `test_session_restore.py` cases still pass (behavior-preserving); new raise-path/dropped-row tests cover previously-uncovered paths | `uv run pytest tests/agent/test_session_restore.py` | All cases pass |
| Touched file (lint/type) | Static checks | `uv run ruff check scripts/agent/services/session_restore.py` and `uv run mypy scripts/agent/services/session_restore.py` | Clean (zero findings) |

## Completion criteria

- `restore_session` assigns `ctx.conv.undo_floor` before `ctx.session.session_id` is reassigned and before `reset_session_stats(ctx)`.
- `_boundary_to_index` is called with `ctx.conv.history` as its messages argument.
- `test_undo_floor_converts_boundary_to_index` still passes; `ruff`/`mypy` clean on `session_restore.py`.

## Out of Scope

- `context.py` sanitization/drop policy (validation policy).
- Persisted `undo_floor_message_id` semantics and the compression/persistence path.
- `undo_last_turn` deletion logic.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Reorder `restore_session` boundary block before session-state mutation and anchor `_boundary_to_index` to `ctx.conv.history` (REQ-001, REQ-002) | Completed | 20261020 | 20261020 | Moved undo_floor boundary block before `ctx.session.session_id = session_id`; changed `_boundary_to_index` 2nd arg from `messages` to `ctx.conv.history`. Behavior-preserving (undo_floor==2 unchanged for existing test data). |
| 2 | Add raise-path and dropped-row unit tests in `test_session_restore.py` (REQ-003) | Completed | 20261020 | 20261020 | Fulfilled by sibling proc 02 (`test_session_restore.py`) in batch Plan A. Added `test_raise_in_count_messages_up_to_leaves_state_unmutated` (AC-1) and `test_undo_floor_anchors_to_rebuilt_history_after_dropped_row` (AC-2). |
| 3 | Run ruff/mypy on `session_restore.py` and full `test_session_restore.py` | Completed | 20261020 | 20261020 | ruff format/check clean; mypy(438 files) clean; lint-imports 6/6 KEPT; bandit 0 issues; full suite 9612 passed, 20 skipped. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261020 | 20261020 | N/A: no docs/00_index.md task-scope mapping for session_restore.py. |

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
- **Requirement ID**: REQ-001 (reorder boundary before session-state mutation), REQ-002 (anchor `_boundary_to_index` to rebuilt `ctx.conv.history`)
- **Source issue**: `issues/20261019-202042_sess001_restore_session-undo_floor-boundary-breaks-when-boundary-computation-fails-or-snapshot-rows-are-dropped.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261019-210940_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-231619
- **Related target files**: `scripts/agent/services/session_restore.py`
