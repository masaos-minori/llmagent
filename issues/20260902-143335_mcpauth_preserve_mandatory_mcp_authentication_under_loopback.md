# Preserve mandatory MCP authentication and secret handling under loopback-only deployment

## Priority
High

## Summary
Keep Bearer-token authentication mandatory for HTTP MCP services once `loopbackonly` removes
external HTTP publication, and verify that secrets cannot be omitted or exposed through logs
and diagnostics.

## Background
This issue's rationale depends on `loopbackonly` landing (or at least being the accepted
target direction) — it exists specifically to prevent authentication from being dropped as a
"no longer needed" simplification once external access is removed.

## Problem
Loopback-only binding prevents access from other hosts, but does not authenticate processes on
the same host. Another local user, compromised process, or incorrectly isolated workload may
still attempt to call an MCP endpoint.

## Reason for Change
Removing authentication because external publication is prohibited would weaken defense in
depth and introduce a new trust assumption not required by the loopback migration.
Authentication configuration is startup-sensitive and not reliably applied through hot reload,
so it must be migrated and tested together with the Production-only startup policy.

## Implementation Intent
Retain Bearer-token authentication for every HTTP MCP service; require non-empty credentials
at startup; load secrets through approved environment variables or secret files rather than
committed TOML values; ensure Agent and MCP server configurations reference matching secret
sources; reject missing/malformed authentication configuration before tool discovery; return
HTTP 401 for missing/invalid credentials; redact token values from logs, exceptions,
diagnostics, configuration previews, and audit records; document that authentication, MCP
definitions, and bind-address changes require full process restart rather than `/reload`; keep
Event Bus loopback-only until a separate authentication model is implemented (do not invent a
partial Event Bus authentication mechanism here).

## Target Files or Areas
- `scripts/shared/mcp_config.py`
- `scripts/mcp_servers/server.py`
- `scripts/agent/startup.py`
- `scripts/agent/services/mcp_tool_discovery.py`
- Agent HTTP transport and MCP invocation code
- `config/agent.toml`
- `config/*_mcp_server.toml`
- Secret-injection deployment files
- Authentication, logging, diagnostics, and startup tests

## Required Changes
- Require non-empty authentication credentials during startup; reject missing or malformed authentication configuration before tool discovery.
- Confirm secrets load through approved environment variables or secret files, not committed TOML values; confirm Agent and MCP server configurations reference matching secret sources.
- Confirm HTTP 401 is returned for missing/invalid credentials.
- Redact token values from logs, exceptions, diagnostics, configuration previews, and audit records.
- Document that authentication, MCP definitions, and bind-address changes require full process restart rather than `/reload`.
- Confirm Event Bus remains loopback-only and is not documented as authenticated.

## Constraints
- Do not store live secrets in repository-controlled configuration.
- Do not remove authentication because the service listens on loopback.
- Do not log or return token contents.
- Do not implement Event Bus authentication as a side effect of this issue.
- Do not change public API payloads unless required for a confirmed authentication defect.

## Acceptance Criteria
- An HTTP MCP server cannot start without valid configured authentication.
- The Agent cannot complete MCP discovery when credentials are missing or mismatched.
- Missing or invalid credentials return HTTP 401; authentication remains active for loopback requests.
- Tokens are absent from logs, diagnostics, exceptions, previews, and audit records.
- Secret values are supplied through approved environment or file mechanisms.
- Restart requirements are documented and tested where practical.
- Event Bus remains loopback-only and is not falsely documented as authenticated.

## Testing Expectations
Add startup tests for missing, empty, malformed, and mismatched credentials; HTTP tests for
valid/invalid Bearer tokens; log-capture tests proving secret redaction. Run MCP transport,
discovery, startup, audit, and diagnostics regression suites.

## Documentation Impact
Update the security architecture, MCP authentication reference, deployment secret
instructions, and restart/hot-reload guidance. State explicitly that loopback restriction and
MCP authentication are separate controls.

## Out of Scope
- Event Bus authentication implementation.
- Public HTTP access, TLS, or reverse-proxy deployment.
- General secret-management redesign unrelated to MCP authentication.

## Dependencies
Rationale depends on `loopbackonly`'s direction (this issue exists to ensure that migration
does not drop authentication as a side effect); can be implemented independently since current
authentication behavior should already be mandatory regardless of bind-address scope.

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Before editing, trace authentication from secret loading through Agent request construction
and MCP middleware validation. Confirm which fields are restart-only. Preserve the existing
authentication contract where it is already correct, and add only the validation, migration,
redaction, and tests required to make the behavior mandatory and verifiable.
