# Implementation procedure: `tests/test_runtime_tool_routing_integration.py` (end-to-end `enabled_for_llm` regression guard)

Source plan: `plans/done/20260721-032809_plan.md` ("Fix `enabled_for_llm` never being set True
for discovered tools"), Implementation step 3.

**Filename check — not a duplicate of prior docs**: `implementations/done/` already contains 2
docs targeting this same file (`20260720-142433`, `20260720-150343`), from an earlier plan cycle
(RuntimeToolRegistry routing-layer wiring / browser-mcp merge). Direct grep of the current real
file confirms it only ever calls `build_runtime_tool(...)` directly with hand-built fixtures
(`_make_runtime_registry()`, lines 61-98, both explicitly passing `enabled_for_llm=True`) and
never imports or calls `McpToolDiscoveryService`/`discover_all()` (`grep -n
"McpToolDiscoveryService\|discover_all" tests/test_runtime_tool_routing_integration.py` → no
hits). This confirms the exact gap the source plan describes: no test exercises the real
`build_runtime_tool()` call site inside discovery, so this bug class went undetected by all
existing `enabled_for_llm=True` call sites. This doc is not a duplicate.

## Goal

Add an end-to-end regression test that runs the real `McpToolDiscoveryService.discover_all()`
(HTTP mocked, not `build_runtime_tool()` hand-built) through to
`RuntimeToolRegistry.llm_tool_definitions()`, proving a normal discovered tool stays visible to
the LLM and a `"enabled": false` discovered tool does not — the exact chain that the pre-fix bug
broke silently because no test called the real discovery→registry path.

## Scope

**In scope**
- `tests/test_runtime_tool_routing_integration.py` — add one new test class exercising
  `McpToolDiscoveryService.discover_all()` (mocked HTTP) → `RuntimeToolRegistry` →
  `llm_tool_definitions()`.

**Out of scope**
- The production fix itself — tracked in `implementations/20260721-162943_mcp_tool_discovery.py.md`.
  This test must be verified to **fail** against pre-fix code (see Validation plan) — that failure
  is the acceptance criterion proving this test would have caught the original bug.
- `ToolRouteResolver`/`RuntimeToolRegistry.resolve()` — routing is independent of
  `enabled_for_llm`; existing tests in this file already cover routing and are unchanged.
- Any change to `_make_runtime_registry()` or the file's existing hand-built-fixture tests —
  those stay as-is; this is a purely additive new test class.

## Assumptions

1. This file already imports `httpx`, `MagicMock`, `AsyncMock`-equivalent patterns are not yet
   present here (this file uses plain `MagicMock(spec=httpx.AsyncClient)` for `ToolExecutor`
   construction, e.g. `_make_executor()` lines 47-55) — the new test needs its own
   `AsyncMock(spec=httpx.AsyncClient)` with a mocked `.get()`, mirroring the pattern already used
   in `tests/agent/services/test_mcp_tool_discovery.py` (that file's `_async_result()`/`_resp()`
   helpers), not the `MagicMock` pattern used elsewhere in *this* file for `ToolExecutor`.
2. `McpToolDiscoveryService` needs an `AgentContext`-shaped object exposing
   `ctx.cfg.mcp.mcp_servers` (a `dict[str, McpServerConfig]`) and
   `ctx.services_required.http` (the mocked async client) — a `MagicMock()` built ad hoc in the
   new test (mirroring `tests/agent/services/test_mcp_tool_discovery.py::_make_ctx()`) is
   sufficient; this file does not need to import that helper (it lives in a different test
   module/package), a local equivalent is simpler and keeps this file self-contained.
3. `RuntimeToolRegistry.llm_tool_definitions()` (`scripts/shared/runtime_tool_registry.py:85-93`)
   returns `[{"name", "description", "parameters"}, ...]` filtered to `tool.enabled_for_llm`
   entries only — the new test asserts on the set of `"name"` values returned, not on routing
   behavior.
4. Per the source plan's Design §3 and Risks section, this test must be verified to fail against
   the pre-fix code (temporarily revert the 1-line fix in `mcp_tool_discovery.py`, confirm this
   new test fails, then reapply the fix) before being considered a valid regression guard — this
   is a mandatory manual verification sub-step during implementation, not optional.

## Implementation

### Target file

`tests/test_runtime_tool_routing_integration.py` (existing).

### Procedure

1. Add new imports at the top of the file (alongside the existing `shared.runtime_tool`/
   `shared.runtime_tool_registry` imports, lines 20-24): `from unittest.mock import AsyncMock` (in
   addition to the existing `MagicMock` import) and
   `from agent.services.mcp_tool_discovery import McpToolDiscoveryService`.
2. Add a new test class `TestDiscoveryToLlmVisibilityEndToEnd` near the end of the file, after the
   existing test classes.
3. Add a helper (module-level or class-local) building a mocked HTTP client returning a
   `/v1/tools` response with two tool entries: one with no `enabled` key (or `"enabled": true`)
   and one with `"enabled": false`.
4. Add one test method that: builds the mocked `ctx`, runs
   `result = await McpToolDiscoveryService(ctx).discover_all()`, then asserts on
   `result.registry.llm_tool_definitions()`:
   - the visible tool's name is present in the returned definitions.
   - the disabled tool's name is absent from the returned definitions.
   - (optional, strengthens the "real call site" guarantee) also assert
     `result.registry.get(<disabled_name>).enabled_for_llm is False` directly, confirming the
     value came from the real `_dedupe_and_build()`/`build_runtime_tool()` path, not a hand-built
     fixture.

### Method

Plain `pytest` async test class, following this file's existing conventions (`@pytest.mark.asyncio`
is used elsewhere in the repo's async tests; confirm this file's own async test marker style — if
this file currently has no async tests, check `pyproject.toml`'s `asyncio_mode` setting to decide
whether `@pytest.mark.asyncio` is required or implicit).

### Details

Pseudocode sketch (no production code — test code only):

```python
class TestDiscoveryToLlmVisibilityEndToEnd:
    @staticmethod
    def _http_with_tools() -> AsyncMock:
        http = AsyncMock(spec=httpx.AsyncClient)
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {
            "tools": [
                {
                    "name": "visible_tool",
                    "description": "stays visible",
                    "inputSchema": {"type": "object"},
                },
                {
                    "name": "hidden_tool",
                    "description": "explicitly disabled",
                    "inputSchema": {"type": "object"},
                    "enabled": False,
                    "disabled_reason": "config-gated",
                },
            ]
        }
        http.get = AsyncMock(return_value=resp)
        return http

    @pytest.mark.asyncio
    async def test_disabled_discovered_tool_excluded_from_llm_payload(self) -> None:
        http = self._http_with_tools()
        ctx = MagicMock()
        ctx.cfg.mcp.mcp_servers = {
            "srv": McpServerConfig(transport=TransportType.HTTP, url="http://127.0.0.1:9100")
        }
        ctx.services_required.http = http

        result = await McpToolDiscoveryService(ctx).discover_all()

        names = {d["name"] for d in result.registry.llm_tool_definitions()}
        assert "visible_tool" in names
        assert "hidden_tool" not in names
        assert result.registry.get("hidden_tool").enabled_for_llm is False
```

Note: `McpServerConfig`/`TransportType` are already imported at the top of this file (lines
16-19); no new import needed for those two names.

## Validation plan

| Check | Command | Target |
|---|---|---|
| Targeted test | `uv run pytest tests/test_runtime_tool_routing_integration.py -v` | new test passes post-fix |
| Pre-fix failure check (mandatory, per Assumption 4) | temporarily revert the 1-line change in `implementations/20260721-162943_mcp_tool_discovery.py.md`, rerun the same command | new test fails (proves it is a real regression guard); then reapply the fix and rerun to confirm green |
| Full suite | `uv run pytest -q` | no new failures |
| Lint/format | `uv run ruff format tests/ && uv run ruff check tests/` | 0 errors |
| Pre-commit | `uv run pre-commit run --all-files` | pass |
| Diff-scoped coverage | `uv run coverage run -m pytest tests/ && uv run coverage xml && uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | ≥ 90% on changed lines |
