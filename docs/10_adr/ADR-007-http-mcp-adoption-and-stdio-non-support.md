---
title: "ADR-007: Adoption of HTTP MCP and Non-Support of stdio"
area: governance
tags:
  - mcp
  - http
  - transport
related:
  - ADR-002-config-isolation.md
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
  - ADR-004-environment-failure-handling-policy.md
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

This ADR unifies the official Transport between the Agent and MCP servers on HTTP and canonicalizes the decision not to use stdio, together with its operation and safety conditions. It distinguishes subprocess startup from the Tool Transport and defines the responsibilities for Timeout, Retry, and Health Check. It records that MCP servers bind to loopback only, are authenticated with a Bearer token, and that exposure beyond localhost is not supported. The stdio transport value is rejected at configuration load.

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
9. MCP servers bind only to a loopback address (a non-loopback host is rejected at startup) and every MCP server configuration must carry a non-empty authentication token. Every MCP server verifies the Bearer token on every endpoint, except as listed in Exceptions. Exposure beyond localhost is not supported; it would additionally require TLS, which is not implemented. (Explicit in code — `scripts/mcp_servers/server.py` `MCPServer.run_http()`, `scripts/agent/startup_validation.py`)
10. Fault isolation, operational monitoring, independent deployment take priority over the cost of HTTP Serialization and Socket communication.

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

With HTTP, MCP servers can be started, stopped, Health Checked, and monitored independently of the Agent. Fault isolation becomes possible and operational monitoring becomes easier.

### 2. Second Reason for Adoption — Security

With HTTP, each server can authenticate every caller with a Bearer token and reject requests that do not carry it. A stdio channel offers no comparable per-request authentication point.

### 3. Third Reason for Adoption — Deployment Independence

With HTTP, a server can be restarted, upgraded, or replaced without restarting the Agent, and its health can be probed by tools other than the Agent.

## Alternatives Considered

### Alternative A: Stdio Transport support

#### Description

Officially support the stdio Transport and use stdin/stdout for communication between the Agent and MCP servers.

#### Advantages

- The MCP standard protocol
- Simple implementation
- Suitable for local inter-process communication

#### Disadvantages

- No fault isolation
- Operational monitoring is difficult
- No per-request authentication point
- No independent deployment

#### Reason for Rejection

Rejected to prioritize Operability and Security, because it would rule out fault isolation and operational monitoring.

#### Reconsideration Conditions

- It is used only in the local development environment
- Fault isolation is not needed

### Alternative B: No subprocess startup mode

#### Description

Abolish the subprocess startup mode and make everything external persistent mode.

#### Advantages

- Simple structure
- Few dependencies

#### Disadvantages

- Automatic startup is no longer possible
- Manual management is required
- Failure recovery is delayed

#### Reason for Rejection

Rejected to prioritize Operability, because it would rule out automatic startup and automatic restart.

#### Reconsideration Conditions

- Manual management is acceptable
- Automatic startup is not needed

### Alternative C: No authentication for remote exposure

#### Description

Do not implement authentication; prevent external exposure with Firewall restrictions only.

#### Advantages

- Simple implementation
- Low overhead

#### Disadvantages

- Security risk
- Accessible without authentication
- Auditing is difficult

#### Reason for Rejection

Rejected to prioritize Security and prevent unauthenticated access.

#### Reconsideration Conditions

- Firewall restrictions are sufficiently robust
- Unauthenticated access is acceptable

## Consequences

### Positive Consequences

- Independent lifecycle management of MCP servers becomes possible
- Fault isolation is ensured
- Operational monitoring becomes easier
- Per-request authentication with a Bearer token becomes possible
- Independent deployment becomes possible

### Negative Consequences

- HTTP Serialization overhead
- Socket communication cost
- Authentication tokens must be provisioned for every server
- Placement on a separate host is not possible without designing TLS/mTLS (see Review Triggers)

### Operational Consequences

- A Health Check of each MCP server is evaluated at startup and its liveness state is tracked at runtime
- A configuration change requires restarting the owning process
- Incident response starts from the MCP server's Health Check result and its configuration file

### Security Consequences

- Trust boundary: privileges are granted only within each process
- Secret handling: follow the principle of minimal exposure

## Invariants

- INV-01: MCP servers expose HTTP Endpoints as independent processes.
- INV-02: The Agent performs Tool Discovery, Health Checks, and Tool Calls through a common HTTP Transport.
- INV-03: Even with subprocess startup, Tool communication after startup is over HTTP.
- INV-04: The Agent does not use stdin/stdout for MCP Tool communication.
- INV-05: There is no Fallback to the stdio Transport.
- INV-06: stdio is not a valid transport value in the configuration schema.
- INV-07: Connection Timeout, response Timeout, Retry, Semaphore, Circuit Breaker, structured errors, and logging are handled in the common Transport layer.
- INV-08: MCP servers can be started, stopped, Health Checked, and monitored independently of the Agent.
- INV-09: MCP servers bind only to a loopback address. Every enabled server entry carries a non-empty authentication token, and every MCP server rejects requests without a matching Bearer token, except as listed in Exceptions.
- INV-10: Fault isolation, operational monitoring, and independent deployment take priority over the cost of HTTP Serialization and Socket communication.
- INV-11: The names of the MCP server liveness states managed by McpServerHealthRegistry (HEALTHY/DEGRADED/UNAVAILABLE/HALF_OPEN) are not changed implicitly, because multiple callers outside the Transport layer compare them directly.

## Exceptions

- mdq-mcp attaches the authentication middleware with an empty token and does not verify Bearer tokens at the HTTP layer. Its security boundary is the fail-closed `allowed_dirs` path authorization (see `mcp_05_05_mdq-enforcement-and-lockdown.md`). The Agent-side `auth_token` for mdq must still be non-empty. Changing this exception requires a decision recorded in this ADR.

## Failure Policy

### Fail-Fast Conditions

- When a required (mandatory) MCP server Health Check fails at startup
- When an MCP server configuration has an empty authentication token (startup validation)
- When an MCP server is configured to bind to a non-loopback address (`run_http()` raises)
- When the configuration names an unsupported transport (such as stdio)

### Fail-Open or Degraded Conditions

- A non-mandatory MCP server that is unavailable is disabled and startup continues in a partial-availability state (ADR-004: an availability failure of a non-mandatory component disables it and startup continues in a partial-availability state)

### Retry Policy

- Retry target: HTTP 429/502/503/504 and transport-level request errors other than timeouts (for example, connection errors)
- Retry count: bounded
- Backoff: increasing delay between attempts for retryable HTTP statuses (`scripts/shared/http_transport.py`)
- Errors not retried: timeouts and other HTTP status codes

### Fallback Policy

Not applicable (no Fallback exists; in particular, falling back to stdio is prohibited, see INV-05)

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

- **Test**: Communication after subprocess startup happens over HTTP
  - **Verifies**: INV-03
  - **Type**: Integration
  - **Blocking**: Yes
  - **Implementation**: `tests/shared/test_mcp_config.py::TestMcpServerConfigValidation::test_stdio_transport_rejected` (the only transport value is `http`, for every startup mode)

- **Test**: Tool Call Timeouts and Transport Errors are converted into common errors
  - **Verifies**: INV-07
  - **Type**: Regression
  - **Blocking**: Yes
  - **Implementation**: `tests/shared/test_tool_transport_invoker.py::TestToolTransportInvoker::test_transport_error_returns_error_type_transport`, `tests/integration/test_mcp_transport_crash.py::test_d05_http_timeout_races_lifecycle_termination`

- **Test**: Health Checks are also usable from outside the Agent
  - **Verifies**: INV-08
  - **Type**: Integration
  - **Blocking**: Yes
  - **Implementation**: `tests/agent/test_http_lifecycle_health_check.py`

- **Test**: No path references stdio as a runtime Transport
  - **Verifies**: INV-04
  - **Type**: Regression
  - **Blocking**: Yes
  - **Implementation**: `tests/shared/test_mcp_config.py::TestMcpServerConfigValidation::test_stdio_transport_rejected`, `tests/shared/test_mcp_config.py` (`test_unsupported_transport_raises_from_toml`)

- **Test**: Circuit Breaker state transitions (reaching the DEGRADED/UNAVAILABLE thresholds, the HALF_OPEN cooldown, returning to UNAVAILABLE on a HALF_OPEN failure) behave as specified
  - **Verifies**: INV-11
  - **Type**: Unit
  - **Blocking**: Yes
  - **Implementation**: `tests/shared/test_mcp_health.py`

- **Test**: A non-loopback bind address is rejected by `run_http()`
  - **Verifies**: INV-09
  - **Type**: Unit
  - **Blocking**: Yes
  - **Implementation**: `tests/mcp_servers/test_mcp_server_base.py::TestBindAddressValidation::test_private_lan_rejected`

### Startup Validation

- MCP server Discovery and Health Check results are evaluated at startup

### Deployment Validation

- MCP server Health Check passes after deployment

### Runtime Monitoring

- Health Check: MCP server liveness state managed by `McpServerHealthRegistry` (HEALTHY/DEGRADED/UNAVAILABLE/HALF_OPEN)
- Degraded condition: a non-mandatory MCP server is unavailable (ADR-004: availability failure of a non-mandatory component)

### Manual Review

- Review of MCP server Health Check failures
- INV-01, INV-02, INV-10 have no dedicated automated test (they are structural properties of the transport and server base classes)

## Implementation Notes

- Each MCP server is an independent HTTP server process started through `MCPServer.run_http()`, which enforces loopback-only binding. Each server module attaches the Bearer-token authentication middleware through `attach_auth_middleware()`; mdq-mcp attaches it with an empty token (see Exceptions) and rag-pipeline-mcp does not attach it (MCP-005).
- `HttpTransport.call()` posts to `/v1/call_tool` with a bounded retry for 429/502/503/504 and for transport request errors other than timeouts; timeouts and other HTTP status errors surface as `TransportError`.
- `ToolTransportInvoker.invoke()` applies the per-server Semaphore and records success or failure in `McpServerHealthRegistry`.
- `TransportType` accepts only `http`; the startup mode (`none`, `persistent`, `subprocess`) selects how the process is launched, not the transport.

This chapter is not a basis for design decisions. See Implementation References for the current file/symbol list.

## Known Deviations

- **Known Issue**: MCP-005 — tracked in governance_03 Part 1 (rag-pipeline-mcp does not attach the Bearer authentication middleware; violates INV-09)

Do not unconditionally align the ADR text with the current implementation; manage discrepancies as Known Issues.

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

## Approval

### Required Reviewers

- Architecture Owner
- Affected Component Owner
- Security Reviewer: when there is a security impact
- Operations Reviewer: when operations, monitoring, or recovery are affected
- Data Owner: when data ownership, schema, or retention are affected

### Approval Record

- **Approved By**: Task-level approval decision (repository administrator; individual reviewer names are not recorded)
- **Approval Date**: Not recorded (individual approval dates are not recorded for a task-level approval decision)
- **Approval Reference**: `docs/00_governance/governance_01_documentation-policy.md` ADR Acceptance Evidence Standard
- **Decision Change (2026-10-08)**: The removal of the TLS and separate-host claims, the mdq-mcp authentication exception, and the MCP-005 deviation were approved as a task-level approval decision (repository administrator instruction); individual reviewer names are not recorded.

This ADR's `Accepted` status uses the task-level approval decision defined by the governance document above as its acceptance evidence. No formal Approval Record with individual reviewer names and approval dates has been created.

## Related ADRs

- ADR-002: Per-Process Configuration Ownership and Config Isolation
- ADR-004: Failure Handling Policy Across Environments

## Implementation References

- `scripts/mcp_servers/server.py` — `MCPServer.run_http()`
- `scripts/shared/http_transport.py` — `HttpTransport.call()`
- `scripts/shared/tool_transport_invoker.py` — `ToolTransportInvoker.invoke()`
- `scripts/shared/mcp_health.py` — `McpServerHealthRegistry.record_failure()`
- `config/*_mcp_server.toml` — MCP server configuration files, authentication tokens (environment variables or secret files)
- HTTP endpoints — `POST /v1/call_tool`, `GET /v1/tools`, `GET /health`
- Tests — `tests/mcp_servers/`, `tests/shared/test_mcp_config.py`, `tests/shared/test_mcp_health.py`

## Completion Checklist

Confirm the following before changing the ADR to Accepted.

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
- [ ] Each Invariant has a corresponding Verification (INV-01, INV-02, INV-10 have no automated test)
- [x] Automatable verification does not rely only on Manual Review
- [x] The relationship with existing ADRs is recorded
- [x] The ADR does not contradict related Specifications
- [x] Discrepancies with the current implementation are registered as Known Issues (MCP-005)
- [x] The Owner and required Reviewers are defined
- [x] Review Triggers are recorded
- [x] The ADR is registered in the ADR index and the Document Guides of related areas
