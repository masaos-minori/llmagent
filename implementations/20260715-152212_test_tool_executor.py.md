# Implementation Procedure: tests/test_tool_executor.py

Source plan: `plans/20260715-140914_plan.md`

## Prior-doc status

`implementations/done/20260703-111258_test_tool_executor_py.md` and
`implementations/done/20260707-143200_test_tool_executor.py.md` target the
same file but are from unrelated, already-applied past plans (error boundary
classification, stampede-exception-release fix respectively) — neither
addresses cache-bypass routing or cache-hit `server_key`/`source`
attribution. Confirmed against current source (`tests/test_tool_executor.py`,
read in relevant sections): `TestCacheStampede` (lines 33-155) still uses
`write_file` as the tool name in four direct `_execute_with_cache()` /
`_execute_with_stampede_protection()` calls, and
`test_cache_hit_no_health_registry_update` (lines 748-764) still asserts
`result.source == ""` at line 762. Neither this plan's tool-name swap nor its
new bypass/attribution tests exist yet. This document is written fresh.

## Goal

Update the existing cache/stampede tests so they exercise a read-only tool
name (avoiding the misleading appearance of testing cache behavior on a
now-cache-bypassed write tool), update the stale `source == ""` cache-hit
assertion to `source == "cache"`, and add new tests proving: side-effecting
tools bypass the cache on `execute()`, read-only tools still hit the cache,
and cache hits preserve `server_key`.

## Scope

**In scope**
- In `TestCacheStampede` (lines 33-155): change tool name from `"write_file"`
  to `"read_text_file"` in all four direct-call tests
  (`test_concurrent_calls_share_inflight_future`,
  `test_inflight_cleared_after_completion`,
  `test_raw_execute_exception_releases_concurrent_waiter` — uses
  `"test_tool"`, unaffected — `test_inflight_cleaned_up_after_exception` —
  also uses `"test_tool"`, unaffected). Only the two tests that literally pass
  `"write_file"` (lines 58-60, 88) need the swap.
- `test_cache_hit_no_health_registry_update` (line 762): change
  `assert result.source == ""` to `assert result.source == "cache"`.
- Add `test_side_effect_tool_bypasses_cache` — call `execute()` twice with the
  same args on a tool name known to be a side effect (e.g. `"write_file"`),
  using a monkeypatched `_raw_execute` that increments a counter; assert the
  counter is 2 and `self._cache` stays empty.
- Add `test_trigger_workflow_bypasses_cache` and
  `test_fts_rebuild_bypasses_cache` — same shape, proving the three newly
  classified tools from this plan (`rag_delete_document` also covered,
  optionally combined into one parametrized test or kept separate per the
  plan's explicit test names) bypass the cache via `execute()`.
- Add `test_read_text_file_uses_cache` — call `execute()` twice on a read-only
  tool name via a monkeypatched `_raw_execute`; assert the counter stays at 1
  on the second call (cache hit) and `stat_cache_hits` increments.
- Add `test_cache_hit_preserves_server_key` — prime the cache via a mocked
  `_raw_execute` returning a `ToolCallResult` with a non-empty `server_key`,
  call `execute()` twice, assert the second (cached) result's `server_key`
  matches and `source == "cache"`.

**Out of scope**
- No change to `TestHttpTransportRetry` or any other test class in this file
  beyond `TestCacheStampede` and `test_cache_hit_no_health_registry_update`.
- No change to `_make_executor()` helper's signature (used elsewhere in the
  file) unless the new tests need a plugin-free, fully-constructed
  `ToolExecutor` — reuse `_make_executor()` where possible; fall back to
  `ToolExecutor.__new__(ToolExecutor)` + manual attribute setup (matching the
  existing `TestCacheStampede` pattern) when testing `execute()` end-to-end
  requires bypassing plugin lookup deterministically.

## Assumptions

- Depends on `implementations/20260715-152212_tool_executor.py.md` (the
  `is_side_effect` branch in `execute()`),
  `implementations/20260715-152212_tool_executor_helpers.py.md` (widened
  `_SIDE_EFFECT_TOOLS`), and `implementations/20260715-152212_tool_constants.py.md`
  (new write-tool frozensets) all being applied first.
- `write_file` is already in `WRITE_TOOLS` (confirmed in
  `scripts/shared/tool_constants.py`) — it is a side effect both before and
  after this plan, making it a valid, minimal-diff choice for the new
  bypass tests without depending on the plan's newly added frozensets.
- `PluginToolInvoker.try_execute()` returns `None` for all MCP tool names used
  in these tests (confirmed by existing tests already calling `execute()`-
  adjacent methods with plain MCP tool names without mocking the plugin
  invoker) — so `execute()`'s plugin branch is a no-op for these test tool
  names and does not need to be mocked separately.

## Implementation

### Target file

`tests/test_tool_executor.py`

### Procedure

1. In `test_concurrent_calls_share_inflight_future` (line 58-60) and
   `test_inflight_cleared_after_completion` (line 88), change
   `"write_file"` → `"read_text_file"` and the corresponding cache-key
   assertion `"write_file:"` → `"read_text_file:"` (line 90).
2. At line 762, change `assert result.source == ""` to
   `assert result.source == "cache"`.
3. Add the five new test functions/methods (see Details) after
   `TestCacheStampede` or as a new `TestExecuteCacheBypass` class placed
   directly after it (recommended, to keep `execute()`-level tests separate
   from the existing `_execute_with_cache()`-level direct-call tests).

### Method

Direct-call tests (`TestCacheStampede`) keep testing `_execute_with_cache()`/
`_execute_with_stampede_protection()` directly — only their tool-name literal
changes. New tests target `execute()` itself (the public entry point that
now contains the bypass branch), using a monkeypatched `_raw_execute` on a
manually constructed `ToolExecutor.__new__(ToolExecutor)` instance, mirroring
the existing `TestCacheStampede` setup pattern (set `_cache`, `_cache_ttl`,
`_cache_max_size`, `_inflight`, `stat_cache_hits`, `_raw_execute` directly;
additionally set `_plugin_invoker = PluginToolInvoker()` so `execute()`'s
plugin check runs and returns `None` for MCP tool names).

### Details

```python
class TestExecuteCacheBypass:
    def _make_bare_executor(self) -> ToolExecutor:
        executor = ToolExecutor.__new__(ToolExecutor)
        executor._cache = {}
        executor._cache_ttl = 60.0
        executor._cache_max_size = 100
        executor._inflight = {}
        executor.stat_cache_hits = 0
        executor._plugin_invoker = PluginToolInvoker()
        return executor

    @pytest.mark.asyncio
    async def test_side_effect_tool_bypasses_cache(self) -> None:
        call_count = 0

        async def _fake_raw_execute(tool_name: str, args: dict[str, Any]) -> ToolCallResult:
            nonlocal call_count
            call_count += 1
            return ToolCallResult(output="ok", is_error=False, request_id="", server_key="file_write")

        executor = self._make_bare_executor()
        executor._raw_execute = _fake_raw_execute

        await executor.execute("write_file", {"path": "a"})
        await executor.execute("write_file", {"path": "a"})

        assert call_count == 2
        assert executor._cache == {}

    @pytest.mark.asyncio
    async def test_trigger_workflow_bypasses_cache(self) -> None:
        call_count = 0

        async def _fake_raw_execute(tool_name: str, args: dict[str, Any]) -> ToolCallResult:
            nonlocal call_count
            call_count += 1
            return ToolCallResult(output="ok", is_error=False, request_id="", server_key="cicd")

        executor = self._make_bare_executor()
        executor._raw_execute = _fake_raw_execute

        await executor.execute("trigger_workflow", {"workflow": "ci"})
        await executor.execute("trigger_workflow", {"workflow": "ci"})

        assert call_count == 2
        assert executor._cache == {}

    @pytest.mark.asyncio
    async def test_fts_rebuild_bypasses_cache(self) -> None:
        call_count = 0

        async def _fake_raw_execute(tool_name: str, args: dict[str, Any]) -> ToolCallResult:
            nonlocal call_count
            call_count += 1
            return ToolCallResult(output="ok", is_error=False, request_id="", server_key="mdq")

        executor = self._make_bare_executor()
        executor._raw_execute = _fake_raw_execute

        await executor.execute("fts_rebuild", {})
        await executor.execute("fts_rebuild", {})

        assert call_count == 2
        assert executor._cache == {}

    @pytest.mark.asyncio
    async def test_read_text_file_uses_cache(self) -> None:
        call_count = 0

        async def _fake_raw_execute(tool_name: str, args: dict[str, Any]) -> ToolCallResult:
            nonlocal call_count
            call_count += 1
            return ToolCallResult(output="ok", is_error=False, request_id="", server_key="file_read")

        executor = self._make_bare_executor()
        executor._raw_execute = _fake_raw_execute

        await executor.execute("read_text_file", {"path": "a"})
        await executor.execute("read_text_file", {"path": "a"})

        assert call_count == 1
        assert executor.stat_cache_hits == 1

    @pytest.mark.asyncio
    async def test_cache_hit_preserves_server_key(self) -> None:
        async def _fake_raw_execute(tool_name: str, args: dict[str, Any]) -> ToolCallResult:
            return ToolCallResult(
                output="ok", is_error=False, request_id="", server_key="rag_pipeline"
            )

        executor = self._make_bare_executor()
        executor._raw_execute = _fake_raw_execute

        await executor.execute("rag_run_pipeline", {})
        second = await executor.execute("rag_run_pipeline", {})

        assert second.server_key == "rag_pipeline"
        assert second.source == "cache"
```

Notes:
- `rag_run_pipeline` is a read-only RAG tool (in `RAG_TOOLS`, not in
  `RAG_WRITE_TOOLS`), so it is safe to use for the cache-hit attribution test.
- All new tests construct `ToolCallResult` directly rather than mocking
  `PluginToolInvoker.try_execute()` — confirm during implementation that
  `PluginToolInvoker()` with no registered plugins returns `None` for these
  tool names (matches existing `_plugin_invoker` behavior); if not, mock
  `executor._plugin_invoker.try_execute` to return `None` explicitly instead
  of relying on the real class.

## Validation plan

| Check | Command | Expected outcome |
|---|---|---|
| Depends on | `implementations/20260715-152212_tool_executor.py.md`, `implementations/20260715-152212_tool_executor_helpers.py.md`, `implementations/20260715-152212_tool_constants.py.md` applied first | `execute()` has the bypass branch; new frozensets exist |
| Format/lint | `uv run ruff format tests/test_tool_executor.py && uv run ruff check tests/test_tool_executor.py` | 0 errors |
| Type check | `uv run mypy tests/test_tool_executor.py` | 0 new errors |
| Targeted tests | `uv run pytest tests/test_tool_executor.py -v` | All existing (updated) + new tests pass |
| Full suite | `uv run pytest -v` | No new failures |
| Coverage | `uv run coverage run -m pytest tests/ && uv run coverage xml && uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | ≥ 90% on changed lines |
