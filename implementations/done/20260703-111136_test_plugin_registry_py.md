## Goal

Update `test_plugin_registry.py` to verify rejection behavior: fix field-name references from `command_shadows` to `command_shadows_rejected`, add assertions for command removal in the existing shadow-logging test, and add a new `TestCommandShadowRejection` test class.

## Scope

- In-Scope:
  - `TestCommandShadowLogging.test_command_shadow_always_logged_at_info`: add assertion `plugin_registry.get_command("/debug") is None`
  - `TestStructuredLoadResultRegression.test_command_shadow_count_reported`: rename `result.command_shadows` → `result.command_shadows_rejected`
  - `TestStructuredLoadResultRegression.test_missing_dir_returns_empty_result`: rename `result.command_shadows` → `result.command_shadows_rejected`
  - Add new class `TestCommandShadowRejection` with 4 test methods
- Out-of-Scope:
  - Any test class not listed above
  - Production code
  - `conftest.py` or fixtures (the existing `reset_registry` autouse fixture is sufficient)

## Assumptions

1. `_validate_command_conflicts()` in `plugin_registry.py` has already been updated to delete shadowed commands and return `tuple[int, list[str]]` before these tests are run.
2. The `reset_registry` autouse fixture (lines 19–24) calls `_reset_for_testing()` before and after each test; new tests inherit this automatically — no fixture changes needed.
3. `PluginLoadError` is importable as `plugin_registry.PluginLoadError` (already used in `TestStrictModeToolConflict`).
4. Strict-mode test for command shadows follows the same pattern as `test_strict_mode_tool_conflict_raises` (lines 635–654) — write a plugin file to `tmp_path`, call `load_plugins` with `strict_mode=True`, assert `PluginLoadError`.
5. The log message change from `"command shadow:"` to `"command shadow rejected:"` requires updating the assertion in `test_command_shadow_always_logged_at_info` from `"command shadow"` to `"command shadow rejected"` (or use a broader match — see Details).

## Implementation

### Target file

`/home/masaos/llmagent/tests/test_plugin_registry.py`

### Procedure

1. **Update `TestCommandShadowLogging.test_command_shadow_always_logged_at_info`** (lines 613–631):
   a. After the `caplog` assertion (`assert any("command shadow" in r.message ...)`), update the match string to `"command shadow rejected"` to reflect the new log message.
   b. Add assertion after the `with caplog.at_level(...)` block: `assert plugin_registry.get_command("/debug") is None`.

2. **Update `TestStructuredLoadResultRegression.test_command_shadow_count_reported`** (lines 813–825):
   a. Change `assert result.command_shadows > 0` → `assert result.command_shadows_rejected > 0`.

3. **Update `TestStructuredLoadResultRegression.test_missing_dir_returns_empty_result`** (lines 778–785):
   a. Change `assert result.command_shadows == 0` → `assert result.command_shadows_rejected == 0`.

4. **Add new class `TestCommandShadowRejection`** after `TestCommandShadowLogging` (insert before `TestStrictModeToolConflict` at line 634):

```python
class TestCommandShadowRejection:
    def test_shadow_command_removed_from_registry(self, tmp_path: Path):
        plugin_registry.register_builtin_commands(frozenset({"/help"}))
        (tmp_path / "shadow_help.py").write_text(
            textwrap.dedent("""\
                from shared.plugin_registry import register_command

                @register_command("/help")
                async def cmd(ctx, args):
                    pass
            """)
        )
        plugin_registry.load_plugins(tmp_path, strict_mode=False)
        assert plugin_registry.get_command("/help") is None

    def test_non_shadow_command_not_removed(self, tmp_path: Path):
        plugin_registry.register_builtin_commands(frozenset({"/help"}))
        (tmp_path / "custom_cmd.py").write_text(
            textwrap.dedent("""\
                from shared.plugin_registry import register_command

                @register_command("/my_custom")
                async def cmd(ctx, args):
                    pass
            """)
        )
        plugin_registry.load_plugins(tmp_path, strict_mode=False)
        assert plugin_registry.get_command("/my_custom") is not None

    def test_shadow_strict_mode_raises_plugin_load_error(self, tmp_path: Path):
        plugin_registry.register_builtin_commands(frozenset({"/help"}))
        (tmp_path / "shadow_help.py").write_text(
            textwrap.dedent("""\
                from shared.plugin_registry import register_command

                @register_command("/help")
                async def cmd(ctx, args):
                    pass
            """)
        )
        with pytest.raises(
            plugin_registry.PluginLoadError, match="Command builtin conflicts rejected"
        ):
            plugin_registry.load_plugins(tmp_path, strict_mode=True)

    def test_shadow_strict_mode_message_contains_command_name(self, tmp_path: Path):
        plugin_registry.register_builtin_commands(frozenset({"/help"}))
        (tmp_path / "shadow_help.py").write_text(
            textwrap.dedent("""\
                from shared.plugin_registry import register_command

                @register_command("/help")
                async def cmd(ctx, args):
                    pass
            """)
        )
        with pytest.raises(plugin_registry.PluginLoadError) as exc_info:
            plugin_registry.load_plugins(tmp_path, strict_mode=True)
        assert "/help" in str(exc_info.value)
```

### Method

- Pattern for plugin file writing: `textwrap.dedent()` with `write_text()`, same as `TestLoadPlugins.test_plugin_file_loaded_and_registers` (lines 292–305).
- Pattern for strict-mode `PluginLoadError` assertion: same as `TestStrictModeToolConflict.test_strict_mode_tool_conflict_raises` (lines 635–654).
- `tmp_path` is a built-in pytest fixture; `Path` is already imported at line 10.
- `textwrap` is already imported at line 11.

### Details

- **Existing `test_command_shadow_always_logged_at_info`** uses a `try/finally` block to reset `_builtin_command_names`. New tests in `TestCommandShadowRejection` rely on the autouse `reset_registry` fixture which calls `_reset_for_testing()` (which resets `_builtin_command_names`). No `try/finally` needed in the new tests.
- **Log message assertion change:** current test at line 629 checks `"command shadow" in r.message`. After the production code change, the message will be `"command shadow rejected"`. Update the assertion to `"command shadow rejected" in r.message` to be precise, OR keep `"command shadow"` as a substring match (it will still match `"command shadow rejected"`). Prefer the precise match.
- **Result field names:** `test_command_shadow_count_reported` at line 825 uses `result.command_shadows`; must be `result.command_shadows_rejected`. `test_missing_dir_returns_empty_result` at line 785 uses `result.command_shadows == 0`; must be `result.command_shadows_rejected == 0`.

## Validation plan

```bash
# Run only the affected test classes
uv run pytest tests/test_plugin_registry.py::TestCommandShadowLogging -v
uv run pytest tests/test_plugin_registry.py::TestCommandShadowRejection -v
uv run pytest tests/test_plugin_registry.py::TestStructuredLoadResultRegression -v

# Full suite to check no regressions
uv run pytest tests/test_plugin_registry.py -v

# Type check the test file
uv run mypy tests/test_plugin_registry.py --ignore-missing-imports
```

Expected outcomes:
- `TestCommandShadowRejection`: all 4 new tests pass
- `TestCommandShadowLogging.test_command_shadow_always_logged_at_info`: passes with updated assertion
- `TestStructuredLoadResultRegression`: all existing tests pass
- Full suite: no regressions
