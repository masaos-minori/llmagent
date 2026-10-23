---
title: "ADR-007: Adoption of HTTP MCP and Non-Support of stdio"
area: governance
tags:
  - mcp
  - http
  - transport
related:
  - adr_02_01_002_platform-config-isolation.md
  - mcp_01_system_overview.md
  - mcp_02_01_endpoints-and-transport.md
  - mcp_02_02_startup-modes-and-health.md
  - mcp_03_01_dispatch-and-routing.md
  - mcp_03_03_transport-and-health.md
  - mcp_03_04_tool-call-tracing-and-lifecycle.md
  - mcp_03_05_lifecycle-and-new-server.md
  - mcp_06_01_configuration-file-inventory.md
  - mcp_06_03_long-running-http-operation-startup_modesubprocess.md
  - mcp_06_12_new-mcp-server-addition-checklist.md
  - governance_03_issue-and-uncertainty-management.md
  - adr_02_01_004_platform-environment-failure-handling-policy.md
  - governance_01_documentation-policy.md
  - mcp_05_05_mdq-enforcement-and-lockdown.md
---

# ADR-007: Adoption of HTTP MCP and Non-Support of stdio

## Keywords

- mcp
- http transport
- stdio
- health check

## Status

Accepted

## Summary

This ADR makes HTTP the only Transport between the Agent and MCP servers and rejects stdio, with loopback-only binding and Bearer authentication on every MCP server, including mdq-mcp, whose `allowed_dirs` path authorization is a separate boundary applied after authentication. It distinguishes subprocess startup from the Tool Transport and assigns Timeout, Retry, and Health Check responsibilities. See Decision, Exceptions, and Failure Policy for the normative text.

## Context

### Problem

MCP (Model Context Protocol) normally uses the stdio Transport, but this project adopts the HTTP Transport for communication between the Agent and MCP servers. The decision not to use stdio, together with its operation and safety conditions, must be made clear. It must also be distinguished that even with subprocess startup, Tool communication after startup is done over HTTP.

### Constraints

- Execution on a single host with multiple processes is assumed
- Each MCP server runs as its own process with its own configuration file (ADR-002)
- Security requirement: MCP servers accept only authenticated requests and bind only to a loopback address
- Operational requirement: MCP servers must be startable, stoppable, and health-checkable independently of the Agent
- The MCP servers' startup mode (external persistent or Agent-launched subprocess) must not change the Tool transport

## Assumptions

- Target environment: a single host, multiple processes
- Expected scale: limited concurrency
- Trust boundary: privileges are granted only within each process
- External dependencies: none (configuration files are local files)
- Items to re-evaluate if the assumptions no longer hold: multi-host configuration, distributed execution, integration with an external configuration store

## Decision

### Decision Details

1. The Decision is that MCP servers expose HTTP Endpoints as independent processes.
2. The Agent performs Tool Discovery, Health Checks, and Tool Calls through a common HTTP Transport.
3. Even with subprocess startup, Tool communication after startup is over HTTP.
4. The Agent does not use stdin/stdout for MCP Tool communication.
5. There is no Fallback to the stdio Transport.
6. stdio is not a valid transport value: the configuration schema accepts only `http`. (Explicit in code — `scripts/shared/mcp_config.py` `TransportType`)
7. Connection Timeout, response Timeout, Retry, Semaphore, Circuit Breaker, structured errors, and logging are handled in the common Transport layer.
8. MCP servers can be started, stopped, Health Checked, and monitored independently of the Agent.
9. MCP servers bind only to a loopback address (a non-loopback host is rejected at startup) and every MCP server configuration must carry a non-empty authentication token. Every MCP server, including mdq-mcp, rejects a request without a matching Bearer token on every endpoint. mdq-mcp's `allowed_dirs` is a separate, fail-closed resource-authorization boundary applied only after successful authentication; it neither replaces authentication nor is replaced by it. Exposure beyond localhost is not supported; it would additionally require TLS, which is not implemented. (Explicit in code — `scripts/mcp_servers/server.py` `MCPServer.run_http()`, `scripts/agent/startup_validation.py`, `scripts/mcp_servers/mdq/mdq_server.py`)
10. The Agent and each MCP server read their own token from their own configuration file (the Agent from `agent.toml`, mdq-mcp from `mdq_mcp_server.toml`); the two values must match, but neither process reads the other's file (ADR-002).
11. Fault isolation, operational monitoring, independent deployment take priority over the cost of HTTP Serialization and Socket communication.
12. Each MCP server validates its own security configuration and publishes the result as a security posture on `GET /health`; the Agent validates only that posture's contract version and shape, never the server's configuration file (item 10). A posture `FAILED` result aborts startup.

### Scope

- **Target components**: `HttpTransport`, `MCPServer`, `ToolTransportInvoker`, `McpServerHealthRegistry`
- **Target processes**: the Agent process and each MCP server process
- **Target data**: MCP configuration files, authentication tokens
- **Target Environment Profile**: production (the only supported execution mode; ADR-004 applies one failure-handling policy to every environment)
- **Target APIs or processing paths**: `POST /v1/call_tool`, `GET /v1/tools`, `GET /health`

### Out of Scope

- Detailed implementation of security authentication (handled by a separate ADR)
- Detailed configuration of metrics collection
- Detailed logging format
- Performance benchmark thresholds

## Rationale

### 1. Primary Reason for Adoption — Operability

With HTTP, MCP servers can be started, stopped, Health Checked, and monitored independently of the Agent (Decision 8), which enables fault isolation and easier operational monitoring.

### 2. Second Reason for Adoption — Security

With HTTP, each server can authenticate every caller with a Bearer token and reject requests that do not carry it. A stdio channel offers no comparable per-request authentication point.

Bearer authentication decides whether a caller may use the MCP API; `allowed_dirs` decides whether an authenticated caller may operate on a given path. Keeping both avoids a token that is configured but never verified, keeps one authentication contract for every HTTP MCP server, blocks unauthenticated access inside the allowed directories, gives defense in depth against a path-authorization defect, and avoids an exception that would become dangerous in a multi-process or multi-user deployment.

### 3. Third Reason for Adoption — Deployment Independence

With HTTP, a server can be restarted, upgraded, or replaced without restarting the Agent, and its health can be probed by tools other than the Agent.

## Alternatives Considered

### Alternative A: Stdio Transport support

Officially support the stdio Transport (stdin/stdout between the Agent and MCP servers).

- **Advantages:** the MCP standard protocol; simple implementation; suitable for local inter-process communication
- **Disadvantages:** no fault isolation; operational monitoring is difficult; no per-request authentication point; no independent deployment
- **Reason for Rejection:** Rejected to prioritize Operability and Security, because it would rule out fault isolation and operational monitoring.
- **Reconsideration Conditions:** it is used only in the local development environment; fault isolation is not needed

### Alternative B: No subprocess startup mode

Abolish the subprocess startup mode and make everything external persistent mode.

- **Advantages:** simple structure; few dependencies
- **Disadvantages:** automatic startup is no longer possible; manual management is required; failure recovery is delayed
- **Reason for Rejection:** Rejected to prioritize Operability, because it would rule out automatic startup and automatic restart.
- **Reconsideration Conditions:** manual management is acceptable; automatic startup is not needed

### Alternative C: No authentication for remote exposure

Do not implement authentication; prevent external exposure with Firewall restrictions only.

- **Advantages:** simple implementation; low overhead
- **Disadvantages:** security risk; accessible without authentication; auditing is difficult
- **Reason for Rejection:** Rejected to prioritize Security and prevent unauthenticated access.
- **Reconsideration Conditions:** Firewall restrictions are sufficiently robust; unauthenticated access is acceptable

### Alternative D: Keep an authentication exception for mdq-mcp

- **Advantages:** No server-side token provisioning for mdq-mcp
- **Disadvantages:** `allowed_dirs` is resource authorization, not caller authentication; the Agent-side token would be a requirement with no effect; unauthenticated local processes could call mdq-mcp
- **Reason for Rejection:** Rejected to keep one Bearer authentication contract for every HTTP MCP server.
- **Reconsideration Conditions:** Not applicable

### Alternative E: OAuth 2.1 or mTLS

- **Advantages:** Suited to external clients, other hosts, and several resource owners
- **Disadvantages:** Large change to the loopback HTTP and shared-secret model; not needed for a single-host, single-user deployment
- **Reason for Rejection:** Not adopted for the current single-host scope.
- **Reconsideration Conditions:** External clients, other hosts, or several resource owners are introduced

### Alternative F: Unix domain socket or OS peer credential

- **Advantages:** Authenticates the caller without a shared secret
- **Disadvantages:** Conflicts with the unified HTTP loopback transport; large impact on the operating platform
- **Reason for Rejection:** Not adopted for the current scope.
- **Reconsideration Conditions:** The HTTP loopback transport policy changes

## Consequences

### Positive Consequences

- Independent lifecycle management of MCP servers becomes possible
- Fault isolation is ensured
- Operational monitoring becomes easier
- Per-request authentication with a Bearer token becomes possible, with one contract for every HTTP MCP server
- The Agent-side mdq token is an effective credential, and authentication and path authorization form two defense layers
- Independent deployment becomes possible

### Negative Consequences

- HTTP Serialization overhead
- Socket communication cost
- Authentication tokens must be provisioned for every server, including mdq-mcp, and a token change needs the Agent and the server to be updated and restarted together
- A token mismatch fails startup or connection, and authentication regression tests and an operating procedure are required
- Placement on a separate host is not possible without designing TLS/mTLS (see Review Triggers)

### Operational Consequences

- A Health Check of each MCP server is evaluated at startup and its liveness state is tracked at runtime
- A configuration change requires restarting the owning process
- Incident response starts from the MCP server's Health Check result and its configuration file

### Security Consequences

- Trust boundary: privileges are granted only within each process
- Secret handling: follow the principle of minimal exposure
- The Agent holds no copy of server security settings; posture is published on the authenticated `/health` response

## Invariants

- INV-01: MCP servers expose HTTP Endpoints as independent processes.
- INV-02: The Agent performs Tool Discovery, Health Checks, and Tool Calls through a common HTTP Transport.
- INV-03: Even with subprocess startup, Tool communication after startup is over HTTP.
- INV-04: The Agent does not use stdin/stdout for MCP Tool communication.
- INV-05: There is no Fallback to the stdio Transport.
- INV-06: stdio is not a valid transport value in the configuration schema.
- INV-07: Connection Timeout, response Timeout, Retry, Semaphore, Circuit Breaker, structured errors, and logging are handled in the common Transport layer.
- INV-08: MCP servers can be started, stopped, Health Checked, and monitored independently of the Agent.
- INV-09: MCP servers bind only to a loopback address. Every enabled server entry carries a non-empty authentication token, and every MCP server, including mdq-mcp, rejects requests without a matching Bearer token.
- INV-10: Fault isolation, operational monitoring, and independent deployment take priority over the cost of HTTP Serialization and Socket communication.
- INV-11: The names of the MCP server liveness states managed by McpServerHealthRegistry (HEALTHY/DEGRADED/UNAVAILABLE/HALF_OPEN) are not changed implicitly, because multiple callers outside the Transport layer compare them directly.
- INV-12: mdq-mcp applies fail-closed `allowed_dirs` authorization only after successful Bearer authentication; authentication does not replace path authorization, and path authorization does not replace authentication.

## Exceptions

Not applicable

## Failure Policy

### Fail-Fast Conditions

- When a required (mandatory) MCP server Health Check fails at startup
- When an MCP server configuration has an empty authentication token (Agent startup validation)
- When an MCP server process, including mdq-mcp, starts with an empty or unset authentication token (the server refuses to start)
- When an MCP server request has a missing, malformed, or non-matching `Authorization` header (HTTP 401); this is a Safety/Integrity failure, not an availability failure
- When mdq-mcp's `allowed_dirs` is empty or a requested path is not inside it, or cannot be canonicalized (the request is denied, fail-closed, after authentication)
- When an MCP server is configured to bind to a non-loopback address (`run_http()` raises)
- When the configuration names an unsupported transport (such as stdio)
- When an MCP server reports a posture check as `FAILED` on `GET /health` (Safety/Integrity, not an availability failure)

### Fail-Open or Degraded Conditions

- A non-mandatory MCP server that is unavailable is disabled and startup continues in a partial-availability state (ADR-004: an availability failure of a non-mandatory component disables it and startup continues in a partial-availability state). A posture `FAILED` result is not an availability failure.

### Retry Policy

- Retry target: HTTP 429/502/503/504 and transport-level request errors other than timeouts (for example, connection errors)
- Retry count: bounded
- Backoff: increasing delay between attempts for retryable HTTP statuses (`scripts/shared/http_transport.py`)
- Errors not retried: timeouts and other HTTP status codes

### Fallback Policy

Not applicable (no Fallback exists; in particular, falling back to stdio is prohibited, see INV-05). An authentication or authorization failure never triggers a fallback to another transport, an in-process path, or an unauthenticated retry.

## Data Ownership and Persistence

- **System of Record**: MCP configuration files (TOML format)
- **Derived Data**: none
- **Ownership**: the owning MCP server process (owner of its configuration file, see ADR-002)
- **Persistence**: file system (`config/` directory)
- **Transaction Boundary**: per configuration-file load
- **Recovery Source**: configuration files (manual recovery)
- **Deletion Rule**: deleting a configuration file requires restarting the related processes

## Verification

### Automated Tests

| Test | Verifies | Type | Blocking | Implementation |
|---|---|---|---|---|
| Communication after subprocess startup happens over HTTP | INV-03 | Integration | Yes | `tests/shared/test_mcp_config.py::TestMcpServerConfigValidation::test_stdio_transport_rejected` (the only transport value is `http`, for every startup mode) |
| Tool Call Timeouts and Transport Errors are converted into common errors | INV-07 | Regression | Yes | `tests/shared/test_tool_transport_invoker.py::TestToolTransportInvoker::test_transport_error_returns_error_type_transport`, `tests/integration/test_mcp_transport_crash.py::test_d05_http_timeout_races_lifecycle_termination` |
| Health Checks are also usable from outside the Agent | INV-08 | Integration | Yes | `tests/agent/test_http_lifecycle_health_check.py` |
| No path references stdio as a runtime Transport | INV-04 | Regression | Yes | `tests/shared/test_mcp_config.py::TestMcpServerConfigValidation::test_stdio_transport_rejected`, `tests/shared/test_mcp_config.py` (`test_unsupported_transport_raises_from_toml`) |
| Circuit Breaker state transitions (reaching the DEGRADED/UNAVAILABLE thresholds, the HALF_OPEN cooldown, returning to UNAVAILABLE on a HALF_OPEN failure) behave as specified | INV-11 | Unit | Yes | `tests/shared/test_mcp_health.py` |
| mdq-mcp rejects a missing, malformed, or non-matching Bearer token (401) on `/v1/tools`, `/v1/call_tool`, and `/health`, and refuses to start with an empty or unset token | INV-09 | Unit | Yes | `tests/mcp_servers/mdq/test_mdq_authentication.py::TestAuthentication`, `tests/mcp_servers/mdq/test_mdq_authentication.py::TestStartupRequiresToken` |
| mdq-mcp rejects an unauthenticated request before any path decision is disclosed, and denies an authenticated request for a path outside `allowed_dirs` (including `..` traversal and symlink escape) | INV-12 | Unit | Yes | `tests/mcp_servers/mdq/test_mdq_authentication.py::TestAuthenticationBeforeAuthorization`, `tests/mcp_servers/mdq/test_mdq_path_jail.py` |
| Agent startup is fatal when any MCP server lacks an authentication token | INV-09 | Unit | Yes | `tests/agent/test_startup_severity_classification.py::TestCheckServicesSeverityClassification::test_mcp_auth_fatal_when_any_server_missing_token` |
| A non-loopback bind address is rejected by `run_http()` | INV-09 (loopback bind) | Unit | Yes | `tests/mcp_servers/test_mcp_server_base.py::TestBindAddressValidation::test_private_lan_rejected` |
| Each of the shell, github, and file-read/write/delete servers rejects a request without a matching Bearer token (401) and refuses to start with an empty token | INV-09 | Unit | Yes | `tests/mcp_servers/shell/test_shell_server_auth.py`, `tests/mcp_servers/github/test_github_server_auth.py`, `tests/mcp_servers/file/test_file_server_auth.py` |

### Startup Validation

- MCP server Discovery and Health Check results are evaluated at startup
- Posture results are read from `GET /health` before Tool definitions are registered

### Deployment Validation

- MCP server Health Check passes after deployment

### Runtime Monitoring

- Health Check: MCP server liveness state managed by `McpServerHealthRegistry` (HEALTHY/DEGRADED/UNAVAILABLE/HALF_OPEN)
- Degraded condition: a non-mandatory MCP server is unavailable (ADR-004: availability failure of a non-mandatory component)

### Manual Review

- Review of MCP server Health Check failures
- INV-01, INV-02, INV-10 have no dedicated automated test (they are structural properties of the transport and server base classes)

## Implementation Notes

- Each MCP server is an independent HTTP server process started through `MCPServer.run_http()`, which enforces loopback-only binding. Every server module attaches the Bearer-token authentication middleware through `attach_auth_middleware()` with its own `auth_token`: rag-pipeline-mcp uses `MCP_RAG_PIPELINE_AUTH_TOKEN` and mdq-mcp uses `MCP_MDQ_AUTH_TOKEN`, each read from its server config and refused when empty. The mdq-mcp middleware protects `/health`, `/v1/tools`, and `/v1/call_tool`; a tool call for a path denied by `allowed_dirs` is returned as a tool-level error result (HTTP 200 with `is_error`), per the MCP tool-error contract.
- `HttpTransport.call()` posts to `/v1/call_tool` with a bounded retry for 429/502/503/504 and for transport request errors other than timeouts; timeouts and other HTTP status errors surface as `TransportError`.
- `ToolTransportInvoker.invoke()` applies the per-server Semaphore and records success or failure in `McpServerHealthRegistry`.
- The security posture travels on the existing authenticated `/health` response.

See Implementation References for the current file/symbol list.

## Known Deviations

Not applicable

## Review Triggers

Re-evaluate this ADR when any of the following conditions occurs.

- The operational scale or concurrency changes significantly
- The deployment changes from a single host to multiple hosts or a distributed configuration
- Security or audit requirements change
- Performance targets or resource constraints change
- An external protocol or adopted library is changed or discontinued
- Failure history shows that the assumptions or the Failure Policy are no longer valid
- The reasons for rejecting an alternative no longer hold
- The MCP standard officially supports Transports other than stdio
- Exposure of an MCP server beyond localhost becomes necessary (authentication and TLS/mTLS would then have to be designed)
- Fault isolation is no longer needed
- Multiple Agents or OS users share an MCP server, or a tool that writes or deletes is added to mdq-mcp
- OAuth 2.1, mTLS, or a Unix socket is considered as an authentication method, or token rotation without downtime is required
- The Security Posture contract changes the posture payload that `/health` carries

## Approval

### Required Reviewers

- Architecture Owner
- Affected Component Owner
- Security Reviewer: when there is a security impact
- Operations Reviewer: when operations, monitoring, or recovery are affected
- Data Owner: when data ownership, schema, or retention are affected

### Approval Record

- **Approved By**: Task-level approval decision (repository owner; individual reviewer names are not recorded)
- **Approval Date**: Not recorded (individual approval dates are not recorded for a task-level approval decision)
- **Approval Reference**: `docs/00_governance/governance_01_documentation-policy.md` ADR Acceptance Evidence Standard
- **Current Decision Approval**: Task-level approval decision (repository owner instruction) covers the current decision text as of 2026-10-15; individual reviewer names are not recorded.

This ADR's `Accepted` status uses the task-level approval decision defined by the governance document above as its acceptance evidence. No formal Approval Record with individual reviewer names and approval dates has been created.

## Related ADRs

- ADR-002: Per-Process Configuration Ownership and Config Isolation
- ADR-004: Failure Handling Policy Across Environments

## Implementation References

- `scripts/mcp_servers/server.py` — `MCPServer.run_http()`, `attach_auth_middleware()`
- `scripts/mcp_servers/mdq/mdq_server.py` — mdq-mcp authentication setup
- `scripts/mcp_servers/mdq/auth.py` — `authorize_path()`
- `scripts/shared/http_transport.py` — `HttpTransport.call()`
- `scripts/shared/tool_transport_invoker.py` — `ToolTransportInvoker.invoke()`
- `scripts/shared/mcp_health.py` — `McpServerHealthRegistry.record_failure()`
- `config/*_mcp_server.toml` — MCP server configuration files, authentication tokens (environment variables or secret files)
- HTTP endpoints — `POST /v1/call_tool`, `GET /v1/tools`, `GET /health`
- Tests — `tests/mcp_servers/`, `tests/shared/test_mcp_config.py`, `tests/shared/test_mcp_health.py`

## Completion Checklist

Acceptance conditions and their current state.

- [x] The problem to solve is clear
- [x] The Decision is narrowed to one primary design decision
- [x] The Decision is stated in clear terms such as mandatory, prohibited, canonical, or Fallback conditions
- [x] The reasons for adoption are explained from perspectives other than the current implementation
- [x] Substantive alternatives and the reasons for rejecting them are recorded
- [x] Positive Consequences are recorded
- [x] Negative Consequences are recorded
- [x] The impact on Security has been evaluated
- [x] The impact on Operations, Monitoring, and Recovery has been evaluated
- [x] Verifiable Invariants are defined
- [x] Exceptions or out-of-scope cases are clear
- [x] Each Invariant has a corresponding Verification (gaps: Verification > Manual Review)
- [x] Automatable verification does not rely only on Manual Review
- [x] The relationship with existing ADRs is recorded
- [x] The ADR does not contradict related Specifications
- [x] Discrepancies with the current implementation are registered as Known Issues (no confirmed deviations)
- [x] The Owner and required Reviewers are defined
- [x] Review Triggers are recorded
- [x] The ADR is registered in the ADR index and the Document Guides of related areas
