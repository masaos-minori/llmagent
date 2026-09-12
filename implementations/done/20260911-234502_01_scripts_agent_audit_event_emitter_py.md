## Goal

Invoke `on_turn_start`/`on_turn_end` from inside `AuditEventEmitter.emit_turn_start()`/`emit_turn_end()`; remove the now-unused `on_llm_wait_start`/`on_llm_wait_end` constructor parameters and storage (this class never needs them — they move exclusively to `LlmTurnExecutor`).

## Scope

- Add conditional callback invocations at the start of `emit_turn_start()` and end of `emit_turn_end()`.
- Remove `on_llm_wait_start`/`on_llm_wait_end` constructor parameters and instance attributes (`self._on_llm_wait_start`, `self._on_llm_wait_end`) from `AuditEventEmitter.__init__`.

## Assumptions

- `emit_turn_start()` is called exactly once per real turn by `Orchestrator._execute_turn()` (confirmed via `orchestrator.py:213-220`).
- `emit_turn_end()` is called exactly once per real turn by `Orchestrator._execute_turn()`.
- The callbacks are already stored as `self._on_turn_start`/`self._on_turn_end` but never invoked — this is dead storage.

## Design decisions

- Place `self._on_turn_start()` invocation at the very start of `emit_turn_start()`, before any audit logging, so the callback fires at the true turn boundary.
- Place `self._on_turn_end()` invocation at the very end of `emit_turn_end()`, after all metadata/stats building, so the callback sees the complete turn result.
- Both invocations gated on truthiness check (`if self._on_turn_start:`) matching the existing pattern used by `call_on_llm_wait_end()`/`call_on_turn_end()` in `LlmTurnExecutor`.

## Alternatives considered

- Invoking callbacks inside `Orchestrator._execute_turn()` instead — rejected because `AuditEventEmitter` already stores these callbacks and is the natural single call site.
- Using a separate event bus — overkill for two simple callback invocations.

## Implementation

### Target file

`scripts/agent/audit_event_emitter.py`

### Procedure

1. In `emit_turn_start()`: add `if self._on_turn_start: self._on_turn_start()` at the start of the method body, before the audit logger check.
2. In `emit_turn_end()`: add `if self._on_turn_end: self._on_turn_end()` at the end of the method body, after all metadata/stats building and before the final return.
3. In `__init__`: remove `on_llm_wait_start: Callable[[], Any] | None = None` parameter and `self._on_llm_wait_start = on_llm_wait_start` assignment.
4. In `__init__`: remove `on_llm_wait_end: Callable[[], None] | None = None` parameter and `self._on_llm_wait_end = on_llm_wait_end` assignment.

### Method

- Read current `emit_turn_start()` (lines 75-91) and `emit_turn_end()` (lines 129+) bodies to identify exact insertion points.
- Read current `__init__` signature (lines 55-68) to identify which parameters/assignments to remove.

### Details

**`emit_turn_start()` change:**
```python
async def emit_turn_start(self) -> None:
    if self._on_turn_start:
        self._on_turn_start()
    ctx = self._ctx
    ...
```

**`emit_turn_end()` change:**
```python
def emit_turn_end(self, ...) -> dict[str, str]:
    ...
    if self._on_turn_end:
        self._on_turn_end()
    return result
```

**`__init__` changes:**
- Remove line 56: `on_llm_wait_start: Callable[[], Any] | None = None,`
- Remove line 57: `on_llm_wait_end: Callable[[], None] | None = None,`
- Remove line 67: `self._on_llm_wait_start = on_llm_wait_start`
- Remove line 68: `self._on_llm_wait_end = on_llm_wait_end`

## Compatibility considerations

- `Orchestrator.__init__` currently passes `on_llm_wait_start`/`on_llm_wait_end` kwargs to `AuditEventEmitter(...)` construction (orchestrator.py:141-142). After removing these parameters from `AuditEventEmitter.__init__`, those kwargs must be dropped there too — handled in the `orchestrator.py` procedure document.
- No other file constructs `AuditEventEmitter` directly with these kwargs (confirmed via architecture/dependency analysis).

## Security considerations

N/A: no new security-sensitive behavior introduced.

## Rollback considerations

- If callback invocation causes issues, revert to pre-modification state: remove the two conditional invocations and restore the removed constructor parameters.
- The rollback is bounded to this one file only.

## Validation plan

- Unit test: `uv run pytest tests/agent/test_orchestrator.py::TestHandleLlmTurnOptionalCallbacks::test_wait_and_turn_callbacks_invoked_on_success -q` — should pass with un-skipped test.
- Regression: `uv run pytest tests/agent/test_orchestrator.py -q` — expected 87 passed, 0 skipped.
- Static: `uv run ruff check scripts/agent/audit_event_emitter.py`; `uv run mypy scripts/agent/audit_event_emitter.py`.

## Completion criteria

- `emit_turn_start()` invokes `self._on_turn_start()` before audit logging.
- `emit_turn_end()` invokes `self._on_turn_end()` after stats building.
- `__init__` no longer accepts `on_llm_wait_start`/`on_llm_wait_end` parameters.
- No lint/type errors introduced.

## Out of scope

- Removing `on_llm_wait_start`/`on_llm_wait_end` from `Orchestrator` — handled in `orchestrator.py` procedure document.
- Removing `on_llm_wait_start`/`on_llm_wait_end` from `LlmTurnExecutor` — handled in `llm_turn_executor.py` procedure document.
- Test corrections — handled in `test_orchestrator.py` procedure document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | |
| 2 | Add or update tests per Validation plan | Completed | — | — | N/A: no test changes needed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | N/A: no changes made |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — | N/A: no documentation updates needed |

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
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: issues/20260911-150000_orchcb01_turn-and-llm-wait-callbacks-never-invoked.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260911-211456_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260911-234502
- **Related target files**: scripts/agent/audit_event_emitter.py
