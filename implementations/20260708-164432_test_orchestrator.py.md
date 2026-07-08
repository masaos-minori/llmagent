# Implementation: H-7 — Remove TestHandleTurnToolResultStore from test_orchestrator.py

## Goal

Delete the `TestHandleTurnToolResultStore` test class entirely — it asserts that
`Orchestrator.handle_turn()` causes a partial-completion write to `ctx.tool_result_store`, a
behavior removed by the companion `llm_transport_errors.py` change (H-4, already covered by
`implementations/20260708-163427_llm_transport_errors.py.md`) together with the H-7 field
removal.

## Scope

**Target**: `tests/test_orchestrator.py`

**Depends on**: `scripts/agent/llm_transport_errors.py`'s H-4 change and
`scripts/agent/context.py`'s H-7 change already applied (or applied together with this doc).

**Out of scope**: every other test class in this file, and the shared `_make_err()` helper
(lines 112+) — used extensively by ~24 other test methods across the file and must NOT be
removed.

## Assumptions

1. `TestHandleTurnToolResultStore` (lines 659-686) contains exactly two test methods:
   `test_partial_completion_saves_to_tool_result_store` and
   `test_prestream_error_does_not_save_to_tool_result_store` — both assert on
   `ctx.tool_result_store.store` directly, which becomes meaningless once
   `handle_partial_completion()` never calls it (the "does not save" test would still trivially
   pass, but the "saves" test would start failing — deleting the whole class is simpler and more
   honest than patching one test to expect the opposite while leaving a class name that implies
   the store IS still used).
2. No other test class references `ctx.tool_result_store` in this file (confirmed by the earlier
   full-file grep showing only this one class's two methods as matches).

## Implementation

### Target file

`tests/test_orchestrator.py`

### Procedure

#### Step 1: Confirm the class boundaries and no other references

```bash
grep -n "tool_result_store" tests/test_orchestrator.py
```

Expected: matches only within lines 659-686 (the `TestHandleTurnToolResultStore` class body).

#### Step 2: Delete the class

Remove the entire block (lines 658-686, including the two blank lines that separate it from the
surrounding classes so spacing stays consistent with the rest of the file):

```python
class TestHandleTurnToolResultStore:
    @pytest.mark.asyncio
    async def test_partial_completion_saves_to_tool_result_store(self) -> None:
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)
        err = _make_err(kind="PREMATURE_EOF", partial_text="partial answer")

        with patch.object(orch._llm_runner, "run", AsyncMock(side_effect=err)):
            await orch.handle_turn("hello")

        ctx.tool_result_store.store.assert_called_once()
        call_kwargs = ctx.tool_result_store.store.call_args.kwargs
        assert call_kwargs["tool_name"] == "llm_partial_completion"
        assert call_kwargs["is_error"] is True
        assert "INCOMPLETE" in call_kwargs["summary"]

    @pytest.mark.asyncio
    async def test_prestream_error_does_not_save_to_tool_result_store(self) -> None:
        ctx = _make_ctx()
        orch = _make_orchestrator(ctx)
        err = _make_err(kind="CONNECT_ERROR", partial_text="")

        with patch.object(orch._llm_runner, "run", AsyncMock(side_effect=err)):
            await orch.handle_turn("hello")

        # Pre-stream fail: no partial output, so tool_result_store should NOT be called
        ctx.tool_result_store.store.assert_not_called()
```

Ensure the class immediately following (`TestToolLoopGuardHelpers`, currently starting after two
blank lines at what is line 691 pre-deletion) retains the same two-blank-line separation from
whatever class now precedes it after this deletion.

### Method

- Pure deletion of one class and its two methods; no replacement test is added — the plan does
  not ask for new coverage of "handle_turn never touches tool_result_store" at the orchestrator
  level (that invariant is already covered at the lower level by
  `tests/test_llm_partial_completion.py`'s `test_partial_completion_does_not_write_tool_result_store`,
  per the H-4 test doc).

### Details

- `_make_ctx()` and `_make_orchestrator()` (helpers used by the deleted class) remain in the file
  for use by other test classes — do not remove them; only the one class using
  `tool_result_store` specifically goes away.
- `AsyncMock`, `patch.object`, and `pytest` imports at the top of the file remain in use by other
  test classes — no import cleanup needed from this deletion alone.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Lint | `ruff check tests/test_orchestrator.py` | 0 errors |
| Type check | `mypy tests/test_orchestrator.py` | no new errors |
| Grep (class removed) | `grep -n "TestHandleTurnToolResultStore\|tool_result_store" tests/test_orchestrator.py` | no matches |
| Tests (targeted) | `uv run pytest tests/test_orchestrator.py -v` | all remaining tests pass |
| Tests (full) | `uv run pytest -v` | no new failures |
| Pre-commit | `pre-commit run --all-files` | pass |
