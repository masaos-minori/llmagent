# MCP Routing, Lifecycle, and Execution

- System overview → [04_mcp_01_system_overview.md](04_mcp_01_system_overview.md)

## Purpose

Document tool routing, server startup/shutdown lifecycle, ToolExecutor internals,
watchdog behavior, idle timeout, and the procedure for adding a new server.

---

## Tool Call Dispatch Flow

Agent sets `server_key` and `tool_name` in dispatch log context. `X-Request-Id` (from server response header) correlates the agent dispatch log with the transport and server audit log.

```
LLM returns tool_call
   → ToolRouteResolver.resolve(tool_name) → server_key
   → ToolExecutor.execute(tool_name, args)
        1. Plugin tool check (@register_tool)   — bypasses cache and MCP
        2. Cache check (TTL + LRU)             — returns cached result if hit; no HealthRegistry update
        3. _raw_execute()
             → McpServerHealthRegistry: is_unavailable? → return error immediately (no attempt made)
             → LifecycleProtocol.ensure_ready(server_key)
             → concurrency semaphore acquire (if configured)
             → HttpTransport.call() or StdioTransport.call()
             → HealthRegistry.record_success() on success / record_failure() on transport error
             → return ToolCallResult(output, is_error, request_id, server_key)
```

---

## ToolRouteResolver (`shared/route_resolver.py`)

Resolves `tool_name → server_key` in two steps (priority order). At runtime, **discovery map (live `/v1/tools`) has the highest priority and overrides all lower layers**:

1. **Discovery map (highest priority):** Live `/v1/tools` metadata with `server_key` field.
    Built from `build_discovery_map()` at startup when servers respond to `/v1/tools`.
    If a tool is found here, it routes to the server specified in the discovery map — even if the registry says something different.

2. **Tool registry:** Primary routing layer from `shared/tool_registry.py`.
    The `ToolRegistry` singleton maps each tool name to exactly one server key. Superseded by discovery map for any tool found in live `/v1/tools` responses.

3. **Unknown tools fail immediately:** When a tool name is not found in any routing layer, `ValueError` is raised with the message `"Unknown tool: <tool_name>"`. No fallback exists — every tool must be explicitly registered.

4. **Unknown tools fail immediately:** When a tool name is not found in any routing layer, `ValueError` is raised with the message `"Unknown tool: <tool_name>"`. No fallback exists — every tool must be explicitly registered.

| Tool set | Server key |
|---|---|
| `READ_TOOLS` (9 tools: list_directory, read_text_file, etc.) | `file_read` |
| `WRITE_TOOLS` (write_file, edit_file, create_directory, move_file) | `file_write` |
| `DELETE_TOOLS` (delete_file, delete_directory) | `file_delete` |
| `shell_run` | `shell` |
| `search_web` | `web_search` |
| `GITHUB_TOOLS` (github_search_repositories, github_get_file_contents) | `github` |
| `RAG_TOOLS` (rag_run_pipeline, rag_debug_pipeline) | `rag_pipeline` |
| `CICD_TOOLS` (trigger_workflow, get_workflow_runs, get_workflow_status, get_workflow_logs) | `cicd` |
| `MDQ_TOOLS` (search_docs, get_chunk, outline, index_paths, refresh_index, stats, grep_docs) | `mdq` |
| `GIT_TOOLS` (git_status, git_log, git_diff, git_branch, git_show, git_add, git_commit, git_checkout, git_pull, git_push) | `git` |
| `SQLITE_TOOLS` (query_sqlite) | `sqlite` |
| No match | `ValueError` |

**Note:** `query_sqlite` IS in `tool_constants.py` static table (routed to `sqlite` server key). No explicit `tool_names` config is required.

**Important:** Unknown tools fail immediately with a `ValueError`. New tools must always be registered via `ToolRegistry` (via `tool_constants.py` frozensets) or live discovery.

```python
resolver = ToolRouteResolver(server_configs)
server_key = resolver.resolve("read_text_file")  # → "file_read"
```

---

## Routing Source of Truth

The `ToolRouteResolver` resolves tool calls using a two-layer cascade. At runtime, **discovery map (live `/v1/tools`) has the highest priority and overrides all lower layers**.

| Input | Role | Requirement |
|---|---|---|
| Live `/v1/tools` discovery | **Priority 1 — override source** | Optional; if present, supersedes registry for any tool found here |
| `shared/tool_registry.py` | **Priority 2 — primary routing layer** | Read-only at runtime; changes require code edit |

**Summary of ownership rules:**
- To add a tool: add to the appropriate frozenset in `tool_constants.py`. The registry auto-populates at import time.
- Discovery map takes precedence over the registry — if `/v1/tools` returns a different `server_key` for a tool, the discovery map wins.
- `tool_names` in config is NOT a routing input; it is drift validation metadata only.
- Unknown tools fail immediately with `ValueError` — no fallback exists.

---

## Tool Registry (`shared/tool_registry.py`)

Single source of truth for MCP tool definitions and ownership.

| ソース | 種別 | 説明 |
|---|---|---|
| Live `/v1/tools` discovery | **Priority 1** | ルーティングの最上位優先度; レジストリを上書き |
| `shared/tool_registry.py` | **Priority 2** | ツール→サーバー逆引き; `tool_constants.py` frozensetからimport時に自動構築 |

### Ownership model

- Each tool belongs to **exactly one server** (identified by `server_key`).
- The registry is populated at import time from `tool_constants.py` frozensets.
- Config `mcp_servers.toml` `tool_names` lists are validated against the registry but not required as a source of truth.
- Server `/v1/tools` responses are validated against the registry at startup for drift detection.
- **Important:** Live discovery map (priority 1) can override the registry. If `/v1/tools` returns a different `server_key` for a tool than the registry, the discovery map wins.

### Drift validation

Three comparison functions detect configuration drift:

| Function | Compares | When called |
|---|---|---|
| `validate_routing_against_config()` | Config `tool_names` vs registry | Startup (`check_routing_drift()` in `repl_health.py`) |
| `validate_routing_against_live()` | Live `/v1/tools` vs registry | Not yet wired (future) |
| `validate_all_routing()` | Both above combined | Not yet wired (future) |

> **Startup validation semantics** — The `validate_routing_against_live()` and
> `validate_all_routing()` functions above compare live `/v1/tools` against the
> internal routing registry. These are distinct from `_check_tool_definitions` in
> `repl_health.py`, which compares configured `tool_definitions` (from `agent.toml`)
> against live `/v1/tools`. For `tool_definitions_strict` startup-failure behavior,
> see [04_mcp_06 §Startup Validation Behavior](04_mcp_06_configuration_and_operations.md#startup-validation-behavior-tool_definitions_strict).

Drift warnings appear at agent startup:

```
WARNING Routing drift [file_read]: [file_read] tool 'read_multiple_files' in registry but not in config. Update config/mcp_servers.toml tool_names or the registry to resolve.
```

### Adding a new tool

| Step | Action | Required? |
|---|---|---|
| 1 | Add the tool name to the appropriate frozenset in `shared/tool_constants.py` | **[Required]** |
| 2 | Registry auto-populates from these frozensets at import time — no manual registry edit needed | (automatic) |
| 3 | Implement `dispatch()` handler in the owning MCP server (`mcp/<name>/server.py`) | **[Required]** |
| 4 | Expose tool in `/v1/tools` endpoint (return tool definition with `server_key` field) | **[Recommended]** — enables priority-1 discovery routing |
| 5 | Add LLM schema to `config/tools_definitions.toml` (OpenAI function-calling format) | **[Required]** — if tool should be visible to LLM |
| 6 | Add `tool_safety_tiers` entry in `config/agent.toml` for the new tool | **[Required]** — all tools must have a declared safety tier |
| 7 | Add tool name to `tool_names` in `config/mcp_servers.toml` for the owning server | **[Optional]** — enables startup drift validation only; routing does not require it |

**Recommended procedure**: Add to ToolRegistry frozenset (step 1) + expose in `/v1/tools` endpoint (step 4). Config `tool_names` (step 7) is NOT a routing input; it is drift validation metadata only. Unknown tools fail immediately — no fallback exists.

### Verification

After completing registration:

```bash
uv run pytest tests/test_tool_constants.py tests/test_route_resolver.py -v
```

Expected: all routing tests pass. If `tool_definitions_strict = true`, restart the agent and confirm startup logs show `"Routing: N/N tools mapped"` with no unmapped warnings.

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
- **Retry:** retries on HTTP 429/502/503/504, up to 3 attempts with decreasing delay: attempt 0 waits 4s, attempt 1 waits 2s, attempt 2 waits 1s before the final exhaustion error. Formula: 2^(RETRY_MAX - attempt - 1). This is NOT exponential backoff (delays decrease with each attempt). Only the final outcome (success or TransportError after all retries exhausted) is recorded in HealthRegistry.
- **Non-retryable errors:** HTTP timeout (`httpx.TimeoutException`) and HTTPStatusError for non-429/502/503/504 status codes are immediately propagated without retry.

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

**State transitions:**

```
HEALTHY ──(failure × threshold)──→ UNAVAILABLE
   ↑                                    │
   │                            (cooldown 30s elapsed)
   │                                    ↓
   └──(record_success)────────── HALF_OPEN (trial probe)
                                        │
                              (failure)─┘ → UNAVAILABLE (cooldown reset)
```

| State | Condition |
|---|---|
| `HEALTHY` | No failures or after successful call |
| `DEGRADED` | Failure count < threshold (default 3) |
| `UNAVAILABLE` | Failure count ≥ threshold; dispatch blocked |
| `HALF_OPEN` | 30s cooldown elapsed; one trial dispatch allowed |

| Method | Description |
|---|---|
| `record_failure(server_key)` | Increment failure count; `HALF_OPEN → UNAVAILABLE` (cooldown reset); threshold reached → `UNAVAILABLE` |
| `record_success(server_key)` | Reset failure count and `_unavailable_since`; `HALF_OPEN → HEALTHY` |
| `get_state(server_key)` | Current state; returns `HEALTHY` for unknown key |
| `is_unavailable(server_key)` | `True` if `UNAVAILABLE` and cooldown not yet elapsed; side effect: transitions to `HALF_OPEN` when cooldown elapses |

**Constructor:** `McpServerHealthRegistry(failure_threshold=3, half_open_cooldown_sec=30.0)`
- `half_open_cooldown_sec`: seconds after entering `UNAVAILABLE` before a trial dispatch is allowed (default 30s, fixed — not exponential backoff)

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

> **Production transport guidance:**
> For production deployments, use `transport = "http"` with `startup_mode = "subprocess"` for agent-managed HTTP servers (agent spawns uvicorn), or `startup_mode = "persistent"` for pre-existing HTTP servers (agent connects only).
> HTTP transports support watchdog, health checks, and remote monitoring.
> `stdio` transport serializes all requests through a single `asyncio.Lock` and provides
> no health-check endpoint — use it only for local/embedded single-tool subprocesses.
>
> See [04_mcp_02 §When to use stdio](04_mcp_02_protocol_and_transport.md#when-to-use-stdio).

| startup_mode | When | Action |
|---|---|---|
| `persistent` (stdio) | Agent launch | `StdioTransport.start()` immediately |
| `ondemand` (stdio) | First tool call | `ensure_ready()` auto-starts |
| `subprocess` (http) | Agent launch | `start_http_subprocess()` — spawn uvicorn, poll `/health` up to `startup_timeout_sec` |
| `persistent` (http) | Pre-existing | Agent connects to existing HTTP endpoint; no lifecycle action needed |

---

## End-to-End Tool Call Tracing

### Correlation Keys

| Key | Created by | Where it appears |
|---|---|---|
| `X-Session-Id` | Agent (`ctx.session.session_id`) | HTTP request header; MCP server access log; agent audit log |
| `X-Request-Id` | MCP server (per-request UUID) | HTTP response header; MCP server access log; agent audit log (`x_request_id`) |
| `server_key` | `McpServerConfig.key` | Agent routing log; `ToolCallResult.server_key`; health registry; transport error counters |
| `tool_name` | LLM tool call | Agent audit log; MCP server request log; tool error counters |

To trace one tool call, join on `X-Request-Id` (unique per call) and `X-Session-Id` (spans the session).

---

### Success Path Example

```
1. Agent: LLM emits tool_use for "read_text_file"
   → tool_runner.execute_one_tool_call(ctx, name="read_text_file", ...)
   → ToolRouteResolver.resolve("read_text_file") → server_key="file_read"

2. Agent → Server (HTTP):
   POST /v1/call_tool
   X-Session-Id: 42
   body: {"name": "read_text_file", "args": {...}}

3. MCP server (file-read-mcp):
   Server log: INFO [42] read_text_file args=... → OK
   Response: X-Request-Id: abc-123, is_error=false, result="..."

4. Agent receives:
   ToolCallResult(output="...", is_error=False, request_id="abc-123", server_key="file_read")

5. Agent audit_tool_exec():
    audit log entry (JSON-lines): {"event":"tool_exec","task_id":"...","tool":"read_text_file","mcp_request_id":"abc-123","is_error":false,"error_type":"","ts":...}

6. Health registry:
   HealthRegistry.record_success("file_read") → state remains HEALTHY
```

---

### Failure Path Example (Transport Error)

```
1-2. Same as above.

3. MCP server unreachable (timeout / 5xx):
   HttpTransport raises TransportError.

4. Agent:
   ToolExecutor._record_transport_error("file_read", error)
   → stat_transport_errors["file_read"] += 1
   → HealthRegistry.record_failure("file_read") → state: HEALTHY → DEGRADED

5. ToolCallResult:
   (output=str(error), is_error=True, server_key="file_read", error_type="transport")

6. audit_tool_exec():
    audit log (JSON-lines): {"event":"tool_exec","task_id":"...","tool":"read_text_file","mcp_request_id":"","is_error":true,"error_type":"transport","ts":...}
    Note: mcp_request_id="" because no response was received.

7. Watchdog (next interval):
   repl_health.watchdog_loop() polls file-read-mcp /health
   → if alive: HealthRegistry.record_success("file_read") → HALF_OPEN → HEALTHY
   → if dead: HealthRegistry.record_failure("file_read") → DEGRADED → UNAVAILABLE
```

---

### Tool Error vs Transport Error in Tracing

| Field | Tool error | Transport error |
|---|---|---|
| `is_error` | `True` | `True` |
| `error_type` | `"tool"` | `"transport"` |
| `mcp_request_id` | Set (server responded) | `""` (no response received) |
| `HealthRegistry` | `record_success()` (server responded) | `record_failure()` (server unreachable) |
| `stat_tool_errors` | Incremented | Not changed |
| `stat_transport_errors` | Not changed | Incremented |

A tool error means the server processed the request but returned an error.
A transport error means the agent never received a response from the server.

See [04_mcp_06 §End-to-End Tool Call Tracing](04_mcp_06_configuration_and_operations.md#end-to-end-tool-call-tracing) for the operational tracing procedure.

---

## Watchdog (`_watchdog_loop`)

MCP 障害の診断手順については `04_mcp_06` §MCP Failure Diagnosis を参照。

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
- `healthcheck_mode="ping_tool"` (stdio): sends `__list_tools__` RPC to verify response (stdio control-plane only, not part of routing)

### idle_timeout for ondemand servers

- `0` (default): server stays alive until agent exits
- Positive value: `shutdown_idle()` in each watchdog cycle stops servers idle > `idle_timeout_sec`
- Actual stop may be delayed up to `idle_timeout_sec + mcp_watchdog_interval`

---

## Lifecycle Flow

ツール定義の起動時バリデーション動作については `04_mcp_06` §Startup Validation Behavior を参照。

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

### How to Add a New Tool Safely

When adding a new tool, follow the canonical 7-step procedure from the [Adding a new tool](#adding-a-new-tool) section above.

Key points:
1. **Add the tool name to `shared/tool_constants.py` frozenset** [Required] — `_populate_default_registry()` reads these frozensets at import time and builds the priority-2 routing registry automatically. No manual registry edit is needed.
2. **Add `GET /v1/tools` endpoint** [Recommended] — enables priority-1 live discovery routing, which overrides all lower layers.
3. **Add `tool_names` to server config** [Optional] — drift validation hint only; routing does not require it.
4. **Add LLM schema to `config/tools_definitions.toml`** [Required if tool visible to LLM]
5. **Add `tool_safety_tiers` entry in `config/agent.toml`** [Required — all tools must have a declared safety tier]

```toml
[mcp_servers.my_server]
transport = "http"
url = "http://127.0.0.1:8015"
tool_names = ["my_tool_a", "my_tool_b"]
```

### Routing Priority Summary

| Layer | Priority | Role | Override? |
|---|---|---|---|
| Live `/v1/tools` discovery | 1 (highest) | Runtime override from MCP server tool list | Yes — supersedes all lower layers |
| `ToolRegistry` (auto-populated from `tool_constants.py` frozensets at import time) | 2 | Primary routing source; populated by `_populate_default_registry()` | No — only overridden by layer 1 |

**Key rules:**
- **New tools must always be registered via `ToolRegistry`** (layer 2). Unknown tools fail immediately with `ValueError`.
- **Live discovery (layer 1) can override routing** — if `/v1/tools` returns a different `server_key`, the discovery map wins.
- **Config `tool_names` are not routing inputs** — they are validation hints for drift detection only.

### New Server/Tool Registration Checklist

| Artifact | Required? | Notes |
|---|---|---|
| `shared/tool_constants.py` — add tool to frozenset | **Required** | `_populate_default_registry()` reads frozensets at import |
| `config/tools_definitions.toml` — add LLM schema | **Required** (if tool visible to LLM) | OpenAI function-calling format; required for the LLM to call the tool |
| `config/agent.toml` — add `tool_safety_tiers` entry | **Required** | All tools must have a declared safety tier |
| `config/<server>.toml` — server config file | **Required** | Server must be defined before first use |
| `deploy/deploy.sh` — add install/copy step | **Required** (new server) | Deployment must include the new server |
| Update `routing.md` | **Required** | Document guide must reference the new server |
| `config/mcp_servers.toml` `tool_names` | **[Optional]** | Drift validation hint only; routing does not require it |

### Manual steps

1. Subclass `MCPServer` in `mcp/<name>/server.py`; override `dispatch()`
2. Add `GET /v1/tools` endpoint returning tool definitions with `server_key` field
3. Add tool names to `shared/tool_constants.py` frozenset (owned by this server)
4. Add LLM schemas to `config/tools_definitions.toml` (OpenAI function-calling format)
5. Add `tool_safety_tiers` entries to `config/agent.toml` for each tool
6. Add `[mcp_servers.<key>]` entry to `config/mcp_servers.toml` with `tool_names` (optional drift hint)
7. Add new files to `deploy/deploy.sh` copy list
7. Add startup step to `deploy/setup_services.sh`

### Tool_names config (drift detection only)

The tool registry auto-populates from `tool_constants.py` frozensets at import time.
Optionally add `tool_names` to the server config in `mcp_servers.toml` for drift detection:

```toml
[mcp_servers.my_server]
transport = "http"
url = "http://127.0.0.1:8015"
tool_names = ["my_tool_a", "my_tool_b"]
```

If `tool_names` is omitted or incomplete, the registry will still route correctly (priority 2),
but startup drift validation will emit warnings.
