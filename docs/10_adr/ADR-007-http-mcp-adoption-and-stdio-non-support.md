---
title: "ADR-007: Adoption of HTTP MCP and Non-Support of stdio"
area: governance
tags:
  - mcp
  - http
  - transport
decision_scope:
  - mcp
related:
  - ADR-002-config-isolation.md
  - mcp_01_system_overview.md
  - mcp_02_01_endpoints-and-transport.md
  - mcp_02_02_startup-modes-and-health.md
  - mcp_03_01_dispatch-and-routing.md
  - mcp_03_03_transport-and-health.md
  - mcp_03_04_tool-call-tracing-and-lifecycle.md
  - mcp_03_05_lifecycle-and-new-server.md
  - mcp_06_02_configuration-file-inventory.md
  - mcp_06_05_long-running-http-operation-startup_modesubprocess.md
  - mcp_06_15_new-mcp-server-addition-checklist.md
  - governance_03_issue-and-uncertainty-management.md
supersedes: []
superseded_by: null
---

# ADR-007: Adoption of HTTP MCP and Non-Support of stdio

## Keywords
<placeholder>

## Status

Accepted

The available Status values are as follows.

- `Proposed`: Under proposal; before review or approval
- `Accepted`: Adopted and effective as the current design
- `Rejected`: Considered but not adopted
- `Deprecated`: No longer recommended, but partially remaining
- `Superseded`: Replaced by a successor ADR

To change the decision after acceptance, do not edit the body directly; create a new ADR and change this ADR to Superseded.

## Summary

This ADR unifies the official Transport between the Agent and MCP servers on HTTP and canonicalizes the decision not to use stdio, together with its operation and safety conditions. It distinguishes subprocess startup from the Tool Transport and defines the responsibilities for Timeout, Retry, and Health Check. It records the authentication and TLS requirements for remote exposure. Remaining references to stdio are removed or marked Deprecated.

## Context

### Problem

MCP (Model Context Protocol) normally uses the stdio Transport, but this project adopts the HTTP Transport for communication between the Agent and MCP servers. The decision not to use stdio, together with its operation and safety conditions, must be made clear. It must also be distinguished that even with subprocess startup, Tool communication after startup is done over HTTP.

### Constraints

- Execution on a single host with multiple processes is assumed
- In the deployment environment, the existence of each MCP server's configuration file must be confirmed before startup
- Security requirement: Secrets must be exposed only to the processes that need them
- Data integrity: each MCP server's configuration must be managed independently
- Operational requirement: the impact scope and restart targets of a configuration change must be determinable per owning process

### Assumptions

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
6. Where stdio remains in configuration Schemas or documents, it is removed or marked Deprecated.
7. Connection Timeout, response Timeout, Retry, Semaphore, Circuit Breaker, structured errors, and logging are handled in the common Transport layer.
8. MCP servers can be started, stopped, Health Checked, and monitored independently of the Agent.
9. Exposure beyond localhost requires authentication and TLS.
10. Record the reasons for prioritizing fault isolation, operational monitoring, independent deployment, and placement on separate hosts over the cost of HTTP Serialization and Socket communication.

### Scope

- **Target components**: `HttpTransport`, `MCPServer`, `ToolTransportInvoker`, `McpServerHealthRegistry`
- **Target processes**: the Agent process and each MCP server process
- **Target data**: MCP configuration files, authentication tokens
- **Target Environment Profile**: all environments (local/dev/production)
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

With HTTP, security controls through authentication (Bearer Token) and TLS become possible. These controls are difficult with stdio.

### 3. Third Reason for Adoption — Portability

With HTTP, placement on separate hosts becomes possible. Even if an MCP server is deployed on a separate host, it can communicate with the same protocol.

Do not use "the current code is implemented this way" as the sole reason for adoption.

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
- Authentication and TLS are difficult
- No placement on separate hosts
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
- Security controls through authentication and TLS become possible
- Placement on separate hosts becomes possible
- Independent deployment becomes possible

### Negative Consequences

- HTTP Serialization overhead
- Socket communication cost
- Authentication must be implemented
- TLS configuration is required

### Operational Consequences

- The existence of each MCP server's configuration file must be confirmed at startup
- A configuration change requires restarting the owning process
- Incident response requires investigating configuration files

If not applicable, write "Not applicable".

### Security Consequences

- Trust boundary: privileges are granted only within each process
- Authentication and authorization: permission decisions based on configuration files
- Secret handling: follow the principle of minimal exposure
- Fail-Closed: abort startup when a configuration file is missing
- Audit Log: record configuration loading events

If not applicable, write "Not applicable".

## Invariants

- INV-01: MCP servers expose HTTP Endpoints as independent processes.
- INV-02: The Agent performs Tool Discovery, Health Checks, and Tool Calls through a common HTTP Transport.
- INV-03: Even with subprocess startup, Tool communication after startup is over HTTP.
- INV-04: The Agent does not use stdin/stdout for MCP Tool communication.
- INV-05: There is no Fallback to the stdio Transport.
- INV-06: Where stdio remains in configuration Schemas or documents, it is removed or marked Deprecated.
- INV-07: Connection Timeout, response Timeout, Retry, Semaphore, Circuit Breaker, structured errors, and logging are handled in the common Transport layer.
- INV-08: MCP servers can be started, stopped, Health Checked, and monitored independently of the Agent.
- INV-09: Exposure beyond localhost requires authentication and TLS.
- INV-10: Fault isolation, operational monitoring, independent deployment, and placement on separate hosts take priority over the cost of HTTP Serialization and Socket communication.
- INV-11: The names of the MCP server liveness states managed by McpServerHealthRegistry (HEALTHY/DEGRADED/UNAVAILABLE/HALF_OPEN) are not changed implicitly, because multiple callers outside the Transport layer compare them directly.

## Exceptions

None

## Failure Policy

### Fail-Fast Conditions

- When an MCP server Health Check fails
- When authentication token validation fails
- When TLS certificate validation fails

### Fail-Open or Degraded Conditions

- In the local development environment, minor consistency mismatches are recorded as warnings

### Retry Policy

- Retry target: HTTP 429/502/503/504
- Retry count: up to 3
- Backoff: increasing delay between attempts (`scripts/shared/http_transport.py`)
- Errors not retried: timeouts, other HTTP status codes

If not applicable, write "Not applicable".

### Fallback Policy

- Fallback targets: none
- Fallback destination: none
- Conditions that prohibit Fallback: falling back to stdio
- Where Fallback reasons are recorded: audit log

If not applicable, write "Not applicable".

## Data Ownership and Persistence

- **System of Record**: MCP configuration files (TOML format)
- **Derived Data**: regenerable derived data (SHA256 checksums of configuration files)
- **Ownership**: MCP team (owner of the configuration files)
- **Persistence**: file system (`config/` directory)
- **Transaction Boundary**: per configuration-file load
- **Recovery Source**: configuration files (manual recovery)
- **Deletion Rule**: deleting a configuration file requires restarting the related processes

If not applicable, write "Not applicable".

## Verification

### Automated Tests

- **Test**: Communication after subprocess startup happens over HTTP
  - **Verifies**: INV-03
  - **Type**: Integration
  - **Blocking**: Yes

- **Test**: Tool Call Timeouts and Transport Errors are converted into common errors
  - **Verifies**: INV-07
  - **Type**: Regression
  - **Blocking**: Yes

- **Test**: Health Checks are also usable from outside the Agent
  - **Verifies**: INV-08
  - **Type**: Integration
  - **Blocking**: Yes

- **Test**: No path references stdio as a runtime Transport
  - **Verifies**: INV-04
  - **Type**: Regression
  - **Blocking**: Yes

- **Test**: Circuit Breaker state transitions (reaching the DEGRADED/UNAVAILABLE thresholds, the HALF_OPEN cooldown, returning to UNAVAILABLE on a HALF_OPEN failure) behave as specified (`tests/shared/test_mcp_health.py`)
  - **Verifies**: INV-11
  - **Type**: Unit
  - **Blocking**: Yes

### Startup Validation

- DB connectivity is confirmed at startup
- Whether configuration files are valid (parseable TOML, required fields)

### Deployment Validation

- Check the DB Schema before and after deployment
- The post-deployment consistency check passes

### Runtime Monitoring

- Health Check: DB connection state, DLQ task state, Broker queue backlog, Slow Consumer detection
- Metrics: Event publish count, ACK count, NACK count, DLQ promotion count
- Logs: Event publish events, ACK events, NACK events, DLQ events
- Alert conditions: `db_unavailable`, `dlq_task_stopped`, `broker_queue_backlog_high`, `slow_consumers_detected`
- Degraded condition: failure of a dependency

If not applicable, write "Not applicable".

### Manual Review

- Investigation of DLQ promotions
- DB Schema verification before deployment

Register any Invariant without Verification as an unverified item in an Issue.

## Implementation Notes

Briefly describe how the current implementation realizes the Decision.

This chapter is not a basis for design decisions. List detailed APIs, Classes, and Functions in the Implementation References.

Do not record line numbers; reference by File Path and Symbol name.

## Known Deviations

Record any discrepancy between this ADR and the current implementation, configuration, tests, or documents.

There are currently no deviations to record (MCP-001 and MCP-002 have both been resolved).

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

Add review conditions specific to this ADR.

- The MCP standard officially supports Transports other than stdio
- TLS/mTLS implementation becomes necessary
- Persistent storage moves to something other than files
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

This ADR's `Accepted` status uses the task-level approval decision defined by the governance document above as its acceptance evidence. No formal Approval Record with individual reviewer names and approval dates has been created.

## Related Documents

### Related ADRs

- ADR-002: Per-Process Configuration Ownership and Config Isolation

### Specifications

- [MCP System Overview](../22_mcp/mcp_01_system_overview.md) — MCP architecture overview
- [Endpoints and Transport](../22_mcp/mcp_02_01_endpoints-and-transport.md) — endpoints and Transport
- [Startup Modes and Health](../22_mcp/mcp_02_02_startup-modes-and-health.md) — startup modes and health
- [Dispatch and Routing](../22_mcp/mcp_03_01_dispatch-and-routing.md) — dispatch and routing
- [Transport and Health](../22_mcp/mcp_03_03_transport-and-health.md) — Transport and health
- [Transport Error Tracing and Lifecycle Flow](../22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md) — transport error tracing and lifecycle flow
- [Lifecycle and New Server](../22_mcp/mcp_03_05_lifecycle-and-new-server.md) — lifecycle
- [Configuration File Inventory](../22_mcp/mcp_06_02_configuration-file-inventory.md) — list of configuration files
- [Long-running HTTP Operation Startup Mode/Subprocess](../22_mcp/mcp_06_05_long-running-http-operation-startup_modesubprocess.md) — startup modes for HTTP operation
- [New MCP Server Addition Checklist](../22_mcp/mcp_06_15_new-mcp-server-addition-checklist.md) — checklist for adding an MCP server

### Operations

<!-- TODO: Document 'mcp_05_7-mcp-operations.md' was deleted -->

### Known Issues

- [Issue and Uncertainty Management](../00_governance/governance_03_issue-and-uncertainty-management.md) — MCP known issues

### Implementation References

- `scripts/mcp_servers/server.py` — `MCPServer.run_http()`
- `scripts/shared/http_transport.py` — `HttpTransport.call_tool()`
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
- [x] Each Invariant has a corresponding Verification
- [x] Automatable verification does not rely only on Manual Review
- [x] Migration, or the reason no migration is needed, is recorded
- [x] The relationship with existing ADRs is recorded
- [x] The ADR does not contradict related Specifications
- [ ] Discrepancies with the current implementation are registered as Known Issues
- [ ] The Owner and required Reviewers are defined
- [ ] Review Triggers are recorded
- [ ] The ADR is registered in the ADR index and the Document Guides of related areas
