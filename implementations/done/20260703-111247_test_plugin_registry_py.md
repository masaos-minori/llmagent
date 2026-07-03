## Goal

Add a `TestRegistryIsolation` class to `tests/test_plugin_registry.py` with two new tests that explicitly verify sequential `load_plugins()` call accumulation semantics and `_reset_for_testing()` clean-state semantics.

## Scope

- In-Scope:
  - Add class `TestRegistryIsolation` after `TestReset` (currently ending around line 371).
  - Add test `test_repeated_load_accumulates_registrations`: call `load_plugins()` twice with different plugin dirs, assert both tools registered.
  - Add test `test_reset_between_loads_yields_clean_state`: call `load_plugins()` once, reset, call again with only a second tool, assert second tool present and first tool absent.
- Out-of-Scope:
  - Modifying any existing test method.
  - Changing the `reset_registry` autouse fixture.
  - Any change outside `test_plugin_registry.py`.

## Assumptions

1. The existing module-level `reset_registry` autouse fixture (lines 19-24) calls `_reset_for_testing()` before and after each test, so `TestRegistryIsolation` tests automatically start and end with a clean registry — no additional fixture needed in the new class.
2. `tmp_path` is a pytest built-in fixture providing a per-test temporary directory, available in all test methods that declare it as a parameter.
3. Each test method must write distinct tool names to avoid cross-fixture pollution (not a concern given autouse reset, but still good practice).
4. The `load_plugins()` function accepts `Path` objects (confirmed by type signature `plugin_dir: str | Path`).
5. Plugin files must declare `-> tuple[str, bool]` return annotation to pass `register_tool()` validation.

## Implementation

### Target file

`/home/masaos/llmagent/tests/test_plugin_registry.py`

### Procedure

1. After the closing line of `class TestReset:` (around line 371), add a blank line then the new class.
2. Insert the following class:
   ```python
   class TestRegistryIsolation:
       def test_repeated_load_accumulates_registrations(self, tmp_path: Path):
           """Sequential load_plugins() calls add to existing registries without clearing."""
           dir_a = tmp_path / "plugins_a"
           dir_a.mkdir()
           (dir_a / "tool_a.py").write_text(
               textwrap.dedent("""\
                   from shared.plugin_registry import register_tool

                   @register_tool("isolation_tool_a")
                   async def t(args: dict) -> tuple[str, bool]:
                       return "", False
               """)
           )
           dir_b = tmp_path / "plugins_b"
           dir_b.mkdir()
           (dir_b / "tool_b.py").write_text(
               textwrap.dedent("""\
                   from shared.plugin_registry import register_tool

                   @register_tool("isolation_tool_b")
                   async def t(args: dict) -> tuple[str, bool]:
                       return "", False
               """)
           )

           plugin_registry.load_plugins(dir_a)
           plugin_registry.load_plugins(dir_b)

           assert plugin_registry.get_tool("isolation_tool_a") is not None
           assert plugin_registry.get_tool("isolation_tool_b") is not None

       def test_reset_between_loads_yields_clean_state(self, tmp_path: Path):
           """_reset_for_testing() between load_plugins() calls clears earlier registrations."""
           dir_a = tmp_path / "plugins_a"
           dir_a.mkdir()
           (dir_a / "tool_a.py").write_text(
               textwrap.dedent("""\
                   from shared.plugin_registry import register_tool

                   @register_tool("isolation_reset_tool_a")
                   async def t(args: dict) -> tuple[str, bool]:
                       return "", False
               """)
           )
           dir_b = tmp_path / "plugins_b"
           dir_b.mkdir()
           (dir_b / "tool_b.py").write_text(
               textwrap.dedent("""\
                   from shared.plugin_registry import register_tool

                   @register_tool("isolation_reset_tool_b")
                   async def t(args: dict) -> tuple[str, bool]:
                       return "", False
               """)
           )

           plugin_registry.load_plugins(dir_a)
           plugin_registry._reset_for_testing()
           plugin_registry.load_plugins(dir_b)

           assert plugin_registry.get_tool("isolation_reset_tool_a") is None
           assert plugin_registry.get_tool("isolation_reset_tool_b") is not None
   ```
3. Ensure `textwrap` and `Path` are already imported (confirmed: `textwrap` at line 11, `Path` at line 12, `pytest` at line 14, `plugin_registry` at line 14-15).
4. Run the new tests.

### Method

- Use `tmp_path.mkdir()` with subdirectory names to keep plugin dirs separate within the same test's tmp directory.
- Tool names must be unique across all tests in the file to avoid leakage if `reset_registry` fixture somehow does not fire (defensive naming with `isolation_` prefix).
- `textwrap.dedent()` with escaped newlines follows the existing pattern in `TestLoadPlugins` and `TestLoadPluginsConflict`.

### Details

- Insert point: after the last line of `class TestReset:` (`assert plugin_registry.get_pipeline_post_stages() == []` at line 370, followed by a blank line before the next class at line 373).
- The autouse `reset_registry` fixture at module level (lines 19-24) ensures `_reset_for_testing()` is called before and after each test, including the new ones. The `_reset_for_testing()` call inside `test_reset_between_loads_yields_clean_state` is an explicit mid-test reset, distinct from the fixture's boundary resets.
- `TestRegistryIsolation` test names use the word `isolated` in the class name and action verbs in method names to communicate lifecycle semantics clearly.

## Validation plan

```bash
# Run only the new class
uv run pytest tests/test_plugin_registry.py::TestRegistryIsolation -v

# Run full plugin registry test suite
uv run pytest tests/test_plugin_registry.py -v
```

Expected: both new tests in `TestRegistryIsolation` pass; no regressions in existing tests.
