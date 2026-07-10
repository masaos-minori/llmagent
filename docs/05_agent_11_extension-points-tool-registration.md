---
title: "Agent Extension Points"
category: agent
tags:
  - agent
  - agent
  - extension
  - plugin
  - register
related:
  - 05_agent_00_document-guide.md
---

# Agent Extension Points

ython
@register_tool(name: str, *, known_tools: frozenset[str] = frozenset(), override_policy: str = "reject")
async handler(args: dict) -> tuple[str, bool]   # (result_text, is_error)
```

- Registers a local Python function as a tool handler
- Bypasses MCP routing entirely
- Called by `ToolExecutor.execute()` **before** cache check and MCP dispatch
- Return value: `(result_text: str, is_error: bool)`

**Return-type validation (fail-fast):** At registration time, `@register_tool` inspects
the function's return annotation. If the annotation is missing or is not `tuple[str, bool]`,
a `ValueError` is raised immediately — the tool is **not** registered. Fix the annotation
before deployment.

```python
# Contract: must annotate return type as tuple[str, bool]
@register_tool("echo")
async def tool_echo(args: dict) -> tuple[str, bool]:   # required
    return str(args.get("text", "")), False
```

**Why fail-fast instead of warn?** Silent warnings were missed in production, causing
unexpected behavior at call time. Failing at registration makes the error unmissable.

**Runtime return value validation:** `ToolExecutor.execute()` validates the actual return value at call time. It checks that the return is a `tuple` with **exactly 2 elements** (`len == 2`), that `result[0]` is `str`, and that `result[1]` is `bool`. A tuple with more or fewer than 2 elements raises `ValueError`. A non-`str` first element raises `TypeError`. A non-`bool` second element raises `TypeError`.

- Access: `plugin_registry.get_tool(name)` → `Callable | None`

### Plugin Tool Precedence and Conflict Policy

Plugin tools are registered via the `@register_tool()` decorator in plugin files
located in the `plugins/` directory. When a plugin tool shares the same name as an
MCP tool, the outcome depends on `plugin_tool_override`:

- **`plugin_tool_override = false` (default):** The conflicting plugin tool is
  rejected at startup and removed from the registry.
- **`plugin_tool_override = true`:** The plugin tool takes precedence over the MCP
  tool for the session (plugin tools are checked first in `ToolExecutor.execute()`).

#### Conflict Detection

When `plugin_tool_override = false` (default):

- At startup, all known MCP tool names are collected from `ToolRegistry`.
- If a plugin tool name matches any known MCP tool, the tool is **rejected** (removed from the registry).
- Log: `[plugin] conflict: tool '<name>' in '<module>' shadows MCP tool — rejected`
- Only the conflicting tool is removed; the plugin module and other tools continue loading.

When `plugin_tool_override = true`:

- Conflicts are allowed and logged: `[plugin] conflict: tool '<name>' in '<module>' shadows MCP tool — allowed`
- The plugin tool takes precedence over the MCP tool for the session.

#### Configuration

Set in `config/agent.toml`:

```toml
plugin_tool_override = false  # or true to allow shadowing
plugin_strict = false         # or true to fail startup on first plugin import error
```

#### Strict Plugin Loading Mode

When `plugin_strict = true`, all plugin files are attempted first. After the full load loop, if any failures occurred, a single `PluginLoadError` (subclass of `RuntimeError`) is raised with all failure details aggregated in the message.

#### Safety Tier Enforcement

In production mode, all registered tools must have a declared safety tier entry in `tool_safety_tiers`. Missing tiers produce a fatal `RuntimeError` at startup via `ProductionConfigValidator.validate()`. This ensures no tool can operate without a defined risk classification. Unknown tier keys (keys not matching any registered tool name) also produce a fatal error in production.

**CI auto-detect:** If `plugin_strict` is absent from config and the `CI` environment variable is set (GitHub Actions, CircleCI, etc.), `plugin_strict` defaults to `True` automatically. Explicit `plugin_strict = false` in config always overrides this.

Default is `false` (fail-open): failures are logged as `[plugin] skipped: <filename> (<ErrorType>)` and loading continues.

Per-failure entry in `PluginLoadResult.failed`: `PluginFailure(path="<filename>", error="Plugin load failed (<filename>): <ErrorType>: <message>")`

`PluginLoadResult` fields: `loaded_count`, `failed`, `tool_conflicts_shadowed`, `tool_conflicts_allowed`, `command_shadows_rejected`

The most recent `PluginLoadResult` is accessible via `plugin_registry.get_last_load_result()` and displayed by `/plugin status`.

#### Precedence Order

1. Plugin tools (checked first in `ToolExecutor.execute()`)
2. MCP tools (routed via `ToolRouteResolver`)
3. Built-in commands (slash commands, not tool calls)

To avoid confusion, give plugin tools names that do not overlap with existing MCP tool names.

**Priority vs MCP:** plugin tools are checked first. A plugin tool with the same name as
an MCP tool will shadow the MCP tool for all calls in that session (unless conflict detection rejects it).

#### Observability Limitations

Plugin tools emit `tool_exec` audit events via `audit_tool_exec()` with `source="plugin"` and empty `mcp_request_id`. However, unlike MCP tool events, plugin audit events lack:

- **No `X-Request-Id`**: Plugin tools do not go through the HTTP transport layer, so there is no `request_id` to correlate with server-side logs.
- **No `server_key`**: The `server_key` field is always empty for plugin tools.

This means plugin tool audit events cannot be correlated with MCP server access logs. See [05_agent_10_operations-and-observability.md](05_agent_10_operations-and-observability.md#plugin-tool-audit-events) for details.

---

## `@register_pipeline_st

age`

```python
@register_pipeline_stage(when: str = "post")
handler(hits: list[dict], query: str) -> list[dict]
```

- `when="post"`: hook runs after cross-encoder rerank stage
- Receives the reranked hits list and the original query string
- Must return the (possibly modified) hits list
- All registered post-rerank stages run in registration order
- Access: `plugin_registry.get_pipeline_post_stages()` → `list[Callable]`

**Current limitation:** only `when="post"` is supported (post-rerank). Pre-search
and pre-rerank hooks are not yet implemented.

---

## Registry API (`shared/

## Related Documents

- `agent`
- `extension`
- `plugin`

## Keywords

agent
extension
plugin
register
