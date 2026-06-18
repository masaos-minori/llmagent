# MCP Configuration and Operations

- Security model → [04_mcp_05_security_and_safety_model.md](04_mcp_05_security_and_safety_model.md)

## Purpose

Document all configuration files, per-server config keys, OpenRC operations, startup
verification, health probes, audit log reading, and the new-server addition checklist.

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
| web-search-mcp | `config/web_search_mcp_server.toml` |
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

### API key env files (OpenRC `conf.d/`)

| File | Key |
|---|---|
| `/etc/conf.d/web-search-mcp` | `BRAVE_API_KEY`, `BING_API_KEY` |
| `/etc/conf.d/github-mcp` | `GITHUB_TOKEN` |
| `/etc/conf.d/cicd-mcp` | `GITHUB_TOKEN` |

---

## McpServerConfig Fields (agent.toml `[mcp_servers.*]`)

| Field | Type | Default | Description |
|---|---|---|---|
| `transport` | `TransportType` | required | `TransportType.HTTP` (`"http"`) or `TransportType.STDIO` (`"stdio"`); string literals accepted at runtime via `__post_init__` conversion |
| `url` | `str` | required | HTTP server base URL (http only) |
| `cmd` | `list[str]` | required | Subprocess command (stdio or subprocess mode) |
| `openrc_service` | `str` | required | OpenRC service name for watchdog restart |
| `startup_mode` | `str` | `"persistent"` | `"persistent"` / `"ondemand"` / `"subprocess"` |
| `healthcheck_mode` | `str` | `""` | `"http"` / `"process"` / `"ping_tool"` (auto-inferred if empty) |
| `idle_timeout_sec` | `int` | `0` | ondemand auto-stop delay (0 = disabled) |
| `startup_timeout_sec` | `int` | `30` | subprocess mode: health poll timeout |
| `working_dir` | `str` | `""` | stdio subprocess working directory (empty = inherit) |
| `env` | `dict[str, str]` | `{}` | Additional env vars for stdio subprocess |
| `tool_names` | `list[str]` | `[]` | Explicit tool routing (empty = static fallback) |
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
| sqlite max_rows | 100 | `config/sqlite_mcp_server.toml` |
| git max_log_entries | 50 | `config/git_mcp_server.toml` |

---

## OpenRC Operations

```bash
# Start all persistent servers
rc-service web-search-mcp start
rc-service file-mcp start
rc-service github-mcp start
rc-service shell-mcp start
rc-service rag-pipeline-mcp start
rc-service cicd-mcp start
rc-service mdq-mcp start
rc-service git-mcp start
# sqlite-mcp uses startup_mode=subprocess; started by agent automatically

# Check status
rc-service web-search-mcp status

# Enable at boot
rc-update add web-search-mcp default
```

`file-mcp` OpenRC service covers all 3 file servers (read: 8005, write: 8007, delete: 8008).

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
curl -s http://127.0.0.1:8004/health | jq   # web-search: dependencies.brave_api_key/bing_api_key, details.providers
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
| Server not started | OpenRC not enabled | `rc-service <server> status` |
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

## New Tool Registration Procedure

When adding a new tool to an **existing** MCP server:

1. **Add the tool name to `shared/tool_constants.py`**
   - Add to the appropriate frozenset (`READ_TOOLS`, `WRITE_TOOLS`, etc.)
   - If no set fits, create a new `<SERVER>_TOOLS` frozenset and add it to `get_all_mcp_tool_names()`

2. **Add the tool name to `tool_names` in the server config (`config/agent.toml`)**
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
- [ ] Create `init.d/<server-name>` OpenRC script (mode 755)
- [ ] Add startup step to `deploy/setup_services.sh`
- [ ] Add `tool_safety_tiers` entries to `config/agent.toml` for all new tools
- [ ] Update `routing.md` if new documentation is needed
