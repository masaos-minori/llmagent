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
        3. MCP server dispatch via internal method
             → McpServerHealthRegistry: is_unavailable? → return error immediately (no attempt made)
             → LifecycleProtocol.ensure_ready(server_key)
             → concurrency semaphore acquire (if configured)
             → HttpTransport.call()
             → HealthRegistry.record_success() on success / record_failure() on transport error
             → return ToolCallResult(output, is_error, request_id, server_key)
```

---

## ToolRouteResolver (`shared/route_resolver.py`)

Resolves `tool_name → server_key` using `ToolRegistry` as the **sole routing authority**.
Live `/v1/tools` discovery is used only for startup drift validation, not for routing.

1. **Tool registry (sole routing authority):** `ToolRegistry` singleton from `shared/tool_registry.py`.
    Maps each tool name to exactly one server key. Populated at import time from `tool_constants.py` frozensets via internal registry population function.

2. **Unknown tools fail immediately:** When a tool name is not found in the registry, `ValueError` is raised with the message `"Unknown tool: <tool_name>"`. No fallback exists — every tool must be explicitly registered in `tool_constants.py`.

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
| `MDQ_TOOLS` (search_docs, get_chunk, outline, index_paths, refresh_index, stats, grep_docs, fts_consistency_check, fts_rebuild) | `mdq` |
| `GIT_TOOLS` (git_status, git_log, git_diff, git_branch, git_show, git_add, git_commit, git_checkout, git_pull, git_push) | `git` |
| No match | `ValueError` |

**Important:** Unknown tools fail immediately with a `ValueError`. New tools must always be registered via `ToolRegistry` (via `tool_constants.py` frozensets).

```python
resolver = ToolRouteResolver(server_configs)
server_key = resolver.resolve("read_text_file")  # → "file_read"
```

---

## Routing Source of Truth

`ToolRegistry` is the **sole routing authority**. Live `/v1/tools` discovery is validation-only and does not affect routing decisions.

| Input | Role | Requirement |
|---|---|---|
| `shared/tool_registry.py` | **Sole routing authority** | Populated at import time from `tool_constants.py` frozensets |
| Live `/v1/tools` discovery | **Validation source only** | Optional; used by `check_routing_drift_vs_live()` at startup to detect drift — does not affect routing |

**Summary of ownership rules:**
- To add a tool: add to the appropriate frozenset in `tool_constants.py`. The registry auto-populates at import time.
- Live `/v1/tools` is used for startup drift validation only — it does NOT override registry routing.
- `tool_names` in config is NOT a routing input; it is drift validation metadata only.
- Unknown tools fail immediately with `ValueError` — no fallback exists.

---

## Tool Registry (`shared/tool_registry.py`)

Single source of truth for MCP tool definitions and ownership.

| ソース | 種別 | 説明 |
|---|---|---|
| `shared/tool_registry.py` | **唯一のルーティング権威** | ツール→サーバー逆引き; `tool_constants.py` frozensetからimport時に自動構築 |
| Live `/v1/tools` discovery | **起動時バリデーションのみ** | ルーティングには使用しない; `check_routing_drift_vs_live()` でドリフト検出に使用 |

### Ownership model

- Each tool belongs to **exactly one server** (identified by `server_key`).
- The registry is populated at import time from `tool_constants.py` frozensets.
- Config `*_mcp_server.toml` `tool_names` lists (in each `[mcp_servers.<key>]` section) are validated against the registry but not required as a source of truth.
- Server `/v1/tools` responses are validated against the registry at startup for drift detection.
- **Important:** Live discovery does NOT override the registry. If `/v1/tools` returns a different `server_key` for a tool than the registry, this is flagged as drift by `check_routing_drift_vs_live()` at startup.

### Drift validation

Three comparison functions detect configuration drift:

| Function | Compares | When called |
|---|---|---|
| `validate_routing_against_config()` | Config `tool_names` vs registry | Startup (`check_routing_drift()` in `repl_health.py`) |
| `validate_routing_against_live()` | Live `/v1/tools` vs registry | Startup (`check_routing_drift_vs_live()` in `repl_health.py`) |
| `validate_all_routing()` | Both above combined | Not yet wired (future) |

> **Startup validation semantics** — The `validate_routing_against_live()` and
> `validate_all_routing()` functions above compare live `/v1/tools` against the
> internal routing registry. These are distinct from the tool definitions check in
> `repl_health.py`, which compares configured `tool_definitions` (from `agent.toml`)
> against live `/v1/tools`. For `tool_definitions_strict` startup-failure behavior,
> see [04_mcp_06 §Startup Validation Behavior](04_mcp_06_configuration_and_operations.md#startup-validation-behavior-tool_definitions_strict).

Drift warnings appear at agent startup:

```
WARNING Routing drift [file_read]: [file_read] tool 'read_multiple_files' in registry but not in config. Update file_read_mcp_server.toml [mcp_servers.file_read] tool_names or the registry to resolve.
```

### Adding a new tool

| Step | Action | Required? |
|---|---|---|
| 1 | Add the tool name to the appropriate frozenset in `shared/tool_constants.py` | **[Required]** |
| 2 | Registry auto-populates from these frozensets at import time — no manual registry edit needed | (automatic) |
| 3 | Implement `dispatch()` handler in the owning MCP server (`mcp/<name>/server.py`) | **[Required]** |
| 4 | Expose tool in `/v1/tools` endpoint (return tool definition with `server_key` field) | **[Recommended]** — enables startup drift detection via `check_routing_drift_vs_live()` |
| 5 | Add LLM schema to `config/tools_definitions.toml` (OpenAI function-calling format) | **[Required]** — if tool should be visible to LLM |
| 6 | Add `tool_safety_tiers` entry in `config/security.toml` for the new tool | **[Required]** — all tools must have a declared safety tier |
| 7 | Add tool name to `tool_names` in `config/<key>_mcp_server.toml` `[mcp_servers.<key>]` section | **[Optional]** — enables startup drift validation only; routing does not require it |

**Recommended procedure**: Add to ToolRegistry frozenset (step 1) + expose in `/v1/tools` endpoint (step 4). Config `tool_names` (step 7) is NOT a routing input; it is drift validation metadata only. Unknown tools fail immediately — no fallback exists. Exposing the tool in `/v1/tools` enables startup drift detection via `check_routing_drift_vs_live()`; it does not affect routing.

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
- Cache key: `"tool_name:args_json"` (plain string; NOT MD5)
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
- Raises `TransportError` on all transport-level failures (timeout, HTTP non-2xx, malformed response, retry exhausted); does NOT return `is_error=True` directly
- Transport error handler catches `TransportError` and converts it to `ToolCallResult(error_type="transport")`
- `set_session_id(session_id)` injects `X-Session-Id` header per request
- **Retry:** retries on HTTP 429/502/503/504, up to 3 attempts with decreasing delay: attempt 0 waits 4s, attempt 1 waits 2s, attempt 2 waits 1s before the final exhaustion error. Formula: 2^(RETRY_MAX - attempt - 1). This is NOT exponential backoff (delays decrease with each attempt). Only the final outcome (success or TransportError after all retries exhausted) is recorded in HealthRegistry.
- **Non-retryable errors:** HTTP timeout (`httpx.TimeoutException`) and HTTPStatusError for non-429/502/503/504 status codes are immediately propagated without retry.

---

## McpServerHealthRegistry (`shared/mcp_config.py`)

Per-server failure tracker created in `_build_tool_executor()` (factory.py) and shared
between `ToolExecutor` (via `set_health_registry()`) and `AppServices.health_registry`.
Both hold the same object; health state recorded by `ToolExecutor` is immediately visible
via `AppServices.health_registry`.

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
| `record_degraded(server_key, reason)` | Explicitly set state to `DEGRADED` with an optional reason string; called by watchdog for reachable-but-non-restartable servers |
| `get_degraded_reason(server_key)` | Return the last recorded degraded reason string, or `None` if none set |
| `record_success(server_key)` | Reset failure count, unavailable timestamp, and degraded reasons; `HALF_OPEN → HEALTHY` |
| `get_state(server_key)` | Current state; returns `HEALTHY` for unknown key |
| `is_unavailable(server_key)` | `True` if `UNAVAILABLE` and cooldown not yet elapsed; side effect: transitions to `HALF_OPEN` when cooldown elapses |

**Constructor:** `McpServerHealthRegistry(failure_threshold=3, half_open_cooldown_sec=30.0)`
- `half_open_cooldown_sec`: seconds after entering `UNAVAILABLE` before a trial dispatch is allowed (default 30s, fixed — not exponential backoff)

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
   Transport error handler records the error for "file_read"
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

## Watchdog

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
- Calls `GET /health` for HTTP servers (all modes: subprocess, persistent, externally-managed)
- **Restart is gated on `restart_recommended` body field:**
  - `reachable=False` (no HTTP response): attempt restart for subprocess-mode servers if under `mcp_watchdog_max_restarts`
  - `reachable=True` and `restart_recommended=true`: attempt restart as above
  - `reachable=True` and `restart_recommended=false`: no restart; if `operator_action_required=true`, log WARNING (missing credentials, missing binary, etc.)
- On restart: terminates the subprocess (`proc.terminate()`), waits 3s, kills if needed; then starts a new HTTP subprocess and polls `/health`
- Externally-managed servers (non-subprocess): logs warning only, no restart
- Max restarts: `mcp_watchdog_max_restarts` (default 3)

---

## Lifecycle Flow

ツール定義の起動時バリデーション動作については `04_mcp_06` §Startup Validation Behavior を参照。

```
AgentREPL.run()
  → MCP server startup
       → startup_mode="subprocess" (http): start_http_subprocess() + health poll
            stderr → /opt/llm/logs/mcp/{server_key}.stderr.log (append mode)
       → startup_mode="persistent" (http): no lifecycle action needed
   → [REPL loop]
        → tool call → ToolExecutor._raw_execute()
             → ensure_ready(server_key):
                  if _shutting_down: return immediately (shutdown guard)
                  if subprocess-mode and not running: start() [auto-restart on demand]
        → watchdog task: health check + restart on failure
   → finally: lifecycle.shutdown_all()
                  sets _shutting_down=True (blocks further start/restart calls)
                + close stderr log file handles
                + AsyncClient.close()
```

`_ServerLifecycleRouter._shutting_down` guards `ensure_ready()`, `start_http_subprocess()`,
`restart()`, and `shutdown_idle()`: once `shutdown_all()` is called, these methods return
immediately with a log line and do not delegate to `HttpServerLifecycleManager`.

### Process Introspection

`HttpServerLifecycleManager` exposes read-only snapshots of managed subprocesses for
diagnostics (e.g. `/mcp status` command, `mcp_status.py`):

- `get_process_snapshot(server_key) -> dict | None` — `{pid, pgid, running, last_exit_code}`
  for a known `server_key`, or `None` if unknown. `pgid` is looked up from `_http_pgids`
  (populated at `start()` via `os.getpgid()`, H-8 process-group shutdown).
- `get_process_info(server_key) -> ProcessInfoSnapshot | None` — same fields plus
  `managed` and `stderr_log`, as a typed dataclass.
- `list_processes() -> list[ProcessInfoSnapshot]` — snapshots for all currently managed
  subprocess servers.

These methods only read `proc.poll()` / cached state; they never terminate or restart
a process.

`_ServerLifecycleRouter` (the facade in `factory.py`) exposes all three as thin
delegations to `HttpServerLifecycleManager`, so callers such as `McpStatusService`
access them via `getattr(lifecycle, "get_process_snapshot", None)` duck-typing
without reaching into `_http_mgr` internals.

---

## Adding a New MCP Server

### How to Add a New Tool Safely

When adding a new tool, follow the canonical 7-step procedure from the [Adding a new tool](#adding-a-new-tool) section above.

Key points:
1. **Add the tool name to `shared/tool_constants.py` frozenset** [Required] — Internal registry population function reads these frozensets at import time and builds the routing registry automatically. No manual registry edit is needed.
2. **Add `GET /v1/tools` endpoint** [Recommended] — enables startup drift validation via `check_routing_drift_vs_live()`; does not affect routing.
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

| Layer | Role | Routing? |
|---|---|---|
| `ToolRegistry` (auto-populated from `tool_constants.py` frozensets at import time) | **Sole routing authority**; populated by internal registry population function | Yes |
| Live `/v1/tools` discovery | **Validation source only**; used by `check_routing_drift_vs_live()` at startup to detect drift | No |

**Key rules:**
- **New tools must always be registered via `ToolRegistry`**. Unknown tools fail immediately with `ValueError`.
- **Live discovery does NOT affect routing** — if `/v1/tools` returns a different `server_key`, it is flagged as drift, not applied as a routing override.
- **Config `tool_names` are not routing inputs** — they are validation hints for drift detection only.

### New Server/Tool Registration Checklist

| Artifact | Required? | Notes |
|---|---|---|
| `shared/tool_constants.py` — add tool to frozenset | **Required** | Registry reads frozensets at import |
| `config/tools_definitions.toml` — add LLM schema | **Required** (if tool visible to LLM) | OpenAI function-calling format; required for the LLM to call the tool |
| `config/security.toml` — add `tool_safety_tiers` entries | **Required** | All tools must have a declared safety tier |
| `config/<key>_mcp_server.toml` — server config file | **Required** | Server app config + `[mcp_servers.<key>]` transport section |
| `deploy/deploy.sh` — add install/copy step | **Required** (new server) | Deployment must include the new server |
| Update `routing.md` | **Required** | Document guide must reference the new server |

### Manual steps

1. Subclass `MCPServer` in `mcp/<name>/server.py`; override `dispatch()`
2. Add `GET /v1/tools` endpoint returning tool definitions with `server_key` field
3. Add tool names to `shared/tool_constants.py` frozenset (owned by this server)
4. Add LLM schemas to `config/tools_definitions.toml` (OpenAI function-calling format)
5. Add `tool_safety_tiers` entries to `config/security.toml` for each tool
6. Create `config/<key>_mcp_server.toml` with app config and `[mcp_servers.<key>]` transport section
7. Add new files to `deploy/deploy.sh` copy list
8. Add startup step to `deploy/setup_services.sh`

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
