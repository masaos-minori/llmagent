# Agent Extension Points

- Runtime architecture → [05_agent_02_runtime-architecture.md](05_agent_02_runtime-architecture.md)

## Purpose

Document the plugin architecture, all `@register_*` decorators, extension rules,
and priority relationships between built-in features and extensions.

---

## Plugin Architecture

Plugins are Python files in `plugins/*.py` (relative to the project root, 2 levels above `scripts/`).

**Loading:**
1. `AgentREPL._init_plugin_registry()` calls `plugin_registry.load_plugins(plugin_dir)` at startup
2. Each `*.py` file is imported in alphabetical order
3. `@register_*` decorators run at import time and register handlers globally
4. Errors during load are logged individually with file name and error reason (fail-open by default)
5. When `plugin_strict=true` in config, the first import failure aborts startup
6. After loading, plugin command names are checked against built-in commands; shadowing is logged as a warning
7. Directory not found → 0 plugins loaded (no error)

Startup log format (individual failure):
`Plugin load failure: <filename> — <ErrorType>: <message>`

Startup log format (command shadowing warning):
`Plugin command "/name" shadows built-in command. The built-in command will take precedence.`

```python
# plugins/my_plugin.py
from shared.plugin_registry import register_command, register_tool, register_pipeline_stage

@register_command("/ping")
async def cmd_ping(ctx, args: str) -> None:
    print("pong")

@register_tool("echo")
async def tool_echo(args: dict) -> tuple[str, bool]:
    return str(args.get("text", "")), False

@register_pipeline_stage(when="post")
def post_rerank(hits, query):
    return hits   # modify and return hits list
```

---

## `@register_command`

```python
@register_command(name: str, *, prefix: bool = False)
handler(ctx: AgentContext, args: str) -> None  # sync or async
```

- `name`: slash command string including `/` (e.g., `"/ping"`)
- `prefix=False`: exact match only
- `prefix=True`: accepts trailing arguments (`line.startswith(name + " ")`)
- Dispatch priority: **lower** than built-in commands (checked second)
- Access: `plugin_registry.get_command(name)` → `(handler, is_prefix) | None`

**Built-in vs plugin priority:**
Built-in commands in `_COMMANDS` list are matched first. If no built-in matches,
`_dispatch_plugin()` is called. A plugin cannot override a built-in command name.

---

## `@register_tool`

```python
@register_tool(name: str, *, known_tools: frozenset[str] = frozenset(), override_policy: str = "reject")
async handler(args: dict) -> tuple[str, bool]   # (result_text, is_error)
```

- Registers a local Python function as a tool handler
- Bypasses MCP routing entirely
- Called by `ToolExecutor.execute()` **before** cache check and MCP dispatch
- Return value: `(result_text: str, is_error: bool)`

**Return-type validation:** At registration time, `@register_tool` inspects the
function's return annotation. If the annotation is present and is not
`tuple[str, bool]`, a warning is logged. This check is non-blocking — the tool
is still registered regardless of the annotation.

- Access: `plugin_registry.get_tool(name)` → `Callable | None`

### Plugin Tool Precedence and Conflict Policy

Plugin tools are registered via the `@register_tool()` decorator in plugin files
located in the `plugins/` directory. By default, plugin tools **shadow** MCP tools
when they share the same name — this is because plugin tool lookup in
`ToolExecutor.execute()` runs before MCP routing.

#### Conflict Detection

When `plugin_tool_override = false` (default):

- At startup, all known MCP tool names are collected from `tool_constants.py`.
- If a plugin tool name matches any known MCP tool, registration is **rejected**
  with a clear error message: `Plugin tool "name" conflicts with MCP tool "name". Set plugin_tool_override = true to allow.`
- Only the conflicting plugin file is skipped; other plugins continue loading.

When `plugin_tool_override = true`:

- Conflicts are allowed but logged as warnings: `Plugin tool "name" shadows MCP tool; override policy allows it`.
- The plugin tool takes precedence over the MCP tool for the session.

#### Configuration

Set in `config/agent.toml`:

```toml
plugin_tool_override = false  # or true to allow shadowing
plugin_strict = false         # or true to fail startup on first plugin import error
```

#### Strict Plugin Loading Mode

When `plugin_strict = true`, the first plugin import failure raises an exception that aborts agent startup. This is useful for CI/CD pipelines where plugin failures should be treated as build errors.

Default is `false` (fail-open): plugin import failures are logged as warnings and other plugins continue loading.

Error message format (both modes): `Plugin load failed (<filename>): <error_type>: <message>`

#### Precedence Order

1. Plugin tools (checked first in `ToolExecutor.execute()`)
2. MCP tools (routed via `ToolRouteResolver`)
3. Built-in commands (slash commands, not tool calls)

To avoid confusion, give plugin tools names that do not overlap with existing MCP tool names.

**Priority vs MCP:** plugin tools are checked first. A plugin tool with the same name as
an MCP tool will shadow the MCP tool for all calls in that session (unless conflict detection rejects it).

---

## `@register_pipeline_stage`

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

## Registry API (`shared/plugin_registry.py`)

| Function | Description |
|---|---|
| `get_command(name)` | `(handler, is_prefix) \| None` |
| `iter_commands()` | Dict snapshot of all registered commands |
| `get_tool(name)` | `Callable \| None` |
| `get_pipeline_post_stages()` | List snapshot of all post-rerank stage handlers |
| `load_plugins(plugin_dir, *, known_tools, override_policy)` | Import all `*.py` in dir; return count; skip conflicting plugins when policy is "reject" |
| `_reset_for_testing()` | Clear all registries (test-only) |

---

## Extension Rules

1. Plugin tools cannot be cached by `ToolExecutor` (only MCP tool results are cached)
2. Plugin commands cannot use the same name as any built-in command
3. Plugin files that raise exceptions during import are skipped silently — always test plugins before deployment
4. `@register_pipeline_stage` hooks run inside the RAG pipeline context; exceptions are caught and logged by `run_pipeline_stages()` — the pipeline continues with the hits unchanged
5. Plugin tool handlers must be `async` functions; command handlers can be sync or async

#### Hook Failure Behavior

In normal mode (default), exceptions raised by post-rerank hooks are:
- Caught by `run_pipeline_stages()` in `shared/plugin_registry.py`
- Logged as warnings with the hook name, error type, and query context
- Skipped: the pipeline continues with the hits as they were before that hook ran

In strict mode (`hook_strict=True` on `RagPipeline.run()`), the first hook failure
raises the original exception to the caller. Use this mode in tests to verify hook behavior.

Log format: `Plugin hook "<name>" failed on query "<query>": <ErrorType>: <message>`

---

## Adding a New MCP Server

Use the built-in wizard (recommended):

```
agent[:#1]> /mcp install <server-name>
```

This generates:
- `scripts/mcp/<name>/server.py` — FastAPI scaffold (MCPServer subclass)
- `config/<module>_mcp_server.json` — config template
- `init.d/<server-name>` — OpenRC startup script (mode 755)
- `conf.d/<server-name>` — API key env template (optional)

Manual steps after wizard:
1. Add tool definitions to `config/agent.toml` → `tool_definitions`
2. Add server entry to `config/mcp_servers.toml` → `[mcp_servers.<key>]`
3. Add files to `deploy/deploy.sh` copy list
4. Add OpenRC startup to `deploy/setup_services.sh`

See [04_mcp_03_routing_lifecycle_and_execution.md](04_mcp_03_routing_lifecycle_and_execution.md)
for full MCP server addition procedure.
