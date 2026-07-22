# Implementation procedure: `tests/agent/services/test_mcp_tool_discovery.py` (`enabled_for_llm` coverage)

Source plan: `plans/done/20260721-032809_plan.md` ("Fix `enabled_for_llm` never being set True
for discovered tools"), Implementation step 2.

**Filename check — not a duplicate of prior docs**: `implementations/done/` already contains 4
docs targeting this same file (`20260717-203931`, `20260717-224812`, `20260718-084145`,
`20260718-084859`), from the earlier plan cycle that designed/built the test module itself.
Direct grep of the current real test file confirms zero occurrences of `enabled_for_llm`
(`grep -c enabled_for_llm tests/agent/services/test_mcp_tool_discovery.py` → `0`) — no existing
test asserts anything about this field. This doc is not a duplicate.

## Goal

Add unit test coverage proving `McpToolDiscoveryService.discover_all()` derives
`RuntimeTool.enabled_for_llm` from each `/v1/tools` entry's `enabled` key
(`entry.get("enabled", True)`), covering: key absent → `True`; `"enabled": true` → `True`;
`"enabled": false` → `False`.

## Scope

**In scope**
- `tests/agent/services/test_mcp_tool_discovery.py` — add test cases to (or a new test class
  alongside) `TestDiscoverAllHappyPath`.

**Out of scope**
- The production fix itself — tracked in `implementations/20260721-162943_mcp_tool_discovery.py.md`.
  This test doc's cases will fail until that fix lands (or, if implemented first, must be run
  after it to confirm green).
- The end-to-end integration test through `RuntimeToolRegistry`/`_filter_disabled_tool_definitions()`
  — tracked separately in `implementations/{ts}_test_runtime_tool_routing_integration.py.md`.

## Assumptions

1. The existing mocking pattern in this file is reusable as-is: `_async_result()` /  `_resp()` /
   `_server()` / `_make_ctx()` helpers (lines 42-71) and the `AsyncMock(spec=httpx.AsyncClient)` +
   `_make_ctx({key: _server()}, http)` pattern used throughout `TestDiscoverAllHappyPath`
   (lines 77-135). No new fixture infrastructure is needed.
2. `result.registry.get(name)` (used throughout existing tests, e.g. line 100) is the correct way
   to fetch the built `RuntimeTool` and assert on `.enabled_for_llm`.
3. Per the source plan's own verification, no server currently sends `"enabled"` as anything but
   a JSON boolean — but this test suite should still cover the boundary cases the fix explicitly
   handles (key absent vs. explicit `true`/`false`), not a non-bool value (that is the concern of
   the separate, optional `_validate_and_normalize_entry()` type-check doc, not this test file).

## Implementation

### Target file

`tests/agent/services/test_mcp_tool_discovery.py` (existing).

### Procedure

1. Add a new test class `TestDiscoverAllEnabledForLlm` after `TestDiscoverAllHappyPath` (after
   line 135), following the existing class-per-concern layout used throughout this file
   (`TestDiscoverAllMalformedEntries`, `TestDiscoverAllUnreachableServers`, etc.).
2. Add three test methods to it, each following the existing
   `http = AsyncMock(...); http.get = _async_result(_resp(200, {...})); ctx = _make_ctx(...);
   result = await McpToolDiscoveryService(ctx).discover_all()` shape used by every existing test
   in this file:
   - `test_enabled_key_absent_defaults_to_true`: entry has no `"enabled"` key at all → assert
     `result.registry.get(<name>).enabled_for_llm is True`.
   - `test_enabled_true_stays_visible`: entry has `"enabled": True` → assert `.enabled_for_llm is
     True`.
   - `test_enabled_false_hides_tool_from_llm`: entry has `"enabled": False` (optionally with a
     `"disabled_reason"` string alongside it, mirroring the 4 real servers that emit this schema)
     → assert `.enabled_for_llm is False`, while also asserting the tool is still present in
     `result.registry.all_tools()` (i.e. it is excluded from the *LLM payload*, not from the
     registry entirely — a distinct concept from the duplicate-exclusion tests elsewhere in this
     file).

### Method

Plain `pytest` test class, mirroring the file's existing style (async test methods decorated
`@pytest.mark.asyncio`, no new fixtures/classes beyond the test class itself).

### Details

Pseudocode sketch (no production code — test code only, write directly per this file's existing
patterns):

```python
class TestDiscoverAllEnabledForLlm:
    @pytest.mark.asyncio
    async def test_enabled_key_absent_defaults_to_true(self) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _async_result(
            _resp(200, {"tools": [{"name": "grep", "description": "d", "inputSchema": {}}]})
        )
        ctx = _make_ctx({"srv": _server()}, http)

        result = await McpToolDiscoveryService(ctx).discover_all()

        assert result.registry.get("grep").enabled_for_llm is True

    @pytest.mark.asyncio
    async def test_enabled_true_stays_visible(self) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _async_result(
            _resp(
                200,
                {
                    "tools": [
                        {
                            "name": "read_file",
                            "description": "d",
                            "inputSchema": {},
                            "enabled": True,
                        }
                    ]
                },
            )
        )
        ctx = _make_ctx({"srv": _server()}, http)

        result = await McpToolDiscoveryService(ctx).discover_all()

        assert result.registry.get("read_file").enabled_for_llm is True

    @pytest.mark.asyncio
    async def test_enabled_false_hides_tool_from_llm(self) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _async_result(
            _resp(
                200,
                {
                    "tools": [
                        {
                            "name": "delete_file",
                            "description": "d",
                            "inputSchema": {},
                            "enabled": False,
                            "disabled_reason": "feature flag off",
                        }
                    ]
                },
            )
        )
        ctx = _make_ctx({"srv": _server()}, http)

        result = await McpToolDiscoveryService(ctx).discover_all()

        tool = result.registry.get("delete_file")
        assert tool.enabled_for_llm is False
        # still present in the registry (routing-visible); only LLM-payload visibility is gated
        assert "delete_file" in {t.name for t in result.registry.all_tools()}
```

## Validation plan

| Check | Command | Target |
|---|---|---|
| Targeted unit tests | `uv run pytest tests/agent/services/test_mcp_tool_discovery.py -v` | all pass, including the 3 new cases above |
| Full suite | `uv run pytest -q` | no new failures |
| Lint/format | `uv run ruff format tests/ && uv run ruff check tests/` | 0 errors |
| Type check | `uv run mypy scripts/` (per `rules/coding.md`, `mypy` targets `scripts/`; `tests/` is covered by pre-commit's mypy run per `rules/coding.md`'s mypy note) | no new errors |
| Pre-commit | `uv run pre-commit run --all-files` | pass |
| Diff-scoped coverage | `uv run coverage run -m pytest tests/ && uv run coverage xml && uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | ≥ 90% on changed lines (test-only file, trivially covered by running the new tests) |
