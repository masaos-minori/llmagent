---
title: "Agent Extension Points - Registry API and Rules"
category: agent
tags:
  - agent
  - extension-points
  - plugin-registry
  - extension-rules
  - mcp-server
related:
  - 05_agent_00_document-guide.md
  - 05_agent_11_01_extension-points-plugin-command.md
  - 05_agent_11_02_extension-points-tool-registration.md
source:
  - 05_agent_11_01_extension-points-plugin-command.md
---

# Agent Extension Points

- Runtime architecture → [05_agent_02_runtime-architecture.md](05_agent_02_runtime-architecture.md)

## Registry API (`shared/plugin_registry.py`)

| Function | Description |
|---|---|
| `get_command(name)` | `(handler, is_prefix) \| None` |
| `iter_commands()` | Dict snapshot of all registered commands |
| `get_tool(name)` | `Callable \| None` |
| `get_pipeline_post_stages()` | List snapshot of all post-rerank stage handlers |
| `load_plugins(plugin_dir, *, known_tools, override_policy, strict_mode)` | Import all `*.py` in dir; returns `PluginLoadResult` with loaded/failed/conflict counts; raises `PluginLoadError` in strict mode |

### Test Isolation

A test-only function is the **only** supported way to clear global registry state.

Rules:
- Tests that call `load_plugins()` or any `@register_*` decorator **must** call
  this function in a `pytest.fixture(autouse=True)` before (and optionally after)
  each test function.
- Production code (non-test modules) must **never** call this function.
- Direct mutation of internal registries is also forbidden in tests;
  use this function + public decorators instead.

Example:
```python
import pytest
import shared.plugin_registry as plugin_registry

@pytest.fixture(autouse=True)
def reset_registry():
    # Clear all registries (test-only function)
    yield
    # Clear all registries again after test
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

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_11_01_extension-points-plugin-command.md`
- `05_agent_11_02_extension-points-tool-registration.md`

## Keywords

Registry API
test isolation
extension rules
hook failure behavior
adding a new MCP server
