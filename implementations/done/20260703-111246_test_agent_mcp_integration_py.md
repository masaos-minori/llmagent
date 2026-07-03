## Goal

Refactor `test_a11_plugin_tool_error_does_not_propagate` to register the failing tool via `register_tool()` decorator and clean up via `_reset_for_testing()`, eliminating direct mutation of the private `plugin_registry._tools` dict.

## Scope

- In-Scope:
  - Rewrite the body of `test_a11_plugin_tool_error_does_not_propagate` to use `plugin_registry._reset_for_testing()` + `plugin_registry.register_tool()` for setup, and `plugin_registry._reset_for_testing()` for teardown (or a local autouse fixture in the test or in `tests/integration/conftest.py`).
  - Add `import shared.plugin_registry as plugin_registry` at module level (currently the import is inline inside the test function at line 161).
- Out-of-Scope:
  - Any other test in the file.
  - The `tests/integration/conftest.py` file beyond adding an optional autouse fixture for registry isolation.
  - Changes to `ToolExecutor` or `plugin_registry` logic.

## Assumptions

1. The current implementation at line 163 directly assigns to `plugin_registry._tools["_test_failing_plugin"]`, bypassing the `register_tool()` type-hint contract; the refactored version must satisfy the `tuple[str, bool]` return type annotation requirement enforced by `register_tool()`.
2. The tool must still raise `RuntimeError("exploded")` when called, so the handler must be declared as `async def` and raise inside. A lambda generator expression (`lambda args: (_ for _ in ()).throw(...)`) cannot be registered via `register_tool()` due to the type annotation contract — use `async def` instead.
3. Since the failing handler raises before returning, it cannot have a valid `tuple[str, bool]` return in practice, but the type annotation on the function must still be `-> tuple[str, bool]` to pass `register_tool()`'s static check at decoration time. The runtime raise makes the annotation moot.
4. No other test in `tests/integration/test_agent_mcp_integration.py` currently manipulates the plugin registry, so a module-scoped autouse fixture in `conftest.py` is not necessary but may be added for defense-in-depth.
5. After the refactor, `plugin_registry._tools` must not be referenced in the test file (confirmed by grep result showing only lines 163 and 172).

## Implementation

### Target file

`/home/masaos/llmagent/tests/integration/test_agent_mcp_integration.py`

### Procedure

1. Add `import shared.plugin_registry as plugin_registry` to the module-level imports (after the existing imports at lines 16-20).
2. Replace the inline `from shared import plugin_registry` import inside `test_a11` (line 161) with nothing (the module-level import suffices).
3. Rewrite `test_a11_plugin_tool_error_does_not_propagate` body as follows:
   ```python
   @pytest.mark.asyncio
   async def test_a11_plugin_tool_error_does_not_propagate():
       plugin_registry._reset_for_testing()
       try:
           @plugin_registry.register_tool("_test_failing_plugin")
           async def _failing_handler(args: dict) -> tuple[str, bool]:
               raise RuntimeError("exploded")

           async with httpx.AsyncClient() as http:
               executor = _make_http_executor(http)
               result = await executor.execute("_test_failing_plugin", {})

           assert result.is_error
           assert "plugin error" in result.output
       finally:
           plugin_registry._reset_for_testing()
   ```
4. Verify `plugin_registry._tools` no longer appears anywhere in the file.
5. Run the targeted test.

### Method

- Use `try/finally` for guaranteed cleanup even on assertion failure.
- The `@plugin_registry.register_tool()` decorator validates the `-> tuple[str, bool]` annotation at decoration time; the function body raises before any return, satisfying test intent.
- The `_make_http_executor` function uses `discovery_map={_HTTP_TOOL: _HTTP_KEY}`, so `"_test_failing_plugin"` falls through to `plugin_registry.get_tool()` (plugin path) rather than MCP routing — this is the intended execution path.

### Details

- Current lines 159-175 are the entire `test_a11` function.
- The `_make_http_executor` at line 27 creates a `ToolExecutor` with `server_configs={_HTTP_KEY: cfg}` and `discovery_map={_HTTP_TOOL: _HTTP_KEY}`. The tool name `"_test_failing_plugin"` is not in `discovery_map`, so `ToolExecutor.execute()` checks `plugin_registry.get_tool()` first — confirmed by the production code path in `tool_executor.py`.
- After cleanup: `grep -n 'plugin_registry\._tools' tests/integration/test_agent_mcp_integration.py` must return empty.

## Validation plan

```bash
# Confirm _tools direct mutation is gone
grep -n 'plugin_registry\._tools' /home/masaos/llmagent/tests/integration/test_agent_mcp_integration.py

# Run the specific test
uv run pytest tests/integration/test_agent_mcp_integration.py::test_a11_plugin_tool_error_does_not_propagate -v

# Run full integration test file
uv run pytest tests/integration/test_agent_mcp_integration.py -v
```

Expected: first grep returns empty; `test_a11` passes; full integration suite passes.
