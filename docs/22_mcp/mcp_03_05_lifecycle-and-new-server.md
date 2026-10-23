---
title: "Process Introspection and Adding a New MCP Server"
area: mcp
tags:
  - mcp
  - lifecycle
  - process-introspection
related:
  - mcp_00_document-guide.md
  - mcp_03_03_transport-and-health.md
  - mcp_06_11_new-tool-registration-procedure.md
  - adr_02_02_003_agent-runtime-tool-registry-routing-authority.md
---
# Process Introspection and Adding a New MCP Server

## Process Introspection

`HttpServerLifecycleManager` provides read-only snapshots of managed subprocesses for diagnostic purposes (e.g., via the `/mcp status` command or `mcp_status.py`).

- Per-server snapshot (`pid`, `pgid`, `running`, `last_exit_code`; `None` for an unknown key), a typed variant that adds `managed` and `stderr_log`, and a listing of all managed servers.
These methods only perform `proc.poll()` or read cached states; they do not terminate or restart processes. A snapshot exists only while the manager holds a process entry: shutdown removes that entry before signalling, so after an unconfirmed termination the surviving record is the reported failure (server key, outcome, and the pid and pgid in the agent log), not a snapshot.

The `_ServerLifecycleRouter` facade (`agent/lifecycle_router.py`) delegates these methods, so callers such as `McpStatusService` use them without touching the manager internals.

---

## Adding a New MCP Server

### Adding a new tool

#### How to safely add a new tool

When adding a new tool, follow the standard procedure in [mcp_06_11_new-tool-registration-procedure.md](mcp_06_11_new-tool-registration-procedure.md).

Key points:
1. **Declare the tool in the owning server's `GET /v1/tools` response (its `TOOL_LIST` entry), with the schema-2.0 fields [REQUIRED]** — Live discovery of `/v1/tools` is the sole basis for routing: `RuntimeToolRegistry` is built from it at startup. A tool that is missing from `/v1/tools`, or whose entry fails schema-2.0 validation, is excluded from the registry and is not routable (see [ADR-003](../10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md)).
2. **Add the tool name to the frozenset in `shared/tool_constants.py` [REQUIRED for the static ownership seed — not a routing input]** — The static `ToolRegistry` built from these frozensets is used only as drift-detection input (compared against live `/v1/tools` and the configured `tool_names`) and for static classification; it never decides routing.
3. **Add `tool_names` to the server configuration [OPTIONAL]** — Only serves as a hint for drift validation; not required for routing.
4. **Add the LLM schema to `[[tool_definitions]]` in `config/agent.toml` [REQUIRED if you want the tool visible to the LLM]**
5. **Add an entry to `tool_safety_tiers` in `config/agent.toml` [REQUIRED — all tools must declare their safety tier]**

### Summary of Routing Precedence

See [ADR-003](../10_adr/adr_02_02_003_agent-runtime-tool-registry-routing-authority.md) for rationale and invariants.

### New Server/Tool Registration Checklist

| Item | Required? | Notes |
|---|---|---|
| Owning server's `/v1/tools` (`TOOL_LIST`) — declare the tool with schema-2.0 fields | **Required** | Sole routing basis; a missing or invalid entry leaves the tool unroutable |
| `shared/tool_constants.py` — Add tool to frozenset | **Required** (static seed) | Feeds drift detection and static classification only; not a routing input |
| `config/agent.toml` — Add to `[[tool_definitions]]` | **Required** (if tool is to be visible to LLM) | OpenAI function-calling format; required for LLM to call the tool |
| `config/agent.toml` — Add `tool_safety_tiers` entry | **Required** | All tools must declare a safety tier |
| `config/<key>_mcp_server.toml` — Server config file | **Required** (for new servers) | Server application settings (server-specific values only). The `[mcp_servers.<key>]` transport section belongs in `config/agent.toml`. |
| `deploy/deploy.sh` — Add installation/copy step | **Required** (for new servers) | The deployment must include the new server |
| Update `routing.md` (repository root) | **Required** | Documentation guide must reference the new server |

### Manual Procedure

Follow [mcp_06_12_new-mcp-server-addition-checklist.md](mcp_06_12_new-mcp-server-addition-checklist.md). The server subclasses `MCPServer` and overrides `dispatch()`, and its `GET /v1/tools` returns `server_key` plus the schema-2.0 fields. With `startup_mode = "subprocess"` the agent starts the server, so `deploy/setup_services.sh` needs no per-server step.

### Setting `tool_names` (Drift Detection Only)

Runtime routing is built from live `/v1/tools` discovery (`RuntimeToolRegistry`); the static `ToolRegistry` built from the `tool_constants.py` frozensets is drift-detection input only. For drift detection, you can optionally add `tool_names` to the `[mcp_servers.<key>]` server configuration in `config/agent.toml`.

Even if `tool_names` is omitted or incomplete, routing is still determined by `/v1/tools` discovery (`RuntimeToolRegistry` is the sole routing authority, ADR-003), but a warning will be issued during startup drift validation.

## Keywords

- mcp
- lifecycle
- process introspection
- new mcp server
- tool_constants
- tool_safety_tiers
- deploy
