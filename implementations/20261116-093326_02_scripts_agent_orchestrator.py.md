## Goal

Route any post-commit in-turn exception through the same all-or-nothing compensation as
`ConversationPersistenceError` so no partial turn survives (`REQ-001`), while preserving the
`is_partial` signal (`is_partial=True` for a mid-turn committed exception, `is_partial=False`
for `ConversationPersistenceError`) and the `BaseException`/`CancelledError` propagation that
escapes `orchestrator` (`REQ-002`, `REQ-003`).

## Scope
**Release unit**: N/A: not part of a release unit

Code change to `scripts/agent/orchestrator.py` only. The persistence half lives in
`scripts/agent/turn_persistence.py` (sibling document).

## Assumptions

- `orchestrator._execute_turn` holds the `TurnPersistence` `boundary` reference
  (`boundary` at line 173, assigned at line 176 via `self._ctx.session.turn_boundary`), so it
  can call `rollback_partial_turn()` on failure.
- `rollback_partial_turn` (sibling document) gates compensation on an internal committed-state
  flag, so calling it from the orchestrator never compensates a turn that persisted nothing
  (`REQ-004`).

## Design decisions

- **Where compensation is invoked: the `except BaseException` branch of `_execute_turn`
  (line 192-195), delegating to `boundary.rollback_partial_turn()`.** The orchestrator cannot
  see whether a write committed, so it relies on the flag exposed by the sibling; it only needs
  to route and read the `bool` return to set `is_partial`.
- **Guard `boundary is not None`.** `boundary` is declared `TurnPersistence | None` and assigned
  inside the `try` (line 176); an exception during `emit_turn_start` (line 175) or
  `turn_boundary` (line 176) leaves it `None`, and `rollback_partial_turn` would otherwise
  raise `AttributeError`.

## Alternatives considered

- Calling `rollback_partial_turn()` in the `finally` block instead of the `except`: rejected,
  because `finally` also runs on the successful path and on the `ConversationPersistenceError`
  path (which already compensated), risking a double compensation.
- Deriving `is_partial` solely from `partial_text`: insufficient, because a plain
  `RuntimeError`/`ValueError` after a commit carries no `partial_text`, so `is_partial` would be
  `False` even though rows were compensated (`REQ-002`).

## Implementation
### Target file
`scripts/agent/orchestrator.py`

### Procedure
1. In `_execute_turn`, in the `except BaseException` branch (lines 192-195), call
   `await boundary.rollback_partial_turn()` when `boundary` is not `None`, and OR its `bool`
   return into `is_partial` so a compensated mid-turn exception is recorded as partial.

### Method
Change only the body of the `except BaseException as exc:` handler at
`scripts/agent/orchestrator.py:192-195`:

```python
        except BaseException as exc:
            error_kind = exc.__class__.__name__
            if boundary is not None:
                compensated = await boundary.rollback_partial_turn()
                is_partial = bool(getattr(exc, "partial_text", "")) or compensated
            raise
```

- Keep `error_kind = exc.__class__.__name__` and the trailing `raise` unchanged so propagation
  still escapes end-to-end (`REQ-003`).
- `rollback_partial_turn` returns `True` only when a write had committed (sibling document); the
  `or` makes `is_partial=True` for a compensated mid-turn exception (`REQ-002`). The existing
  `getattr(exc, "partial_text", "")` is preserved for instrumented exceptions.
- Leave the `except ConversationPersistenceError` branch (lines 183-191) untouched: it already
  knows compensation ran and sets `is_partial=False` (`REQ-005`).

### Details
- The `if boundary is not None` guard is required for type safety (`boundary` is
  `TurnPersistence | None`) and to avoid compensating during setup failures where nothing was
  persisted.
- Compensation runs on a worker thread inside `rollback_partial_turn` (`_compensate` offloaded
  via `asyncio.to_thread`), preserving the single-connection invariant (`REQ-006`).
- The `finally` block (lines 196-202) emits `turn_end` with the updated `is_partial`; setting
  `is_partial` before re-raising ensures the audit record reflects the compensation.

### Companion test files
- `tests/agent/test_orchestrator.py` (existing)
  - Procedure: add an end-to-end test that raises a non-`sqlite3.Error` after a partial commit
    inside `_execute_turn`, asserting compensation deletes the partial rows, `is_partial=True` is
    recorded, and the exception still propagates; regression-confirm the existing
    `ConversationPersistenceError` (`is_partial=False`) and propagation tests.
  - Validation: `uv run pytest tests/agent/test_orchestrator.py` — new case passes and existing
    propagation/`sqlite3.Error` regression is unchanged (`REQ-001`, `REQ-002`, `REQ-003`,
    `REQ-005`).

## Compatibility considerations

- Additive: only the body of an existing `except` branch changes; no new public symbol,
  signature, or import is introduced.
- The `ConversationPersistenceError` path and its `is_partial=False` contract are unchanged
  (`REQ-005`).

## Security considerations

N/A: no authentication, authorization, or input-handling change.

## Rollback considerations

Revert the single commit to `scripts/agent/orchestrator.py`; no persisted data shape changes.

## Validation plan

- `uv run pytest tests/agent/test_orchestrator.py` — a non-`sqlite3.Error` exception after a
  partial commit is compensated end-to-end and still propagates; existing propagation and
  `sqlite3.Error` regression passes.
- `uv run ruff check scripts/agent/orchestrator.py`;
  `uv run mypy --no-namespace-packages scripts/agent/orchestrator.py` — clean.

## Completion criteria

- A non-`sqlite3.Error` exception after a committed write triggers compensation via
  `rollback_partial_turn` and still propagates (`REQ-001`, `REQ-003`).
- `is_partial=True` for a compensated mid-turn committed exception and `is_partial=False` for
  `ConversationPersistenceError` (`REQ-002`); compensation does not fire before any write
  committed (`REQ-004`).
- The `sqlite3.Error` path and propagation semantics are unchanged (`REQ-005`, `REQ-006`).

## Out of Scope

- The committed-state signal and `rollback_partial_turn` (sibling document).
- Changing how `partial_text` is set on exceptions (`error_injection_service`,
  `llm_turn_executor`).
- Repository write transactions, append-only mechanics, or connection handling.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-003`
- **Source issue**: `issues/20261115-081702_persis001_persistence-compensation-sqlite-only.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261115-194058_persis001_persistence-compensation-sqlite-only.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261116-093326
- **Related target files**: `scripts/agent/orchestrator.py`, `tests/agent/test_orchestrator.py`
