# Implementation: Add source=="plugin" assertions and close aggregated-error test gap (tests/shared/test_plugin_tool_invoker.py, tests/test_plugin_registry.py)

## Goal

Close the test-coverage gap where `ToolCallResult.source == "plugin"` is set by `plugin_tool_invoker.py` in every outcome branch but never actually asserted in `tests/shared/test_plugin_tool_invoker.py`. Additionally confirm (and fill, if missing) `tests/test_plugin_registry.py` coverage for two specific behaviors: an aggregated `PluginLoadError` message naming all three failure categories at once, and repeated-load / `_reset_for_testing()` semantics.

## Scope

**In-Scope:**
- `tests/shared/test_plugin_tool_invoker.py` — add `assert result.source == "plugin"` to the 5 existing tests that return a non-`None` `ToolCallResult` (success, exception, and 3 contract-violation variants)
- `tests/test_plugin_registry.py` — add one new test asserting the aggregated `PluginLoadError` message mentions all three failure categories (load/import failure, tool-conflict rejection, command-conflict rejection) when they occur simultaneously; confirm the repeated-load / `_reset_for_testing()` test already exists (it does — see Assumptions) and needs no addition

**Out-of-Scope:**
- `test_no_plugin_returns_none` in `test_plugin_tool_invoker.py` — returns `None`, has no `.source` to assert; not touched
- Any change to `scripts/shared/plugin_tool_invoker.py`, `scripts/shared/plugin_registry.py`, or `scripts/shared/plugin_auto_discover.py` — all already behave correctly; this phase only adds/confirms test assertions
- Any other test class in `test_plugin_registry.py` beyond the one new aggregated-message test

## Assumptions

1. `tests/shared/test_plugin_tool_invoker.py` (confirmed by direct read) has 6 test methods in `TestPluginToolInvoker`:
   - `test_no_plugin_returns_none` — returns `None`; excluded (no `source` field to assert)
   - `test_valid_plugin_returns_result` — success path
   - `test_plugin_exception_returns_error_result` — exception path
   - `test_invalid_tuple_length_returns_error_result` — contract violation (tuple length)
   - `test_wrong_output_type_returns_error_result` — contract violation (output type)
   - `test_wrong_is_error_type_returns_error_result` — contract violation (is_error type)
   
   The latter 5 are "the 5 existing outcome tests" the plan refers to; none currently assert `result.source` (confirmed: `grep -c "result.source" tests/shared/test_plugin_tool_invoker.py` returns 0). `scripts/shared/plugin_tool_invoker.py` (confirmed by direct read) sets `source="plugin"` in all 3 of its return statements (success, exception, contract-violation), so this is purely a missing-assertion gap.
2. `tests/test_plugin_registry.py` (confirmed by direct read) already has:
   - `TestRegistryIsolation.test_repeated_load_accumulates_registrations` and `test_reset_between_loads_yields_clean_state` (lines ~375-437) — these already fully cover the repeated-load / `_reset_for_testing()` semantics the plan's Task 55 asks to confirm. **No addition needed for this part.**
   - `TestPluginLoadError.test_aggregated_error_strict_mode` and `test_aggregated_error_contains_all_module_names` (lines ~605-621) — cover aggregation of 2 *load/import* failures together.
   - `TestStrictModeToolConflict.test_strict_mode_combined_import_and_conflict_errors` (line ~852) — covers aggregation of 1 load failure + 1 tool conflict together (2 of 3 categories).
   - `TestCommandShadowRejection.test_shadow_strict_mode_raises_plugin_load_error` / `test_shadow_strict_mode_message_contains_command_name` — cover command-conflict rejection alone in strict mode.
   - **No existing test asserts a single aggregated `PluginLoadError` message containing all three categories simultaneously** (load failure + tool conflict + command conflict in one `load_plugins()` call). This is the one genuine gap per plan Assumption 6 / Implementation Step 3, and must be added.
3. `plugin_registry.register_builtin_commands()` and `known_tools=` are the mechanisms already used elsewhere in the file (`TestCommandShadowRejection`, `TestStrictModeToolConflict`) to set up tool/command conflicts; the new test reuses this established pattern rather than inventing a new one.
4. The `reset_registry` autouse fixture (module-level, lines ~19-26) resets registries before/after every test; the new test needs no additional fixture setup.

## Implementation

### Target file

Primary: `tests/shared/test_plugin_tool_invoker.py`
Secondary: `tests/test_plugin_registry.py`

### Procedure

**A. `tests/shared/test_plugin_tool_invoker.py`:**
1. In `test_valid_plugin_returns_result`, add `assert result.source == "plugin"` after the existing `assert result.error_type == ""` line.
2. In `test_plugin_exception_returns_error_result`, add `assert result.source == "plugin"` after the existing `assert result.error_type == "tool"` line.
3. In `test_invalid_tuple_length_returns_error_result`, add `assert result.source == "plugin"` after the existing `assert result.error_type == "plugin_contract"` line.
4. In `test_wrong_output_type_returns_error_result`, add `assert result.source == "plugin"` after the existing `assert result.error_type == "plugin_contract"` line.
5. In `test_wrong_is_error_type_returns_error_result`, add `assert result.source == "plugin"` after the existing `assert result.error_type == "plugin_contract"` line.
6. Do not modify `test_no_plugin_returns_none`.

**B. `tests/test_plugin_registry.py`:**
1. Read the file in full (already done for this planning pass — see Assumptions) to confirm no existing test covers the 3-category-simultaneous aggregation case.
2. Add one new test, e.g. `test_aggregated_error_contains_load_tool_and_command_failures`, to `TestPluginLoadError` (or a new small class alongside it — either placement is acceptable; keep it near the other aggregation tests for discoverability).
3. Confirm (no code change) that `TestRegistryIsolation` already satisfies the repeated-load/`_reset_for_testing()` requirement.

### Method

**A. Example of the assertion-insertion pattern** (applied identically to all 5 tests, using `test_invalid_tuple_length_returns_error_result` as illustration):

```python
    @pytest.mark.asyncio
    async def test_invalid_tuple_length_returns_error_result(self) -> None:
        async def _fn(args: dict) -> Any:
            return ("ok",)

        plugin_registry._tools["bad_len"] = (_fn, "bad_len")
        invoker = PluginToolInvoker()
        result = await invoker.try_execute("bad_len", {})
        assert result is not None
        assert result.is_error is True
        assert "tuple" in result.output.lower()
        assert result.error_type == "plugin_contract"
        assert result.source == "plugin"  # <-- new line
```

Apply the same single-line addition (`assert result.source == "plugin"`) to the other 4 tests, each placed as the last assertion in its test body.

**B. New aggregated test** (sketch; combine one import failure, one tool conflict, and one command conflict in a single `strict_mode=True` call):

```python
def test_aggregated_error_contains_load_tool_and_command_conflicts(
    self, tmp_path: Path
) -> None:
    plugin_registry.register_builtin_commands(frozenset({"/help"}))
    (tmp_path / "bad.py").write_text("raise RuntimeError('import_fail')")
    (tmp_path / "tool_conflict.py").write_text(
        textwrap.dedent("""\
            from shared.plugin_registry import register_tool

            @register_tool("list_directory")
            async def t(args) -> tuple[str, bool]:
                return "", False
        """)
    )
    (tmp_path / "cmd_conflict.py").write_text(
        textwrap.dedent("""\
            from shared.plugin_registry import register_command

            @register_command("/help")
            async def cmd(ctx, args):
                pass
        """)
    )
    with pytest.raises(PluginLoadError) as exc_info:
        plugin_registry.load_plugins(
            tmp_path,
            known_tools=frozenset({"list_directory"}),
            override_policy="reject",
            strict_mode=True,
        )
    msg = str(exc_info.value)
    assert "import_fail" in msg
    assert "Tool MCP conflicts rejected" in msg
    assert "Command builtin conflicts rejected" in msg
```

(Exact fixture/message-substring wording should be re-verified against the current `load_plugins()` strict-mode aggregation message format at implementation time — this sketch follows the substrings already used by the two existing partial-aggregation tests, `"Tool MCP conflicts rejected"` from `test_strict_mode_combined_import_and_conflict_errors` and `"Command builtin conflicts rejected"` from `test_shadow_strict_mode_raises_plugin_load_error`.)

### Details

- Keep assertion insertion mechanical and minimal — one line per test, no restructuring of existing test bodies.
- For the new registry test, reuse `tmp_path`, `textwrap.dedent`, and `frozenset` patterns already established elsewhere in the same file (consistent style, no new helper needed).
- Do not rename or remove any existing test.
- English-only comments per `rules/coding.md`.

## Validation plan

Relevant subset of the plan's Validation plan table, filtered to these target files:

| Check | Tool | Target |
|---|---|---|
| Lint | `uv run ruff check tests/shared/test_plugin_tool_invoker.py tests/test_plugin_registry.py` | 0 errors |
| Tests | `uv run pytest tests/shared/test_plugin_tool_invoker.py tests/test_plugin_registry.py -v` | All pass, including the new `source` assertions and the new aggregation test |
| Regression | `uv run pytest tests/test_tool_executor.py -k "plugin" -q` | No new failures |

No mypy/lint-imports impact expected (test-only, no new imports beyond what's already used in the file), but the full toolchain sequence in `rules/toolchain.md` should still be run once all phases are complete.
