---
title: "MCP System Overview"
area: mcp
tags:
  - mcp
  - system
  - overview
  - architecture
related:
  - 04_mcp_00_document-guide.md
---

# MCP System Overview

- Document Guide $\rightarrow$ [04_mcp_00_document-guide.md](04_mcp_00_document-guide.md)

## Purpose

The MCP (Model Context Protocol) layer provides the agent with safe and controlled access to external resources (File System, GitHub, Web Search, SQLite, Shell, RAG, CI/CD, Git) through a set of independent server processes.

---

## Scope

**In scope:**
- Server implementations in `mcp_servers/`
- `shared/tool_executor.py`, `shared/route_resolver.py`, `shared/mcp_config.py`
- MCP servers are defined in `config/agent.toml` under `[mcp_servers.*]`. The tools provided by each server are managed via a frozenset in `tool_constants.py` and registered through `ToolRegistry` (for drift detection). At runtime, `RuntimeToolRegistry` (`shared/runtime_tool_registry.py`) is the sole authority for routing, constructed from live `/v1/tools` discovery upon startup.

**Out of scope:**
- Internal implementation of the Agent REPL
- Search logic of the RAG pipeline

---

## Configuration Model (2 Layers)

MCP server configuration is split into two layers.

**Layer 1 — Agent Process Configuration (`config/agent.toml`)**

Configuration for managing the lifecycle and transport of MCP servers on the agent side:
- `mcp_servers.<key>.startup_mode` — subprocess / persistent / none
- `mcp_servers.<key>.transport` — http
- `mcp_servers.<key>.url` — HTTP endpoint
- `mcp_servers.<key>.cmd` — Subprocess startup command

(`healthcheck_mode` was removed on 2026-07-17 — it was redundant wiring as HTTP is the only transport and always automatically derived as `"http"`)

**Layer 2 — MCP Server Local Application Configuration (`config/*_mcp_server.toml`)**

Application settings specific to each MCP server:
- allowlists / denylists
- Resource limits
- Audit paths
- allowed_repos / allowed_repos_mode (GitHub specific)
- command_allowlist (Shell specific)
- allowed_dirs (File server specific)
- auth_token_env / auth_token_file (Secret references)

---

## Server Catalog

Configuration, tools, security settings, and operational notes per server $\rightarrow$ [04_mcp_04_01_web-search-file-read-github.md](04_mcp_04_01_web-search-file-read-github.md) (the canonical catalog).

| Server | Port | Transport | Startup Mode | Tool Count | Role |
|---|---|---|---|---|---|
| web-search-mcp | 8004 | HTTP | subprocess | 2 (Updated: 1 -> 2 due to browser_fetch integration) | Web Search (DuckDuckGo) |
| file-read-mcp | 8005 | HTTP | subprocess | 9 | Local File Reading |
| github-mcp | 8006 | HTTP | subprocess | 21 | GitHub API |
| file-write-mcp | 8007 | HTTP | subprocess | 4 | Local File Writing |
| file-delete-mcp | 8008 | HTTP | subprocess | 2 | Local File Deletion |
| shell-mcp | 8009 | HTTP | subprocess | 1 | Sandboxed Shell Execution |
| rag-pipeline-mcp | 8010 | HTTP | subprocess | 4 | RAG Search Pipeline |
| cicd-mcp | 8012 | HTTP | subprocess | 4 | GitHub Actions CI/CD |
| mdq-mcp | 8013 | HTTP | subprocess | 7 | Markdown Context Compression |
| git-mcp | 8014 | HTTP | subprocess | 10 | Local Git Operations |

---

## Transport Mechanisms

### HTTP transport (Most servers)

``` text
Agent ToolExecutor
  $\rightarrow$ POST http://127.0.0.1:{port}/v1/call_tool
  $\rightarrow$ {"name": "tool_name", "args": {...}}
  $\leftarrow$ {"result": "...", "is_error": false}
```

Servers run as subprocesses on loopback.

### Transport Selection Guide

> **Production Default: Always use HTTP (`transport = "http"`). For HTTP servers managed by the agent (when the agent starts uvicorn), use `startup_mode = "subprocess"`; for existing HTTP servers (where the agent only connects), use `startup_mode = "persistent"`.**
> HTTP supports health checks, concurrent requests, and remote monitoring.

---

## Startup Modes

| `startup_mode` | `transport` | Behavior |
|---|---|---|
| `none` | N/A | Disabled mode — no subprocess startup or lifecycle operations |
| `persistent` | `http` | Externally managed server; agent connects to an existing HTTP endpoint |
| `subprocess` | `http` | Agent starts a uvicorn subprocess at startup and polls `/health` |

**Default Value:** If `startup_mode` is omitted in config, it defaults to `"none"`. To enable a server, you must explicitly specify `"persistent"` or `"subprocess"`.

---

## Major Components

| Component | File | Responsibility |
|---|---|---|
| `MCPServer` | `scripts/mcp_servers/server.py` | Base class: HTTP startup, `/v1/call_tool`, `/v1/tools`, `/health` |
| `CallToolRequest` / `CallToolResponse` | `scripts/mcp_servers/models.py` | Common Pydantic models for all servers |
| `ToolExecutor` | `shared/tool_executor.py` | Routing, concurrent execution, health registry |
| `ToolRouteResolver` | `shared/route_resolver.py` | Resolves tool_name $\rightarrow$ server_key (references only `RuntimeToolRegistry.resolve()`) |
| `RuntimeToolRegistry` | `shared/runtime_tool_registry.py` | **Sole routing authority**. Constructed via live `/v1/tools` discovery using McpToolDiscoveryService |
The runtime routing authority is `RuntimeToolRegistry`. The `tool_names` field in `config/agent.toml` is not an input for routing (it is used for observation and drift verification only). See `docs/04_mcp_06_03` for details. |
| `ToolRegistry` | `shared/tool_registry.py` | Seed data for drift detection regarding tool definitions and ownership (constructed at import from frozenset in `tool_constants.py`; not used for routing) |
| `McpServerConfig` | `shared/mcp_config.py` | Transport settings per server |
| `McpServerHealthRegistry` | `shared/mcp_health.py` | Server status: HEALTHY/DEGRADED/UNAVAILABLE/HALF_OPEN/UNKNOWN (only re-exports `shared/mcp_config.py`) |
| `HttpTransport` | `shared/http_transport.py` | HTTP POST to MCP servers |

---

## Relationship between server, protocol, and shared

``` text
agent/factory.py
  $\rightarrow$ builds ToolExecutor (shared/tool_executor.py)
       $\rightarrow$ uses ToolRouteResolver (shared/route_resolver.py)
       $\rightarrow$ uses HttpTransport (shared/http_transport.py)
       $\rightarrow$ uses McpServerConfig (shared/mcp_config.py)
       $\rightarrow$ uses McpServerHealthRegistry (shared/mcp_health.py)

MCP server processes (mcp_servers/<name>/server.py)
   $\rightarrow$ inherit MCPServer (scripts/mcp_servers/server.py)
   $\rightarrow$ use CallToolRequest / CallToolResponse (scripts/mcp_servers/models.py)
  $\rightarrow$ implement dispatch(name, args) $\rightarrow$ DispatchResult
```

---

## Major Constraints

| Constraint | Value | Source |
|---|---|---|
| Max response size | 512 KB (`MCP_MAX_RESPONSE_SIZE = 524288`) | `scripts/mcp_servers/server.py` |
| Auth header | `Authorization: Bearer <token>` (when `auth_token` is configured) | `scripts/mcp_servers/server.py` |
| Health threshold | Default: 3 consecutive failures $\rightarrow$ UNAVAILABLE | `shared/mcp_health.py` (`McpServerHealthRegistry`) |

---

## Implementation Notes

- State transitions in `McpServerHealthRegistry` are not simple ternary values, but five: `HEALTHY` / `DEGRADED` / `UNAVAILABLE` / `HALF_OPEN` / `UNKNOWN`. A server that becomes `UNAVAILABLE` automatically transitions to `HALF_OPEN` (a trial state allowing one request) after 30 seconds (`half_open_cooldown_sec`) upon calling `is_unavailable()`, acting as a simple circuit breaker (Explicit in code, `shared/mcp_health.py`).
- `record_degraded()` does not overwrite the current state if it is `UNAVAILABLE` or `HALF_OPEN` (to avoid breaking the circuit breaker and trial window) (Explicit in code).

---

## Related Chapters

| Topic | File |
|---|---|
| Protocol details, HTTP format | [04_mcp_02_01_endpoints-and-transport.md](04_mcp_02_01_endpoints-and-transport.md) |
| Audit log | [04_mcp_02_03_audit-logging-and-errors.md](04_mcp_02_03_audit-logging-and-errors.md) |
| Routing, Lifecycle, ToolExecutor | [04_mcp_03_01_dispatch-and-routing.md](04_mcp_03_01_dispatch-and-routing.md) |
| Per-server specification | [04_mcp_04_01_web-search-file-read-github.md](04_mcp_04_01_web-search-file-read-github.md) |
| Security and Safety model | [04_mcp_05_01_access-control-and-allowlists.md](04_mcp_05_01_access-control-and-allowlists.md) |
| Configuration and Operations | [04_mcp_06_02_configuration-file-inventory.md](04_mcp_06_02_configuration-file-inventory.md) |
| Known issues and inconsistencies | [04_mcp_90_inconsistencies_and_known_issues.md](04_mcp_90_inconsistencies_and_known_issues.md) |

---

## Keywords

mcp
system
overview
architecture
health-registry
half-open
circuit-breaker
