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
  - mcp_06_01_configuration-file-inventory.md
  - governance_03_issue-and-uncertainty-management.md
  - mcp_06_02_mcpserverconfig-fields-agenttoml-mcp_servers.md
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

Lifecycle and transport of MCP servers as seen by the agent (`startup_mode`, `transport`, `url`, `cmd` under `mcp_servers.<key>`; field details in `mcp_06_02`). HTTP is the only transport, so the health check mode is always derived as `"http"` and is not a configuration key.

**Layer 2 — MCP Server Local Application Configuration (`config/*_mcp_server.toml`)**

Application settings specific to each MCP server: allowlists and denylists (`allowed_dirs`, `allowed_repos`, `command_allowlist`), resource limits, audit paths, and `auth_token` (a secret reference such as `${ENV:...}`). Each process reads only its own layer.

---

## Server Catalog

Ports are configured per server in `config/agent.toml` (`mcp_servers`). Configuration, tools, security settings, and operational notes per server → [mcp_04_01_web-search-file-read-github.md](mcp_04_01_web-search-file-read-github.md) (the canonical catalog).

All servers use HTTP transport. Each server's `startup_mode` is set in `config/agent.toml`; the default configuration starts a server in `subprocess` mode unless it is disabled with `startup_mode = "none"`.

| Server | Role |
|---|---|
| web-search-mcp | Web Search (DuckDuckGo) and browser page fetch |
| file-read-mcp | Local File Reading |
| github-mcp | GitHub API |
| file-write-mcp | Local File Writing |
| file-delete-mcp | Local File Deletion |
| shell-mcp | Sandboxed Shell Execution |
| rag-pipeline-mcp | RAG Search Pipeline |
| cicd-mcp | GitHub Actions CI/CD |
| mdq-mcp | Markdown Context Compression (FTS5/BM25 search) |
| git-mcp | Local Git Operations |

---

---

## Transport Mechanisms

### HTTP transport (all servers)

``` text
Agent ToolExecutor
  → POST http://127.0.0.1:{port}/v1/call_tool
  → {"name": "tool_name", "args": {...}}
  ← {"result": "...", "is_error": false}
```

HTTP is the only supported transport (`TransportType` in `scripts/shared/mcp_config.py`). Servers started with `startup_mode = "subprocess"` run as subprocesses on loopback.

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

Responsibilities:

- `MCPServer` (`scripts/mcp_servers/server.py`) is the base class for all servers: HTTP startup, `/v1/call_tool`, `/v1/tools`, `/health`. Request/response models are shared by all servers.
- `ToolExecutor` (`shared/tool_executor.py`) owns routing, concurrent execution, and the health registry. It resolves tool names through `ToolRouteResolver` and sends calls through `HttpTransport`.
- `RuntimeToolRegistry` (`shared/runtime_tool_registry.py`) is the sole routing authority. It is constructed from live `/v1/tools` discovery at startup.
- `ToolRegistry` (`shared/tool_registry.py`) is seed data for drift detection of tool definitions and ownership, built from the frozensets in `tool_constants.py`. It is not used for routing.
- `McpServerConfig` (`shared/mcp_config.py`) holds per-server transport settings. `McpServerHealthRegistry` (`shared/mcp_health.py`) tracks HEALTHY/DEGRADED/UNAVAILABLE/HALF_OPEN/UNKNOWN status.

The `tool_names` field in `config/agent.toml` is not an input for routing (observation and drift verification only). See `mcp_06_02_mcpserverconfig-fields-agenttoml-mcp_servers.md` for details.

---

---

## Major Constraints

| Constraint | Value | Source |
|---|---|---|
| Max response size | Fixed limit (`MCP_MAX_RESPONSE_BYTES`) | `scripts/mcp_servers/server.py` |
| Auth header | `Authorization: Bearer <token>` (`auth_token` is required on both sides for every HTTP server including mdq-mcp, and every server verifies it) | `scripts/mcp_servers/server.py` |
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
| Configuration and Operations | [mcp_06_01_configuration-file-inventory.md](mcp_06_01_configuration-file-inventory.md) |
| Known issues and inconsistencies | [governance_03_issue-and-uncertainty-management.md](../00_governance/governance_03_issue-and-uncertainty-management.md) (Part 1, Area: MCP) |

---

## Keywords

- mcp
- system
- overview
- architecture
- health-registry
- half-open
- circuit-breaker
