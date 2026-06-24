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
| sqlite-mcp | `config/sqlite_mcp_server.toml` |
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
| `transport` | `TransportType` | required | `TransportType.HTTP` (`"http"`) or `TransportType.STDIO` (`"stdio"`); string literals accepted at runtime via `__post_init__` conversion |
| `url` | `str` | required | HTTP server base URL (http only) |
| `cmd` | `list[str]` | required | Subprocess command (stdio or subprocess mode) |
| `startup_mode` | `str` | `"persistent"` | `"persistent"` / `"ondemand"` / `"subprocess"` |
| `healthcheck_mode` | `str` | `""` | `"http"` / `"process"` / `"ping_tool"` (auto-inferred if empty) |
| `idle_timeout_sec` | `int` | `0` | ondemand auto-stop delay (0 = disabled) |
| `startup_timeout_sec` | `int` | `30` | subprocess mode: health poll timeout |
| `working_dir` | `str` | `""` | stdio subprocess working directory (empty = inherit) |
| `env` | `dict[str, str]` | `{}` | Additional env vars for stdio subprocess |
| `tool_names` | `list[str]` | `[]` | Validation hint (optional); registry routes regardless. Empty = no validation. |
| `auth_token` | `str` | `""` | Bearer token for auth (empty = no auth) |
| `role` | `str` | `""` | Human-readable role label for `/mcp` display |

**Validation rules:**
- `transport="http"` → `url` must be non-empty
- `transport="stdio"` → `cmd` must be non-empty
- `startup_mode="subprocess"` only valid with `transport="http"` (ValueError otherwise)
- `healthcheck_mode` auto-inferred: `http` → `"http"`; `stdio` → `"process"`

---

## Major Default Values

| Parameter | Default | Config file |
|---|---|---|
| Max response bytes | 512 KB | hardcoded in `mcp/server.py` |
| stdio timeout | 60.0 sec | hardcoded in `shared/tool_executor.py` |
| Tool cache TTL | 300 sec | `config/tools.toml::tool_cache_ttl` |
| Tool cache max size | 200 entries | `config/tools.toml::tool_cache_max_size` |
| Watchdog interval | 0 (disabled) | `config/agent.toml::mcp_watchdog_interval` |
| Health registry threshold | 3 failures | hardcoded in `shared/mcp_config.py` |
| startup_timeout_sec | 30 sec | `McpServerConfig.startup_timeout_sec` |
| github default_per_page | 10 | `config/github_mcp_server.toml` |
| github max_per_page | 100 | `config/github_mcp_server.toml` |
| shell max_timeout_sec | 300 sec | `config/shell_mcp_server.toml` |
| shell sandbox_backend | `"none"` (local) / `"firejail"` (prod) | `config/shell_mcp_server.toml` |
| sqlite max_rows | 100 | `config/sqlite_mcp_server.toml` |
| git max_log_entries | 50 | `config/git_mcp_server.toml` |

---

## Long-Running HTTP Operation (startup_mode=subprocess)

Used by `sqlite-mcp` by default:

```toml
[mcp_servers.sqlite]
transport = "http"
url = "http://127.0.0.1:8011"
cmd = ["/opt/llm/venv/bin/uvicorn", "mcp.sqlite.server:app", "--host", "127.0.0.1", "--port", "8011", "--workers", "1"]
startup_mode = "subprocess"
startup_timeout_sec = 30
```

Agent spawns uvicorn at launch, polls `/health` every 1 second up to `startup_timeout_sec`.
`RuntimeError` if health check never succeeds.

---

## stdio Subprocess Operation (ondemand)

Example config:

```toml
[mcp_servers.shell]
transport = "stdio"
cmd = ["/opt/llm/venv/bin/python", "-m", "mcp.shell.server", "--stdio"]
startup_mode = "ondemand"
healthcheck_mode = "ping_tool"
idle_timeout_sec = 300
tool_names = ["shell_run"]
working_dir = "/opt/llm"
env = {}
```

---

## Verification Methods

### Health probes

```bash
# Individual server health checks (all return 4-field nested format)
curl -s http://127.0.0.1:8004/health | jq   # web-search: base response only
curl -s http://127.0.0.1:8005/health | jq   # file-read: base response only
curl -s http://127.0.0.1:8006/health | jq   # github: dependencies.github_token
curl -s http://127.0.0.1:8007/health | jq   # file-write: base response only
curl -s http://127.0.0.1:8008/health | jq   # file-delete: base response only
curl -s http://127.0.0.1:8009/health | jq   # shell: base response only
curl -s http://127.0.0.1:8010/health | jq   # rag-pipeline: base response only
curl -s http://127.0.0.1:8011/health | jq   # sqlite: base response only
curl -s http://127.0.0.1:8012/health | jq   # cicd: dependencies.github_token
curl -s http://127.0.0.1:8013/health | jq   # mdq: details.service
curl -s http://127.0.0.1:8014/health | jq   # git: base response only

# Base response shape: {"status":"ok","ready":bool,"dependencies":{},"details":{}}
```

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
| `ValueError` on startup | Invalid `startup_mode`+`transport` combo | Check `mcp_servers.toml` |

---

## Reading Audit Logs

### MCP server audit log (per-call)

```bash
# View raw audit lines
tail -f /opt/llm/logs/audit.log | grep '"action":'

# GitHub operations
tail -100 /opt/llm/logs/github-audit.log

# Shell executions
tail -100 /opt/llm/logs/shell_audit.log

# File deletions
tail -100 /opt/llm/logs/delete_audit.log

# Git operations
tail -100 /opt/llm/logs/git-mcp.log
```

### Per-server log files

| Server | Log path |
|---|---|
| web-search-mcp | `/opt/llm/logs/web-search-mcp.log` |
| file-read-mcp | `/opt/llm/logs/file-read-mcp.log` |
| file-write-mcp | `/opt/llm/logs/file-write-mcp.log` |
| file-delete-mcp | `/opt/llm/logs/file-delete-mcp.log` |
| github-mcp | `/opt/llm/logs/github-mcp.log` |
| shell-mcp | `/opt/llm/logs/shell-mcp.log` |
| mdq-mcp | `/opt/llm/logs/mdq-mcp.log` |
| git-mcp | `/opt/llm/logs/git-mcp.log` |

---

## End-to-End Tool Call Tracing

To trace a failed tool call across agent, transport, and server logs:

1. Find the `X-Request-Id` in the agent dispatch log:
   ```bash
   grep "tool_name=my_tool" /opt/llm/logs/agent.log | grep "X-Request-Id"
   ```
2. Search transport log for the same `X-Request-Id`:
   ```bash
   grep "X-Request-Id=<id>" /opt/llm/logs/audit.log
   ```
3. Search server audit log for the `X-Request-Id`:
   ```bash
   grep "<id>" /opt/llm/logs/github-audit.log  # or relevant server audit log
   ```
4. Check health state for `server_key` at that timestamp in `/opt/llm/logs/agent.log`.
5. If health changed: check watchdog actions log for restart/failover.

---

### Error Type Distinction in Audit Logs

Tool execution audit events include an `error_type` field:

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
   NO  → Transport failure (error_type="transport" in audit log). See §Error Type Distinction.
   YES → continue

2. Did the tool return an error response (is_error=true)?
   YES → Tool-level error (error_type="tool" in audit log). See §Error Type Distinction.
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
| `db_allowlist` = `[]` | sqlite-mcp denies everything |
| `read_only = true` (git-mcp) | git writes blocked even if `allowed_repo_paths` is set |
| `tool_definitions_strict = true` | Agent startup aborts on tool name mismatch |
| `mcp_watchdog_interval = 0` | No auto-restart of failed subprocess servers (LOCAL profile default; PRODUCTION default is 30.0) |

---

## Startup Validation Behavior (`tool_definitions_strict`)

`_check_tool_definitions` runs at agent startup and compares `tool_definitions` from `config/agent.toml` against live `/v1/tools` responses. Behavior depends on server reachability and `tool_definitions_strict`:

| Scenario | `strict = false` | `strict = true` |
|---|---|---|
| **Partial unreachable** — some servers respond | Validation proceeds with reachable servers; unreachable servers logged as `WARNING` | Same — only reachable tools compared; mismatch in reachable tools raises `RuntimeError` |
| **All unreachable** — no server responds | Validation skipped; `INFO: "All MCP servers unreachable ... skipping tool definition check"` | Same — cannot validate zero tools; skipped |
| **Tool mismatch** — reachable but names differ | `WARNING` per direction (missing_in_server / extra_on_servers) | `RuntimeError: "Strict mode: tool definition mismatch detected. Mismatches: .... Unreachable servers: ...."` |

**Key points:**
- Unreachable servers never cause `RuntimeError` by themselves; only a tool name mismatch in strict mode does.
- When all servers are unreachable, strict mode does **not** raise — validation is skipped.
- The error message clearly separates mismatches from unreachable servers for operator debugging.

---

## Watchdog Behavior

The watchdog loop (`watchdog_loop()` in `agent/repl_health.py`) periodically probes all MCP
servers and attempts to restart them when they fail. It runs as a background asyncio task.

### Configuration

| Setting | LOCAL default | PRODUCTION default | Effect |
|---|---|---|---|
| `mcp_watchdog_interval` | `0` (disabled) | `30.0` | Probe interval in seconds; `0` = disabled |
| `mcp_watchdog_max_restarts` | `3` | `3` | Max restart attempts per server before giving up |

### Disabled state consequences

When `mcp_watchdog_interval = 0`:
- The watchdog loop still starts but logs a warning: `Watchdog: disabled (interval=0) — failed servers will not be auto-restarted`
- Crashed HTTP servers will remain unreachable until the agent process is restarted manually
- Crashed subprocess servers (shell-mcp, sqlite-mcp) will not be restarted automatically

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

1. **Add the tool name to `shared/tool_constants.py`**
   - Add to the appropriate frozenset (`READ_TOOLS`, `WRITE_TOOLS`, etc.)
   - If no set fits, create a new `<SERVER>_TOOLS` frozenset and add it to `get_all_mcp_tool_names()`

2. **Add the tool name to `tool_names` in the server config (`config/agent.toml`)** (optional — for validation only; routing does not require this)
   - Find the `[mcp_servers.<server_key>]` block
   - Append the tool name to `tool_names = [...]`

3. **Verify routing coverage at startup**
   - Start the agent or run `uv run pytest tests/test_route_resolver.py -v`
   - Startup logs confirm: `"Routing: N/N tools mapped"`
   - If a warning appears (`"N-1/N tools mapped; 1 unmapped: [tool_name]"`), the tool is missing from step 1 or 2

> **Note:** If the tool name follows the `github_` prefix convention and the server key is `github`,
> no entry in `tool_constants.py` is needed — prefix matching handles it automatically.

---

## New MCP Server Addition Checklist

When adding a server:

- [ ] Create `scripts/mcp/<name>/server.py` (inherit `MCPServer`, override `dispatch()`)
- [ ] Create `config/<name>_mcp_server.toml`
- [ ] Add `[mcp_servers.<key>]` entry to `config/mcp_servers.toml` (transport, url, cmd, etc.)
- [ ] Add tool definitions to `config/tools_definitions.toml`
- [ ] If tools not in `shared/tool_constants.py` frozensets: set `tool_names` in server config
- [ ] Add new files to `deploy/deploy.sh` copy list
- [ ] Add startup step to `deploy/setup_services.sh`
- [ ] Add `tool_safety_tiers` entries to `config/agent.toml` for all new tools
- [ ] Update `routing.md` if new documentation is needed

---

## Pre-Production Fail-Open Checklist

Before deploying to production, verify:

- [ ] `tool_definitions_strict = true` (fatal on schema mismatch)
- [ ] shell-mcp: `shell_sandbox_backend = "firejail"` (not `"none"`)
- [ ] `cicd-mcp`: `workflow_allowlist` explicitly set (not empty — fail-open by default)
- [ ] `security_profile = "production"` in `config/agent.toml` (enables startup enforcement)
- [ ] `mcp_watchdog_interval = 30.0` (auto-restart enabled)
- [ ] Health check thresholds reviewed (`startup_timeout_sec`, `mcp_watchdog_max_restarts`)
- [ ] Audit log paths configured and writable
