# Implementation and Test Procedure: TestApprovalPendingGuard in test_orchestrator.py

## Goal

Add `TestApprovalPendingGuard` to `tests/test_orchestrator.py` to verify that `Orchestrator.handle_turn()` returns early and calls `on_error` when `ctx.workflow.approval_pending=True`.

## Scope

**In:**
- `tests/test_orchestrator.py` — append `TestApprovalPendingGuard` class

**Out:**
- Modifying `orchestrator.py` (already implemented)
- Adding tests for other orchestrator behaviors

## Assumptions

1. `_make_ctx()` returns a `MagicMock`; `ctx.workflow.approval_pending` is a MagicMock attribute that evaluates to truthy when set to `True`.
2. `_make_orchestrator()` accepts an `on_error` callable that is called by `self._on_error(...)`.
3. `handle_turn()` with `approval_pending=True` must:
   - call `on_error` exactly once with a `RuntimeError` whose message contains `/approve` or `/reject`
   - return without calling the LLM (i.e. `ctx.services.llm` is not called)
4. The test must be async (uses `@pytest.mark.asyncio`).

## Implementation

### Target file
`tests/test_orchestrator.py`

### Procedure
Append the following class after the existing `TestToolLoopGuardHelpers` class.

### Method
Use the existing `_make_ctx()` and `_make_orchestrator()` fixtures. Set `ctx.workflow.approval_pending = True` before calling `handle_turn()`. Pass a `MagicMock` as `on_error` to capture the call.

### Details

```python
# ── approval_pending guard ────────────────────────────────────────────────────


class TestApprovalPendingGuard:
    @pytest.mark.asyncio
    async def test_handle_turn_blocked_when_approval_pending(self) -> None:
        """handle_turn() must call on_error and return without LLM call when approval_pending=True."""
        on_error = MagicMock()
        ctx = _make_ctx()
        ctx.workflow.approval_pending = True
        orch = _make_orchestrator(ctx, on_error=on_error)

        await orch.handle_turn("do something")

        on_error.assert_called_once()
        err = on_error.call_args[0][0]
        assert isinstance(err, RuntimeError)
        assert "/approve" in str(err) or "/reject" in str(err)
        # LLM must not be called
        ctx.services.llm.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_turn_not_blocked_when_approval_not_pending(self) -> None:
        """handle_turn() must proceed normally when approval_pending=False."""
        on_error = MagicMock()
        ctx = _make_ctx()
        ctx.workflow.approval_pending = False
        orch = _make_orchestrator(ctx, on_error=on_error)

        # Patch the LLM to return a stop response immediately
        stop_response = LLMResponse(content="ok", stop_reason="stop", usage=None)
        with patch.object(
            orch, "_run_turn", new=AsyncMock(return_value=TurnResult(text="ok", tool_calls=[]))
        ):
            await orch.handle_turn("do something")

        # on_error must NOT have been called due to the approval guard
        # (it may be called for other reasons, but not the guard path)
        for call in on_error.call_args_list:
            err = call[0][0]
            assert "Approval is pending" not in str(err)
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Test discovery | `uv run pytest tests/test_orchestrator.py::TestApprovalPendingGuard -v` | 2 tests collected |
| Tests pass | `uv run pytest tests/test_orchestrator.py::TestApprovalPendingGuard -v` | PASSED |
| No regression | `uv run pytest tests/test_orchestrator.py -v` | all pass |
| Lint | `uv run ruff check tests/test_orchestrator.py` | 0 errors |
