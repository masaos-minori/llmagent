---
title: "MCP System Overview"
area: mcp
tags:
  - mcp
  - system
  - overview
  - architecture
related:
  - mcp_00_document-guide.md
  - mcp_02_01_endpoints-and-transport.md
  - mcp_02_03_audit-logging-and-errors.md
  - mcp_03_01_dispatch-and-routing.md
  - mcp_04_01_web-search-file-read-github.md
  - mcp_05_01_access-control-and-allowlists.md
  - mcp_06_02_configuration-file-inventory.md
  - governance_03_issue-and-uncertainty-management.md
---

# MCP System Overview

- Document Guide → [mcp_00_document-guide.md](mcp_00_document-guide.md)

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

(HTTP is the only transport, so the health check mode is always derived as `"http"` and is not a configuration key)

**Layer 2 — MCP Server Local Application Configuration (`config/*_mcp_server.toml`)**

Application settings specific to each MCP server:
- allowlists / denylists
- Resource limits
- Audit paths
- allowed_repos / allowed_repos_mode (GitHub specific)
- command_allowlist (Shell specific)
- allowed_dirs (File server specific)
- auth_token (Secret reference, e.g. `${ENV:...}`)

---

## Server Catalog

Ports are configured per server in `config/agent.toml` (`mcp_servers`). Configuration, tools, security settings, and operational notes per server → [mcp_04_01_web-search-file-read-github.md](mcp_04_01_web-search-file-read-github.md) (the canonical catalog).

| Server | Transport | Startup Mode | Role |
|---|---|---|---|
| web-search-mcp | HTTP | subprocess | Web Search (DuckDuckGo) |
| file-read-mcp | HTTP | subprocess | Local File Reading |
| github-mcp | HTTP | subprocess | GitHub API |
| file-write-mcp | HTTP | subprocess | Local File Writing |
| file-delete-mcp | HTTP | subprocess | Local File Deletion |
| shell-mcp | HTTP | subprocess | Sandboxed Shell Execution |
| rag-pipeline-mcp | HTTP | subprocess | RAG Search Pipeline |
| cicd-mcp | HTTP | subprocess | GitHub Actions CI/CD |
| mdq-mcp | HTTP | subprocess | Markdown Context Compression |
| git-mcp | HTTP | subprocess | Local Git Operations |

---

## Transport Mechanisms

### HTTP transport (Most servers)

``` text
Agent ToolExecutor
  → POST http://127.0.0.1:{port}/v1/call_tool
  → {"name": "tool_name", "args": {...}}
  ← {"result": "...", "is_error": false}
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
| `ToolRouteResolver` | `shared/route_resolver.py` | Resolves tool_name → server_key (references only `RuntimeToolRegistry.resolve()`) |
| `RuntimeToolRegistry` | `shared/runtime_tool_registry.py` | **Sole routing authority**. Constructed via live `/v1/tools` discovery using McpToolDiscoveryService |
The runtime routing authority is `RuntimeToolRegistry`. The `tool_names` field in `config/agent.toml` is not an input for routing (it is used for observation and drift verification only). See `mcp_06_03_mcpserverconfig-fields-agenttoml-mcp_servers.md` for details. |
| `ToolRegistry` | `shared/tool_registry.py` | Seed data for drift detection regarding tool definitions and ownership (constructed at import from frozenset in `tool_constants.py`; not used for routing) |
| `McpServerConfig` | `shared/mcp_config.py` | Transport settings per server |
| `McpServerHealthRegistry` | `shared/mcp_health.py` | Server status: HEALTHY/DEGRADED/UNAVAILABLE/HALF_OPEN/UNKNOWN (re-exported by `shared/mcp_config.py`) |
| `HttpTransport` | `shared/http_transport.py` | HTTP POST to MCP servers |

---

## Relationship between server, protocol, and shared

``` text
agent/factory.py
  → builds ToolExecutor (shared/tool_executor.py)
       → uses ToolRouteResolver (shared/route_resolver.py)
       → uses HttpTransport (shared/http_transport.py)
       → uses McpServerConfig (shared/mcp_config.py)
       → uses McpServerHealthRegistry (shared/mcp_health.py)

MCP server processes (mcp_servers/<name>/server.py)
   → inherit MCPServer (scripts/mcp_servers/server.py)
   → use CallToolRequest / CallToolResponse (scripts/mcp_servers/models.py)
  → implement dispatch(name, args) → DispatchResult
```

---

## Major Constraints

| Constraint | Value | Source |
|---|---|---|
| Max response size | Fixed limit (`MCP_MAX_RESPONSE_BYTES`) | `scripts/mcp_servers/server.py` |
| Auth header | `Authorization: Bearer <token>` (when `auth_token` is configured) | `scripts/mcp_servers/server.py` |
| Health threshold | Consecutive failures reaching `failure_threshold` → UNAVAILABLE | `shared/mcp_health.py` (`McpServerHealthRegistry`) |
| Circuit breaker recovery | `UNAVAILABLE` auto-transitions to `HALF_OPEN` (a trial state allowing one request) after `half_open_cooldown_sec` on `is_unavailable()`. | `shared/mcp_health.py` (`McpServerHealthRegistry`) |

---

## Chapter Map

| Topic | File |
|---|---|
| Protocol details, HTTP format | [mcp_02_01_endpoints-and-transport.md](mcp_02_01_endpoints-and-transport.md) |
| Audit log | [mcp_02_03_audit-logging-and-errors.md](mcp_02_03_audit-logging-and-errors.md) |
| Routing, Lifecycle, ToolExecutor | [mcp_03_01_dispatch-and-routing.md](mcp_03_01_dispatch-and-routing.md) |
| Per-server specification | [mcp_04_01_web-search-file-read-github.md](mcp_04_01_web-search-file-read-github.md) |
| Security and Safety model | [mcp_05_01_access-control-and-allowlists.md](mcp_05_01_access-control-and-allowlists.md) |
| Configuration and Operations | [mcp_06_02_configuration-file-inventory.md](mcp_06_02_configuration-file-inventory.md) |
| Known issues and inconsistencies | [governance_03_issue-and-uncertainty-management.md](../00_governance/governance_03_issue-and-uncertainty-management.md) (Part 1, Area: MCP) |

---

## Keywords

mcp
system
overview
architecture
health-registry
half-open
circuit-breaker
