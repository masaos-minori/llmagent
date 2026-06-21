# MCP Routing, Lifecycle, and Execution

- System overview → [04_mcp_01_system_overview.md](04_mcp_01_system_overview.md)

## Purpose

Document tool routing, server startup/shutdown lifecycle, ToolExecutor internals,
watchdog behavior, idle timeout, and the procedure for adding a new server.

---

## Tool Call Dispatch Flow

```
LLM returns tool_call
  → ToolRouteResolver.resolve(tool_name) → server_key
  → ToolExecutor.execute(tool_name, args)
       1. Plugin tool check (@register_tool)   — bypasses cache and MCP
       2. Cache check (TTL + LRU)             — returns cached result if hit
       3. _raw_execute()
            → McpServerHealthRegistry: is_unavailable? → return error immediately
            → LifecycleProtocol.ensure_ready(server_key)
            → concurrency semaphore acquire (if configured)
            → HttpTransport.call() or StdioTransport.call()
            → return ToolCallResult(output, is_error, request_id, server_key)
```

---

## ToolRouteResolver (`shared/route_resolver.py`)

Resolves `tool_name → server_key` in four steps (priority order):

1. **Discovery map (highest priority):** Live `/v1/tools` metadata with `server_key` field.
   Built from `build_discovery_map()` at startup when servers respond to `/v1/tools`.

2. **Tool registry:** Canonical source of truth from `shared/tool_registry.py`.
   The `ToolRegistry` singleton maps each tool name to exactly one server key.

3. **Config-driven:** `McpServerConfig.tool_names` provides an explicit mapping.
   Built at constructor time into an inverse dict `{tool_name: server_key}`.

4. **Static fallback (lowest priority):** `_fallback_route()` uses frozensets in `shared/tool_constants.py`:

| Tool set | Server key |
|---|---|
| `READ_TOOLS` (9 tools: list_directory, read_text_file, etc.) | `file_read` |
| `WRITE_TOOLS` (write_file, edit_file, create_directory, move_file) | `file_write` |
| `DELETE_TOOLS` (delete_file, delete_directory) | `file_delete` |
| `shell_run` | `shell` |
| `search_web` | `web_search` |
| `github_*` (prefix match) | `github` |
| `RAG_TOOLS` (rag_run_pipeline, rag_debug_pipeline) | `rag_pipeline` |
| `CICD_TOOLS` (trigger_workflow, get_workflow_runs, get_workflow_status, get_workflow_logs) | `cicd` |
| `MDQ_TOOLS` (search_docs, get_chunk, outline, index_paths, refresh_index, stats, grep_docs) | `mdq` |
| `GIT_TOOLS` (git_status, git_log, git_diff, git_branch, git_show, git_add, git_commit, git_checkout, git_pull, git_push) | `git` |
| `SQLITE_TOOLS` (query_sqlite) | `sqlite` |
| No match | `ValueError` |

**Note:** `query_sqlite` IS in `tool_constants.py` static table (routed to `sqlite` server key). No explicit `tool_names` config is required.

```python
resolver = ToolRouteResolver(server_configs)
server_key = resolver.resolve("read_text_file")  # → "file_read"
```

---

## Tool Registry (`shared/tool_registry.py`)

Single source of truth for MCP tool definitions and ownership.

### Ownership model

- Each tool belongs to **exactly one server** (identified by `server_key`).
- The registry is populated at import time from `tool_constants.py` frozensets.
- Config `mcp_servers.toml` `tool_names` lists are validated against the registry but not required as a source of truth.
- Server `/v1/tools` responses are validated against the registry at startup for drift detection.

### Drift validation

Three comparison functions detect configuration drift:

| Function | Compares | When called |
|---|---|---|
| `validate_routing_against_config()` | Config `tool_names` vs registry | Startup |
| `validate_routing_against_live()` | Live `/v1/tools` vs registry | Startup |
| `validate_all_routing()` | Both above combined | Startup |

Drift warnings appear at agent startup:

```
WARNING Routing drift [file_read]: [file_read] tool 'read_multiple_files' in registry but not in config. Update config/mcp_servers.toml tool_names or the registry to resolve.
```

### Adding a new tool

1. Add the tool name to the appropriate frozenset in `shared/tool_constants.py`.
2. The registry auto-populates from these frozensets at import time.
3. Update `config/mcp_servers.toml` `tool_names` for the owning server (validation will warn if missing).
4. Add full OpenAI function-calling format to `config/tools_definitions.toml` for LLM exposure.

### Key API

```python
from shared.tool_registry import get_registry, validate_all_routing

registry = get_registry()
server_key = registry.get_server_for_tool("read_text_file")  # → "file_read"
tool_names = registry.get_tool_names("file_read")  # → ["read_text_file", ...]
all_tools = registry.get_all_tool_names()  # → frozenset of all tool names
mismatches = validate_all_routing(server_configs, live_tool_lists)  # → dict[str, list[str]]
```

```python
executor = ToolExecutor(
    http=httpx.AsyncClient(...),
    cache_ttl=300.0,
    server_configs=server_configs,
    cache_max_size=200,
    concurrency_limits={"file_write": 1},
    lifecycle=lifecycle_router,
)
result = await executor.execute("read_text_file", {"path": "/opt/llm/..."})
# result: ToolCallResult(output, is_error, request_id, server_key)
```

### Cache behavior

- Only caches `is_error=False` results
- Cache key: `f"{tool_name}:{_json_dumps(args)}"` (plain string; NOT MD5)
- Entries expire after `cache_ttl` seconds
- LRU eviction when `cache_max_size > 0` (`0` = unlimited)
- Cache hit: `request_id=""` (no live request made)
- Statistics: `stat_cache_hits: int`

### Concurrency limits

`concurrency_limits={"server_key": N}` limits concurrent calls to N per server.
Implemented as lazily-created `asyncio.Semaphore`. Unknown keys → warning log only.

### Side-effect detection

```python
_SIDE_EFFECT_TOOLS = WRITE_TOOLS | DELETE_TOOLS | frozenset({"shell_run"})
is_side_effect(tool_name: str) -> bool
```

When `execute_all_tool_calls()` detects any side-effect tool, it serializes all calls in
that round (even non-side-effect tools), regardless of `serial_tool_calls` setting.

---

## HttpTransport (`shared/tool_executor.py`)

```python
HttpTransport(http, base_url, server_key, cfg=McpServerConfig)
result = await transport.call("tool_name", {"arg": "val"})
```

- Adds `Authorization: Bearer <token>` when `cfg.auth_token` is non-empty
- Catches all HTTP and request errors; returns `is_error=True` with message
- `set_session_id(session_id)` injects `X-Session-Id` header per request

---

## StdioTransport (`shared/tool_executor.py`)

```python
transport = StdioTransport(cmd=["python", "-m", "mcp.shell.server", "--stdio"],
                            server_key="shell", working_dir="", env=None)
await transport.start()
result = await transport.call("shell_run", {"command": "ls"})
await transport.stop()
```

- per-instance `asyncio.Lock` serializes concurrent calls
- `is_alive() -> bool`: `returncode is None`
- Timeout: `_STDIO_CALL_TIMEOUT = 60.0` seconds
- `stop()`: close stdin → wait 5s → SIGTERM → wait 3s → SIGKILL
- `working_dir` non-empty: `Path(working_dir).is_dir()` checked at `start()` (raises `ValueError` if missing)
- `env` non-empty: `{**os.environ, **env}` merged for subprocess

---

## McpServerHealthRegistry (`shared/mcp_config.py`)

Per-server failure tracker injected into `ToolExecutor`.

| State | Condition |
|---|---|
| `HEALTHY` | No failures or after successful call |
| `DEGRADED` | Failure count < threshold (default 3) |
| `UNAVAILABLE` | Failure count ≥ threshold; `_raw_execute()` blocks dispatch |

| Method | Description |
|---|---|
| `record_failure(server_key)` | Increment failure; return new state |
| `record_success(server_key)` | Reset failure count; returns `None` |
| `get_state(server_key)` | Current state; returns HEALTHY for unknown key |
| `is_unavailable(server_key)` | `True` if UNAVAILABLE |

> **Resolved (2026-06-18):** `ToolExecutor._raw_execute()` now calls `record_success()` on transport success and `record_failure()` on `TransportError`. DEGRADED/UNAVAILABLE transitions work correctly.

---

## _ServerLifecycleRouter (`factory.py`)

Manages HTTP subprocess and stdio server lifecycle. Implements `LifecycleProtocol`.

```python
class _ServerLifecycleRouter:
    async def ensure_ready(server_key: str) -> None
    async def shutdown_all() -> None
    async def shutdown_idle() -> None
    def restart(server_key: str) -> None  # for watchdog
```

### ensure_ready (ondemand stdio)

1. Fast path: `transport.is_alive()` (no lock)
2. Acquire per-server `asyncio.Lock`
3. Double-check: `transport.is_alive()` again
4. If not alive: `StdioTransport.start()` + `tool_executor.set_transport()`

### startup_mode behavior

| startup_mode | When | Action |
|---|---|---|
| `persistent` (stdio) | Agent launch | `StdioTransport.start()` immediately |
| `ondemand` (stdio) | First tool call | `ensure_ready()` auto-starts |
| `subprocess` (http) | Agent launch | `start_http_subprocess()` — spawn uvicorn, poll `/health` up to `startup_timeout_sec` |

---

## Watchdog (`_watchdog_loop`)

Runs as asyncio background task. Activated when `mcp_watchdog_interval > 0`.

**Profile-aware defaults:**

| `security_profile` | `mcp_watchdog_interval` default |
|---|---|
| `local` (default) | `0.0` — watchdog disabled |
| `production` | `30.0` — watchdog enabled |

Set `mcp_watchdog_interval` explicitly in `config/agent.toml` to override the profile default.

At startup, the agent logs one of:
- `Watchdog enabled: interval=<N>s, max_restarts=<M>` — when interval > 0
- `Watchdog disabled (mcp_watchdog_interval=0)` — when interval is 0

- Polls every `mcp_watchdog_interval` seconds
- Checks `/health` for HTTP servers (all modes: subprocess, persistent, externally-managed)
- On failure: calls `_ServerLifecycleRouter.restart(server_key)` for subprocess-mode servers
  1. `proc.terminate()` → wait 3s → `proc.kill()` if needed
  2. `start_http_subprocess()` — respawn + poll `/health`
- Externally-managed servers: logs warning only (no restart capability)
- Max restarts: `mcp_watchdog_max_restarts` (default 3)
- `healthcheck_mode="ping_tool"` (stdio): sends `__list_tools__` RPC to verify response

### idle_timeout for ondemand servers

- `0` (default): server stays alive until agent exits
- Positive value: `shutdown_idle()` in each watchdog cycle stops servers idle > `idle_timeout_sec`
- Actual stop may be delayed up to `idle_timeout_sec + mcp_watchdog_interval`

---

## Lifecycle Flow

```
AgentREPL.run()
  → _start_mcp_servers()
       → startup_mode="persistent" (stdio): StdioTransport.start()
       → startup_mode="subprocess" (http): start_http_subprocess() + health poll
  → [REPL loop]
       → first tool call on ondemand server: ensure_ready() auto-starts
       → watchdog task: health check + restart on failure
  → finally: lifecycle.shutdown_all() + AsyncClient.close()
```

---

## Adding a New MCP Server

### Option 1: Wizard (recommended)

```
agent[:#N]> /mcp install <server-name>
```

Generates:
- `scripts/mcp/<name>/server.py` — FastAPI scaffold (`MCPServer` subclass)
- `config/<module>_mcp_server.json` — config template
- `conf.d/<server-name>` — API key env template (optional)

### Option 2: Manual steps

1. Subclass `MCPServer` in `mcp/<name>/server.py`; override `dispatch()`
2. Add `GET /v1/tools` endpoint returning tool definitions with `server_key` field
3. Add tool names to `shared/tool_constants.py` frozenset (owned by this server)
4. Add tool definitions to `config/agent.toml` → `tool_definitions`
5. Add `[mcp_servers.<key>]` entry to `config/mcp_servers.toml` with `tool_names`
6. Add new files to `deploy/deploy.sh` copy list
7. Add startup step to `deploy/setup_services.sh`

### Config-driven routing for new server

The tool registry auto-populates from `tool_constants.py` frozensets at import time.
Add `tool_names` to the server config in `mcp_servers.toml` to match the registry:

```toml
[mcp_servers.my_server]
transport = "http"
url = "http://127.0.0.1:8015"
tool_names = ["my_tool_a", "my_tool_b"]
```

If `tool_names` is omitted or incomplete, the registry will still route correctly (priority 2),
but startup drift validation will emit warnings.
