---
title: "Agent Extension Points - Plugin Architecture and Commands"
category: agent
tags:
  - agent
  - extension-points
  - plugin-architecture
  - register-command
related:
  - 05_agent_00_document-guide.md
  - 05_agent_11_extension-points-tool-registration.md
  - 05_agent_11_extension-points-registry-rules.md
source:
  - 05_agent_11_extension-points-plugin-command.md
---

# Agent Extension Points

- Runtime architecture → [05_agent_02_runtime-architecture.md](05_agent_02_runtime-architecture.md)

## Purpose

Document the plugin architecture, all `@register_*` decorators, extension rules,
and priority relationships between built-in features and extensions.

---

## Plugin Architecture

Plugins are Python files in `plugins/*.py` (relative to the project root, 2 levels above `scripts/`).

**Loading:**
1. Plugin registry initialization calls `plugin_registry.load_plugins(plugin_dir)` at startup
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
Built-in commands are matched first. If no built-in matches, plugin commands are tried. Plugin commands that share a name with a built-in
command are **rejected at load time** (removed from the plugin command registry).
They will not appear in `iter_commands()` and cannot be dispatched. This is a
startup-time enforcement, not a dispatch-time priority.

#### Command Shadow Policy

Plugin commands that share a name with a built-in command are subject to **Option A (reject)** policy:

- At load time, the shadowing command is **removed** from the command registry and will not appear in `iter_commands()` or be dispatched.
- Log: `[plugin] command shadow rejected: '<name>' in '<module>' shadows built-in`
- When `plugin_strict = true`, a `PluginLoadError` is raised after all plugins are loaded, with a message containing `"Command builtin conflicts rejected: /help, /debug"` (comma-separated list of rejected command names).
- In non-strict mode (default), the rejection is silent beyond the log line — startup continues normally.
- `/plugin status` reports the count under `"Command shadows (rejected)"`.

---

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_11_extension-points-tool-registration.md`
- `05_agent_11_extension-points-registry-rules.md`

## Keywords

plugin architecture
@register_command
command shadow policy
