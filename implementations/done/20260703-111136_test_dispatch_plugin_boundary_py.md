## Goal

Create `tests/test_dispatch_plugin_boundary.py` with 7 pytest-asyncio test cases that verify the word-boundary dispatch behavior of `CommandRegistry._dispatch_plugin()` after the fix in Step 1.

## Scope

- In-Scope:
  - New file `tests/test_dispatch_plugin_boundary.py`
  - `TestDispatchPluginBoundary` class with 7 test methods covering the scenarios specified in the plan
  - An `autouse` fixture that calls `plugin_registry._reset_for_testing()` before and after each test
- Out-of-Scope:
  - Modifications to `test_plugin_registry.py`, `test_cmd_plugins.py`, or `test_command_registry_consistency.py`
  - Testing built-in `dispatch()` — already tested elsewhere
  - Testing plugin tool or pipeline stage registration

## Assumptions

1. `shared.plugin_registry._reset_for_testing()` clears the command registry and is safe to call as a pytest fixture, as confirmed by its use in `tests/test_plugin_registry.py` (lines 20-24).
2. `plugin_registry.register_command(name, prefix=True/False)` is the correct API for registering plugin commands in tests, as used throughout `test_plugin_registry.py`.
3. `plugin_registry.iter_commands()` returns `dict[str, tuple[Callable, bool]]`; iterating it in `_dispatch_plugin()` will reflect commands registered via `register_command()`.
4. `CommandRegistry` can be instantiated with a mock `AgentContext` and `OutputPort` for unit testing; however, since `_dispatch_plugin()` only uses `self._ctx` when calling the handler, and the handlers in this test will capture args without touching `ctx`, a `MagicMock` context is sufficient.
5. `pytest-asyncio` is available in the test environment (it is used throughout the test suite, e.g., `test_plugin_registry.py` line 431).

## Implementation

### Target file

`/home/masaos/llmagent/tests/test_dispatch_plugin_boundary.py`

### Procedure

1. Create the new file `/home/masaos/llmagent/tests/test_dispatch_plugin_boundary.py`.
2. Add module-level imports: `from __future__ import annotations`, `import pytest`, `import shared.plugin_registry as plugin_registry`, and import `CommandRegistry` from `agent.commands.registry`.
3. Add a mock `AgentContext` (use `unittest.mock.MagicMock`) for the `CommandRegistry` constructor, and a minimal `OutputPort` stub or `MagicMock`.
4. Write the `autouse` fixture `reset_registry` that calls `plugin_registry._reset_for_testing()` before and after each test (see pattern in `test_plugin_registry.py` lines 19-24).
5. Write the `TestDispatchPluginBoundary` class with `@pytest.mark.asyncio` on each async test method.
6. In a setup helper or directly in each test, register two commands:
   - `/foo` with `prefix=True` — a sync or async handler that records `(ctx, args)` into a `captured` dict.
   - `/exact` with `prefix=False` (default) — a handler that records invocation.
7. Implement the 7 test scenarios as separate `async def test_*` methods:

   | Test method name | Input to `_dispatch_plugin` | Expected return | Expected args |
   |---|---|---|---|
   | `test_prefix_exact_match` | `/foo` | `True` | `""` |
   | `test_prefix_with_space_args` | `/foo bar` | `True` | `"bar"` |
   | `test_prefix_with_extra_spaces` | `/foo  bar` | `True` | `"bar"` (stripped) |
   | `test_prefix_false_positive_guard` | `/foobar` | `False` | not called |
   | `test_exact_command_match` | `/exact` | `True` | handler invoked |
   | `test_exact_command_with_trailing_text` | `/exact bar` | `False` | not called |
   | `test_unknown_command` | `/unknown` | `False` | not called |

8. For each test that expects `True`, also assert the handler was called with the expected `args`.
9. For each test that expects `False`, assert the handler was NOT called.

### Method

- Directly call `await registry._dispatch_plugin(line)` rather than going through the public `dispatch()` method, to isolate `_dispatch_plugin()` specifically.
- Use a `captured: dict` in the outer test scope (or closure) to record handler invocations — same pattern as `ran: dict[str, bool]` in `test_plugin_registry.py` line 503.
- `plugin_registry.register_command` with `prefix=True` registers a prefix command; `prefix=False` (default) registers an exact-match command.
- Handler signature: `def handler(ctx: object, args: str) -> None` (sync handlers are fine; `asyncio.iscoroutinefunction` handles sync vs async in `_dispatch_plugin`).
- `CommandRegistry.__init__` validates all entries in `_COMMANDS` have matching handler methods — this is fine because plugin commands are in `plugin_registry`, not `_COMMANDS`; instantiation will succeed with a valid `AgentContext` mock.

### Details

- **Import path for `CommandRegistry`:** `from agent.commands.registry import CommandRegistry`
- **Import path for `plugin_registry`:** `import shared.plugin_registry as plugin_registry`
- **`_reset_for_testing()` fixture pattern** (from `test_plugin_registry.py` lines 19-24):
  ```python
  @pytest.fixture(autouse=True)
  def reset_registry():
      plugin_registry._reset_for_testing()
      yield
      plugin_registry._reset_for_testing()
  ```
- **`CommandRegistry` instantiation:** `CommandRegistry` requires an `AgentContext` and validates `_COMMANDS` handlers; use `MagicMock(spec=AgentContext)` (or a fully stubbed context). Since `_dispatch_plugin` does not call `self._out` and does not access `self._ctx` unless the handler does, a `MagicMock()` with no spec is also acceptable.
- **`_dispatch_plugin` call:** `result = await registry._dispatch_plugin("/foo bar")`
- **Captured args pattern:**
  ```python
  captured: dict[str, str] = {}
  @plugin_registry.register_command("/foo", prefix=True)
  def foo_handler(ctx: object, args: str) -> None:
      captured["args"] = args
  ```
- **Test structure example:**
  ```python
  async def test_prefix_with_extra_spaces(self, registry):
      captured: dict[str, str] = {}
      @plugin_registry.register_command("/foo", prefix=True)
      def foo_handler(ctx: object, args: str) -> None:
          captured["args"] = args
      result = await registry._dispatch_plugin("/foo  bar")
      assert result is True
      assert captured["args"] == "bar"
  ```
- Use a `@pytest.fixture` for `registry` that returns a fresh `CommandRegistry(MagicMock(), MagicMock())` — or instantiate inline per test.
- **Note on `CommandRegistry.__init__` guard:** it iterates `_COMMANDS` checking `hasattr(self, cmd.handler)`. All `_COMMANDS` handlers are defined via mixins, so instantiation will succeed as long as a real `CommandRegistry` object is constructed (not a mock). Pass a `MagicMock()` as the `ctx` argument.

## Validation plan

- Run the new test file: `uv run pytest tests/test_dispatch_plugin_boundary.py -v` — all 7 test cases must be green.
- Run full suite: `uv run pytest` — zero failures, zero new errors.
- Confirm no import errors: `uv run python -c "from tests.test_dispatch_plugin_boundary import *"` (optional smoke check).
