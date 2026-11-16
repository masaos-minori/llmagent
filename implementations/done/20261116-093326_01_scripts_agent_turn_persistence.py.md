## Goal

Expose a committed-state signal and a rollback entry point on `TurnPersistence` so an
unhandled non-`sqlite3.Error` exception that escapes a turn after at least one write
committed triggers the same all-or-nothing compensation as `sqlite3.Error` (`REQ-001`,
`REQ-004`, `REQ-006`).

## Scope
**Release unit**: N/A: not part of a release unit

Code change to `scripts/agent/turn_persistence.py` only. The orchestrator half lives in
`scripts/agent/orchestrator.py` (sibling document).

## Assumptions

- Each write method's `try/except sqlite3.Error` reaches its normal end only on success,
  because `_fail_from_error` is typed `NoReturn` and always raises; therefore a line after
  the `try/except` runs only when the worker-thread write committed.
- A committed write means the append-only rows above the turn-start marker now exist and
  must be deleted on a later in-turn failure (the contract at the top of the module).

## Design decisions

- **Where compensation is decided: centralized in the orchestrator (plan Design approach
  (b)), not per-method broadening.** A compensable exception can occur outside every write
  method's `try` (tool execution, compression, cancellation), so per-method broadening
  alone cannot satisfy `REQ-001`. The orchestrator already holds the `TurnPersistence`
  `boundary` reference (`_execute_turn` line 173), so it can read the committed-state signal
  and roll back. Approach (a) (broadening the per-method `except`) is optional and only
  closes the rare in-write-call gap; it is not required.
- The committed-state signal is a single boolean flag set after a successful worker-thread
  write and gated by `rollback_partial_turn` (new), so compensation never fires before any write
  commits (`REQ-004`).

## Alternatives considered

- Broadening the per-method `except sqlite3.Error` to `except Exception`: rejected as
  insufficient on its own because it cannot see post-write exceptions raised elsewhere in
  the turn; kept only as an optional supplement.
- Centralizing without a signal (e.g. always compensating on any `BaseException`): rejected
  because it would roll back turns that persisted nothing, violating `REQ-004`.

## Implementation
### Target file
`scripts/agent/turn_persistence.py`

### Procedure
1. Add a committed-state flag to `TurnPersistence` (initialized `False`).
2. Set the flag to `True` at the end of each of the four write methods
   (`save`, `save_many`, `save_phase_grouped`, `replace_messages`) — i.e. after the
   existing `try/except sqlite3.Error`, which is reached only on success.
3. Add a public `async def rollback_partial_turn(self) -> bool` that, when the flag is
   `True`, runs `_compensate()` then restores `conv.history` to the turn-start snapshot and
   resets `undo_floor`; when the flag is `False` it returns without effect.

### Method
- In `__init__`, add `self._write_committed = False` alongside `self._pre_rewrite_image`.
- In `save` (after line 108's `except` block), `save_many`, `save_phase_grouped`, and
  `replace_messages`, insert `self._write_committed = True` as the last statement of the
  method body. Because `_fail_from_error` always raises, this line executes only after a
  committed write; do not place it inside the `try`.
- Add `rollback_partial_turn` (new) after `_fail_from_error`:
  ```python
  async def rollback_partial_turn(self) -> bool:
      \"\"\"Compensate a partial turn after a non-persistence exception escaped.

      Returns True if compensation ran (a write had committed), False otherwise
      (REQ-004). Mirrors the finally of _fail_from_error: _compensate() then
      restore_messages + undo_floor reset. Compensation runs on a worker thread
      like the writes (REQ-006).
      \"\"\"
      if not self._write_committed:
          return False
      try:
          await self._compensate()
      except sqlite3.Error as comp_exc:
          logger.error(
              "Turn compensation failed after unhandled exception: %s", comp_exc
          )
      finally:
          await self.conv.restore_messages(self._snapshot)
          self.conv.undo_floor = self._undo_floor_at_turn_start
      return True
  ```
  Reuse `_compensate` (already offloaded to a worker thread) and the same memory-restore
  pattern as `_fail_from_error` so the delete-above-marker and pre-rewrite-image paths are
  identical to the `sqlite3.Error` path.

### Details
- Do not change `_fail_from_error`, `_compensate`, or the `sqlite3.Error` handlers
  (`REQ-005`): the `sqlite3.Error` path and the `ConversationPersistenceError`
  `is_partial=False` contract are unchanged.
- Keep compensation on the worker thread via `_compensate`; `restore_messages` runs on the
  calling (event-loop) thread exactly as `_fail_from_error` does today, preserving the
  single-connection invariant.
- Optional supplement (approach (a)): if desired, widen the four `except sqlite3.Error` to
  also catch a narrow in-write-call non-`sqlite3.Error`, but only after confirming it does
  not swallow exceptions that should propagate before a commit. Not required for `REQ-001`.

### Companion test files
- `tests/agent/test_turn_persistence.py` (existing)
  - Procedure: add a test that calls each write method, then raises a non-`sqlite3.Error`
    (`RuntimeError`) from a later write, asserting `_compensate` deletes the partial rows,
    `conv.history` is restored, and `rollback_partial_turn` (new) returns `True`; add a test that
    a non-`sqlite3.Error` raised before any write commits leaves no rows deleted and returns
    `False` (`REQ-001`, `REQ-004`).
  - Validation: `uv run pytest tests/agent/test_turn_persistence.py` — new cases pass and the
    existing `sqlite3.Error` regression is unchanged (`REQ-005`).

## Compatibility considerations

- The new flag and method are additive; no existing symbol, signature, or behavior changes.
- `rollback_partial_turn` (new) is a new public method; the orchestrator sibling calls it only in
  its `BaseException` branch.

## Security considerations

N/A: no authentication, authorization, or input-handling change.

## Rollback considerations

Revert the two commits (turn_persistence.py, orchestrator.py); the flag and method are
new and touch no persisted data shape.

## Validation plan

- `uv run pytest tests/agent/test_turn_persistence.py` — new non-`sqlite3.Error` after
  partial-commit test asserts partial rows deleted and memory restored; existing
  `sqlite3.Error` regression passes.
- `uv run ruff check scripts/agent/turn_persistence.py`; `uv run mypy --no-namespace-packages scripts/agent/turn_persistence.py` — clean.

## Completion criteria

- A non-`sqlite3.Error` exception after a committed write triggers `_compensate` and memory
  restore; before any write commits, `rollback_partial_turn` (new) is a no-op (`REQ-001`,
  `REQ-004`).
- Compensation runs on a worker thread (`REQ-006`); the `sqlite3.Error` path and
  `is_partial=False` contract are unchanged (`REQ-005`).

## Out of Scope

- Orchestrator routing (sibling document).
- Changing repository write transactions, append-only mechanics, or connection handling.
- Broadening compensation to startup/recovery paths outside a running turn.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-16 | 2026-11-16 | Added _write_committed flag + rollback_partial_turn to turn_persistence.py |
| 2 | Add or update tests per Validation plan | Completed | 2026-11-16 | 2026-11-16 | Added TestRollbackPartialTurn (2 cases) to test_turn_persistence.py |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-16 | 2026-11-16 | pytest 152 passed; ruff + mypy clean |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-11-16 | 2026-11-16 | N/A: no doc change in scope |

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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-004`, `REQ-005`, `REQ-006`
- **Source issue**: `issues/20261115-081702_persis001_persistence-compensation-sqlite-only.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261115-194058_persis001_persistence-compensation-sqlite-only.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261116-093326
- **Related target files**: `scripts/agent/turn_persistence.py`, `tests/agent/test_turn_persistence.py`
