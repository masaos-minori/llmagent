# MCP Integrated Plugin System — Build Plan

## Goal

- Standardize external system access through MCP servers.
- Route local files, local databases, scripts, and internal APIs through safe tool calls.
- Remove direct dependencies from the Agent to the OS or external services.
- Build an IDE-independent, local-first, and extensible integration layer for real work.
- Keep compatibility with future interconnection to other MCP hosts.

## Scope

- Define the MCP Gateway adoption policy.
- Define a unified call path from MCP Client to MCP Servers.
- Define MCP coverage for Git, Browser, FileSystem, CI/CD, SQLite, and Script Runner.
- Define execution guards:
  - path allowlist
  - command allowlist
  - size limits
  - readonly / readwrite separation
- Define publishing modes:
  - local URL
  - tunnel
  - port-forward
  - auth token
- Define the rule that Workers under the Orchestrator access external systems only through MCP Gateway.
- Define integration with the current Agent:
  - `tool_definitions`
  - `mcp_servers`
  - `/mcp`
  - `/mcp install`

## Assumptions

- The current Agent calls MCP servers over HTTP and uses `/v1/call_tool` and `/v1/tools`. Tool definitions are passed to the LLM from `config/agent.json`.
- The current Agent already uses `web-search-mcp`, `file-mcp`, and `github-mcp`, and `/mcp` can show connectivity and tool lists.
- `agent_config.py` already has `McpServerConfig` with `transport=http|stdio`, `url`, `cmd`, and `openrc_service`.
- The ToolExecutor-equivalent layer already handles MCP routing, TTL cache, and error handling.
- `/mcp install <name>` can already generate a new MCP server template and a manual follow-up guide.
- Control features such as plan mode, approval flow, serial tool execution, and tool definition strict mode already exist.

## Unknowns

- Whether MCP Gateway should be a single server or a set of function-specific MCP servers.
- Whether FileSystem, Script, and SQLite should be combined into one server or split by responsibility.
- Where auth tokens should be issued:
  - per Agent
  - per Worker
  - per Server
- Whether write-operation approval should be enforced by the Gateway or judged on the Agent side.
- Whether CI/CD and internal APIs should use HTTP MCP or stdio MCP.
- How far tunnel / port-forward should be allowed in a local-first model.
- Where to draw the boundary between the current `file-mcp` and future FS MCP / Script MCP / SQLite MCP.

## Affected areas

### Core runtime

- `agent_repl.py`
- `orchestrator.py`
- `agent_context.py`
- `agent_config.py`
- `agent_commands.py`
- `tool_executor.py`

### Existing MCP-related areas

- `config/agent.json`
- `tool_definitions`
- `mcp_servers`
- `/mcp`
- `/mcp install`
- approval flow
- serial tool call control

### New MCP servers or gateway modules

- `fs-mcp` or `mcp-gateway/filesystem`
- `sqlite-mcp` or `mcp-gateway/sqlite`
- `script-mcp` or `mcp-gateway/script`
- `browser-mcp`
- `git-actions-mcp` or `ci-mcp`
- shared authentication / authorization layer

### Ops / deployment

- OpenRC service definitions
- deploy scripts
- token distribution method
- local URL / tunnel / port-forward settings
- audit logs

## Design

### 1. Base structure

Recommended structure:

```text
Agent
  ↓
MCP Client
  ↓
MCP Servers / MCP Gateway
```

Policy:

- The Agent should call external tools only through MCP.
- External system access should be isolated inside MCP servers.
- Workers should not access the OS or external APIs directly.
- Audit, permission control, and connection methods should be centralized at the MCP boundary.

### 2. MCP targets

Initial targets:

- Git MCP
- Browser MCP
- FileSystem MCP
- GitHub Actions / CI MCP
- SQLite MCP
- Script Runner MCP

Recommended priority:

1. FileSystem MCP
2. SQLite MCP
3. Script Runner MCP
4. Refactoring Git MCP / GitHub MCP responsibilities
5. Browser MCP
6. CI/CD MCP

### 3. MCP Gateway responsibilities

The MCP Gateway should provide:

- unified tool publication
- execution target validation
- mandatory execution guards
- auth token validation
- audit log output
- unified error format

Minimum feature set:

- `list_files`
- `read_file`
- `search_file`
- `write_file`
- `query_sqlite`
- `invoke_script`

### 4. Execution guards

Required guards:

#### FileSystem

- path allowlist
- max file size limit
- readonly / readwrite separation
- explicit approval for delete / overwrite

#### Script Runner

- command allowlist
- argument array enforcement
- timeout
- stdout / stderr size limits
- execution user restriction

#### SQLite

- database allowlist
- separate read-only and write queries
- result-row limit

#### Browser / HTTP API

- destination allowlist
- required token
- request ID assignment
- response size limit

### 5. Authentication and publishing mode

Initial policy:

- Use loopback URL as the default for local development.
- Use tunnel / port-forward only when external exposure is required.
- Add auth tokens to all externally reachable MCPs.
- Even local-only MCPs should support a common auth header for future consistency.

Minimum requirements:

- `Authorization: Bearer <token>`
- `X-Request-Id`
- request ID recording in audit logs

### 6. Integration with the current Agent

#### Tool routing

- Keep the current `tool_definitions` model.
- Reorganize tool names by MCP responsibility.
- Keep the design open so the current `file-mcp` can later split into `fs-mcp`, `sqlite-mcp`, and `script-mcp`.

#### Config

- Treat `config/agent.json` `mcp_servers` as the source of truth.
- Reuse `McpServerConfig` fields:
  - `transport`
  - `url`
  - `cmd`
  - `openrc_service`
- Add Gateway settings such as auth token and allowlists.

#### `/mcp`

- Show not only connectivity, but also:
  - server role
  - mode
  - auth required
  - write capability

#### `/mcp install`

- Extend templates for:
  - FS
  - SQLite
  - Script
  - Browser
  - CI MCPs
- Include generated examples for:
  - `agent.json`
  - OpenRC definitions
  - auth settings

### 7. Policy under Orchestrator integration

- Workers should access external systems only through MCP Gateway.
- Allowed tools should be restricted per Worker role.
- PatchWorker should receive only minimal FileSystem / Script permissions.
- Retriever should mainly use Browser / FileSystem / SQLite.
- Validator should mainly use Script / CI.
- Integrator should mainly use Git / FileSystem.

### 8. Phased rollout policy

#### Phase 1

- Reorganize existing `file-mcp`, `github-mcp`, and `web-search-mcp`.
- Add minimum FileSystem / SQLite / Script MCPs.
- Add only the shared authentication and audit-log framework.

#### Phase 2

- Add Browser MCP and CI/CD MCP.
- Extend `/mcp` and `/mcp install`.
- Unify allowlist, approval, and audit handling.

#### Phase 3

- Finalize either Gateway consolidation or responsibility-based server split.
- Tighten allowed-tools control by Worker role.
- Add publishing control for future external host integration.

## Implementation steps

### Phase 1: Base additions

- Inventory existing MCP servers and responsibilities.
- Add MCP Gateway settings to `config/agent.json`:
  - auth token
  - path allowlist
  - command allowlist
  - readonly / readwrite mode
- Add matching settings to `agent_config.py`.
- Add new server keys and tool routing to `tool_executor.py`.
- Add minimum FileSystem MCP.
- Add minimum SQLite MCP.
- Add minimum Script Runner MCP.
- Add `request_id / tool / target / elapsed` to audit logs.

### Phase 2: CLI and operations integration

- Extend `/mcp` display fields.
- Extend `/mcp install` template generation targets.
- Add OpenRC service definitions.
- Reflect the MCP addition flow in deploy scripts.
- Connect approval flow and write-capability display.

### Phase 3: Advanced expansion

- Add Browser MCP.
- Add CI/CD MCP.
- Add allowed-tools control by Worker role.
- Finalize tunnel / port-forward / token operation rules.
- If needed, reorganize into a consolidated MCP Gateway version.

## Validation plan

### Unit tests

- allowlist checks
- readonly / readwrite checks
- command allowlist checks
- auth token validation
- request ID assignment
- tool routing

### Integration tests

- Agent → MCP calls succeed
- `/v1/tools` matches `tool_definitions`
- new servers appear in `/mcp`
- `/mcp install` generates templates correctly
- OpenRC start / stop works

### Security tests

- reject paths outside allowlist
- reject commands outside allowlist
- reject requests without token
- limit oversized responses
- verify write-mode restrictions

### Regression tests

- existing `web-search-mcp`, `file-mcp`, and `github-mcp` remain stable
- existing tool loop remains stable
- `serial_tool_calls` and approval flow remain intact
- `tool_definitions_strict` remains intact

## Risks

### 1. Unclear responsibility boundaries

- If `file-mcp` overlaps with new FS / SQLite / Script MCPs, operations become confusing.
- Mitigation:
  - define a responsibility matrix early
  - fix tool name → server key mapping

### 2. Gaps in permission control

- Weak path or command restrictions may allow dangerous operations.
- Mitigation:
  - require allowlists
  - separate read and write
  - enforce audit logging

### 3. Inconsistency with existing configuration

- If `tool_definitions` and `/v1/tools` diverge, startup failure or incorrect behavior may occur.
- Mitigation:
  - validate under strict mode
  - auto-generate config examples through `/mcp install`

### 4. Operational complexity from server growth

- More MCP servers increase OpenRC, deploy, and token-management complexity.
- Mitigation:
  - keep Phase 1 minimal
  - preserve the Gateway consolidation option

### 5. Security weakness when externally exposed

- Tunnel / port-forward usage is risky if authentication is weak.
- Mitigation:
  - require tokens
  - record request IDs
  - keep the design extensible to future mTLS or request signing
