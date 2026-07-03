# Implementation: Create `tests/shared/test_plugin_tool_registration.py`

## Goal

Create a new test file `tests/shared/test_plugin_tool_registration.py` with 6 tests for
plugin registration-time validation, covering:
1. Valid annotation registers successfully
2. Missing annotation raises `ValueError`
3. Wrong annotation type raises `ValueError`
4. Invalid plugin not added to registry after failed registration
5. Non-strict `load_plugins()` records failure and continues
6. Strict mode `load_plugins()` raises `PluginLoadError`

## Scope

- In-Scope: New file `tests/shared/test_plugin_tool_registration.py` with `TestPluginToolRegistration`
  class (6 test methods).
- Out-of-Scope: No changes to production code. `tests/shared/__init__.py` must already exist.

## Assumptions

1. `tests/shared/__init__.py` exists (see `implementations/20260704-073815_tests_shared_init_py.md`).
2. `plugin_registry._reset_for_testing()` is callable for test isolation.
3. `plugin_registry.load_plugins(path, strict_mode=False)` accepts a `Path` and optional
   `strict_mode` keyword argument.
4. `plugin_registry.load_plugins()` returns an object with `.loaded_count` (int) and
   `.failed` (list of objects with `.error` str attribute).
5. `plugin_registry.PluginLoadError` is raised in strict mode when any plugin fails.
6. `plugin_registry.get_tool(name)` returns `None` if the tool is not registered.
7. `uv run pytest` with `asyncio_mode = "auto"` is the test runner.

## Implementation

### Target file

`tests/shared/test_plugin_tool_registration.py` (new file)

### Procedure

1. Create `tests/shared/test_plugin_tool_registration.py` with the content below.
2. Run `uv run ruff format tests/shared/test_plugin_tool_registration.py`.
3. Run `uv run ruff check tests/shared/test_plugin_tool_registration.py` — expect 0 errors.
4. Run `uv run pytest tests/shared/test_plugin_tool_registration.py -v` — expect 6 passed.

### Method

```python
"""tests/shared/test_plugin_tool_registration.py
Tests for plugin registration-time validation via register_tool() and load_plugins().
"""

from __future__ import annotations

from pathlib import Path

import pytest
from shared import plugin_registry


@pytest.fixture(autouse=True)
def reset_registry() -> None:
    plugin_registry._reset_for_testing()
    yield
    plugin_registry._reset_for_testing()


class TestPluginToolRegistration:
    def test_valid_annotation_registers_successfully(self) -> None:
        @plugin_registry.register_tool("valid_tool")
        async def handler(args: dict) -> tuple[str, bool]:
            return "ok", False

        assert plugin_registry.get_tool("valid_tool") is not None

    def test_missing_annotation_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="missing return type annotation"):

            @plugin_registry.register_tool("bad_tool")
            async def handler(args):  # noqa: ANN001,ANN201
                return "ok", False

    def test_wrong_annotation_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="expected return type"):

            @plugin_registry.register_tool("wrong_tool")
            async def handler(args: dict) -> str:
                return "x"

    def test_invalid_plugin_not_in_registry(self) -> None:
        try:

            @plugin_registry.register_tool("absent_tool")
            async def handler(args):  # noqa: ANN001,ANN201
                return "ok", False
        except ValueError:
            pass
        assert plugin_registry.get_tool("absent_tool") is None

    def test_non_strict_load_records_failure_and_continues(self, tmp_path: Path) -> None:
        (tmp_path / "bad.py").write_text(
            "from shared.plugin_registry import register_tool\n"
            "@register_tool('bad')\n"
            "async def h(args): return 'x', False\n"
        )
        (tmp_path / "ok.py").write_text(
            "from shared.plugin_registry import register_tool\n"
            "@register_tool('ok')\n"
            "async def h(args: dict) -> tuple[str, bool]: return 'x', False\n"
        )
        result = plugin_registry.load_plugins(tmp_path)
        assert result.loaded_count == 1
        assert len(result.failed) == 1
        assert "missing return type annotation" in result.failed[0].error

    def test_strict_mode_raises_plugin_load_error(self, tmp_path: Path) -> None:
        (tmp_path / "bad.py").write_text(
            "from shared.plugin_registry import register_tool\n"
            "@register_tool('bad')\n"
            "async def h(args): return 'x', False\n"
        )
        with pytest.raises(plugin_registry.PluginLoadError):
            plugin_registry.load_plugins(tmp_path, strict_mode=True)
```

### Details

- `test_non_strict_load_records_failure_and_continues` depends on require-21 (add `ValueError`
  to `load_plugins()` except tuple in `plugin_auto_discover.py`). Until require-21 is implemented,
  this test may fail because `ValueError` from `register_tool()` is not caught.
- `reset_registry` fixture uses `autouse=True` to clean state before and after each test.
- `# noqa: ANN001,ANN201` suppresses ruff annotations warnings for intentionally unannotated
  handler functions used to trigger `ValueError` in tests.

## Validation plan

```bash
# Lint
uv run ruff check tests/shared/test_plugin_tool_registration.py
# Expected: 0 errors

# Run 6 tests
uv run pytest tests/shared/test_plugin_tool_registration.py -v
# Expected: 6 passed (or 5 passed + 1 xfail until require-21 is implemented)

# Regression
uv run pytest tests/test_plugin_registry.py -q
# Expected: all pass
```
