## Goal

Add `call_on_llm_wait_start()` helper; wrap `handle_llm_turn()`'s `runner.run(...)` call with `call_on_llm_wait_start()` before and `call_on_llm_wait_end()` in a `finally` block after; remove `on_turn_start`/`on_turn_end` constructor parameters, storage, and the now-unused `call_on_turn_end()` helper; correct `on_llm_wait_start`'s type annotation to `Callable[[], None] | None`.

## Scope

- Add `call_on_llm_wait_start()` helper method mirroring existing `call_on_llm_wait_end()`.
- Wrap `runner.run(...)` call in `handle_llm_turn()` with `try/finally` for symmetric wait callback invocation.
- Remove dead `on_turn_start`/`on_turn_end` storage and unused `call_on_turn_end()` helper.
- Correct `on_llm_wait_start` type annotation from `Callable[[], Any] | None` to `Callable[[], None] | None`.

## Assumptions

- `LLMTurnRunner.run()` catches `LLMTransportError` internally (line 85, via `_stream_llm`) and converts it to a `TurnResult` rather than propagating it — confirmed by reading `llm_turn_runner.py:83-88`.
- The `try/finally` design (rather than a type-specific `except LLMTransportError` clause) satisfies test `test_wait_end_invoked_in_except_branch`'s intent without depending on an exception path that does not exist at the `handle_llm_turn()` level.
- `call_on_llm_wait_end()` already exists as a helper; only `call_on_llm_wait_start()` needs to be added.

## Design decisions

- Use `try/finally` around `runner.run(...)` so `on_llm_wait_end` fires symmetrically even if `run()` raises — matching the bracketing semantics implied by the "wait_start/wait_end" naming.
- Place `call_on_llm_wait_start()` immediately before `runner.run(...)`, and `call_on_llm_wait_end()` in the `finally` block after.
- Keep `self.call_on_error(result.exception)` inside the `try` block (before `finally`), preserving existing error-handling behavior.

## Alternatives considered

- Using `except LLMTransportError` specifically — rejected because `LLMTurnRunner.run()` never propagates `LLMTransportError` out to `handle_llm_turn()` under any code path found during investigation.
- Placing callbacks outside the `try/finally` — rejected because it would break symmetric invocation when `run()` raises.

## Implementation

### Target file

`scripts/agent/llm_turn_executor.py`

### Procedure

1. In `__init__`: remove `on_turn_start: Callable[[], None] | None = None` parameter and `self._on_turn_start = on_turn_start` assignment.
2. In `__init__`: remove `on_turn_end: Callable[[], None] | None = None` parameter and `self._on_turn_end = on_turn_end` assignment.
3. In `__init__`: correct `on_llm_wait_start: Callable[[], Any] | None = None` to `on_llm_wait_start: Callable[[], None] | None = None`.
4. Add `call_on_llm_wait_start()` helper method mirroring `call_on_llm_wait_end()`.
5. In `handle_llm_turn()`: wrap `runner.run(...)` call with `try/finally`:
   - Before `runner.run(...)`: add `self.call_on_llm_wait_start()`
   - After `runner.run(...)`: keep existing `if result.exception is not None:` branch
   - In `finally`: add `self.call_on_llm_wait_end()`
6. Remove `call_on_turn_end()` helper method entirely.

### Method

- Read current `__init__` signature (lines 45-55) to identify which parameters/assignments to modify/remove.
- Read current `handle_llm_turn()` body (lines 74-99) to identify exact insertion points for `try/finally`.
- Read current `call_on_llm_wait_end()` (lines 59-62) and `call_on_turn_end()` (lines 64-67) to understand the helper pattern.

### Details

**`__init__` changes:**
```python
# Before:
def __init__(
    self,
    ctx: AgentContext,
    *,
    diagnostic_store: DiagnosticStore | None = None,
    tracer: Any = None,
    on_turn_start: Callable[[], None] | None = None,
    on_turn_end: Callable[[], None] | None = None,
    on_error: Callable[[Exception], None] | None = None,
    on_llm_wait_start: Callable[[], Any] | None = None,
    on_llm_wait_end: Callable[[], None] | None = None,
) -> None:
    ...
    self._on_turn_start = on_turn_start
    self._on_turn_end = on_turn_end
    self._on_error = on_error
    self._on_llm_wait_start = on_llm_wait_start
    self._on_llm_wait_end = on_llm_wait_end

# After:
def __init__(
    self,
    ctx: AgentContext,
    *,
    diagnostic_store: DiagnosticStore | None = None,
    tracer: Any = None,
    on_error: Callable[[Exception], None] | None = None,
    on_llm_wait_start: Callable[[], None] | None = None,
    on_llm_wait_end: Callable[[], None] | None = None,
) -> None:
    ...
    self._on_error = on_error
    self._on_llm_wait_start = on_llm_wait_start
    self._on_llm_wait_end = on_llm_wait_end
```

**New helper method (add after line 67):**
```python
def call_on_llm_wait_start(self) -> None:
    """Invoke on_llm_wait_start if configured."""
    if self._on_llm_wait_start:
        self._on_llm_wait_start()
```

**`handle_llm_turn()` change:**
```python
async def handle_llm_turn(
    self,
    llm_url: str,
    *,
    workflow_id: str = "",
    task_id: str = "",
    stage_id: str = "",
    attempt_id: str = "",
) -> TurnResult:
    guard = ToolLoopGuard(self._ctx)
    runner = LLMTurnRunner(
        self._ctx,
        guard,
        tracer=self._tracer,
    )
    try:
        self.call_on_llm_wait_start()
        result = await runner.run(
            llm_url,
            workflow_id=workflow_id,
            task_id=task_id,
            stage_id=stage_id,
            attempt_id=attempt_id,
        )
        if result.exception is not None:
            self.call_on_error(result.exception)
    finally:
        self.call_on_llm_wait_end()
    return result
```

**Remove `call_on_turn_end()` method (lines 64-67).**

## Compatibility considerations

- `Orchestrator.__init__` currently passes `on_turn_start`/`on_turn_end` kwargs to `LlmTurnExecutor(...)` construction (orchestrator.py:159-160). After removing these parameters from `LlmTurnExecutor.__init__`, those kwargs must be dropped there too — handled in the `orchestrator.py` procedure document.
- No other file constructs `LlmTurnExecutor` directly with these kwargs (confirmed via architecture/dependency analysis).

## Security considerations

N/A: no new security-sensitive behavior introduced.

## Rollback considerations

- If callback invocation causes issues, revert to pre-modification state: remove the `try/finally` wrapper, restore removed constructor parameters, and restore `call_on_turn_end()`.
- The rollback is bounded to this one file only.

## Validation plan

- Unit test: `uv run pytest tests/agent/test_orchestrator.py::TestHandleLlmTurnOptionalCallbacks::test_wait_and_turn_callbacks_invoked_on_success -q` — should pass with un-skipped test.
- Unit test: `uv run pytest tests/agent/test_orchestrator.py::TestHandleLlmTurnOptionalCallbacks::test_wait_end_error_and_turn_end_invoked_when_run_returns_exception -q` — should pass with corrected mocking strategy.
- Unit test: `uv run pytest tests/agent/test_orchestrator.py::TestHandleLlmTurnOptionalCallbacks::test_wait_end_invoked_in_except_branch -q` — should pass with skip removed.
- Regression: `uv run pytest tests/agent/test_orchestrator.py -q` — expected 87 passed, 0 skipped.
- Static: `uv run ruff check scripts/agent/llm_turn_executor.py`; `uv run mypy scripts/agent/llm_turn_executor.py`.

## Completion criteria

- `call_on_llm_wait_start()` helper exists and mirrors `call_on_llm_wait_end()`.
- `handle_llm_turn()` wraps `runner.run(...)` in `try/finally` with `call_on_llm_wait_start()` before and `call_on_llm_wait_end()` in `finally`.
- `on_turn_start`/`on_turn_end` constructor parameters and storage removed from `LlmTurnExecutor`.
- `call_on_turn_end()` helper removed.
- `on_llm_wait_start` type annotation corrected to `Callable[[], None] | None`.
- No lint/type errors introduced.

## Out of scope

- Removing `on_llm_wait_start`/`on_llm_wait_end` from `Orchestrator` — handled in `orchestrator.py` procedure document.
- Removing `on_llm_wait_start`/`on_llm_wait_end` from `AuditEventEmitter` — handled in `audit_event_emitter.py` procedure document.
- Test corrections — handled in `test_orchestrator.py` procedure document.

## execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | |
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
- **Requirement ID**: REQ-002, REQ-003, REQ-001
- **Source issue**: issues/20260911-150000_orchcb01_turn-and-llm-wait-callbacks-never-invoked.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260911-211456_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260911-234502
- **Related target files**: scripts/agent/llm_turn_executor.py
