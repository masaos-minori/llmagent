# MCP System Overview

- Document guide → [04_mcp_00_document-guide.md](04_mcp_00_document-guide.md)

## Purpose

The MCP (Model Context Protocol) layer provides the agent with safe, controlled access to
external resources (filesystem, GitHub, web search, SQLite, shell, RAG, CI/CD, Git) through
a set of independent server processes.

---

## Scope

**In scope:**
- `mcp/` server implementations
- `shared/tool_executor.py`, `shared/route_resolver.py`, `shared/mcp_config.py`
- 11 MCP servers, totaling 43 tools

**Out of scope:**
- Agent REPL internal implementation
- RAG pipeline search logic

---

## Server Catalog

Per-server configuration, tools, security settings, and operational notes → [04_mcp_04_server_catalog.md](04_mcp_04_server_catalog.md) (authoritative catalog).

| Server | Port | Transport | Startup mode | Tools | Role |
|---|---|---|---|---|---|
| web-search-mcp | 8004 | HTTP | persistent | 1 | Web search (DuckDuckGo) |
| file-read-mcp | 8005 | HTTP | persistent | 9 | Local file reading |
| github-mcp | 8006 | HTTP | persistent | 21 | GitHub API |
| file-write-mcp | 8007 | HTTP | persistent | 4 | Local file writing |
| file-delete-mcp | 8008 | HTTP | persistent | 2 | Local file deletion |
| shell-mcp | 8009 | HTTP | persistent | 1 | Sandboxed shell execution |
| rag-pipeline-mcp | 8010 | HTTP | persistent | 4 | RAG retrieval pipeline |
| sqlite-mcp | 8011 | HTTP | persistent | 1 | SQLite queries |
| cicd-mcp | 8012 | HTTP | persistent | 4 | GitHub Actions CI/CD |
| mdq-mcp | 8013 | HTTP | persistent | 9 | Markdown context compression |
| git-mcp | 8014 | HTTP | persistent | 10 | Local git operations |

---

## Transport Mechanisms

### HTTP transport (most servers)

```
Agent ToolExecutor
  → POST http://127.0.0.1:{port}/v1/call_tool
  → {"name": "tool_name", "args": {...}}
  ← {"result": "...", "is_error": false}
```

Servers run as persistent HTTP processes on loopback.

### stdio transport (optional)

```
Agent StdioTransport
  → stdin: {"id": N, "name": "tool_name", "args": {...}}\n
  ← stdout: {"id": N, "result": "...", "is_error": false, "truncated": false, "total_bytes": N, "actual_visible_bytes": N}\n
```

Currently all 11 servers use HTTP. stdio mode is available via `--stdio` flag on any server.

### Transport Selection Guide

> **Production default: always use HTTP (`transport = "http"`, `startup_mode = "subprocess"` for agent-managed HTTP servers (agent spawns uvicorn), or `startup_mode = "persistent"` for pre-existing HTTP servers (agent connects only)).**
> HTTP supports watchdog, health checks, concurrent requests, and remote monitoring.
>
> **Use stdio only for:** local testing, CI pipelines, embedded single-tool subprocesses
> with low concurrency and no external clients.
>
> See [04_mcp_02 §When to use stdio](04_mcp_02_protocol_and_transport.md#when-to-use-stdio) for the full decision guide.

---

## Startup Modes

| `startup_mode` | `transport` | Behavior |
|---|---|---|
| `persistent` (default) | `http` | Externally managed server; agent connects to existing HTTP endpoint |
| `subprocess` | `http` | Agent starts uvicorn subprocess at launch; polls `/health` |
| `persistent` | `stdio` | Agent starts subprocess at launch; runs for session lifetime |
| `ondemand` | `stdio` | Agent starts subprocess on first tool call; stops after `idle_timeout_sec` |

`subprocess` + `stdio` is invalid (`ValueError` on config validation).

---

## Major Components

| Component | File | Responsibility |
|---|---|---|
| `MCPServer` | `mcp/server.py` | Base class: HTTP/stdio startup, `/v1/call_tool`, `/v1/tools`, `/health` |
| `CallToolRequest` / `CallToolResponse` | `mcp/models.py` | Shared Pydantic models for all servers |
| `ToolExecutor` | `shared/tool_executor.py` | Routing, TTL cache, concurrency, health registry |
| `ToolRouteResolver` | `shared/route_resolver.py` | tool_name → server_key resolution |
| `ToolRegistry` | `shared/tool_registry.py` | Single source of truth for tool definitions and ownership |
| `McpServerConfig` | `shared/mcp_config.py` | Per-server transport configuration |
| `McpServerHealthRegistry` | `shared/mcp_config.py` | Per-server HEALTHY/DEGRADED/UNAVAILABLE state |
| `HttpTransport` | `shared/tool_executor.py` | HTTP POST to MCP server |
| `StdioTransport` | `shared/tool_executor.py` | JSON-RPC over subprocess stdin/stdout |
| `_ServerLifecycleRouter` | `factory.py` | HTTP subprocess + stdio lifecycle management |

---

## Relationship Among server, protocol, and shared

```
agent/factory.py
  → builds ToolExecutor (shared/tool_executor.py)
       → uses ToolRouteResolver (shared/route_resolver.py)
       → uses HttpTransport / StdioTransport (shared/tool_executor.py)
       → uses McpServerConfig (shared/mcp_config.py)
       → uses McpServerHealthRegistry (shared/mcp_config.py)

MCP server processes (mcp/<name>/server.py)
  → inherit MCPServer (mcp/server.py)
  → use CallToolRequest / CallToolResponse (mcp/models.py)
  → implement dispatch(name, args) → DispatchResult
```

---

## Major Constraints

| Constraint | Value | Source |
|---|---|---|
| Max response size | 512 KB (`MCP_MAX_RESPONSE_BYTES = 524288`) | `mcp/server.py` |
| stdio call timeout | 60.0 sec (`_STDIO_CALL_TIMEOUT`) | `shared/tool_executor.py` |
| Auth header | `Authorization: Bearer <token>` (when `auth_token` set) | `mcp/server.py` |
| Health state threshold | 3 consecutive failures → UNAVAILABLE | `shared/mcp_config.py` |

---

## Related Chapters

| Topic | File |
|---|---|
| Protocol details, HTTP/stdio format, audit log | [04_mcp_02_protocol_and_transport.md](04_mcp_02_protocol_and_transport.md) |
| Routing, lifecycle, ToolExecutor | [04_mcp_03_routing_lifecycle_and_execution.md](04_mcp_03_routing_lifecycle_and_execution.md) |
| Per-server specifications | [04_mcp_04_server_catalog.md](04_mcp_04_server_catalog.md) |
| Security and safety model | [04_mcp_05_security_and_safety_model.md](04_mcp_05_security_and_safety_model.md) |
| Configuration and operations | [04_mcp_06_configuration_and_operations.md](04_mcp_06_configuration_and_operations.md) |
| Known bugs and inconsistencies | [04_mcp_90_inconsistencies_and_known_issues.md](04_mcp_90_inconsistencies_and_known_issues.md) |
