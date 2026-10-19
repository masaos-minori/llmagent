# restore_session undo_floor boundary breaks when boundary computation fails or snapshot rows are dropped

## Priority
Medium

## Summary
Make `restore_session` compute the `/undo` compression boundary (`ctx.conv.undo_floor`) correctly and safely: it must not silently become 0 (fully undoable) when the boundary computation raises, and it must stay aligned with the in-memory rebuilt history when `replace_history` drops snapshot rows during untrusted sanitization.

## Background
On `/session load`, `restore_session` rebuilds the in-memory conversation history from the persisted DB rows and re-derives the `/undo` boundary. After a history compression, the compressed snapshot must NOT be undoable; only turns appended after the snapshot are. The boundary is persisted as `sessions.undo_floor_message_id` and converted back to an in-memory history index on restore via `_boundary_to_index`, using `count_messages_up_to` for the snapshot count.

## Problem
Two independent defects break the `/undo` semantics on the restore path:

1. Failure path: `restore_session` switches `ctx.session.session_id` and calls `reset_session_stats` BEFORE computing the boundary. If `count_messages_up_to` raises (DB error), the exception propagates but the session is already switched and `undo_floor` is left at the `ConversationState` default of 0. An `undo_floor` of 0 means every turn is undoable, so the previously non-undoable compressed snapshot becomes undoable after a transient DB error.
2. Index drift: `_boundary_to_index` indexes the rebuilt history using the pre-sanitization `messages` list. `replace_history` validates every restored row as untrusted (`_UNTRUSTED_RESTORE_SOURCE`) and drops any row whose role/content is stripped. If a snapshot row is dropped, the computed index no longer matches the actual rebuilt-history length, silently misaligning `/undo`.

Reproduced the failure path directly: after `count_messages_up_to` raised, `ctx.session.session_id` had already changed and `ctx.conv.undo_floor` was 0.

## Reason for Change
The `/undo` boundary is a data-integrity guarantee: users rely on it to undo only their own recent turns, never the compressed snapshot. A silent `undo_floor=0` after a recoverable DB error lets `/undo` delete the compressed snapshot, which cannot be rebuilt. The current tests mock `count_messages_up_to` and never exercise the raise path or a dropped snapshot row, so neither defect is covered.

## Implementation Intent
Compute the `/undo` boundary BEFORE mutating any session state (before switching `session_id` and before `reset_session_stats`). If the boundary computation fails, surface the error without leaving the session half-restored with `undo_floor=0`. For the index-drift case, derive the boundary index from the actual post-sanitization rebuilt history rather than the pre-sanitization row count, so the floor always matches the live `ctx.conv.history`. Keep the existing `_boundary_to_index` system-prompt adjustment; only anchor it to the messages that actually made it into memory.

## Target Files or Areas
- `scripts/agent/services/session_restore.py` (`restore_session`, `_boundary_to_index`)
- `scripts/agent/context.py` (`replace_history`)
- `tests/agent/test_session_restore.py`

## Required Changes
- Reorder `restore_session` so the boundary is computed and assigned to `ctx.conv.undo_floor` before `ctx.session.session_id` is reassigned and before `reset_session_stats` runs.
- On a raised boundary computation, do not leave `undo_floor` at the fully-undoable default; either propagate before any state mutation or set a safe non-zero boundary consistent with "nothing in the compressed snapshot is undoable".
- Make the boundary index robust to dropped rows: compute it from the messages that survive `replace_history`, not from the raw fetched count alone.
- Add tests: (a) `count_messages_up_to` raises during restore of a compressed session and asserts the session is not left with `undo_floor == 0`; (b) a snapshot row that fails validation and is dropped does not shift the resulting `undo_floor` past the true boundary.

## Constraints
- Preserve the invariant that a compressed snapshot is never undoable after a successful restore.
- Do not change the persisted `sessions.undo_floor_message_id` semantics or the compression path that writes it.
- Keep `restore_session` raising `SessionNotFoundError` / `SessionNoMessagesError` for their existing conditions.

## Acceptance Criteria
- Restoring a compressed session where the boundary computation fails leaves the session in a consistent state with `undo_floor != 0` (or the error propagates before any state change).
- Restoring a session where a snapshot row is dropped yields an `undo_floor` that correctly indexes the rebuilt (post-sanitization) history.
- Existing `test_session_restore.py` cases still pass unchanged.

## Testing Expectations
- New unit tests in `tests/agent/test_session_restore.py` covering both the failure path and the dropped-row path.
- Full `pytest tests/agent/test_session_restore.py` passes; `ruff` and `mypy` clean on touched files.

## Documentation Impact
None required. The behavior is covered by code and tests; no design intent changes.

## Out of Scope
- Changes to the compression path that persists `undo_floor_message_id`.
- Changes to `undo_last_turn` deletion logic.
- Any change to how `replace_history` sanitizes restored rows (validation policy is out of scope here).

## Dependencies
- N/A: none

## Unresolved Questions
- When the boundary computation fails, should the restore be rolled back entirely (restore the previous `session_id`), or is a safe non-zero `undo_floor` sufficient? Confirm the intended failure contract before implementing.

## AI Implementation Instruction
Do not touch the compression/persistence path or the validation policy. Only reorder `restore_session` to compute the boundary before mutating session state, make the boundary index match the rebuilt history, and add the two failing-path tests. Keep the change minimal and preserve all existing exceptions and assertions.

## Traceability
- **Workflow phase**: `python-code-review` + `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261019-202042
- **Related target files**: `scripts/agent/services/session_restore.py`, `scripts/agent/context.py`, `tests/agent/test_session_restore.py`
