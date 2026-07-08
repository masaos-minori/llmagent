# Implementation: H-7 — Remove tool_result_store field from _make_ctx() in test_llm_partial_completion.py

## Goal

Remove the `tool_result_store` field entirely from this file's `_make_ctx()` helper (a
`SimpleNamespace`, which does NOT auto-vivify missing attributes the way `MagicMock` does), and
remove the now-impossible-to-run assertion test that depends on it, matching
`AgentContext` no longer having this field after H-7.

## Scope

**Target**: `tests/test_llm_partial_completion.py`

**Depends on**: apply AFTER `implementations/20260708-163607_test_llm_partial_completion.py.md`
(the H-4 doc, which already renamed `test_partial_completion_writes_tool_result_store` to
`test_partial_completion_does_not_write_tool_result_store` and flipped its assertion to
`assert_not_called()`, but left the `_make_ctx()` mock setup in place). This doc performs the
FURTHER cleanup that H-7 requires: since `_make_ctx()` builds a `SimpleNamespace` (not a
`MagicMock`), removing the `tool_result_store` field means `ctx.tool_result_store` raises
`AttributeError` on access — the H-4 test's `assert_not_called()` check must be deleted, not just
its target renamed, because there is no longer any attribute to assert against.

**Out of scope**: every other test in this file — none reference `tool_result_store`.

## Assumptions

1. `_make_ctx()` builds a plain `SimpleNamespace`, confirmed by its current implementation:

   ```python
   def _make_ctx(history: list | None = None):
       """Minimal AgentContext mock for partial completion tests."""
       if history is None:
           history = []
       llm = SimpleNamespace(stat_partial_completions=0)
       services = SimpleNamespace(llm=llm)
       session = SimpleNamespace(session_id="test-sess-1")
       stats = SimpleNamespace(stat_turns=1)

       tool_result_store = MagicMock()
       tool_result_store.store = MagicMock()

       conv = SimpleNamespace(history=history)

       return SimpleNamespace(
           session=session,
           stats=stats,
           services_required=services,
           tool_result_store=tool_result_store,
           conv=conv,
       )
   ```

   Unlike `MagicMock`-based `ctx` objects used elsewhere in the test suite, a `SimpleNamespace`
   does not auto-create missing attributes — removing the `tool_result_store=...` keyword
   argument means any code path reading `ctx.tool_result_store` raises `AttributeError`, exactly
   mirroring the real post-H-7 `AgentContext` shape.

## Implementation

### Target file

`tests/test_llm_partial_completion.py`

### Procedure

#### Step 1: Remove `tool_result_store` from `_make_ctx()`

Replace the function with:

```python
def _make_ctx(history: list | None = None):
    """Minimal AgentContext mock for partial completion tests."""
    if history is None:
        history = []
    llm = SimpleNamespace(stat_partial_completions=0)
    services = SimpleNamespace(llm=llm)
    session = SimpleNamespace(session_id="test-sess-1")
    stats = SimpleNamespace(stat_turns=1)
    conv = SimpleNamespace(history=history)

    return SimpleNamespace(
        session=session,
        stats=stats,
        services_required=services,
        conv=conv,
    )
```

`MagicMock` may become unused in this file if no other test needs it — check with
`grep -n "MagicMock" tests/test_llm_partial_completion.py` and remove the import
(`from unittest.mock import MagicMock`) if this was the only use.

#### Step 2: Remove the test that asserted on the now-nonexistent attribute

Remove the test added by the H-4 doc:

```python
def test_partial_completion_does_not_write_tool_result_store() -> None:
    """H-4: partial-completion persistence is limited to session_diagnostics."""
    from agent.llm_transport_errors import handle_partial_completion

    ctx = _make_ctx()
    e = _make_transport_error(partial_text="partial output")
    handle_partial_completion(e, ctx, _make_diagnostic_store())
    ctx.tool_result_store.store.assert_not_called()
```

Remove this function entirely (there is no attribute left to assert `assert_not_called()` on —
attempting to access `ctx.tool_result_store` on the updated `SimpleNamespace` raises
`AttributeError` before the assertion is even reached). No replacement test is needed: the
absence of the field itself, combined with `handle_partial_completion()` no longer referencing
`ctx.tool_result_store` anywhere (per its own H-4/H-7 source docs), is a stronger guarantee than
any mock-based assertion could provide — if the source code ever re-added a
`ctx.tool_result_store` read, EVERY test in this file would fail with `AttributeError` rather
than just one, since `_make_ctx()` is the shared fixture for the whole file.

### Method

- `_make_ctx()`: remove the `MagicMock` setup and the `tool_result_store=...` keyword argument.
- Delete the one test function added by the H-4 doc; do not rename or repurpose it further.

### Details

- All other tests in this file (`test_partial_completion_does_not_append_to_history`,
  `test_partial_completion_empty_history_stays_empty`,
  `test_partial_completion_writes_session_diagnostics`,
  `test_partial_completion_calls_save_partial_completion`,
  `test_partial_completion_increments_stat`, `test_non_partial_error_*`,
  `test_handle_llm_transport_error_routes_*`) do not reference `tool_result_store` and are
  unaffected by this change.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Lint | `ruff check tests/test_llm_partial_completion.py` | 0 errors (no unused `MagicMock` import if it was the only use) |
| Type check | `mypy tests/test_llm_partial_completion.py` | no new errors |
| Grep (field gone) | `grep -n "tool_result_store" tests/test_llm_partial_completion.py` | no matches |
| Tests (targeted) | `uv run pytest tests/test_llm_partial_completion.py -v` | all remaining tests pass |
| Tests (full) | `uv run pytest -v` | no new failures once all H-7 docs are applied together |
| Pre-commit | `pre-commit run --all-files` | pass |
