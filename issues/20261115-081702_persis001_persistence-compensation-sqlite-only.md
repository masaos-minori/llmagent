# Turn persistence compensation only fires on `sqlite3.Error`, leaving partial turns on other exceptions

## Priority
Medium

## Summary
`TurnPersistence` compensates a failed turn (deletes partial DB rows, restores the
turn-start memory snapshot) only when the underlying repository write raises
`sqlite3.Error`. Any other exception type raised inside a turn propagates without
compensation, so a turn that already committed some writes leaves partial rows in the
session DB while conversation memory rolls back. Extend the compensation trigger so a
non-`sqlite3.Error` exception after a successful save is compensated the same way.

## Background
`scripts/agent/turn_persistence.py` implements the turn-persistence boundary that makes
one agent turn's session-DB persistence all-or-nothing (AC-001). Every turn write is
delegated to `AgentSession._message_repo` on a worker thread. Each public write method
(`save`, `save_many`, `save_phase_grouped`, `replace_messages`) wraps the worker call in
`try/except sqlite3.Error` and routes to `_fail_from_error`, which calls `_compensate`
(delete-above-marker or restore-pre-rewrite-image), restores `conv.history` to the
turn-start snapshot, and raises `ConversationPersistenceError`.

`orchestrator._execute_turn` (`scripts/agent/orchestrator.py`) distinguishes two cases on
failure: a caught `ConversationPersistenceError` (which knows compensation already ran) and
a generic `except BaseException` that only records `error_kind`/`is_partial` and re-raises.
The generic branch never calls compensation.

## Problem
The compensation trigger is scoped to `sqlite3.Error` alone. When a turn raises any other
exception after at least one write already committed successfully, neither
`TurnPersistence` nor `orchestrator._execute_turn` compensates:

- The committed rows remain in the session DB (append-only rows past the turn marker are
  never deleted).
- `conv.history` is restored to the turn-start snapshot in memory.
- The result is a permanent divergence: the persisted DB contains the partial turn while
  the in-memory conversation does not. On the next load, the turn is reconstructed from DB
  rows that memory has forgotten.

Evidence: `turn_persistence.py` methods catch only `sqlite3.Error` (lines for
`save`/`save_many`/`save_phase_grouped`/`replace_messages`); `_fail_from_error` is the sole
compensation entry point and is only reached from those handlers. `orchestrator.py`
`_execute_turn` catches `ConversationPersistenceError` and then `BaseException` with no
compensation call.

## Reason for Change
The all-or-nothing contract documented at the top of `turn_persistence.py` ("a whole turn
is either fully persisted or fully compensated") is violated for every non-`sqlite3.Error`
failure after a partial commit. Such exceptions are plausible: a worker-thread write can
succeed and a later phase in the same turn raise `RuntimeError`/`ValueError`, or an
`asyncio.CancelledError` can land after a commit. No production occurrence is known yet, so
this is preventive, but the divergence is silent and accumulates across turns.

## Implementation Intent
Make compensation independent of the exception type once a write has committed. At the
responsibility level: a turn that has persisted at least one row must guarantee that a
later in-turn exception either completes the turn's persistence or compensates it — never
leave half of it. Decide at the boundary whether (a) broaden the `except` in each
`TurnPersistence` write method to also catch and compensate non-`sqlite3.Error` exceptions,
or (b) centralize the decision in `orchestrator._execute_turn` so any post-commit exception
routes through the same compensation path as `ConversationPersistenceError`. Preserve the
distinction that `ConversationPersistenceError` means "nothing persisted" (`is_partial=False`)
while a mid-turn exception may have committed rows (`is_partial=True`). Do not change the
transactional guarantees of the repository writes themselves.

## Target Files or Areas
`scripts/agent/turn_persistence.py`, `scripts/agent/orchestrator.py`

## Required Changes
- Ensure a non-`sqlite3.Error` exception raised after a successful in-turn write triggers
  the same compensation as `sqlite3.Error` (delete-above-marker or restore-pre-rewrite-image
  plus memory snapshot restore), so no partial turn survives.
- Preserve the `ConversationPersistenceError` semantics: it still means nothing was
  persisted (`is_partial=False`), while a mid-turn exception that committed rows is recorded
  as partial (`is_partial=True`).
- Keep `BaseException`/`CancelledError` propagation semantics intact (AC-5): propagation must
  still escape `execute_all_tool_calls` and `orchestrator`; only the persistence side effect
  changes.
- Add unit tests covering a non-`sqlite3.Error` exception after a partial commit and confirm
  the DB is left without the partial turn's rows.

## Constraints
- Do not alter the repository's own transactional behavior (`save_phase_grouped` single
  transaction, append-only compensation delete above the marker).
- Do not widen compensation to fire on exceptions raised before any write committed; those
  leave nothing to compensate and must keep propagating unchanged.
- Do not change the disabled-by-default guard policies or unrelated tool-execution paths.
- Compensation must run on a worker thread like the writes (single-connection invariant).

## Acceptance Criteria
- A turn that commits at least one row then raises a non-`sqlite3.Error` exception is
  compensated: no rows above the turn-start marker remain in the session DB.
- `conv.history` is restored to the turn-start snapshot on that failure path.
- The exception still propagates end-to-end (observable by callers).
- Existing `sqlite3.Error` compensation behavior and the `ConversationPersistenceError`
  `is_partial=False` contract are unchanged.
- `ruff`, `mypy`, and the affected test trees pass.

## Testing Expectations
Unit tests in `tests/agent/test_turn_persistence.py`: simulate a successful write followed by
a `RuntimeError`/`ValueError`/`CancelledError` and assert the partial rows are deleted and the
memory snapshot is restored. Regression tests confirm the current `sqlite3.Error` path is
unchanged. Run `uv run ruff check` and `uv run mypy --no-namespace-packages` on the two
touched files, plus `uv run pytest` on the persistence and orchestrator test trees.

## Documentation Impact
Update the failure-behavior description in turn-persistence documentation if it currently
states compensation is limited to SQLite errors; restate it as applying to any in-turn
exception after a partial commit. Do not add implementation-level details forbidden by
`skills/DESIGN.md` "Docs content policy — remove".

## Out of Scope
- Changes to repository write transactions, connection handling, or the append-only
  compensation-delete mechanics.
- Any change to tool-execution gating, approval, or loop-detection logic.
- Broadening compensation to startup or recovery paths outside a running turn.

## Dependencies
`N/A: none`

## Unresolved Questions
- Which exception types actually reach the turn after a partial commit in practice? Confirm
  the realistic trigger set (e.g. `RuntimeError`, `ValueError`, `CancelledError`) before
  choosing the broadest safe handler. 不明
- Should compensation for a mid-turn exception attempt to complete the turn's remaining
  writes first, or always roll back? 不明

## AI Implementation Instruction
Only edit `turn_persistence.py` and `orchestrator.py`. First confirm no existing code
path already compensates non-`sqlite3.Error` exceptions (grep for other callers of
`_compensate`/`_fail_from_error`). Decide between broadening the per-method `except` in
`TurnPersistence` versus centralizing in `orchestrator._execute_turn`, and apply exactly one.
Preserve `CancelledError`/`BaseException` propagation (AC-5) and the
`ConversationPersistenceError` `is_partial=False` contract. Add targeted unit tests for the
partial-commit-then-non-SQLite-exception case. Do not touch tool-execution, approval, or
loop-guard code. Stop and report if the realistic exception trigger set cannot be confirmed
from the current source.

## Traceability
- **Workflow phase**: python-code-review → issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261115-081702
- **Related target files**: scripts/agent/turn_persistence.py, scripts/agent/orchestrator.py
