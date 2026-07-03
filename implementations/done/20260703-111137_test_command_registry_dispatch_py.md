## Goal

Add a parametrized async test that verifies `CommandRegistry.dispatch()` passes stripped args to prefix command handlers, covering both built-in and plugin dispatch paths.

## Scope

- In-Scope:
  - New file `tests/test_command_registry_dispatch.py` containing `test_dispatch_strips_args` parametrized async test
  - Test cases: built-in prefix command with leading space (e.g., `/db help`), built-in prefix command with no trailing input (e.g., `/mcp`), and plugin prefix command with extra whitespace
- Out-of-Scope:
  - Modifying `tests/test_command_registry_consistency.py` (existing handler-signature tests are unrelated)
  - Testing exact-match (non-prefix) commands
  - Testing plugin command registration side-effects

## Assumptions

1. `pytest-asyncio` is available in the test environment (existing async tests in the project use it).
2. The `CommandRegistry` fixture from `test_command_registry_consistency.py` pattern (MagicMock ctx + SimpleNamespace out) is the correct way to instantiate the registry in isolation.
3. To intercept the handler invocation, it is sufficient to monkeypatch a `_cmd_*` method on the registry instance before calling `dispatch()`.
4. Plugin command dispatch is testable by registering a mock handler via `plugin_registry.register()` and then deregistering/resetting after the test.
5. `asyncio_mode = "auto"` or `@pytest.mark.asyncio` decorator is the correct way to run async tests (follow the existing project convention found in other test files).

## Implementation

### Target file

`/home/masaos/llmagent/tests/test_command_registry_dispatch.py`

### Procedure

1. Create `tests/test_command_registry_dispatch.py`.
2. Add imports:
   ```python
   from __future__ import annotations
   import pytest
   from types import SimpleNamespace
   from unittest.mock import AsyncMock, MagicMock, patch
   from agent.commands.registry import CommandRegistry
   ```
3. Define a `registry` pytest fixture identical to the one in `test_command_registry_consistency.py` (MagicMock ctx, SimpleNamespace out).
4. Add the built-in prefix test cases as a parametrized async test:
   ```python
   @pytest.mark.parametrize(
       "input_line, expected_args",
       [
           ("/db help", "help"),         # leading space stripped
           ("/db  help", "help"),        # two spaces stripped
           ("/mcp", ""),                 # exact prefix match, empty args
           ("/db", ""),                  # exact prefix match, empty args
       ],
   )
   @pytest.mark.asyncio
   async def test_builtin_dispatch_strips_args(
       registry: CommandRegistry,
       input_line: str,
       expected_args: str,
   ) -> None:
   ```
   Inside the test body:
   - Use `patch.object(registry, handler_name, new_callable=AsyncMock)` for the relevant handler.
   - Call `await registry.dispatch(input_line)`.
   - Assert the mock was called with `expected_args` as the sole positional argument.
5. Add a plugin prefix test case:
   ```python
   @pytest.mark.asyncio
   async def test_plugin_dispatch_strips_args(registry: CommandRegistry) -> None:
   ```
   Inside the test body:
   - Create an `AsyncMock` handler.
   - Register it via `plugin_registry.register("/myplugin", handler, is_prefix=True)`.
   - Call `await registry.dispatch("/myplugin  value")`.
   - Assert handler was called and `args` argument equals `"value"` (not `"  value"`).
   - Unregister or reset `plugin_registry` in a `finally` block to avoid test pollution.
6. Determine correct pytest-asyncio mode by checking project `pyproject.toml` or `pytest.ini` for `asyncio_mode` setting; apply matching decorator or config.

### Method

- `patch.object(registry, "_cmd_db", new_callable=AsyncMock)` patches the bound method on the instance.
- `mock.assert_called_once_with("help")` verifies the exact args value passed.
- For the plugin test, inspect `plugin_registry` API used elsewhere in the test suite (e.g., `tests/test_plugin_registry.py`) to confirm the `register` / deregister method signatures.
- `asyncio.iscoroutinefunction` check inside `dispatch()` means the mock must be a coroutine function; `AsyncMock` satisfies this automatically.

### Details

- Identify which handler name to patch for `/db` by inspecting `_COMMANDS` in `command_defs_list.py` — look for `CommandDef("/db", True, True, "<handler_name>", ...)` to get the `is_async=True` prefix handler name.
- For `/mcp` exact-match vs. prefix: verify in `_COMMANDS` whether `/mcp` is a prefix command or exact-match; adjust test case accordingly (if exact-match, it has no `args` parameter and is not relevant for the strip test).
- The `plugin_registry` teardown: check if `plugin_registry` has a `clear()` or `unregister()` method; if not, save and restore its internal dict directly.
- Check `pyproject.toml` for `[tool.pytest.ini_options]` `asyncio_mode` to determine whether `@pytest.mark.asyncio` is needed per test or is applied globally.

## Validation plan

| Check | Command | Expected outcome |
|-------|---------|-----------------|
| New test file runs and passes | `uv run pytest tests/test_command_registry_dispatch.py -v` | All new test cases pass |
| Full test suite (no regressions) | `uv run pytest` | All existing tests still pass |
| Ruff lint clean | `uv run ruff check tests/test_command_registry_dispatch.py` | Zero violations |
| mypy type check | `uv run mypy tests/test_command_registry_dispatch.py` | Zero errors |
