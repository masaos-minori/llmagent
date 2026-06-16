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
4. Errors during load are logged and skipped (fail-open)
5. Directory not found → 0 plugins loaded (no error)

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
@register_tool(name: str)
async handler(args: dict) -> tuple[str, bool]   # (result_text, is_error)
```

- Registers a local Python function as a tool handler
- Bypasses MCP routing entirely
- Called by `ToolExecutor.execute()` **before** cache check and MCP dispatch
- Return value: `(result_text: str, is_error: bool)`
- Access: `plugin_registry.get_tool(name)` → `Callable | None`

**Priority vs MCP:** plugin tools are checked first. A plugin tool with the same name as
an MCP tool will shadow the MCP tool for all calls in that session.

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
| `load_plugins(plugin_dir)` | Import all `*.py` in dir; return count |
| `_reset_for_testing()` | Clear all registries (test-only) |

---

## Extension Rules

1. Plugin tools cannot be cached by `ToolExecutor` (only MCP tool results are cached)
2. Plugin commands cannot use the same name as any built-in command
3. Plugin files that raise exceptions during import are skipped silently — always test plugins before deployment
4. `@register_pipeline_stage` hooks run inside the RAG pipeline context; exceptions in hooks propagate to `RagPipeline.run()`
5. Plugin tool handlers must be `async` functions; command handlers can be sync or async

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
