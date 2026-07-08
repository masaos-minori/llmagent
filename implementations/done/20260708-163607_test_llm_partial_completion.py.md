# Implementation: H-4 — Update test_llm_partial_completion.py for removed ToolResultStore call

## Goal

Replace the existing test that asserts `ctx.tool_result_store.store(...)` IS called by
`handle_partial_completion()` with a test asserting it is NOT called, matching the companion
source change (`implementations/20260708-163427_llm_transport_errors.py.md` or its `done/`
copy).

## Scope

**Target**: `tests/test_llm_partial_completion.py`

**Depends on**: `scripts/agent/llm_transport_errors.py`'s H-4 change already applied (or applied
together with this doc).

**Out of scope**: all other tests in this file (`test_partial_completion_does_not_append_to_history`,
`test_partial_completion_empty_history_stays_empty`, `test_partial_completion_writes_session_diagnostics`,
`test_partial_completion_calls_save_partial_completion`, `test_partial_completion_increments_stat`,
`test_non_partial_error_*`, `test_handle_llm_transport_error_routes_*`) — none of these reference
`tool_result_store` and all remain valid as-is.

## Assumptions

1. `_make_ctx()` (module-level helper, lines 24-44) sets up
   `ctx.tool_result_store = MagicMock()` / `ctx.tool_result_store.store = MagicMock()` purely to
   support the call path being removed. Since `handle_partial_completion()` will no longer touch
   `ctx.tool_result_store` at all, this mock setup becomes inert but harmless — no change to
   `_make_ctx()` itself is required (per the plan's Validation Plan, which asks to assert the
   mock is NOT called, implying the mock must still exist on the context object).
2. Only one test (`test_partial_completion_writes_tool_result_store`, lines 104-113) directly
   exercises this call path — confirmed by reading the file in full (see Scope's "Out of scope"
   list covering every other test).

## Implementation

### Target file

`tests/test_llm_partial_completion.py`

### Procedure

#### Step 1: Confirm the current test body

```python
def test_partial_completion_writes_tool_result_store() -> None:
    from agent.llm_transport_errors import handle_partial_completion

    ctx = _make_ctx()
    e = _make_transport_error(partial_text="partial output")
    handle_partial_completion(e, ctx, _make_diagnostic_store())
    ctx.tool_result_store.store.assert_called_once()
    kwargs = ctx.tool_result_store.store.call_args[1]
    assert kwargs.get("tool_name") == "llm_partial_completion"
    assert kwargs.get("is_error") is True
```

#### Step 2: Replace with a negative assertion, renamed to reflect the new invariant

Replace the function (keep it under the same `# ── tool_result_store ──` section header) with:

```python
def test_partial_completion_does_not_write_tool_result_store() -> None:
    """H-4: partial-completion persistence is limited to session_diagnostics."""
    from agent.llm_transport_errors import handle_partial_completion

    ctx = _make_ctx()
    e = _make_transport_error(partial_text="partial output")
    handle_partial_completion(e, ctx, _make_diagnostic_store())
    ctx.tool_result_store.store.assert_not_called()
```

### Method

- Rename `test_partial_completion_writes_tool_result_store` →
  `test_partial_completion_does_not_write_tool_result_store` so the test name matches its
  assertion direction (avoids a misleading name after the behavior flips).
- Drop the `kwargs = ctx.tool_result_store.store.call_args[1]` and subsequent `kwargs.get(...)`
  assertions entirely — they inspected arguments to a call that no longer happens;
  `call_args` would be `None` after `assert_not_called()` passes, so those lines have nothing
  left to check.
- Keep the `# ── tool_result_store ──` section comment/header as-is; the section's role becomes
  "assert this integration point is NOT used" rather than "assert it is used," which is still an
  accurate section description without wording changes.

### Details

- `_make_ctx()` remains unchanged — `ctx.tool_result_store` must still exist as a `MagicMock()`
  on the context object for `assert_not_called()` to be meaningful (asserting a call was not made
  on an attribute that doesn't exist would raise `AttributeError` instead of a clean assertion
  failure, so keeping the mock in place is required, not incidental).
- All other tests in this file remain valid because none of them touch
  `ctx.tool_result_store` — verified via the Scope section's exhaustive "Out of scope" list.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Lint | `ruff check tests/test_llm_partial_completion.py` | 0 errors |
| Type check | `mypy tests/test_llm_partial_completion.py` | no new errors |
| Grep (old assertion gone) | `grep -n "assert_called_once" tests/test_llm_partial_completion.py` | no matches referring to `tool_result_store` |
| Tests (targeted) | `uv run pytest tests/test_llm_partial_completion.py -v` | all pass, including the renamed test |
| Tests (full) | `uv run pytest -v` | no new failures |
| Pre-commit | `pre-commit run --all-files` | pass |
