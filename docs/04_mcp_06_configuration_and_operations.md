# MCP Configuration and Operations

- Security model → [04_mcp_05_security_and_safety_model.md](04_mcp_05_security_and_safety_model.md)

## Purpose

Document all configuration files, per-server config keys, startup verification,
health probes, audit log reading, and the new-server addition checklist.

---

## Configuration File Inventory

### Shared / Agent-level

| File | Affects |
|---|---|
| `config/agent.toml` → `[mcp_servers.*]` | All server transport settings (`McpServerConfig`) |
| `config/agent.toml` → `tool_definitions` | Tool names exposed to LLM |
| `config/agent.toml` → `tool_safety_tiers` | Per-tool risk tier (READ_ONLY/WRITE_SAFE/WRITE_DANGEROUS/ADMIN) |
| `config/agent.toml` → `mcp_watchdog_interval` | Watchdog poll interval (0 = disabled) |
| `config/agent.toml` → `mcp_watchdog_max_restarts` | Watchdog max restart count |

### Per-server config files

| Server | Config file |
|---|---|
| web-search-mcp | `config/web_search_mcp_server.toml` (no API keys needed) |
| file-read-mcp | `config/file_read_mcp_server.toml` |
| file-write-mcp | `config/file_write_mcp_server.toml` |
| file-delete-mcp | `config/file_delete_mcp_server.toml` |
| github-mcp | `config/github_mcp_server.toml` |
| shell-mcp | `config/shell_mcp_server.toml` |
| rag-pipeline-mcp | `config/rag_pipeline_mcp_server.toml` |
| cicd-mcp | `config/cicd_mcp_server.toml` |
| mdq-mcp | `config/mdq_mcp_server.toml` |
| git-mcp | `config/git_mcp_server.toml` |

### API key env files (`conf.d/`)

| File | Key |
|---|---|
| `/etc/conf.d/github-mcp` | `GITHUB_TOKEN` |
| `/etc/conf.d/cicd-mcp` | `GITHUB_TOKEN` |

---

## McpServerConfig Fields (agent.toml `[mcp_servers.*]`)

| Field | Type | Default | Description |
|---|---|---|---|
| `transport` | `TransportType` | required | `TransportType.HTTP` (`"http"`); TOML string values are converted by the config loader, not at runtime |
| `url` | `str` | required | HTTP server base URL |
| `startup_mode` | `str` | `"persistent"` | `"persistent"` / `"subprocess"` |
| `cmd` | `list[str]` | `[]` | Launch command for `startup_mode=subprocess`; must be non-empty when subprocess mode is used |
| `env` | `dict[str, str]` | `{}` | Extra environment variables passed to the subprocess |
| `healthcheck_mode` | `str` | `""` | `"http"` (auto-inferred if empty) |
| `idle_timeout_sec` | `int` | `0` | subprocess auto-stop delay (0 = disabled) |
| `startup_timeout_sec` | `int` | `30` | subprocess mode: health poll timeout |
| `call_timeout_sec` | `float` | `60.0` | per-call timeout for HttpTransport; 0 = no timeout |
| `tool_names` | `list[str]` | `[]` | Validation hint (optional); registry routes regardless. Empty = no validation. See [Routing Source of Truth](04_mcp_03_routing_lifecycle_and_execution.md#routing-source-of-truth). |
| `auth_token` | `str` | `""` | Bearer token for auth (empty = no auth) |
| `role` | `str` | `""` | Human-readable role label for `/mcp` display |

**Validation rules:**
- `transport="http"` → `url` must be non-empty
- `startup_mode="subprocess"` → `cmd` must be non-empty

---

## Major Default Values

| Parameter | Default | Config file |
|---|---|---|
| Max response bytes | 512 KB | hardcoded in `mcp/server.py` |
| call_timeout_sec | 60.0 sec | `McpServerConfig.call_timeout_sec` |
| Tool cache TTL | 300 sec | `config/tools.toml::tool_cache_ttl` |
| Tool cache max size | 200 entries | `config/tools.toml::tool_cache_max_size` |
| Watchdog interval | `0` (disabled, LOCAL default; PRODUCTION default is `30.0`) | `config/agent.toml::mcp_watchdog_interval` |
| Health registry threshold | 3 failures | hardcoded in `shared/mcp_config.py` |
| startup_timeout_sec | 30 sec | `McpServerConfig.startup_timeout_sec` |
| github default_per_page | 10 | `config/github_mcp_server.toml` |
| github max_per_page | 100 | `config/github_mcp_server.toml` |
| shell max_timeout_sec | 300 sec | `config/shell_mcp_server.toml` |
| shell sandbox_backend | `"none"` (local) / `"firejail"` (prod) | `config/shell_mcp_server.toml` |
| git max_log_entries | 50 | `config/git_mcp_server.toml` |

---

## Long-Running HTTP Operation (startup_mode=subprocess)

Agent spawns uvicorn at launch, polls `/health` every 1 second up to `startup_timeout_sec`.
`RuntimeError` if health check never succeeds.

---

## Verification Methods

### Health probes

```bash
# Individual server health checks (all return 4-field nested format)
curl -s http://127.0.0.1:8004/health | jq   # web-search: base response only
curl -s http://127.0.0.1:8005/health | jq   # file-read: dependencies.filesystem
curl -s http://127.0.0.1:8006/health | jq   # github: dependencies.github_token
curl -s http://127.0.0.1:8007/health | jq   # file-write: dependencies.filesystem
curl -s http://127.0.0.1:8008/health | jq   # file-delete: dependencies.filesystem
curl -s http://127.0.0.1:8009/health | jq   # shell: dependencies.shell, details.sandbox_backend
curl -s http://127.0.0.1:8010/health | jq   # rag-pipeline: dependencies.embed_url
curl -s http://127.0.0.1:8012/health | jq   # cicd: dependencies.github_token
curl -s http://127.0.0.1:8013/health | jq   # mdq: details.service
curl -s http://127.0.0.1:8014/health | jq   # git: dependencies.git
# sqlite-mcp (port 8011) — SELECT-only; health check via curl http://127.0.0.1:8011/health

# Base response shape: {"status":"ok","ready":bool,"liveness":true,"restart_recommended":false,"operator_action_required":false,"dependencies":{},"details":{}}
```

### HTTP status code behavior

- **HTTP 200**: Server is fully healthy (`status="ok"`, `ready=true`)
- **HTTP 503**: Server has dependency failures (`status="degraded"`, `ready=false`)

The watchdog inspects both the HTTP status code and the `restart_recommended` body field; restart is only attempted when `restart_recommended=true` or the server is unreachable. HTTP 503 with `restart_recommended=false` (e.g. missing credentials) logs a WARNING but does not restart.

```bash
# Check HTTP status code (not just body)
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8006/health   # 200 if healthy, 503 if degraded
```

### Health probe response examples

**Base response (healthy, all servers):**
```json
{
  "status": "ok",
  "ready": true,
  "liveness": true,
  "restart_recommended": false,
  "operator_action_required": false,
  "dependencies": {},
  "details": {}
}
```
HTTP 200 — fully healthy.

**shell-mcp (port 8009) — degraded:**
```json
{
  "status": "degraded",
  "ready": false,
  "liveness": true,
  "restart_recommended": false,
  "operator_action_required": true,
  "dependencies": {"shell": "sh not found in PATH"},
  "details": {"sandbox_backend": "firejail"}
}
```
HTTP 503 — `sh` is not found in PATH. Watchdog logs WARNING but does NOT restart (`operator_action_required=true`).

**rag-pipeline-mcp (port 8010) — degraded:**
```json
{
  "status": "degraded",
  "ready": false,
  "liveness": true,
  "restart_recommended": false,
  "operator_action_required": true,
  "dependencies": {"embed_url": "not configured"},
  "details": {}
}
```
HTTP 503 — no embedding URL is set. Watchdog logs WARNING but does NOT restart (`operator_action_required=true`).

**github-mcp (port 8006) — degraded:**
```json
{
  "status": "degraded",
  "ready": false,
  "liveness": true,
  "restart_recommended": false,
  "operator_action_required": true,
  "dependencies": {"github_token": "not_set"},
  "details": {}
}
```
HTTP 503 — GitHub token is not set. Watchdog logs WARNING but does NOT restart (`operator_action_required=true`).

**mdq-mcp (port 8013) — degraded:**
```json
{
  "status": "degraded",
  "ready": false,
  "liveness": true,
  "restart_recommended": false,
  "operator_action_required": true,
  "dependencies": {"db_file": "not found: /opt/llm/db/mdq.sqlite"},
  "details": {"service": "mdq-mcp", "database": "/opt/llm/db/mdq.sqlite"}
}
```
HTTP 503 — database file not found. Watchdog logs WARNING but does NOT restart (`operator_action_required=true`).

**git-mcp (port 8014) — degraded:**
```json
{
  "status": "degraded",
  "ready": false,
  "liveness": true,
  "restart_recommended": false,
  "operator_action_required": true,
  "dependencies": {"git": "git not found in PATH"},
  "details": {}
}
```
HTTP 503 — git is not found in PATH. Watchdog logs WARNING but does NOT restart (`operator_action_required=true`).

### /v1/tools verification

```bash
curl -s http://127.0.0.1:8005/v1/tools | jq '.tools[].name'
```

### Agent REPL check

```
agent[:#N]> /mcp
```

Probes all HTTP servers. Expected: all show `OK` with tool list.

### Startup failure checkpoints

| Failure | Cause | Check |
|---|---|---|
| Server not started | Subprocess failed to start | Check stderr; verify port not in use |
| subprocess timeout | uvicorn fails to start | Check stderr; verify port not in use |
| Tool definition mismatch | Config out of sync | `/mcp` → tool count; compare with config |


---

## Reading Audit Logs

The shared audit log at `/opt/llm/logs/audit.log` contains JSON-lines records from both MCP server and agent-side audit events. Each line is a parseable JSON object.

### MCP server audit log (per-call)

Format: JSON-lines, one JSON object per line. Example:
```json
{"event":"mcp_tool_exec","source":"mcp_server","ts":1719500000.0,"session_id":"sess-abc","request_id":"req-uuid","tool":"read_text_file","target":"/tmp/f.txt","outcome":"ok","server_key":"file_read","error_type":""}
```

**Shared audit log** (`/opt/llm/logs/audit.log`): Used by web-search-mcp, file-read-mcp, file-write-mcp, rag-pipeline-mcp, cicd-mcp.

```bash
# View MCP server audit events (JSON-lines format)
tail -f /opt/llm/logs/audit.log | jq 'select(.source == "mcp_server")'
# View all audit events (MCP server + agent-side)
tail -f /opt/llm/logs/audit.log | jq .
```

**Per-server audit logs:**

```bash
# GitHub operations (ISO8601 + op + repo + user)
grep "op=create_pull_request" /opt/llm/logs/github_audit.log

# Shell executions (ISO8601 + cmd + uid + exit)
grep "exit=1" /opt/llm/logs/shell_audit.log

# File deletions (ISO8601 + op + path + user)
grep "op=delete_directory" /opt/llm/logs/delete_audit.log

# MDQ operations (MDQ-specific format)
grep "op=" /opt/llm/logs/mdq_audit.log
```

> **Note:** cicd-mcp, git-mcp, and sqlite-mcp do not have dedicated audit log files. They use `logging.getLogger(__name__)` only.

### Per-server log files

| Server | Log path | Notes |
|---|---|---|
| web-search-mcp | `/opt/llm/logs/web-search-mcp.log` | Dedicated app log |
| file-read-mcp | `/opt/llm/logs/file-read-mcp.log` | Dedicated app log |
| file-write-mcp | `/opt/llm/logs/file-write-mcp.log` | Dedicated app log |
| file-delete-mcp | `/opt/llm/logs/file-delete-mcp.log` | Dedicated app log |
| github-mcp | `/opt/llm/logs/github-mcp.log` | Dedicated app log |
| shell-mcp | `/opt/llm/logs/shell-mcp.log` | Dedicated app log |
| mdq-mcp | `/opt/llm/logs/mdq-mcp.log` | Dedicated app log |
| rag-pipeline-mcp | `/opt/llm/logs/rag-mcp.log` | Dedicated app log |
| cicd-mcp | No dedicated log file | Uses `logging.getLogger(__name__)` |
| git-mcp | No dedicated log file | Uses `logging.getLogger(__name__)` |
| sqlite-mcp | No dedicated log file | Uses `logging.getLogger(__name__)` (SELECT-only, port 8011) |

### Per-server audit log files

| Server | Audit log path | Format |
|---|---|---|
| web-search-mcp | `/opt/llm/logs/audit.log` (shared) | JSON-lines (MCP server audit) |
| file-read-mcp | `/opt/llm/logs/audit.log` (shared) | JSON-lines (MCP server audit) |
| file-write-mcp | `/opt/llm/logs/audit.log` (shared) | JSON-lines (MCP server audit) |
| file-delete-mcp | `/opt/llm/logs/delete_audit.log` | Structured (ISO8601 + op + path + user) |
| github-mcp | `/opt/llm/logs/github_audit.log` | Structured (ISO8601 + op + repo + user) |
| shell-mcp | `/opt/llm/logs/shell_audit.log` | Structured (ISO8601 + op + command + user) |
| mdq-mcp | `/opt/llm/logs/mdq_audit.log` | Structured (MDQ-specific) |
| rag-pipeline-mcp | `/opt/llm/logs/audit.log` (shared) | JSON-lines (MCP server audit) |
| cicd-mcp | `/opt/llm/logs/audit.log` (shared) | JSON-lines (MCP server audit) |
| git-mcp | Config key exists but no write code | `audit_log_path = "/opt/llm/logs/git-mcp.log"` in TOML — no audit write code in service.py; reserved for future implementation |
| sqlite-mcp | Config key not parsed | `audit_log_path = "/opt/llm/logs/sqlite-mcp.log"` in TOML — key is present for future use but not read by `SqliteConfig.from_dict`; no audit log written |

### Agent-side audit log (structured events)

Format: JSON-lines, e.g.:
```json
{"event":"tool_exec","task_id":"turn-123","tool":"shell_run","operation_type":"MCP","mcp_request_id":"abc-456","is_error":true,"error_type":"transport","ts":1719500000.0,"workflow_id":"","session_id":""}
```

```bash
# View raw agent-side audit events (JSON-lines format)
tail -f /opt/llm/logs/audit.log | jq .

# Filter by event type
tail -f /opt/llm/logs/audit.log | jq 'select(.event == "tool_exec")'

# Filter by error type (agent-side JSON-lines format)
grep '"error_type":"transport"' /opt/llm/logs/audit.log

# Filter by tool name
grep '"tool":"shell_run"' /opt/llm/logs/audit.log
```

---

## End-to-End Tool Call Tracing

To trace a failed tool call across agent, transport, and server logs:

1. Find the `mcp_request_id` in the agent-side audit log:
    ```bash
    jq 'select(.mcp_request_id == "<id>")' /opt/llm/logs/audit.log
    ```
2. Search MCP server audit log for the same `request_id` field (JSON-lines format):
    ```bash
    jq 'select(.request_id == "<id>")' /opt/llm/logs/audit.log
    ```
3. Search per-server log for the `X-Request-Id` response header:
    ```bash
    grep "<id>" /opt/llm/logs/github-mcp.log  # or relevant server log
    ```
4. Check health state for `server_key` at that timestamp in `/opt/llm/logs/agent.log`.
5. If health changed: check watchdog actions log for restart/failover.

---

### Error Type Distinction in Audit Logs (Agent-Side)

Agent-side audit events include an `error_type` field:

| error_type | Meaning | Example cause |
|---|---|---|
| `transport` | MCP server unreachable (network failure, timeout, crash) | Server process died, port not listening, HTTP 5xx |
| `tool` | MCP server reachable but tool returned is_error=true | Tool validation failed, database constraint violation |
| _(empty)_ | Successful execution | — |

Example audit log line:
```json
{"event":"tool_exec","tool":"shell_run","is_error":true,"error_type":"transport",...}
```

Filter by error type:
```bash
# Transport failures (server issues)
grep '"error_type":"transport"' /opt/llm/logs/audit.log

# Tool-level failures (business logic errors)
grep '"error_type":"tool"' /opt/llm/logs/audit.log
```

### Per-Server Error Counters

`ToolExecutor` maintains per-server error counters accessible via `ToolExecutor.get_error_counters()`:

```python
{
    "shell-mcp": {"transport": 2, "tool": 5},
    "github-mcp": {"transport": 0, "tool": 1},
}
```

These counters are in-memory (not persisted) and reset on agent restart.

### Repeated Failure Detection

When a tool fails 3+ times within a 5-minute sliding window, a warning is logged:

```
WARNING: Repeated tool failures detected: shell_run failed 3 times in 300s window
```

> **Note:** The watchdog monitors transport availability (health checks). Tool-level errors (`error_type=tool`) do not trigger watchdog restarts — only transport failures (`error_type=transport`) affect server health state.

---

### Side-Effect Serialization

When a round contains side-effect tools (write operations), the scheduler groups them to prevent concurrent modifications. This is intentional for safety but reduces parallelism.

**Serialization triggers:**

| Trigger | Condition | Effect |
|---|---|---|
| `requires_serial` | Tool metadata has `requires_serial=true` | Tool runs alone in its own single-element group |
| `resource_scope_conflict` | Multiple writes to same resource scope | All tools in that scope run serially |
| `is_write_overlap` | Multiple writes without specific scope | All write tools grouped together (write-first) |

**Log format:**
```
ROUND_SERIALIZATION: triggered by shell_run (requires_serial) — 1 tools serialized in this round
Serialization impact: 3 tools grouped serially (normally would run in parallel)
```

**Viewing stats:**
Run `/mcp` to see serialization statistics at the bottom of the MCP status output.

**Why this matters:**
Serialization reduces parallelism but prevents race conditions on shared resources. Before attempting to optimize parallelism, review serialization logs to understand which tools and scopes trigger grouping most frequently.

---

## MCP Failure Diagnosis

Use this flow to trace a failed or unexpected MCP tool call:

```
1. Was the request delivered to the server?
   NO  → Transport failure (error_type="transport" in agent-side audit log). See §Error Type Distinction.
   YES → continue

2. Did the tool return an error response (is_error=true)?
   YES → Tool-level error (error_type="tool" in agent-side audit log). See §Error Type Distinction.
   NO (timeout or silent fail) → continue

3. Has server health status changed?
   YES → See §Watchdog Behavior. Check health transition timestamp.
   NO  → continue

4. Has the watchdog taken action (restart / circuit-break)?
   YES → See §Watchdog Behavior.
   NO  → Check serialization. See §Serialization in Tool Execution.
```

For correlation across agent, transport, and server logs, see §End-to-End Tool Call Tracing.

**Restart-worthy:** health transition to `failed` + repeated transport errors within threshold.
**Not restart-worthy:** single tool error, one-time timeout, or serialization delay.

---

## Settings with High Operational Impact

| Setting | Impact |
|---|---|
| `allowed_dirs` = `[]` | File access completely denied |
| `allowed_repos` = `[]` + `fail_closed` | All GitHub writes denied |
| `command_allowlist` = `[]` | All shell commands denied |
| `repo_allowlist` = `[]` | All cicd-mcp access denied |
| `allowed_repo_paths` = `[]` | All git-mcp access denied |
| `read_only = true` (git-mcp) | git writes blocked even if `allowed_repo_paths` is set |
| `tool_definitions_strict = true` | Agent startup aborts on tool name mismatch |
| `mcp_watchdog_interval = 0` | No auto-restart of failed subprocess servers (LOCAL profile default; PRODUCTION default is 30.0) |

---

## Startup Validation Behavior (`tool_definitions_strict`)

> **Canonical specification.** This section describes `_check_tool_definitions` in `repl_health.py`.
> For routing drift detection (`validate_routing_against_live` in `route_resolver.py`), see
> [04_mcp_03 §Drift validation](04_mcp_03_routing_lifecycle_and_execution.md#drift-validation).
> These are different functions — see also `04_mcp_90 §SPEC-01`.

`_check_tool_definitions` runs at agent startup and compares `tool_definitions` from `config/agent.toml` against live `/v1/tools` responses. Behavior depends on server reachability and `tool_definitions_strict`:

| Scenario | `strict = false` | `strict = true` |
|---|---|---|
| **Partial unreachable** — some servers respond | Validation proceeds with reachable servers; unreachable servers logged as `WARNING` | Same — only reachable tools compared; mismatch in reachable tools raises `RuntimeError` |
| **All unreachable** — no server responds | Validation skipped; `INFO: "All MCP servers unreachable ... skipping tool definition check"` | `RuntimeError: "Strict mode: all MCP servers unreachable — cannot validate tool definitions. Unreachable servers: [...]"` |
| **Tool mismatch** — reachable but names differ | `WARNING` per direction (missing_in_server / extra_on_servers) | `RuntimeError: "Strict mode: tool definition mismatch detected. Mismatches: .... Unreachable servers: ...."` |

**Key points:**
- A tool name mismatch in strict mode raises `RuntimeError`.
- When all servers are unreachable in strict mode, `RuntimeError` is raised listing the unreachable servers. In non-strict mode, validation is skipped with an INFO log.
- The error message clearly separates mismatches from unreachable servers for operator debugging.

---

## Watchdog Behavior

The watchdog loop (`watchdog_loop()` in `agent/repl_health.py`) periodically probes all MCP
servers and attempts to restart them when they fail. It runs as a background asyncio task.

**Note:** The watchdog's periodic `record_success()`/`record_failure()` calls supplement (but do not replace) the per-call HealthRegistry updates from `ToolExecutor._raw_execute()`. Each tool call increments its own failure count independently of the watchdog.

### Configuration

| Setting | LOCAL default | PRODUCTION default | Effect |
|---|---|---|---|
| `mcp_watchdog_interval` | `0` (disabled) | `30.0` | Probe interval in seconds; `0` = disabled |
| `mcp_watchdog_max_restarts` | `3` | `3` | Max restart attempts per server before giving up |

### Disabled state consequences

When `mcp_watchdog_interval = 0`:
- The watchdog loop still starts but logs a warning: `Watchdog: disabled (interval=0) — failed servers will not be auto-restarted`
- Crashed HTTP servers will remain unreachable until the agent process is restarted manually
- Crashed subprocess servers (shell-mcp) will not be restarted automatically

### Verifying watchdog state

Two places show the current watchdog state:

1. **Startup logs** (`/opt/llm/logs/agent.log`):
   ```
   INFO  Watchdog: enabled (interval=30s, max_restarts=3)
   ```
   or
   ```
   WARNING Watchdog: disabled (interval=0) — failed servers will not be auto-restarted
   ```

2. **`/mcp status` command** (REPL):
   ```
   Watchdog    enabled (interval=30s, max_restarts=3)
   ```
   or
   ```
   Watchdog    disabled (interval=0) — no auto-restart
   ```

---

### Tool error monitoring

`ToolExecutor` distinguishes two error categories:

| Category | Log field | Condition |
|----------|-----------|-----------|
| Transport error | `error_type=transport` | Network failure, timeout, server unreachable |
| Tool error | `error_type=tool` | Server reachable; tool execution returned `is_error=true` |

Transport errors affect the MCP server health state and may trigger watchdog restarts.
Tool errors do not — the server is functioning, but the specific tool call failed
(e.g., invalid arguments, upstream API error).

Transport errors are raised by `HttpTransport` as `TransportError` and caught by
`ToolExecutor._record_transport_error()`, which increments `stat_transport_errors`
and calls `HealthRegistry.record_failure()`.

#### Per-server tool error counters

`ToolExecutor.stat_tool_errors` is a `dict[str, int]` (server_key → count) available
for the lifetime of the process. Read it from the agent context:

```python
ctx.services.tools.stat_tool_errors   # {"rag_pipeline": 3, "github": 0}
```

#### Repeated-failure warnings

When the per-server tool error count reaches a multiple of
`repeated_tool_error_threshold` (default: 3), a warning is logged:

```
WARNING repeated tool errors from 'rag_pipeline': 3 failures (error_type=tool)
```

The threshold is configurable at `ToolExecutor` construction time. Counters reset
on process restart. There is no automatic server restart on tool errors (only
transport failures trigger the watchdog).

#### Grep patterns for monitoring

```bash
# Find tool errors for a specific server
grep "error_type=tool" agent.log | grep "rag_pipeline"

# Find repeated-failure warnings
grep "repeated tool errors" agent.log

# Find transport failures
grep "error_type=transport" agent.log
```

---

### Tool scheduling and serialization

The agent executes tool calls in resource-scoped groups. Most tools run in parallel,
but certain conditions force serial execution within a round:

| Condition | Trigger | Log reason |
|-----------|---------|------------|
| Tool has `requires_serial=True` | Any tool with this flag | `requires_serial` |
| Multiple write tools share a `resource_scope` | Two+ write tools with same scope | `resource_scope_conflict` |
| Write tools without a `resource_scope` | Any write tool lacking scope metadata | `is_write_overlap` |
| Side-effect tool in round (`_execute_standard` path) | Any side-effect tool | logged as "Side-effect tool detected" |

Serialization is intentional safety behavior — it prevents concurrent writes from corrupting
shared resources. It does not indicate a configuration error.

#### Reading serialization log entries

Each serialization event logs:

```
INFO ROUND_SERIALIZATION: triggered by <tool_name> (<reason>)
     — <N> tools serialized in this round
```

Example:

```
INFO ROUND_SERIALIZATION: triggered by write_file (is_write_overlap)
     — 2 tools serialized in this round
```

#### Serialization stats in /mcp status

Run `/mcp status` to see cumulative session stats:

```
--- Tool Scheduling ---
  Serialization events this session: 5
  Tools affected by serialization:   12
```

These counters reset on agent restart. A high serialization count relative to
total tool calls may indicate candidates for `resource_scope` annotation or
`requires_serial=False` review — but only after analyzing which tools are
triggering it.

#### Before optimizing

Do not change `requires_serial` or `resource_scope` values without reviewing
the serialization log data. The observability layer provides the data needed
to make safe decisions.

---

## New Tool Registration Procedure

When adding a new tool to an **existing** MCP server:

| Step | Action | Required? |
|---|---|---|
| 1 | Add the tool name to the appropriate frozenset in `shared/tool_constants.py` (e.g., `READ_TOOLS`, `WRITE_TOOLS`, or create a new `<SERVER>_TOOLS` frozenset and add it to `get_all_mcp_tool_names()`) | **[Required]** |
| 2 | Registry auto-populates from these frozensets at import time — no manual registry edit needed | (automatic) |
| 3 | Implement `dispatch()` handler in the owning MCP server (`mcp/<name>/server.py`) | **[Required]** |
| 4 | Expose tool in `/v1/tools` endpoint (return tool definition with `server_key` field) | **[Recommended]** — enables startup drift validation; no effect on routing |
| 5 | Add LLM schema to `config/tools_definitions.toml` (OpenAI function-calling format) | **[Required]** — if tool should be visible to LLM |
| 6 | Add `tool_safety_tiers` entry in `config/security.toml` for the new tool | **[Required]** — all tools must have a declared safety tier |
| 7 | Add tool name to `tool_names` in `config/<key>_mcp_server.toml` `[mcp_servers.<key>]` section | **[Optional]** — enables startup drift validation only; routing does not require it |

**Note**: All tools must be explicitly registered in ToolRegistry. No prefix-based routing exists.

### Verification

After completing registration:

```bash
uv run pytest tests/test_tool_constants.py tests/test_route_resolver.py -v
```

Expected: all routing tests pass. If `tool_definitions_strict = true`, restart the agent and confirm startup logs show `"Routing: N/N tools mapped"` with no unmapped warnings.

---

## New MCP Server Addition Checklist

When adding a server:

- [ ] Create `scripts/mcp/<name>/server.py` (inherit `MCPServer`, override `dispatch()`)
- [ ] Create `config/<key>_mcp_server.toml` with app config and `[mcp_servers.<key>]` transport section
- [ ] Add tool definitions to `config/tools_definitions.toml`
- [ ] Tools are registered in `shared/tool_constants.py` frozensets (auto-routed at startup); config `tool_names` is optional drift validation only
- [ ] Add new files to `deploy/deploy.sh` copy list
- [ ] Add startup step to `deploy/setup_services.sh`
- [ ] Add `tool_safety_tiers` entries to `config/security.toml` for all new tools
- [ ] Update `routing.md` if new documentation is needed

---

## Pre-Production Fail-Open Checklist

Before deploying to production, verify:

- [ ] `tool_definitions_strict = true` (fatal on schema mismatch)
- [ ] shell-mcp: `shell_sandbox_backend = "firejail"` (not `"none"`) and firejail binary installed
- [ ] `cicd-mcp`: `workflow_allowlist` explicitly set (empty = fail-closed: deny all)
- [ ] `security_profile = "production"` in `config/agent.toml` (enables startup enforcement)
- [ ] `mcp_watchdog_interval = 30.0` (auto-restart enabled)
- [ ] Health check thresholds reviewed (`startup_timeout_sec`, `mcp_watchdog_max_restarts`)
- [ ] Audit log paths configured and writable
- [ ] API keys (`github_token`, `auth_token`) set via environment variables, not hardcoded in config
- [ ] `repo_allowlist` non-empty in `cicd_mcp_server.toml` (empty = deny all repos)
- [ ] `allowed_repos` non-empty in `github_mcp_server.toml` (empty = deny all GitHub write ops)

### Installing firejail

```bash
# Debian/Ubuntu
sudo apt-get install firejail

# Alpine
apk add firejail

# Verify installation
firejail --version
```

After installation, update `config/shell_mcp_server.toml`:

```toml
shell_sandbox_backend = "firejail"
```

See `04_mcp_05_security_and_safety_model.md` for the full fail-open/closed policy table.
