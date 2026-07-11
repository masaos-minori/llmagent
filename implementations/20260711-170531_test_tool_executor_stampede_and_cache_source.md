# Implementation: regression + gap tests for stampede-exception fix and cache-hit `source` contract

Source plan: `plans/20260711-170140_plan.md` (Phase 2).

## Goal

Add regression and gap-coverage tests to `tests/test_tool_executor.py` proving:
1. The Phase 1 exception-hang fix actually releases concurrent waiters instead of hanging.
2. `_inflight` is cleaned up even when `_raw_execute()` raises.
3. Calling an unknown tool name raises `ValueError` (the concrete, deterministic exception
   path used to exercise the fix).
4. The existing cache-hit test also asserts `result.source == ""`, proving the already-correct
   `ToolCallResult.source` contract for cache/error paths (per `shared/transport_dto.py`'s
   docstring) is covered by an explicit assertion.

## Scope

**In-Scope:**
- `tests/test_tool_executor.py`:
  - Add `test_raw_execute_exception_releases_concurrent_waiter` (new).
  - Add `test_inflight_cleaned_up_after_exception` (new).
  - Add `test_unknown_tool_raises_value_error` (new).
  - Add `assert result.source == ""` to the existing
    `test_cache_hit_no_health_registry_update` (line 683-698).

**Out-of-Scope:**
- No production code changes — this doc assumes Phase 1's fix
  (`implementations/20260711-170503_tool_executor_stampede_exception_fix.md`) is applied first,
  since these tests validate that fix.
- No changes to `tests/shared/test_tool_executor_stampede.py` (a separate, pre-existing test
  file with similar-but-not-identical stampede tests) — this plan's target file is
  `tests/test_tool_executor.py` specifically, not the `tests/shared/` variant.
- No changes to `tests/test_tool_cache.py` (covered by a separate implementation doc for
  Phase 3).

## Assumptions

1. `tests/test_tool_executor.py::test_cache_hit_no_health_registry_update` (lines 683-698),
   confirmed by direct read, already asserts `result.request_id == ""` and
   `registry.get_state("file_read") == McpServerHealthState.HEALTHY`, but has no assertion on
   `result.source` — this is a gap to close, not a behavior change.
2. `ToolExecutor._raw_execute()` (`tool_executor.py:247-289`) raises `ValueError` when
   `self._resolver.resolve(tool_name)` is called with a tool name absent from `ToolRegistry` —
   confirmed by direct read, uncaught by `_raw_execute()` itself. This is the simplest
   deterministic exception path available to construct the two hang/cleanup tests without
   needing a mock that raises arbitrary exceptions, though a mock is also an option (see
   Method).
3. A test file `tests/shared/test_tool_executor_stampede.py` already exists (confirmed by
   `find`) with tests like `test_concurrent_exception_both_receive_exception` and
   `test_inflight_cleaned_up_on_exception` using a mocked `_raw_execute` that raises
   `RuntimeError`. This plan's new tests in `tests/test_tool_executor.py` are additional
   coverage in the plan's specifically-named target file, using the naming and structure given
   in the plan's Design section — some overlap in what is exercised is acceptable and expected
   (different test file, different exact assertions: this plan requires a hang-guard via
   `asyncio.wait_for` and an unknown-tool `ValueError` variant not present in the other file).
4. `pytest-asyncio` is configured with `asyncio_mode = "auto"` (confirmed via existing async
   test patterns in the codebase) — no `@pytest.mark.asyncio` decorator strictly required, but
   match the existing file's convention by checking how neighboring async tests in
   `tests/test_tool_executor.py` are declared before writing these.
5. `_make_executor()` (or equivalent existing helper in `tests/test_tool_executor.py`) already
   constructs a usable `ToolExecutor` instance for tests — reuse it rather than duplicating
   construction logic.

## Implementation

### Target file

`tests/test_tool_executor.py`

### Procedure

1. Read the existing helper(s) in `tests/test_tool_executor.py` used to construct a
   `ToolExecutor` (e.g. `_make_executor()`) and the existing async test declaration convention.
2. Add `test_unknown_tool_raises_value_error`: call
   `ex._raw_execute("totally_unknown_tool", {})` and assert it raises `ValueError` matching
   "Unknown tool" (or the actual message substring used by `self._resolver.resolve()` —
   confirm exact wording by reading `route_resolver.py`'s `resolve()` before writing the
   `match=` regex).
3. Add `test_inflight_cleaned_up_after_exception`: patch/stub `ex._raw_execute` to raise
   (either the unknown-tool path or a direct mock raising `RuntimeError`/`ValueError`), call
   `_execute_with_stampede_protection(cache_key, tool_name, args)` inside
   `pytest.raises(...)`, then assert `cache_key not in ex._inflight`.
4. Add `test_raw_execute_exception_releases_concurrent_waiter`: use deterministic sequencing
   (an `asyncio.Event` that the mocked/stubbed `_raw_execute` waits on before raising, set only
   after a second concurrent caller has already retrieved the shared `inflight` Future via
   `self._inflight.get(cache_key)`), start two concurrent
   `_execute_with_stampede_protection()` calls for the same `cache_key` via `asyncio.gather`,
   and assert both raise the propagated exception. Wrap the whole test body in
   `asyncio.wait_for(..., timeout=<short value, e.g. 1.0-2.0s>)` so a regression of the Phase 1
   fix fails the test loudly via `TimeoutError` instead of hanging the suite.
5. Add `assert result.source == ""` as a new line inside the existing
   `test_cache_hit_no_health_registry_update` test body, immediately after the existing
   `assert result.request_id == ""` line.
6. Run lint, type check, and the targeted test file per Validation plan below.

### Method

Test signatures (from the plan's Design section, adapted to this file's existing conventions —
confirm exact decorator/import style against neighboring tests before finalizing):

```python
async def test_raw_execute_exception_releases_concurrent_waiter(self) -> None:
    """A second caller awaiting the same inflight future must see the exception, not hang."""
    ex = _make_executor()
    # Use an asyncio.Event to sequence: stub _raw_execute waits on the event before
    # raising; the event is set only after the second caller has retrieved the shared
    # inflight Future. Run both callers via asyncio.gather(..., return_exceptions=True)
    # or two pytest.raises-guarded calls, wrapped in asyncio.wait_for(timeout=...).
    ...

async def test_inflight_cleaned_up_after_exception(self) -> None:
    """cache_key must be removed from self._inflight even when _raw_execute raises."""
    ex = _make_executor()
    with pytest.raises(Exception):  # noqa: <justify narrowing to the actual raised type>
        await ex._execute_with_stampede_protection(cache_key, tool_name, args)
    assert cache_key not in ex._inflight

async def test_unknown_tool_raises_value_error(self) -> None:
    ex = _make_executor()
    with pytest.raises(ValueError, match="Unknown tool"):
        await ex._raw_execute("totally_unknown_tool", {})
```

Existing test update (`test_cache_hit_no_health_registry_update`):
```python
result = await ex._execute_with_cache("read_text_file", {})

assert result.request_id == ""
assert result.source == ""
assert ex.stat_cache_hits == 1
assert registry.get_state("file_read") == McpServerHealthState.HEALTHY
```

### Details

- Use a concrete exception type (not a bare `Exception`) in `pytest.raises(...)` wherever the
  raised type is known/controlled, per this codebase's general preference for narrow,
  intentional assertions; if `pytest.raises(Exception)` is used because the test intentionally
  covers "any exception type", add an inline comment explaining that choice (mirrors the
  production code's own `except Exception` justification).
- The hang-guard test (`test_raw_execute_exception_releases_concurrent_waiter`) must not rely
  on real scheduler timing/sleeps for correctness — use the `asyncio.Event` sequencing
  described in the plan's Risks table to make the test deterministic, not flaky.
- Do not remove or modify any other existing test in the file; these are additive changes only
  plus the single new assertion line.

## Validation plan

Filtered to checks relevant to this file, per the plan's Validation plan table:

| Check | Tool | Target |
|---|---|---|
| Lint | `uv run ruff check tests/test_tool_executor.py` | 0 errors |
| Type check | `uv run mypy scripts/shared/tool_executor.py` (tests dir covered by pre-commit mypy run per `rules/coding.md`) | No new errors |
| Tests | `uv run pytest tests/test_tool_executor.py -v` | All pass, including the 3 new tests and the updated cache-hit test |
| Concurrency hang guard | `test_raw_execute_exception_releases_concurrent_waiter` wrapped in `asyncio.wait_for(..., timeout=...)` | Test fails loudly (timeout) rather than hanging the whole suite if the Phase 1 fix regresses |
| Regression | `uv run pytest tests/test_tool_executor_routing.py tests/test_rag_tools_consistency.py -q` | No new failures |
