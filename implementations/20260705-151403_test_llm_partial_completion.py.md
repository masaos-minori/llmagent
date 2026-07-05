# Implementation: tests/test_llm_partial_completion.py — Partial LLM completion isolation tests

## Goal

Verify that partial LLM completions never enter `ctx.conv.history` or the `messages` table, and that all three failure paths (in-stream, pre-stream, tool-continuation) behave correctly.

## Scope

**In**: Tests for `handle_partial_completion()`, `handle_non_partial_error()`, and the `Orchestrator._process_turn()` paths. DB state assertions after failure.

**Out**: Source file changes.

## Assumptions

1. `handle_partial_completion()` does NOT append to `ctx.conv.history` — invariant to lock down via test.
2. `_handle_llm_error()` returns `TurnResult(persist_as_assistant=False)` — verified in code.
3. `orchestrator.py` only calls `ctx.session.save("assistant", ...)` when `persist_as_assistant=True`.
4. Pre-stream failure path: the user message was already appended to history; the error handler may or may not remove it — test must determine current behavior.
5. Tool-continuation failure: `LLMTurnRunner._handle_llm_error()` returns a fail TurnResult; tool runner adds a synthetic error tool result.

## Implementation

### Target file
`tests/test_llm_partial_completion.py`

### Procedure
1. Test `handle_partial_completion()` directly: verify no history mutation.
2. Test `handle_non_partial_error()` directly: verify no history mutation.
3. Test `Orchestrator._process_turn()` with mocked LLM: verify DB state.
4. Test session reload after failure.

### Method

```python
# Test 1: partial completion does not append to history
def test_partial_completion_not_in_history(mock_ctx_with_session):
    ctx = mock_ctx_with_session
    initial_history_len = len(ctx.conv.history)
    e = LLMTransportError(kind="stream_error", partial_text="partial output")
    handle_partial_completion(e, ctx, mock_diagnostic_store())
    assert len(ctx.conv.history) == initial_history_len

# Test 2: partial completion not persisted to messages table
def test_partial_completion_not_in_messages_table(ctx_with_real_db):
    ctx = ctx_with_real_db
    ctx.session.start("test_session")
    e = LLMTransportError(kind="stream_error", partial_text="partial output")
    handle_partial_completion(e, ctx, mock_diagnostic_store())
    rows = fetch_messages(ctx.session.session_id)
    assert all("partial" not in (r.get("content") or "") for r in rows)

# Test 3: partial completion → session_diagnostics written
def test_partial_completion_writes_session_diagnostics(mock_ctx):
    ds = CapturingDiagnosticStore()
    e = LLMTransportError(kind="stream_error", partial_text="partial output")
    handle_partial_completion(e, mock_ctx, ds)
    assert any("llm_transport_error" in k for k in ds.saved_keys)

# Test 4: partial completion → tool_result_store written
def test_partial_completion_writes_tool_result_store(mock_ctx):
    e = LLMTransportError(kind="stream_error", partial_text="partial output")
    handle_partial_completion(e, mock_ctx, mock_diagnostic_store())
    assert mock_ctx.tool_result_store.last_stored["tool_name"] == "llm_partial_completion"
    assert mock_ctx.tool_result_store.last_stored["is_error"] is True

# Test 5: stat_partial_completions incremented
def test_partial_completion_increments_stat(mock_ctx):
    before = mock_ctx.services_required.llm.stat_partial_completions
    e = LLMTransportError(kind="stream_error", partial_text="partial output")
    handle_partial_completion(e, mock_ctx, mock_diagnostic_store())
    assert mock_ctx.services_required.llm.stat_partial_completions == before + 1

# Test 6: pre-stream error (no partial text) — no assistant message persisted
async def test_pre_stream_error_no_assistant_message(ctx_with_real_db):
    ctx = ctx_with_real_db
    ctx.session.start("test_session")
    # Mock LLM to raise LLMTransportError with empty partial_text
    with patch_llm_to_raise(LLMTransportError(kind="connection_error", partial_text="")):
        await run_one_turn(ctx, "test input")
    rows = fetch_messages_by_role(ctx.session.session_id, "assistant")
    assert len(rows) == 0

# Test 7: tool-continuation error — synthetic tool error present
async def test_tool_continuation_error_synthetic_result(ctx_with_real_db):
    ctx = ctx_with_real_db
    # Mock: LLM succeeds first turn (returns tool call), fails on continuation
    with patch_llm_tool_then_fail():
        await run_one_turn(ctx, "test input")
    # Conversation can continue (no exception propagated)
    # Next turn succeeds
    result = await run_one_turn(ctx, "follow up")
    assert result is not None

# Test 8: session reload after partial completion
def test_session_reload_after_partial(ctx_with_real_db):
    ctx = ctx_with_real_db
    ctx.session.start("test_session")
    # Simulate partial completion
    e = LLMTransportError(kind="stream_error", partial_text="partial")
    handle_partial_completion(e, ctx, mock_diagnostic_store())
    # Reload session
    new_ctx = reload_session(ctx.session.session_id)
    assert "partial" not in str(new_ctx.conv.history)
```

## Validation plan

- `uv run pytest tests/test_llm_partial_completion.py -v` — all pass.
- If any test reveals a violation of the invariant: fix the source before merging tests.
- `ruff check tests/test_llm_partial_completion.py` — 0 errors.
