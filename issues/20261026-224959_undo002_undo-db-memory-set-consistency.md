# Make /undo delete the same turn set from memory and the session database

## Priority
Medium

## Summary
`/undo` computes the memory cut point and the DB delete range independently, so
when memory and DB contents have diverged (persistence failure, orphaned rows), a
single undo can remove different messages from each side. Derive the memory trim
from the same row set the DB actually deletes.

## Background
From a python-code-review pass over the REPL command path (finding F-007). Re-
verified against current source after earlier undone-boundary work (archived
`issues/done/20261014-154803_undo001_undo-compression-boundary.md` and
`issues/done/20261019-202042_sess001_restore_session-undo_floor-boundary-breaks-when-boundary-computation-fails-or-snapshot-rows-are-dropped.md`,
which fixed DB-first ordering and boundary persistence; the set-consistency gap
remains). Evidence (Strongly implied by code):
- `scripts/agent/services/undo_service.py` finds the last user message by memory
  index, calls `ctx.session.undo_last_turn()` (DB deletes from the last user row
  in the DB onward), then trims memory to the memory-derived index.
- `scripts/agent/session.py` `undo_last_turn` selects rows purely from DB state
  (`message_id >= last_user_id`) and returns its own deleted-row count.
- The two "last user turn" positions coincide only while memory and DB are in sync;
  persistence failures and synthetic/orphaned rows break that assumption.

## Problem
After any memory/DB divergence, `/undo` widens it instead of restoring parity: rows
deleted from the DB may not correspond to the messages trimmed from memory (and the
returned counts — DB `n_removed` vs. memory cut index — already differ in the log).

## Reason for Change
`/undo` is the recovery command users reach for after a broken turn; it must be the
one operation guaranteed to bring the two views back together.

## Implementation Intent
Have the DB side return the identity of the rows it deleted (ids, roles, and
content or `tool_call_id`s — `DeletedRow`-style data), then reconcile memory by
removing exactly those messages (or reloading the affected tail from the DB).
Memory should stop computing its own independent cut index for the deletion step;
the memory search may remain for the boundary gate.

## Target Files or Areas
- `scripts/agent/services/undo_service.py`
- `scripts/agent/session.py` (`undo_last_turn`)
- `scripts/agent/session_message_repo.py` (row-level undo support)
- `scripts/agent/services/models.py` (`UndoResult`)

## Required Changes
- Return the deleted rows (ids + roles) from the DB undo step.
- Trim memory by matching the deleted row set rather than an independently computed
  index.
- Log both sides with the same ids for auditability.
- Regression test: diverged memory/DB state → undo leaves both sides consistent.

## Constraints
- Preserve the compression-boundary gate (`undo_floor_message_id` /
  `ctx.conv.undo_floor`) exactly as implemented.
- Preserve the DB-first ordering (DB delete, then memory trim) established by the
  earlier undo work.
- Keep `UndoResult` backward-compatible or update all callers atomically.

## Acceptance Criteria
- Test with an injected divergence (e.g. extra synthetic tool rows in DB): after
  `/undo`, memory history and `fetch_messages` output describe the same conversation.
- Boundary-gate tests from the earlier undo issues still pass.
- `mypy`/`ruff` pass.

## Testing Expectations
- Regression test constructing a diverged session (DB rows != memory history) →
  undo parity assertion.
- Existing undo/compression-boundary tests unchanged.

## Documentation Impact
State the parity guarantee in the `/undo` docs section (intent + failure behavior:
what undo does when memory and DB already differ).

## Out of Scope
- Preventing the divergence in the first place (atomic persistence and orphan-repair
  issues).
- `/undo` UX changes (counts shown to the user beyond parity logging).

## Dependencies
- `issues/20261026-224643_turn001_atomic-turn-persistence.md` — depends on:
  re-verify this issue after turn001 is resolved; if persistence becomes atomic,
  fewer divergence states remain.

## Unresolved Questions
- Confidence for this finding is Medium (Strongly implied by code): the exact
  divergence frequency in practice depends on the persistence-failure fixes; confirm
  the remaining reachable divergence states after turn001/turn002 land.

## AI Implementation Instruction
Do not redesign the boundary mechanism; reuse the existing row-id based boundary.
Keep DB-first ordering. Drive memory changes from returned DB row data, not from an
independent index walk. If matching by content proves ambiguous, prefer a reload of
the tail rows from the DB over heuristic matching, and report the decision.

## Traceability
- **Workflow phase**: `python-code-review`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261026-224959
- **Related target files**: `scripts/agent/services/undo_service.py`, `scripts/agent/session.py`, `scripts/agent/session_message_repo.py`, `scripts/agent/services/models.py`
