# Implementation: H-7 — Update test_error_injection_service.py for removed ToolResultStore call

## Goal

Remove the `ctx.tool_result_store = MagicMock()` fixture setup and replace the
`test_stores_in_tool_result_store` test (which asserts the removed call happened) with a test
asserting it does NOT happen, matching the companion source change
(`implementations/20260708-164010_error_injection_service.py.md` or its `done/` copy).

## Scope

**Target**: `tests/test_error_injection_service.py`

**Depends on**: `scripts/agent/error_injection_service.py`'s H-7 change already applied (or
applied together with this doc).

**Out of scope**: `test_stores_in_diagnostic_store_only`, `test_returns_summary_string`,
`test_multiple_errors_each_store_in_diagnostics`, `test_partial_text_reflected_in_diagnostic_content`
— none of these reference `tool_result_store` and all remain valid as-is.

## Assumptions

1. `_make_context()` (lines 13-18) sets `ctx.tool_result_store = MagicMock()` purely to support
   the call path being removed — after this change, `ctx` (a `MagicMock()`) would still
   auto-create a `.tool_result_store` attribute on access even without this explicit line, but
   removing it for clarity matches the plan's Affected Areas ("tests/test_error_injection_service.py
   (L.16, L.46-54)").
2. Only one test (`test_stores_in_tool_result_store`, lines 46-58) directly exercises this call
   path.

## Implementation

### Target file

`tests/test_error_injection_service.py`

### Procedure

#### Step 1: Remove the fixture setup line

Current `_make_context()` (lines 13-18):

```python
def _make_context() -> MagicMock:
    ctx = MagicMock()
    ctx.conv.history = []
    ctx.tool_result_store = MagicMock()
    ctx.session.session_id = 1
    return ctx
```

Replace with:

```python
def _make_context() -> MagicMock:
    ctx = MagicMock()
    ctx.conv.history = []
    ctx.session.session_id = 1
    return ctx
```

#### Step 2: Replace the test asserting the call happened

Current (lines 46-58):

```python
    def test_stores_in_tool_result_store(self) -> None:
        ctx = _make_context()
        svc = ErrorInjectionService(ctx)
        e = _make_error()

        svc.inject_mid_turn_error(e, turn=3)

        ctx.tool_result_store.store.assert_called_once()
        call_kwargs = ctx.tool_result_store.store.call_args[1]
        assert call_kwargs["turn"] == 3
        assert call_kwargs["tool_name"] == "llm_transport_error"
        assert call_kwargs["is_error"] is True
        ctx.diagnostics.save.assert_called_once()
```

Replace with:

```python
    def test_does_not_store_in_tool_result_store(self) -> None:
        """H-7: mid-turn error persistence is limited to the diagnostic channel."""
        ctx = _make_context()
        svc = ErrorInjectionService(ctx)
        e = _make_error()

        svc.inject_mid_turn_error(e, turn=3)

        ctx.tool_result_store.store.assert_not_called()
        ctx.diagnostics.save.assert_called_once()
```

### Method

- Rename `test_stores_in_tool_result_store` → `test_does_not_store_in_tool_result_store` to
  match its flipped assertion direction.
- Drop the `call_kwargs = ...` inspection lines entirely (nothing to inspect once the call never
  happens); keep the `ctx.diagnostics.save.assert_called_once()` line since the diagnostic write
  is preserved and still worth asserting here (redundant with
  `test_stores_in_diagnostic_store_only` but harmless, and keeps this test self-contained: "the
  call doesn't go to tool_result_store, but the error IS still recorded somewhere").

### Details

- `ctx.tool_result_store` remains accessible on the `MagicMock()`-based `ctx` even after removing
  its explicit setup line in `_make_context()` (MagicMock auto-vivifies attributes), so
  `assert_not_called()` remains meaningful without needing to keep the explicit
  `ctx.tool_result_store = MagicMock()` line.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Lint | `ruff check tests/test_error_injection_service.py` | 0 errors |
| Type check | `mypy tests/test_error_injection_service.py` | no new errors |
| Grep (old assertion gone) | `grep -n "tool_result_store.store.assert_called_once" tests/test_error_injection_service.py` | no matches |
| Tests (targeted) | `uv run pytest tests/test_error_injection_service.py -v` | all pass, including the renamed test |
| Tests (full) | `uv run pytest -v` | no new failures |
| Pre-commit | `pre-commit run --all-files` | pass |
