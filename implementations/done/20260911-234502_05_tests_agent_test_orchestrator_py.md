## Goal

Remove the 3 `@pytest.mark.skip(...)` markers on `TestHandleLlmTurnOptionalCallbacks`'s tests; correct `test_wait_and_turn_callbacks_invoked_on_success` and `test_wait_end_error_and_turn_end_invoked_when_run_returns_exception`'s mocking strategy from `patch.object(orch._llm_executor, "handle_llm_turn", AsyncMock(...))` (which would bypass the new wiring inside `handle_llm_turn()` entirely) to `patch("agent.llm_turn_executor.LLMTurnRunner")` with the mock instance's `.run` configured as an `AsyncMock` returning the same `TurnResult`; `test_wait_end_invoked_in_except_branch` needs no mocking-strategy change.

## Scope

- Remove `@pytest.mark.skip(...)` decorators from all 3 tests.
- Correct mocking strategy for 2 tests that currently patch `orch._llm_executor.handle_llm_turn` wholesale.
- Leave `test_wait_end_invoked_in_except_branch` as-is (it already exercises the real call chain end-to-end).

## Assumptions

- All 3 tests read in full (lines 772-878); confirmed `patch.object(orch._llm_executor, "handle_llm_turn", ...)` replaces the entire method body, which would make the new wiring (placed inside that method) untestable as currently mocked.
- `LLMTurnRunner(self._ctx, guard, tracer=self._tracer)` construction was read in full during Plan investigation; the corrected test only needs to control the `.run(...)` return value, not replicate the constructor call.
- The existing `_make_ctx()`, `_make_err()`, and `TurnResult` fixtures are available and unchanged.

## Design decisions

- Use `patch("agent.llm_turn_executor.LLMTurnRunner")` instead of `patch.object(orch._llm_executor, "handle_llm_turn", ...)`:
  - This lets the real `handle_llm_turn()` body execute with a controlled `runner.run()` return value.
  - The mock instance's `.run` is configured as an `AsyncMock` returning the same `TurnResult` each test already constructs.
- Keep `test_wait_end_invoked_in_except_branch` unchanged — it mocks `ctx.services_required.llm.stream` directly, exercising the real end-to-end call chain including the new wiring.

## Alternatives considered

- Keeping the skip markers — rejected because the fix enables these tests.
- Using `patch.object(orch._llm_executor, "handle_llm_turn", ...)` — rejected because it bypasses the new callback wiring inside `handle_llm_turn()`.

## Implementation

### Target file

`tests/agent/test_orchestrator.py`

### Procedure

1. In `test_wait_and_turn_callbacks_invoked_on_success`:
   - Remove `@pytest.mark.skip(...)` decorator (line 780-784).
   - Replace `patch.object(orch._llm_executor, "handle_llm_turn", AsyncMock(return_value=TurnResult(action="continue", answer="ok")))` with `patch("agent.llm_turn_executor.LLMTurnRunner")` and configure the mock's `.run` method.
2. In `test_wait_end_error_and_turn_end_invoked_when_run_returns_exception`:
   - Remove `@pytest.mark.skip(...)` decorator (line 814-818).
   - Replace `patch.object(orch._llm_executor, "handle_llm_turn", AsyncMock(return_value=TurnResult(...)))` with `patch("agent.llm_turn_executor.LLMTurnRunner")` and configure the mock's `.run` method.
3. In `test_wait_end_invoked_in_except_branch`:
   - Remove `@pytest.mark.skip(...)` decorator (line 859-863).
   - No mocking-strategy change needed.

### Method

- Read current test methods (lines 772-878) to understand existing assertions and fixture usage.
- Confirm `LLMTurnRunner.__init__` does not accept any of the 4 callbacks (its docstring claim to the contrary is a pre-existing inaccuracy, out of scope).

### Details

**`test_wait_and_turn_callbacks_invoked_on_success` changes:**
```python
# Before:
@pytest.mark.asyncio
@pytest.mark.skip(
    reason="on_turn_start/on_turn_end/on_llm_wait_start/on_llm_wait_end are "
    "never invoked anywhere in current code (call_on_error was the only one "
    "wired; fixed separately this session) — see issues/20260911-150000_orchcb01_turn-and-llm-wait-callbacks-never-invoked.md"
)
async def test_wait_and_turn_callbacks_invoked_on_success(self) -> None:
    ctx = _make_ctx()
    on_turn_start = MagicMock()
    on_turn_end = MagicMock()
    on_llm_wait_start = AsyncMock()
    on_llm_wait_end = MagicMock()
    orch = Orchestrator(...)
    orch._diagnostic_store = MagicMock()
    ctx.diagnostics = orch._diagnostic_store

    with patch.object(
        orch._llm_executor,
        "handle_llm_turn",
        AsyncMock(return_value=TurnResult(action="continue", answer="ok")),
    ):
        await orch.handle_turn("hello")

    on_llm_wait_start.assert_called_once()
    on_turn_start.assert_called_once()
    on_llm_wait_end.assert_called_once()
    on_turn_end.assert_called_once()

# After:
@pytest.mark.asyncio
async def test_wait_and_turn_callbacks_invoked_on_success(self) -> None:
    ctx = _make_ctx()
    on_turn_start = MagicMock()
    on_turn_end = MagicMock()
    on_llm_wait_start = AsyncMock()
    on_llm_wait_end = MagicMock()
    orch = Orchestrator(...)
    orch._diagnostic_store = MagicMock()
    ctx.diagnostics = orch._diagnostic_store

    mock_runner = AsyncMock()
    mock_runner.run.return_value = TurnResult(action="continue", answer="ok")
    with patch("agent.llm_turn_executor.LLMTurnRunner", return_value=mock_runner):
        await orch.handle_turn("hello")

    on_llm_wait_start.assert_called_once()
    on_turn_start.assert_called_once()
    on_llm_wait_end.assert_called_once()
    on_turn_end.assert_called_once()
```

**`test_wait_end_error_and_turn_end_invoked_when_run_returns_exception` changes:**
```python
# Before:
@pytest.mark.asyncio
@pytest.mark.skip(
    reason="on_turn_start/on_turn_end/on_llm_wait_start/on_llm_wait_end are "
    "never invoked anywhere in current code (call_on_error was the only one "
    "wired; fixed separately this session) — see issues/20260911-150000_orchcb01_turn-and-llm-wait-callbacks-never-invoked.md"
)
async def test_wait_end_error_and_turn_end_invoked_when_run_returns_exception(
    self,
) -> None:
    ...
    with patch.object(
        orch._llm_executor,
        "handle_llm_turn",
        AsyncMock(
            return_value=TurnResult(
                action="fail",
                answer="",
                exception=err,
                persist_as_assistant=False,
            )
        ),
    ):
        await orch.handle_turn("hello")
    ...

# After:
@pytest.mark.asyncio
async def test_wait_end_error_and_turn_end_invoked_when_run_returns_exception(
    self,
) -> None:
    ...
    mock_runner = AsyncMock()
    mock_runner.run.return_value = TurnResult(
        action="fail",
        answer="",
        exception=err,
        persist_as_assistant=False,
    )
    with patch("agent.llm_turn_executor.LLMTurnRunner", return_value=mock_runner):
        await orch.handle_turn("hello")
    ...
```

**`test_wait_end_invoked_in_except_branch` changes:**
- Only remove `@pytest.mark.skip(...)` decorator (line 859-863).
- No other change needed.

## Compatibility considerations

- The corrected tests must still exercise the real `handle_llm_turn()` body including the new callback wiring.
- `LLMTurnRunner` construction arguments (`self._ctx, guard, tracer=self._tracer`) are not replicated by the test — the mock replaces the entire class, so only `.run()` return value matters.

## Security considerations

N/A: test-only changes, no security-sensitive behavior.

## Rollback considerations

- If corrected tests fail due to unexpected side effects, revert to pre-modification state: restore skip markers and original mocking strategy.
- The rollback is bounded to this one file only.

## Validation plan

- Unit test: `uv run pytest tests/agent/test_orchestrator.py::TestHandleLlmTurnOptionalCallbacks -q` — all 3 tests pass, none skipped.
- Regression: `uv run pytest tests/agent/test_orchestrator.py -q` — expected 87 passed, 0 skipped (baseline: 84 passed, 3 skipped).
- Regression: `uv run pytest tests/integration/test_orchestrator_integration.py -q` — no regression (baseline: 39 passed, 0 skipped).
- Static: `uv run ruff check tests/agent/test_orchestrator.py`; `uv run mypy tests/agent/test_orchestrator.py`.

## Completion criteria

- All 3 `@pytest.mark.skip(...)` markers removed from `TestHandleLlmTurnOptionalCallbacks`.
- `test_wait_and_turn_callbacks_invoked_on_success` uses `patch("agent.llm_turn_executor.LLMTurnRunner")` with mock `.run` returning `TurnResult(action="continue", answer="ok")`.
- `test_wait_end_error_and_turn_end_invoked_when_run_returns_exception` uses `patch("agent.llm_turn_executor.LLMTurnRunner")` with mock `.run` returning `TurnResult(action="fail", exception=err, ...)`.
- `test_wait_end_invoked_in_except_branch` unchanged except for skip removal.
- All 3 tests pass when executed.
- No regression in existing tests.

## Out of scope

- Removing `on_turn_start`/`on_turn_end` from `AuditEventEmitter` — handled in `audit_event_emitter.py` procedure document.
- Removing `on_turn_start`/`on_turn_end` from `LlmTurnExecutor` — handled in `llm_turn_executor.py` procedure document.
- Removing `on_llm_wait_start`/`on_llm_wait_end` from `Orchestrator` — handled in `orchestrator.py` procedure document.
- Removing `on_llm_wait_start`/`on_llm_wait_end` from `ConversationStateManager` — handled in `conversation_state_manager.py` procedure document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | All changes already applied |
| 2 | Add or update tests per Validation plan | Completed | — | — | All 3 callback tests pass |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | ruff/mypy clean; 3 passed |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Not needed | — | — | No docs in scope |

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
- **Requirement ID**: REQ-004
- **Source issue**: issues/20260911-150000_orchcb01_turn-and-llm-wait-callbacks-never-invoked.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260911-211456_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260911-234502
- **Related target files**: tests/agent/test_orchestrator.py
