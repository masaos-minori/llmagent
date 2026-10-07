---
title: "ADR-003: RuntimeToolRegistry as the Sole Routing Authority"
area: governance
tags:
  - system
  - tool-routing
  - runtime-tool-registry
related:
  - ADR-001-workflow-engine-mandatory.md
  - ADR-002-config-isolation.md
  - mcp_03_01_dispatch-and-routing.md
  - mcp_03_02_tool-registry.md
  - mcp_03_06_tool-runtime-availability-metadata.md
  - agent_06_01_tool-execution-and-approval-execution.md
  - shared_03_03_runtime_and_execution-llm-and-mcp-clients.md
  - adr_03_runtime-tool-registry-supporting-sections.md
  - ADR-004-environment-failure-handling-policy.md
---

# ADR-003: RuntimeToolRegistry as the Sole Routing Authority

## Keywords

runtime tool registry
routing authority
drift validation
tool discovery

## Status

Accepted

## Summary

The authority that determines the target MCP server from a Tool name is consolidated into `RuntimeToolRegistry`, preventing duplicated routing through static definitions, configuration, and Discovery results. At startup, Tool definitions obtained from each MCP server are normalized and registered as `RuntimeTool`, and `ToolRouteResolver` references only `RuntimeToolRegistry`. The static `ToolRegistry`, Tool name lists in configuration, and Tool definitions in the LLM Prompt are not used for runtime Routing.

`RuntimeToolRegistry` is also the sole authority not only for Tool ownership and Routing but also for the related group of concepts: LLM visibility, static availability, Dynamic Health, approval state, and execution eligibility. These are mutually distinct concepts and are not merged into a single "enabled/disabled" flag.

## Context

### Problem

When routing from a Tool name to an MCP server happens through multiple paths, ownership conflicts and unexpected Tool routing occur. Specifically, there are the following problems.

- If both `ToolRegistry` (static definitions) and `RuntimeToolRegistry` (live Discovery) have routing authority, ownership of the same Tool name can conflict
- If the `tool_names` list in a configuration file acts as a routing input, mismatches between configuration and Discovery results cause unexpected routing
- Routing an unregistered Tool by inferring from naming conventions allows Security Controls to be bypassed
- When multiple MCP servers expose the same Tool name, it becomes unclear which one to route to, regardless of Profile
- Tool definition existence, Discovery, LLM visibility, Routing ownership, static configuration-derived availability, dynamic server health, approval state, and execution eligibility are distinct concepts; when they are implicitly merged into a single "enabled/disabled" flag, code references the wrong concept, or documentation describes processing stages as filtering when they actually do not

### Constraints

- Execution on a single host with multiple processes is assumed
- In the deployment environment, Tool definitions must be obtained from each MCP server before startup
- Security requirement: execution of unregistered Tools must be rejected
- Data integrity: Safety Tier and Write attributes must reference the same values in Routing, approval, and auditing
- Operational requirement: Discovery results are obtained once at startup and are not re-obtained until the Agent process restarts
- External dependencies: the `/v1/tools` endpoint of each MCP server

## Assumptions

- Target environment: a single host, multiple processes (one Agent process, each MCP server process)
- Expected scale: limited concurrency
- Trust boundary: privileges are granted only within each MCP server
- External dependencies: the MCP servers' `/v1/tools` endpoints
- Items to re-evaluate if the assumptions no longer hold: multi-host configuration, distributed execution, integration with an external tool-definition store, adding or removing MCP servers without restarting the Agent (Hot Reload)

## Decision

### Decision Details

1. At startup, Tool definitions obtained from each MCP server are normalized and registered as `RuntimeTool`.
2. `RuntimeTool` holds the Tool name, owning MCP server, description, Input Schema, Read/Write classification, Safety Tier, execution constraints, and LLM visibility.
3. `ToolRouteResolver` references only `RuntimeToolRegistry`.
4. The static `ToolRegistry`, Tool name lists in configuration, and Tool definitions in the LLM Prompt are not used for runtime Routing.
5. If static definitions are kept, they are limited to tests, expected values, and documentation generation.
6. Unregistered Tools are not routed by inferring from naming conventions. There is no Fallback to the static Registry.
7. When multiple MCP servers expose the same Tool name, startup fails regardless of Profile.
8. Safety Tier and Write attributes reference the same `RuntimeTool` in Routing, approval, and auditing.
9. Registry updates are limited to policy application (`RuntimeToolRegistry.apply_policy()`), which builds a complete replacement mapping and installs it in a single assignment, so lookups never observe a partially updated Registry. (Explicit in code — `scripts/shared/runtime_tool_registry.py`)
10. Defined, Discoverable, Owned, LLM-visible, Statically available, Dynamically available, Routable, Approved, and Executable are distinct concepts and are not merged, without distinction, into a single "enabled/disabled" flag.
11. Static availability (a value based on configuration, computed by each MCP server at Discovery time and taken in once at startup by `McpToolDiscoveryService`) and Dynamic Health (server reachability and Circuit Breaker state, continuously tracked during execution by `McpServerHealthRegistry`/`ToolExecutor`) are separate subsystems. Static availability controls whether a Tool is exposed to the LLM and whether it is eligible for Routing; Dynamic Health controls whether an already Routable call succeeds at runtime. A Tool that is statically enabled but dynamically Down stays visible to the LLM and Routable, and fails only at runtime.
12. Dynamic Health state must not automatically change LLM visibility (such as `enabled_for_llm`).
13. An Approval requirement is not a kind of disabled Tool state. Approval is owned by `agent/tool_policy.py`/`tool_approval.py` and is a per-call policy decision applied after Routing is resolved (risk can vary with arguments); it must not be represented as, or confused with, a disabled Tool.
14. Reflecting Discovery-derived Tool definitions (`raw_definition`, the static `status`, and so on) requires a full restart of the Agent process. Unless the currently approved specification explicitly defines Rediscovery, a Reload operation updates only Policy-derived fields such as Safety Tier and allowlist-derived LLM visibility, and does not re-obtain Discovery-derived Tool definitions. Reload behavior is described only to the extent currently supported.
15. The static `ToolRegistry` may be used only as input data for startup Drift validation (comparison of the configured `tool_names` and the runtime `/v1/tools` responses by `shared/tool_routing_validation.py`, invoked via `agent/services/routing_drift.py`). This use is not a Routing decision itself; it is a diagnostic verification that warns after the fact about the validity of the already determined `RuntimeToolRegistry`-based Routing result, and it does not change the principle that `ToolRouteResolver.resolve()` references only `RuntimeToolRegistry` (Decision Detail #3, INV-02).

### Responsibility Boundaries

- **RuntimeToolRegistry**: the current runtime authority for Tool ownership, Routing, LLM-visibility metadata, and execution-related metadata (Safety Tier, Write attributes, and so on).
- **MCP Live Discovery** (`McpToolDiscoveryService`): the current source of runtime Tool definitions. It calls each MCP server's `/v1/tools` once at startup.
- **Dynamic Health Subsystem** (`McpServerHealthRegistry`, `ToolExecutor`): the current subsystem responsible for reachability and Circuit Breaker state. It has no authority to change LLM visibility.
- **Approval Subsystem** (`agent/tool_policy.py`, `agent/tool_approval.py`): the current subsystem responsible for per-call approval and risk decisions after Tool resolution.

Being Discoverable or Owned alone does not mean the Tool is always Executable. It can fail or be rejected at runtime by Dynamic Health or an Approval decision.

### Scope

- **Target components**: `RuntimeToolRegistry`, `ToolRegistry`, `ToolRouteResolver`, `McpToolDiscoveryService`, `McpServerHealthRegistry`, `ToolExecutor`
- **Target processes**: the Agent process and each MCP server process
- **Target data**: Tool definitions, Discovery results, configuration files
- **Target Environment Profile**: production (the only supported execution mode; ADR-004 applies one failure-handling policy to every environment)
- **Target APIs or processing paths**: `RuntimeToolRegistry.resolve()`, `RuntimeToolRegistry.llm_tool_definitions()`, `RuntimeToolRegistry.apply_policy()`, `ToolRouteResolver.resolve()`, `McpToolDiscoveryService.discover_all()`

### Out of Scope

- Details of individual Tool definition schemas
- Per-MCP-server mandatoriness and failure policy (handled by a separate ADR)
- Implementation details of how each MCP server computes static availability (the responsibility of each MCP server itself; only referenced in this ADR)
- Redesign of the Approval Policy itself (owned by `tool_policy.py`/`tool_approval.py`; only referenced in this ADR)
- Changes to runtime behavior
- Adoption of Rediscovery through Hot Reload (Policy B) (an option that a future ADR may address; this ADR defines only the current policy, Discovery updates through a full restart)
- Monitoring and metrics design (handled by a separate ADR)

## Rationale

### 1. Primary Reason for Adoption — Security

To reject execution of unregistered Tools Fail-Closed. If both static definitions and Discovery results are referenced, a Tool that exists only in a configuration file can be routed to an unexpected MCP server. If RuntimeToolRegistry is the only authority, a Tool whose Discovery failed is not executed.

### 2. Second Reason for Adoption — Data Integrity

Because Safety Tier and Write attributes reference the same values in Routing, approval, and auditing, the approval decision matches the actual privileged operation. If different paths reference different values, a contradiction arises in which an approved Tool actually has Write privileges.

### 3. Third Reason for Adoption — Operability

Because the Routing authority is limited to one, it is always clear which path's value was actually applied. If both static definitions and Discovery results are referenced, it becomes unclear which path's value was actually applied.

### 4. Fourth Reason for Adoption — Correctness / Maintainability

A single "enabled/disabled" concept that actually carries several different meanings causes code to reference the wrong concept and leads to documentation describing processing stages as filtering when they actually do not. Explicitly distinguishing "static availability vs. Dynamic Health" and "Approval vs. disabled state" prevents the cheap and likely mistake of writing a Dynamic Health-driven feature into the same field as LLM visibility.

## Alternatives Considered

This section is maintained in the companion document: [Alternatives Considered](adr_03_runtime-tool-registry-supporting-sections.md#alternatives-considered).

## Consequences

### Positive Consequences

- The Routing authority becomes clear and ownership conflicts are prevented
- Execution of unregistered Tools is rejected Fail-Closed
- Safety Tier and Write attributes are consistent across Routing, approval, and auditing
- Duplicate Tool names across multiple MCP servers are detected at startup
- The shared vocabulary (Defined/Discoverable/Owned/LLM-visible/Statically available/Dynamically available/Routable/Approved/Executable) makes misuse easier to prevent in future MCP server implementations and Agent-side Routing implementations
- Making the Reload/restart boundary explicit prevents the mistaken operational judgment that a Config change has already been reflected in the Live Registry

### Negative Consequences

- Tools of an MCP server whose Discovery fails are not executed (Fail-Closed)
- Adding a new Tool requires updating the Discovery results
- Cost of building RuntimeToolRegistry
- Modifying existing code that depends on static definitions

### Operational Consequences

- Routing is determined at startup based on Discovery results
- Adding or removing Tools at runtime is prohibited
- A configuration change that affects Discovery-derived state requires a full restart of the Agent process and is not reflected by Reload
- Impact on Health Checks: startup is aborted when Discovery fails for a required MCP server; when a non-mandatory MCP server is unavailable, its Tools are disabled and startup continues (ADR-004 Decision Group 7, item 18)
- Incident response: a restart is required when Discovery fails

### Security Consequences

- Trust boundary: only Discovery results are the Routing authority
- Authentication and authorization: RuntimeToolRegistry centrally manages Safety Tier
- Secret handling: not applicable (this ADR handles no Secrets)
- Fail-Open, Fail-Closed: unregistered Tools are Fail-Closed
- Because static availability continues to gate LLM visibility, Config-driven Security Controls (for example, `read_only=true`) are prevented from being weakened by Dynamic Health signals
- Audit Log: Routing, approval, and auditing reference the same Safety Tier

## Invariants

- INV-01: When multiple MCP servers expose the same Tool name, Agent startup is aborted.
- INV-02: `ToolRouteResolver.resolve()` references only `RuntimeToolRegistry` and immediately raises `ValueError` for an unknown Tool name.
- INV-03: Safety Tier and Write attributes reference the same `RuntimeTool` in Routing, approval, and auditing.
- INV-04: The static `ToolRegistry` is not used for runtime Routing and is limited to input data for tests, documentation generation, and startup Drift validation (`shared/tool_routing_validation.py`) (Decision Detail #15).
- INV-05: Defined, Discoverable, Owned, LLM-visible, Statically available, Dynamically available, Routable, Approved, and Executable are treated as distinct concepts and are not merged into a single "enabled/disabled".
- INV-06: A statically disabled Tool must not be exposed to the LLM as executable.
- INV-07: Dynamic Health state must not change LLM visibility such as `enabled_for_llm`.
- INV-08: The approval-required state must not be represented as a disabled Tool state.
- INV-09: Being Discoverable, Owned, Statically Available, or Routable does not mean the Tool is always Executable. It can be rejected at runtime by Dynamic Health or Approval.

## Failure Policy

### Fail-Fast Conditions

- Multiple MCP servers expose the same Tool name
- Initialization of `RuntimeToolRegistry` fails
- An unregistered Tool is requested for Routing

### Fail-Open or Degraded Conditions

Not applicable

### Retry Policy

Dynamic Health uses the Circuit Breaker's CLOSED/OPEN/HALF_OPEN Trial-Recovery Semantics in the execution layer. This ADR does not change that behavior.

### Fallback Policy

There is no Fallback to the static `ToolRegistry` and no Routing by name inference (Decision Details #4 and #6).

## Data Ownership and Persistence

- **System of Record**: `RuntimeToolRegistry` (Discovery results obtained from `McpToolDiscoveryService` at startup)
- **Derived Data**: `ToolRegistry` (for tests and documentation generation)
- **Ownership**: `RuntimeToolRegistry`
- **Persistence**: in memory (per process, rebuilt on restart)
- **Transaction Boundary**: at startup
- **Recovery Source**: Discovery after a restart
- **Deletion Rule**: Not applicable

## Verification

This section is maintained in the companion document: [Verification](adr_03_runtime-tool-registry-supporting-sections.md#verification).

## Implementation Notes

- `McpToolDiscoveryService` is invoked during startup validation, and the resulting `RuntimeToolRegistry` is connected to `ToolExecutor` through `set_runtime_registry()` (Explicit in code — `scripts/agent/startup_validation.py`, `scripts/agent/services/mcp_tool_discovery.py`).
- `ToolRouteResolver.resolve()` consults only `RuntimeToolRegistry` (Explicit in code — `scripts/shared/route_resolver.py`).

See Implementation References for the file/symbol list.

## Known Deviations

No confirmed deviations.

## Review Triggers

- The operational scale or concurrency changes significantly
- The deployment changes from a single host to multiple hosts or a distributed configuration
- Security or audit requirements change
- Performance targets or resource constraints change
- An external protocol or adopted library is changed or discontinued
- Failure history shows that the assumptions or the Failure Policy are no longer valid
- The reasons for rejecting an alternative no longer hold
- Changes to per-MCP-server mandatoriness and failure policy (linked with ADR-004)
- Changes to RuntimeTool field definitions
- Adding or removing MCP servers without restarting the Agent (Hot Reload/Rediscovery, Policy B) becomes a requirement
- The design changes so that availability is computed centrally instead of individually by each MCP server

## Approval

### Required Reviewers

- Architecture Owner
- Affected Component Owner
- Security Reviewer: when there is a security impact
- Operations Reviewer: when operations, monitoring, or recovery are affected
- Data Owner: when data ownership, schema, or retention are affected

### Approval Record

Initial approval (Decision Details #1 to #9):

- **Approved By**: architecture-reviewer
- **Approval Date**: 2026-08-20
- **Approval Reference**: ADR-003 creation

Task-level approval decision (Decision Details #10 to #15 and INV-04, which were added after the initial approval: the integration of the former ADR-013 content and the static `ToolRegistry` drift-validation rule):

- **Approved By**: repository owner
- **Approval Date**: 2026-10-07
- **Approval Reference**: documentation task reviewing the approval scope of ADR-003; the repository owner approved the current content, including Decision Details #10 to #15

## Related ADRs

- ADR-001: Mandatory Workflow Engine
- ADR-002: Config Isolation
- ADR-004: Failure Handling Policy Across Environments

## Implementation References

- `scripts/shared/runtime_tool_registry.py::RuntimeToolRegistry`
- `scripts/shared/route_resolver.py` — `ToolRouteResolver`
- `scripts/shared/tool_registry.py::ToolRegistry`
- `scripts/shared/runtime_tool.py::RuntimeTool`
- `scripts/agent/services/mcp_tool_discovery.py` — `McpToolDiscoveryService`
- `scripts/agent/startup_validation.py` — Discovery invocation and `set_runtime_registry()` wiring
- `scripts/shared/mcp_health.py::McpServerHealthRegistry`
- `scripts/shared/tool_executor.py::ToolExecutor`
- `[mcp_servers.*]` in `config/agent.toml`
- The frozensets in `tool_constants.py` (for tests and documentation generation)
- Tests — `tests/shared/test_runtime_tool_registry.py`, `tests/shared/test_route_resolver.py`

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
- [x] The relationship with existing ADRs is recorded
- [x] The ADR does not contradict related Specifications
- [x] Discrepancies with the current implementation are registered as Known Issues
- [x] The Owner and required Reviewers are defined
- [x] Review Triggers are recorded
- [x] The ADR is registered in the ADR index and the Document Guides of related areas
