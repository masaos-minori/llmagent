# MCP Transport Transparency and Dual Startup Modes — Improvement Procedure Guide

## 1. Objective

Enable transport-transparent MCP usage.

- The agent must use MCP servers without depending on whether the transport is **HTTP** or **stdio**.
- Each MCP server must support two startup modes:
  - **persistent**: always running
  - **ondemand**: started only when needed
- The current model assumes pre-started HTTP services.
  - The agent calls `POST /v1/call_tool`.
  - `/v1/tools` and `/health` are used for definition checks and watchdog probing.
  - Services run as OpenRC-managed persistent processes.

### 1.1 Target State

- The agent uses only a **tool name** and a **server key**.
- HTTP / stdio differences are hidden behind `ToolExecutor`.
- Each server supports either `persistent` or `ondemand` startup behavior.
- `/mcp`, startup-time tool-definition checks, and watchdog behavior must work for **both HTTP and stdio**.
- The current watchdog depends on HTTP `/health`; it must become transport-independent.

---

## 2. Current-State Assessment

### 2.1 Current Standard Operating Model

The current MCP protocol uses an **HTTP + pre-started persistent service** model.

- The agent sends HTTP `POST /v1/call_tool` requests.
- Request format:
  - `{"name": str, "args": {...}}`
- Response format:
  - `{"result": str, "is_error": bool}`
- `GET /v1/tools` is used for tool-definition consistency checks.
- The watchdog probes HTTP `/health` and restarts OpenRC services when needed.

### 2.2 Existing Extensibility in Code

`tool_executor.py` already contains both transports.

- `HttpTransport`
- `StdioTransport`

`StdioTransport` already supports:

- subprocess startup via `start()`
- stdin/stdout JSON-RPC style communication via `call()`
- graceful shutdown via `stop()`
- transport replacement by server key via `set_transport(server_key, transport)`

Therefore, the client-side abstraction already partly exists. However, stdio is not yet a first-class operational mode.

### 2.3 What Is Missing Today

Current gaps:

- The specification, configuration, and operations model are still **HTTP-centric**.
- stdio is not yet a documented first-class mode.
- `mcp_server.py` is only a common base for **HTTP server startup**.
- There is no matching common stdio runtime pattern.
- `file-mcp`, `github-mcp`, and `web-search-mcp` are documented as **HTTP-only** OpenRC-managed persistent services.
- Watchdog, tool-definition checks, and `/mcp` display depend on HTTP `/health` and HTTP `/v1/tools`.
- There is no standard health probing or tool introspection for stdio subprocesses.

---

## 3. Improvement Principles

### 3.1 Core Principles

Implement this improvement according to the following principles.

- **Normalize the transport abstraction**.
  - HTTP and stdio must be represented behind a unified `ToolExecutor`-level client interface.
- **Separate lifecycle policy from transport**.
  - `persistent` versus `ondemand` startup must be an independent configuration axis.
  - Startup policy must not be implicitly tied to HTTP or stdio.
- **Make behavior configuration-driven**.
  - Extend `config/agent.json` / `mcp_servers` with explicit transport and lifecycle controls.
  - The runtime already uses `transport`, `url`, `cmd`, and `openrc_service`.
  - Formalize and extend these fields.
- **Extend the common server base**.
  - Move from an HTTP-only MCP server base to a transport-flexible MCP runtime foundation.
  - The runtime must support both HTTP and stdio.
  - The current `MCPServer.run()` is uvicorn-specific and must be generalized.

---

## 4. Target Architecture

### 4.1 Desired Structure

```text
AgentREPL
  ↓
ToolExecutor
  ├─ McpClientRegistry
  │    ├─ HttpMcpClient
  │    └─ StdioMcpClient
  ├─ ServerLifecycleManager
  │    ├─ persistent startup
  │    └─ on-demand startup
  └─ ToolRouteResolver
       ├─ web_search
       ├─ file
       ├─ github
       └─ future servers...
```

Design intent:

- `AgentREPL` continues to call `ToolExecutor.execute(tool_name, args)`.
- `AgentREPL` does not know the transport.
- `ToolExecutor` reads configuration.
- `ToolExecutor` selects either the HTTP client path or the stdio client path.
- `ToolExecutor` returns the same result contract regardless of transport.
- Since `ToolExecutor` already includes both `HttpTransport` and `StdioTransport`, this is the least disruptive enhancement.

### 4.2 Startup Mode Separation

Each server supports one of the following startup policies.

- `startup_mode = "persistent"`
  - The server stays alive continuously.
  - For HTTP, this means a pre-started OpenRC-managed service.
  - For stdio, this means a subprocess started at agent initialization and kept alive.
- `startup_mode = "ondemand"`
  - The server starts only when first called.
  - It may later stop after an idle timeout.

This enables mixed deployment patterns.

- `web-search-mcp`: HTTP + persistent
- `file-mcp`: stdio + ondemand
- `github-mcp`: either HTTP + persistent or stdio + ondemand, depending on authentication and isolation requirements

---

## 5. Improvement Procedure

### 5.1 Step 1: Extend `McpServerConfig` for Explicit Transport and Startup Mode

#### 5.1.1 What to Change

Formalize and extend `config/agent.json` → `mcp_servers` and the corresponding `McpServerConfig` model so that transport and startup mode are explicit.

The current runtime already uses:

- `transport`
- `url`
- `cmd`
- `openrc_service`

The improvement should build on that structure.

#### 5.1.2 Recommended Config Fields

- `transport`: `http` or `stdio`
- `startup_mode`: `persistent` or `ondemand`
- `url`: base URL for HTTP transport
  - aligned with current MCP URLs such as `web_search_url`, `file_server_url`, and `github_server_url`
- `cmd`: subprocess launch command for stdio mode
  - required because `StdioTransport` uses `asyncio.create_subprocess_exec`
- `openrc_service`: OpenRC service name for persistent HTTP services
  - currently used by the watchdog
- `working_dir`, `env`: working directory and environment injection for stdio startup
- `healthcheck_mode`: `http`, `process`, or `ping_tool`
  - used for transport-specific health checks
- `idle_timeout_sec`: future idle shutdown of ondemand stdio servers

#### 5.1.3 Expected Effect

After this step:

- **transport** becomes an explicit configuration dimension.
- **startup lifecycle** becomes an explicit configuration dimension.
- The system is no longer effectively fixed to HTTP + persistent service operation.

### 5.2 Step 2: Refactor `ToolExecutor` into a Transport-Transparent MCP Client Layer

#### 5.2.1 What to Change

`ToolExecutor` already supports both `HttpTransport` and `StdioTransport`, but routing is hard-coded:

- `search_web` → `web_search`
- `github_*` → `github`
- everything else → `file`

Replace this with **configuration-driven route resolution**.

#### 5.2.2 Recommended Refactoring

- Introduce a `ToolRouteResolver`.
  - It maps `tool_name -> server_key`.
  - It uses `tool_definitions` and/or `mcp_servers[*].tool_names`.
  - It must not rely on prefixes.
- Change `ToolExecutor.execute()`.
  - Resolve `server_key`.
  - Check the configured transport.
  - Call either `HttpTransport.call()` or `StdioTransport.call()`.
  - The caller must not need to know which transport was used.
- Keep the current TTL cache transport-independent.
  - Successful tool results remain cached exactly as before.

#### 5.2.3 Expected Effect

The agent can treat **HTTP and stdio transparently**.

### 5.3 Step 3: Introduce `ServerLifecycleManager` to Unify Persistent and On-Demand Startup

#### 5.3.1 What to Change

`StdioTransport` currently exposes a basic `start()` method.

Startup behavior should instead be managed by a dedicated lifecycle layer that understands policy.

The HTTP side should also support both:

- already running
- start if missing

#### 5.3.2 Recommended Lifecycle Rules

Add `ServerLifecycleManager.ensure_ready(server_key)` with the following behavior.

- `transport=http`, `startup_mode=persistent`
  - only probe `/health`
- `transport=http`, `startup_mode=ondemand`
  - if `/health` fails, attempt launch via `openrc_service` or a configured command
- `transport=stdio`, `startup_mode=persistent`
  - start the subprocess at agent startup
- `transport=stdio`, `startup_mode=ondemand`
  - call `start()` immediately before the first tool call

Also add:

- `shutdown_idle_stdio_servers()`
  - future hook for auto-stopping idle ondemand stdio servers
- cleanup behavior for non-persistent stdio transports during `run()` cleanup
  - this matches the existing `AgentREPL.run()` cleanup philosophy

#### 5.3.3 Expected Effect

This layer allows MCP servers to run either as:

- **always-running services**
- **lazily started services**

without binding that choice to HTTP or stdio.

### 5.4 Step 4: Extend `mcp_server.py` to Support stdio Server Mode

#### 5.4.1 What to Change

`mcp_server.py` is currently an **HTTP-only MCP server base class**.

Current subclass pattern:

- `server_name`
- `http_port`
- `app_module`
- `mcp_tools`
- `run()` launches uvicorn

This must become a **dual-mode MCP server base** supporting both HTTP and stdio runtime modes.

#### 5.4.2 Recommended Refactoring

Keep the shared `dispatch(name, args)` contract, but add:

- `run_http()`
- `run_stdio()`
- `list_tools()`
- `health()`
  - process-alive or ping behavior in stdio mode

In stdio mode:

- use line-delimited JSON or JSON-RPC framing
- keep compatibility with the current `StdioTransport.call()` behavior

Add a `--stdio` command-line flag so the same server code can run in either transport mode.

Examples:

- `python /opt/llm/scripts/web_search_mcp_server.py --stdio`
- `python /opt/llm/scripts/fileop_mcp_server.py --stdio`

#### 5.4.3 Expected Effect

Existing MCP servers become **HTTP / stdio dual-mode** runtimes.

The existing stdio transport in `ToolExecutor` becomes a first-class operating model.

### 5.5 Step 5: Make `web-search-mcp`, `file-mcp`, and `github-mcp` Dual-Mode Servers

#### 5.5.1 What to Change

The current documentation for all three built-in MCP servers describes only **HTTP mode**.

Each server already uses:

- a transport-neutral `dispatch()` model
- `mcp_tools` exposed through the same base abstraction

Therefore, adapt them so `run_stdio()` works with the same dispatch behavior.

#### 5.5.2 Recommended Per-Server Changes

- `WebSearchMCPServer`
  - Keep the existing `dispatch()` for `search_web`.
  - Ensure stdio returns the same formatted result text as HTTP mode.
- `FileopMCPServer`
  - Expose the same 15 tools under stdio as under HTTP.
  - Keep identical dispatch behavior and result formatting.
- `GithubMCPServer`
  - Expose the same GitHub toolset under stdio.
  - Keep the same dispatch and result contract.

#### 5.5.3 Expected Effect

The same MCP server implementation can be deployed as either:

- a **persistent HTTP service**
- a **stdio subprocess**

### 5.6 Step 6: Make Tool-Definition Checking Transport-Independent

#### 5.6.1 What to Change

Today the agent checks MCP tool definitions using HTTP `GET /v1/tools` and compares returned tool names with `tool_definitions`.

Extend this so stdio subprocess servers participate in the same consistency check.

#### 5.6.2 Recommended Implementation

- For HTTP servers:
  - continue using `GET /v1/tools`
- For stdio servers:
  - either send a `tools/list` style JSON-RPC request over stdio
  - or provide an internal command that returns `list_tools()`
- Extract the comparison logic into a `ToolDefinitionChecker`.
  - It chooses internally between HTTP and stdio lookup.
  - It exposes one interface to `AgentREPL`.

#### 5.6.3 Expected Effect

The safety guarantees of `tool_definitions_strict=true` are preserved for **both HTTP and stdio**.

### 5.7 Step 7: Generalize Watchdog and `/mcp` for Both Transport and Startup Modes

#### 5.7.1 What to Change

The current watchdog is designed specifically for **HTTP `/health` probing**.

`/mcp` is also effectively an HTTP service status view.

Both must become transport-aware.

#### 5.7.2 Recommended Behavior

- HTTP / persistent
  - Keep the current `/health` probe + `rc-service restart` flow.
- HTTP / ondemand
  - Prefer **lazy start** over restart when the service is not already up.
- stdio / persistent
  - Use `is_alive()` together with a lightweight ping call for health detection.
  - The current `StdioTransport` already provides `is_alive()`.
- stdio / ondemand
  - Do not treat it as a watchdog target in the same way.
  - Instead, ensure readiness at call time through lifecycle management.
- `/mcp` display
  - Add `transport`, `startup_mode`, `status`, and `tools` columns.
  - Status examples:
    - HTTP: `OK / DOWN`
    - stdio: `RUNNING / STOPPED / STARTING`

The current `/mcp` command already displays MCP server status and tool lists. This is the natural extension of that design.

#### 5.7.3 Expected Effect

Operators can see at a glance:

- which servers use HTTP versus stdio
- which servers are persistent versus on-demand

### 5.8 Step 8: Connect `agent_repl.py` and `agent_commands.py` to the New Lifecycle Model

#### 5.8.1 What to Change

At REPL startup:

- stdio servers configured as `persistent` should be launched ahead of time
- ondemand servers should remain dormant until needed

The current `AgentREPL.run()` flow already:

- initializes components
- checks tool definitions
- optionally starts the watchdog

Therefore, the new lifecycle manager belongs in that setup phase.

#### 5.8.2 Recommended Runtime Changes

- In `_init_components()` or an equivalent setup path, create a `ServerLifecycleManager`.
- Pre-start all `transport=stdio` and `startup_mode=persistent` servers at agent startup.
- Replace `_check_tool_definitions()` with a transport-independent tool-definition checker.
- During `finally` cleanup in `run()`, stop stdio subprocesses and release resources.
  - This matches the current graceful shutdown and cleanup pattern of the REPL.

#### 5.8.3 Expected Effect

From agent startup to shutdown, MCP servers can be managed uniformly regardless of transport or startup policy.

---

## 6. Recommended Configuration Examples

### 6.1 Persistent HTTP Server Example

```json
{
  "web_search": {
    "transport": "http",
    "startup_mode": "persistent",
    "url": "http://127.0.0.1:8004",
    "cmd": [],
    "openrc_service": "web-search-mcp",
    "healthcheck_mode": "http"
  }
}
```

This preserves the current operational model of `web-search-mcp`, already documented as an OpenRC-managed HTTP MCP server exposing `/health` and `/v1/tools`.

### 6.2 On-Demand stdio Server Example

```json
{
  "file": {
    "transport": "stdio",
    "startup_mode": "ondemand",
    "url": "",
    "cmd": [
      "/opt/llm/venv/bin/python",
      "/opt/llm/scripts/fileop_mcp_server.py",
      "--stdio"
    ],
    "openrc_service": "",
    "healthcheck_mode": "process",
    "idle_timeout_sec": 300
  }
}
```

This runs `file-mcp` as an on-demand stdio subprocess instead of an OpenRC-managed HTTP service. Since `StdioTransport` already supports subprocess startup and shutdown, this matches the existing client-side transport design.

### 6.3 Persistent stdio-at-Agent-Startup Example

```json
{
  "github": {
    "transport": "stdio",
    "startup_mode": "persistent",
    "url": "",
    "cmd": [
      "/opt/llm/venv/bin/python",
      "/opt/llm/scripts/github_mcp_server.py",
      "--stdio"
    ],
    "openrc_service": "",
    "healthcheck_mode": "process"
  }
}
```

This starts a stdio subprocess during agent initialization and keeps it alive for the session. Depending on authentication and environment management, this may be preferable to HTTP mode in some deployments, even though the current `github-mcp` documentation assumes persistent HTTP service operation.

---

## 7. Implementation Targets

### 7.1 Primary Files to Modify

- `tool_executor.py`
  - add transport transparency
  - add route resolver
  - call lifecycle manager
  - normalize stdio / HTTP error handling
  - This is the current MCP client integration center.

- `mcp_server.py`
  - add `run_http()` / `run_stdio()`
  - add `list_tools()` / ping support
  - This turns the existing HTTP-only base into a dual-mode server base.

- `web_search_mcp_server.py`, `fileop_mcp_server.py`, `github_mcp_server.py`
  - add `--stdio` startup support
  - add stdio request loop
  - All three are currently documented and implemented as HTTP-only servers.

- `agent_repl.py`
  - connect lifecycle handling
  - add stdio cleanup at shutdown
  - This fits the existing initialization and graceful-finally-cleanup lifecycle.

- `agent_commands.py`
  - extend `/mcp` output to show transport and startup mode
  - The current `/mcp` command is HTTP-oriented and must become more descriptive.

- `config/agent.json` / `agent_config.py`
  - add `startup_mode`, `healthcheck_mode`, and `idle_timeout_sec`
  - The current `McpServerConfig` structure must be extended to support these lifecycle concepts.

### 7.2 Deployment and Operations

- `deploy/deploy.sh`
- `deploy/setup_services.sh`
- `init.d/*`

Persistent HTTP servers continue to use the current OpenRC deployment model. For ondemand stdio servers, OpenRC may no longer be required, but deployment scripts and operational procedures should clearly document which servers are persistent services and which are lazily launched subprocesses. Since the current MCP addition procedure already requires deploy and service updates, this extension should follow the same pattern.

---

## 8. Phased Rollout Plan

### Phase 1: Client-Side Transparency

- Make `ToolExecutor` configuration-driven via route resolver.
- Extend `McpServerConfig` with `startup_mode`.
- Add `ServerLifecycleManager`.
- Extend `/mcp` display.

### Phase 2: Formal stdio Server Support

- Make `mcp_server.py` dual-mode (HTTP / stdio).
- Add `--stdio` support to `web`, `file`, and `github` MCP servers.
- Add transport-independent tool-definition checking.

### Phase 3: Unified Monitoring and Operations

- Add stdio-aware health / ping / watchdog behavior.
- Add idle timeout / auto-stop for ondemand stdio.
- Document mixed persistent / ondemand operations.

---

## 9. Risks and Mitigations

### Risk 1: Tool behavior differs between transports

**Mitigation**

Keep `dispatch()` transport-neutral and ensure that both HTTP and stdio return the same `(result_text, is_error)` contract. Preserving the existing `mcp_server.py` dispatch contract is critical.

### Risk 2: stdio liveness is harder to detect than HTTP health

**Mitigation**

Use `is_alive()` together with a lightweight ping or `list_tools()` call as the health probe for stdio subprocesses. The current watchdog is HTTP-health based, so stdio-specific liveness must be formalized.

### Risk 3: On-demand startup increases first-call latency

**Mitigation**

Recommend `persistent` for high-frequency servers and `ondemand` only for rarely used servers. For example, `web-search-mcp` may stay HTTP + persistent, while `file-mcp` could be stdio + ondemand.

### Risk 4: Conflict with the current OpenRC-centered operating model

**Mitigation**

Keep **HTTP + persistent** as the default production model while introducing stdio + ondemand as an additional supported option. Existing `/health`, watchdog, and service deployment assets should be preserved rather than replaced.

---

## 10. Conclusion

This improvement is fundamentally about **generalizing the current MCP infrastructure without discarding the existing operational model**. Today, the specifications and runbooks assume **HTTP + persistent OpenRC-managed services**, while `tool_executor.py` already contains both **HttpTransport** and **StdioTransport**. Bridging that gap is the core of this guide. Therefore, the recommended initial landing point is the following.

1. Formally define both **`transport`** and **`startup_mode`** in `McpServerConfig`.
2. Introduce a **route resolver** and **ServerLifecycleManager** into `ToolExecutor` so that HTTP and stdio become transparent to the agent.
3. Extend `mcp_server.py` and the existing `web/file/github` servers with **`--stdio` mode**.
4. Make `/mcp`, tool-definition checks, and watchdog behavior **transport-independent**.
5. Keep **HTTP + persistent** as the default operating mode while gradually introducing mixed usage of stdio + ondemand where appropriate.
