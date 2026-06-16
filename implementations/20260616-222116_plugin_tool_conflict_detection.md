# Implementation: Prevent plugin tools from shadowing MCP tools (req 23)

## Goal

Reject plugin tool registration when a plugin tool name conflicts with a known MCP tool by default, while allowing explicit overrides via config flag.

## Affected Files

| # | File | Change |
|---|---|---|
| 1 | `shared/tool_constants.py` | Add `get_all_mcp_tool_names()` function |
| 2 | `shared/plugin_registry.py` | Simplified `register_tool()`, added `iter_tools()` + `_validate_tool_conflicts()` |
| 3 | `agent/config_dataclasses.py` | Add `plugin_tool_override` to `ToolConfig` |
| 4 | `agent/config_builders.py` | Pass `plugin_tool_override` to ToolConfig |
| 5 | `agent/factory.py` | Read override policy, pass to `load_plugins()` |
| 6 | `config/agent.toml` | Add `plugin_tool_override = false` |
| 7 | `tests/test_plugin_registry.py` | Add tests for conflict rejection |
| 8 | `docs/05_agent_11_extension-points.md` | Document precedence rule and override policy |

## Step-by-Step Implementation

### Step 1: Add `get_all_mcp_tool_names()` to `tool_constants.py`

Add a new function at the end of the file (after line 96):

```python
def get_all_mcp_tool_names() -> frozenset[str]:
    """Return all known MCP tool names for conflict checking.

    This is the source of truth used by plugin_registry to detect
    plugin tools that shadow MCP tools.
    """
    return frozenset(
        READ_TOOLS
        | WRITE_TOOLS
        | DELETE_TOOLS
        | RAG_TOOLS
        | CICD_TOOLS
        | MDQ_TOOLS
        | GIT_TOOLS
        | SQLITE_TOOLS,
    )
```

### Step 2: Simplified `register_tool()` in `plugin_registry.py`

Kept original signature `register_tool(name: str)` — no conflict detection at registration time (plugins can't pass MCP tool list).

### Step 3: Modified `load_plugins()` in `plugin_registry.py`

Added `known_tools` and `override_policy` params. After loading all modules, calls `_validate_tool_conflicts()` to remove conflicting tools from the registry.

### Step 3.5: Added `_validate_tool_conflicts()` to `plugin_registry.py`

New function that checks all registered plugin tools against known MCP tool names. In "reject" mode, removes conflicting tools from `_tools` dict. In "allow" mode, logs a warning but keeps them. Also added `iter_tools()` accessor for testing.

### Step 4: Add `plugin_tool_override` field to `ToolConfig`

Add boolean field with validation in `__post_init__`.

### Step 5: Update `_build_tool_config()` in `config_builders.py`

Add config mapping for the new field.

### Step 6: Update `_init_plugin_registry()` in `factory.py`

Read override policy, pass to `load_plugins()`.

### Step 7: Add config entry in `agent.toml`

Add `plugin_tool_override = false` after line 69.

### Step 8: Add tests for conflict detection

Add test classes `TestRegisterToolConflict` and `TestLoadPluginsConflict`.

### Step 9: Update documentation

Document precedence rules and override policy.

## Validation Plan

| Check | Tool | Target |
|---|---|---|
| Format | `uv run ruff format scripts/` | clean |
| Lint | `uv run ruff check scripts/` | 0 errors |
| Type check | `uv run mypy scripts/` | no new errors |
| Tests | `uv run pytest tests/test_plugin_registry.py -v` | all pass |
