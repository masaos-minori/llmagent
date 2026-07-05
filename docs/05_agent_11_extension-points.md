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
4. Errors during load are logged individually with `[plugin] skipped: <filename> (<ErrorType>)`
5. When `plugin_strict=true` in config, all plugins are attempted; a single `PluginLoadError` is raised at the end with aggregated details
6. After loading, a summary line is logged: `[plugin] loaded=N, skipped=M`
7. After loading, plugin tool and command names are checked against built-in names; each conflict is logged with the source module name
8. Directory not found → 0 plugins loaded (no error)

Startup log format (individual skip):
`[plugin] skipped: <filename> (<ErrorType>)`

Startup log format (conflict):
`[plugin] conflict: tool '<name>' in '<module>' shadows MCP tool — rejected|allowed`

Startup log format (command shadow):
`[plugin] command shadow rejected: '<name>' in '<module>' shadows built-in`

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
`_dispatch_plugin()` is called. Plugin commands that share a name with a built-in
command are **rejected at load time** (removed from the plugin command registry).
They will not appear in `iter_commands()` and cannot be dispatched. This is a
startup-time enforcement, not a dispatch-time priority.

#### Command Shadow Policy

Plugin commands that share a name with a built-in command are subject to **Option A (reject)** policy:

- At load time, the shadowing command is **removed** from `_commands` and will not appear in `iter_commands()` or be dispatched.
- Log: `[plugin] command shadow rejected: '<name>' in '<module>' shadows built-in`
- When `plugin_strict = true`, a `PluginLoadError` is raised after all plugins are loaded, with a message containing `"Command builtin conflicts rejected: /help, /debug"` (comma-separated list of rejected command names).
- In non-strict mode (default), the rejection is silent beyond the log line — startup continues normally.
- `/plugin status` reports the count under `"Command shadows (rejected)"`.

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
| `load_plugins(plugin_dir, *, known_tools, override_policy, strict_mode)` | Import all `*.py` in dir; returns `PluginLoadResult` with loaded/failed/conflict counts; raises `PluginLoadError` in strict mode |
| `_reset_for_testing()` | Clear all registries (test-only) |

### Test Isolation

`_reset_for_testing()` is the **only** supported way to clear global registry state.

Rules:
- Tests that call `load_plugins()` or any `@register_*` decorator **must** call
  `_reset_for_testing()` in a `pytest.fixture(autouse=True)` before (and optionally after)
  each test function.
- Production code (non-test modules) must **never** call `_reset_for_testing()`.
- Direct mutation of `_commands`, `_tools`, or `_pipeline_post` is also forbidden in tests;
  use `_reset_for_testing()` + public decorators instead.

Example:
```python
import pytest
import shared.plugin_registry as plugin_registry

@pytest.fixture(autouse=True)
def reset_registry():
    plugin_registry._reset_for_testing()
    yield
    plugin_registry._reset_for_testing()
```

---

## Extension Rules

1. Plugin tools cannot be cached by `ToolExecutor` (only MCP tool results are cached)
2. Plugin commands that share a name with a built-in command are **rejected** at
   load time and removed from the registry. A `PluginLoadError` is raised in strict mode.
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

1. Subclass `MCPServer` in `scripts/mcp/<name>/server.py`; override `dispatch()`
2. Add `GET /v1/tools` endpoint returning tool definitions with `server_key` field
3. Add tool names to `shared/tool_constants.py` frozenset (owned by this server)
4. Add tool definitions to `config/tools_definitions.toml`
5. Create `config/<key>_mcp_server.toml` with app config and `[mcp_servers.<key>]` transport section
6. Add new files to `deploy/deploy.sh` copy list
7. Add startup step to `deploy/setup_services.sh`

See [04_mcp_03_routing_lifecycle_and_execution.md](04_mcp_03_routing_lifecycle_and_execution.md)
for full MCP server addition procedure.
