# Implementation: Harden Plugin Loading and MCP Tool Shadowing for Production

## Goal

Make plugin loading fail-fast in CI/controlled environments and expose plugin load results to operators through a dedicated slash command.

## Scope

**In-Scope:**
- CI-aware `plugin_strict` default: if `CI` env var is set and `plugin_strict` is not explicitly configured, treat as `True` (fail-fast in CI by default)
- Persist `PluginLoadResult` after startup so it can be queried later
- Add `/plugin status` command showing: loaded, failed, skipped, tool conflicts, CI-strict
- Register the command in `command_defs.py`

**Out-of-Scope:**
- Removing the plugin system or the `@register_*` decorator API
- Changing the fail-open behavior in non-CI environments
- Redesigning the plugin loader itself

## Assumptions

1. `os.getenv("CI")` is truthy in GitHub Actions (`CI=true`), CircleCI, Jenkins, etc.
2. Explicit `plugin_strict=true` or `plugin_strict=false` in config always takes precedence over the CI auto-detection default.
3. `PluginLoadResult` is already a frozen dataclass — can be stored safely in a module-level variable in `plugin_registry.py`.
4. The `_COMMANDS` list in `command_defs.py` is the single registration point for built-in slash commands.

## Unknowns & Gaps

| ID | Unknown | Evidence Missing | Resolution | Blocking |
|---|---|---|---|---|
| UNK-01 | Should CI auto-strict override explicit `plugin_strict=false` in config? | Policy undefined | No — explicit config always wins. Auto-detect only applies when the key is absent from config | False |
| UNK-02 | Where should `PluginLoadResult` live between startup and `/plugin status`? | No existing field in AgentContext/AppServices | Store as module-level `_last_load_result` in `plugin_registry.py`; accessible without context coupling | False |
| UNK-03 | Should `/plugin status` show per-plugin details (which files failed)? | Require says "loaded / failed / skipped / overridden" counts | Start with count-level summary; per-file failures shown in list if `failed > 0` | False |

## Implementation

### Target files

- `scripts/agent/config_builders.py` — CI-aware `plugin_strict` default (1-line change)
- `scripts/shared/plugin_registry.py` — add `_last_load_result` + accessor functions
- `scripts/agent/factory.py` — call `plugin_registry.set_last_load_result(result)` after load
- `scripts/agent/commands/cmd_plugins.py` — new file: `_PluginsMixin` with `_cmd_plugin`
- `scripts/agent/commands/command_defs.py` — add `/plugin status` entry
- `scripts/agent/commands/registry.py` — include `_PluginsMixin`
- `tests/test_plugin_ci_strict.py` — new test for CI-strict default
- `tests/test_cmd_plugins.py` — new test for `/plugin status` output

### Procedure

#### Step 1: CI-aware strict default

In `scripts/agent/config_builders.py`, change:
```python
plugin_strict=bool(cfg.get("plugin_strict", False)),
```
to:
```python
plugin_strict=bool(cfg.get("plugin_strict", os.getenv("CI") is not None)),
```

Add `import os` if not already present.

#### Step 2: Persist PluginLoadResult for later query

In `scripts/shared/plugin_registry.py`, add module-level:
```python
_last_load_result: PluginLoadResult | None = None

def get_last_load_result() -> PluginLoadResult | None:
    return _last_load_result

def _set_last_load_result(result: PluginLoadResult) -> None:
    global _last_load_result
    _last_load_result = result
```

At end of `load_plugins()`, before return: `_set_last_load_result(result_obj)`
In `_reset_for_testing()`: `_last_load_result = None`

#### Step 3: Add `/plugin status` command

New file `scripts/agent/commands/cmd_plugins.py`:
```python
class _PluginsMixin(MixinBase):
    def _cmd_plugin(self, args: str) -> None:
        """Handle /plugin status."""
        from shared.plugin_registry import get_last_load_result
        result = get_last_load_result()
        if result is None:
            self._out.write_no_data("Plugin registry not initialized")
            return
        rows = [
            ["Loaded", str(result.loaded_count)],
            ["Failed", str(len(result.failed))],
            ["Tool conflicts (shadowed)", str(result.tool_conflicts_shadowed)],
            ["Tool conflicts (allowed)", str(result.tool_conflicts_allowed)],
            ["Command shadows", str(result.command_shadows)],
        ]
        self._out.write_table(["Metric", "Count"], rows)
        if result.failed:
            self._out.write_section("Failed plugins")
            for f in result.failed:
                self._out.write_item(f"{f.path}: {f.error}")
```

`command_defs.py`: add `CommandDef(name="/plugin", handler="_cmd_plugin", ...)`
`registry.py`: include `_PluginsMixin` in the `CommandRegistry` bases

#### Step 4: Tests

- `tests/test_plugin_ci_strict.py` (new): assert `plugin_strict=True` when `CI=1` and not in config
- `tests/test_cmd_plugins.py` (new): assert `/plugin status` renders loaded/failed counts
- Existing `test_plugin_registry.py`: ensure `_reset_for_testing` clears `_last_load_result`

### Method

- Minimal code changes (1 line) in existing functions
- New file for the `/plugin status` command
- Tests follow existing patterns in respective test files

### Details

- CI auto-detect only applies when `plugin_strict` is absent from config; explicit config always wins
- `_last_load_result` global mutable — mitigated by `_reset_for_testing()` clearing it
- `write_section` / `write_item` methods may not exist on `OutputView`; verify before implementing

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| CI strict default | Unit — monkeypatch `os.environ["CI"]` | `uv run pytest tests/test_plugin_ci_strict.py -v` | all pass |
| `/plugin status` output | Unit — mock `get_last_load_result` | `uv run pytest tests/test_cmd_plugins.py -v` | all pass |
| Plugin registry reset | Unit — existing test | `uv run pytest tests/ -k plugin -v` | all pass |
| Lint | Static | `uv run ruff check scripts/` | 0 errors |
| Type check | Static | `uv run mypy scripts/` | no new errors |
| Full suite | Regression | `uv run pytest -q` | no new failures |

## Risks

- **Risk:** CI auto-strict breaks a CI pipeline that uses plugins with import errors
  → **Mitigation:** deploy-guard note in scope; log "[plugin] CI strict mode auto-enabled" at startup
- **Risk:** `_last_load_result` is a global mutable — test isolation issue
  → **Mitigation:** `_reset_for_testing()` already resets all globals; add `_last_load_result` to it
- **Risk:** `write_section` / `write_item` methods may not exist on `OutputView`
  → **Mitigation:** verify `_out` interface before implementing; use `write_table` rows for failures if needed
