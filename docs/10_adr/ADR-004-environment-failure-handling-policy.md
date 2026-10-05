---
title: "ADR-004: Failure Handling Policy Across Environments"
area: governance
tags:
  - system
  - failure-handling
  - environment
decision_scope:
  - system
related:
  - ADR-001-workflow-engine-mandatory.md
  - ADR-002-config-isolation.md
  - ADR-003-runtime-tool-registry-routing-authority.md
  - ADR-010-rag-fallback.md
  - adr_04_failure-handling-supporting-sections.md
  - deployment_01_deployment.md
  - agent_08_04_configuration-mcp-approval-obs.md
  - agent_10_04_operations-and-observability-validation-and-troubleshooting.md
  - governance_03_issue-and-uncertainty-management.md
---

# ADR-004: Failure Handling Policy Across Environments

## Keywords

failure handling
environment policy
startup validation
health check

## Status

Accepted

## Summary

Single common failure handling policy for every environment. Environment names do not change startup validation, auth/authz, Allowlist enforcement, approval control, Tool ownership, Routing, resource-scope validation, DB integrity, or Workflow requirements. Failures classified into "safety/integrity failures" and "availability failures"; safety/integrity failures always Fail-Fast/Fail-Closed. Mandatory component unavailability aborts startup; only availability failures of non-mandatory components permit continued startup in partial-availability state. Fallback permitted only when another Accepted ADR explicitly defines trigger, destination, eligibility, restrictions, result semantics, observability. ADR-010 RAG fallback is the only such exception.

## Context

### Problem

Environment names must not change startup validation or Fail-Fast/Fail-Closed boundaries. Treating every dependency uniformly as mandatory lets a temporary unavailability of a peripheral component block startup entirely. Safety/integrity failures must always be Fail-Fast/Fail-Closed; availability failures of components not compromising core safety/integrity may permit continued startup on explicit criteria.

### Constraints

- Execution on a single host in a single process is assumed
- In the deployment environment, the existence of the workflow definition file must be confirmed before startup
- There are no constraints from external protocols, libraries, or services
- Security requirement: every operation with side effects must be traceable
- Data integrity: approval state must persist across process boundaries
- Safety, validation, authentication, authorization, approval, Routing, and data integrity requirements must not be relaxed by choosing an environment name or changing the configuration

### Assumptions

- Target environment: single host, single Agent process
- Expected scale: limited concurrency
- Trust boundary: privileges granted only within the Agent process
- External dependencies: none (workflow definition is a local file)
- Re-evaluate if assumptions no longer hold: multi-host configuration, distributed execution, integration with an external workflow engine

## Decision

### Group 1: Common Policy Across Environments

1. Single common failure handling policy for every environment. No environment-specific policies.
2. Target environments: every environment where the system runs.
3. Environment names change none of: startup validation, auth/authz, Allowlist enforcement, approval control, Tool ownership, Routing, resource-scope validation, DB integrity, Workflow requirements, Fail-Fast/Fail-Closed conditions.
### Group 2: Failure Classification

4. Failures classified into two kinds: "safety/integrity failures" and "availability failures". Used to decide impact boundary; not used to relax safety/integrity requirements.
5. Safety/integrity failures include: duplicate Tool ownership, missing/invalid Workflow definition, DB connection failure/schema inconsistency, Config Isolation violations, invalid auth/authz/Allowlist/Safety Tier config, missing Secrets, invalid Tool argument schemas, invalid resource-scope definitions, unestablishable approval control, RuntimeToolRegistry initialization failure, undeterminable Tool ownership uniqueness, undeterminable safe Routing destination, unverifiable execution preconditions, data integrity failures.
6. Safety/integrity failures must not be converted to: partial availability, warning-only continuation, continued execution after disabling a component, Fallback, or No-op treated as success.
7. Availability failures may include: unavailability of MCP server, Embedding service, external search, external RAG service, Observability output destination, other dependency reachability failures.
8. An availability failure alone does not permit startup to continue. Continuing startup permitted only when all hold: target component explicitly classified as non-mandatory, failure localized to that component, every affected function can be safely disabled, no safety/integrity control relaxed, resulting partial-availability state observable.
### Group 3: Component Mandatoriness Classification

9. **Criteria for mandatory components**: a component is mandatory if any applies: required to start/complete core processing; establishes auth/authz/approval/Routing/auditability/Config Isolation/persistence/data integrity; absence prevents operations from being safely rejected; absence could cause incorrect success result; owns canonical state for core processing; an Accepted ADR explicitly defines it as mandatory; failure cannot be safely isolated from other mandatory components.
10. **Criteria for non-mandatory components**: a component may be non-mandatory only if all true: absence does not prevent safe core processing; absence bypasses none of auth/authz/approval/Routing/audit/Config Isolation/data integrity controls; failure can be localized to known set of functions; related functions/Tools can be reliably disabled; calls targeting the function can be rejected Fail-Closed; disabled state and impact are observable; other mandatory components remain safe and internally consistent; any Fallback explicitly defined by an Accepted ADR.
11. A component must not be treated as non-mandatory merely because startup is technically possible.
12. When a component's mandatoriness is undefined or cannot be determined: do not assume non-mandatory. Do not use undefined classification as grounds for continuing startup. Treat as unresolved design/configuration error. Where applicable, record or reference the current Known Issue.
13. **Division of classification responsibility**: this ADR defines classification criteria and failure handling contract. Approved classification of each component recorded by applicable Startup/Agent/MCP Specification. Configuration provides effective values only within range the approved Specification permits. Startup validation verifies effective classification before using it to decide whether startup continues. Configuration alone cannot weaken a mandatory component to non-mandatory without an approved architecture or Specification change.
### Group 4: Startup Fail-Fast Boundary

14. Fail-Fast at startup (startup aborted): Missing/Invalid Workflow definition; Required DB connection failure; DB Schema inconsistency; RuntimeToolRegistry initialization failure; Duplicate Tool ownership; Unavailable required MCP server; Invalid auth/authz/Allowlist/Safety Tier config; Missing Secret; Config Isolation violation; Unestablishable approval control; Environment configuration validation failure; Undeterminable component mandatoriness.
### Group 5: Runtime Fail-Closed Boundary

15. Fail-Closed at runtime (processing rejected): Unknown/Disabled/Unavailable Tool; Ambiguous Tool ownership; Invalid Tool arguments; Missing required approval; Auth/authz failure; Resource-scope validation failure; Allowlist validation failure; Unverifiable execution preconditions; Undeterminable safe execution destination; Request targeting disabled non-mandatory component.
16. Rejected operation must return failure/rejection result. Must not be converted to No-op treated as success. Routing by name inference prohibited. Must not fall back to static Registry. Unless an Accepted ADR explicitly permits, must not redirect to another Tool. Observable reason must be recorded.
### Group 6: Behavior of Mandatory Components

17. When a mandatory component unavailable: abort startup. Make failure and reason observable. Do not silently disable. Do not perform Fallback unless an Accepted ADR explicitly permits it.
### Group 7: Behavior of Non-Mandatory Components

18. When an availability failure occurs in a non-mandatory component: disable component. Permit system to continue startup in partial-availability state. Exclude component's Tools/functions from executable exposure set. Reject new calls targeting those Tools/functions. Report disabled state, failure reason, affected functions, startup-continuation reason. Expose state through currently approved Diagnostics/Observability mechanisms. Do not report system as fully available.
19. If a safety/integrity failure occurs in same component, continuing startup prohibited. Being classified as non-mandatory is not an exemption from safety/integrity failures.
### Group 8: Observability of Partial Availability

20. Disabled state, failure reason, affected functions, and startup-continuation decision observable through currently approved Diagnostics, Health Checks, logs. System in partial-availability state must not be reported as fully available.
### Group 9: Tool Visibility and Execution Boundary

21. Tools associated with a disabled component: must not be presented to LLM as executable; must not be Routable for new calls; must not be executable; must have observable disable reason.
22. ADR-003 remains authority for `RuntimeToolRegistry`, Tool ownership, Routing, static availability, Dynamic Health, LLM visibility, separation of approval state, execution eligibility, Reload/Rediscovery behavior. This ADR defines only failure-handling consequences of how these concepts relate to component mandatoriness classification; does not redefine ADR-003's decisions.
23. Drift validation using static `ToolRegistry` or `tool_names`, Routing fallback to static Registry, Routing by name inference not reintroduced.
24. Distinguish between a component unavailable because of startup classification (disabled due to non-mandatory availability failure) and one dynamically unavailable after startup due to Dynamic Health. Former relates to ADR-003's "static availability" affecting LLM visibility/Routing eligibility. Latter relates to ADR-003's "Dynamic Health", affects only runtime success/failure, does not automatically change LLM visibility. This ADR does not merge/collapse this distinction defined by ADR-003.
### Group 10: Fallback Boundary

25. Fallback prohibited by default.
26. Fallback permitted only when an Accepted ADR explicitly defines all: trigger (Failure Trigger), destination (Destination), eligibility conditions (Eligibility Conditions), restrictions (Restrictions), result semantics (Result Semantics), observability requirements (Observability Requirements).
27. ADR-010 sole authority for approved external-RAG-to-in-process-RAG fallback. ADR-010 permits Fallback only for RAG-related conditions, does not permit general Fail-Open behavior. Ordinary empty RAG result does not automatically trigger Fallback. Safety/integrity failure must not trigger availability Fallback. Fallback must not bypass auth/authz/approval/Allowlist/Routing/data integrity controls.

### Scope

- **Components**: `StartupOrchestrator`, `McpToolDiscoveryService`, `ProductionConfigValidator`, `McpServerHealthRegistry`
- **Processes**: entire Agent process
- **Data**: startup check results, MCP server state, Tool ownership info, approval state
- **Environments**: every environment where the system runs. No environment-specific differences.
- **APIs/paths**: `StartupOrchestrator.run()`, `McpToolDiscoveryService.discover_all()`, `ProductionConfigValidator.validate()`

### Out of Scope

- Failure detection details for individual MCP servers
- Failure detection details for OTel output destinations
- Startup Orchestrator's own precondition checks (Health Checks, pre-startup validation)
- Existing StartupCheckStatus (OK/WARNING/FATAL/SKIPPED) removal
- Existing pipeline.add_fatal()/add_warning() removal
- Concrete mandatory/non-mandatory assignment of individual components (defined by applicable Specification)
- New configuration keys or configuration models
- RuntimeToolRegistry, Routing, availability concepts redesign (ADR-003)
- RAG Fallback changes (ADR-010)

## Rationale

This section is maintained in the companion document: [Rationale](adr_04_failure-handling-supporting-sections.md#rationale).

## Alternatives Considered

This section is maintained in the companion document: [Alternatives Considered](adr_04_failure-handling-supporting-sections.md#alternatives-considered).

## Consequences

This section is maintained in the companion document: [Consequences](adr_04_failure-handling-supporting-sections.md#consequences).

## Invariants

- INV-01: Single common failure handling policy for every environment
- INV-02: Environment names do not relax safety/validation requirements
- INV-03: Missing/invalid Workflow → abort
- INV-04: Duplicate Tool ownership → abort
- INV-05: Required DB connection failure or Schema inconsistency → abort
- INV-06: RuntimeToolRegistry initialization failure → abort
- INV-07: Failures of authentication, authorization, Allowlist, Safety Tier, Config Isolation, or establishing approval control are all Fail-Closed (Fail-Fast) at startup
- INV-08: If a mandatory component is unavailable, startup is aborted
- INV-09: A non-mandatory component can be disabled only in the case of an availability failure
- INV-10: Safety/integrity failures not converted to partial availability
- INV-11: Tools related to a disabled component are not presented to the LLM as executable
- INV-12: Tools related to a disabled component cannot be executed
- INV-13: The partial-availability state and its reason are observable
- INV-14: If a component's mandatoriness is undefined, startup is not permitted to continue
- INV-15: Fallback is permitted only when another Accepted ADR explicitly defines it
- INV-16: ADR-010 remains the authority for the approved RAG Fallback

## Alignment with INV-01/INV-02

With REQ-001's fix (strict-default behavior), the Fail-Fast requirements of INV-01/INV-02 are now enforced at startup time:

1. **INV-01**: Missing required config files cause immediate process termination (no silent-continue).
2. **INV-02**: All processes enforce fail-closed behavior regardless of environment.
3. **No environment-based relaxation**: The strict-default applies uniformly across all environments.

## Verification

This section is maintained in the companion document: [Verification](adr_04_failure-handling-supporting-sections.md#verification).

## Implementation Notes

Briefly describe how the current implementation realizes the Decision.

For the non-persistence of startup validation results, see "6. Non-Persistence of Startup Validation Results" in `## Rationale`.

Retry policy when an MCP server is unreachable: unreachable-handling paths (`mcp_health.py`, `scripts/agent/services/mcp_tool_discovery.py::fetch_tools()`, adjacent files) contain no retry logic; the only retry implementation (`scripts/agent/http_lifecycle_health_checker.py::HealthChecker.startup_poll()`) has no callers. Owner confirmation: current no-retry behavior on these paths is the intended, settled policy.

Not a basis for design decisions. Detailed APIs, Classes, and Functions listed in Implementation References.

Do not record line numbers; reference by file path and symbol name.

## Known Deviations

### ADR-004-D1-profile-config-model-still-present: Environment-conditional required/local branching in McpServerConfig

- **Summary**: `McpServerConfig` branched on `security_profile` to choose `required_in_production` vs `required_in_local`
- **Action**: **Resolved**: removed `SecurityProfile.LOCAL`; `SecurityProfile` now holds only `PRODUCTION`. Mandatoriness decisions are environment-independent.
- **Status**: Resolved

### ADR-004-D2-production-config-validator-severity-downgrade: is_production-gated strict-mode violation downgraded to warning

- **Summary**: Strict-mode violations downgraded to warnings under `is_production` in `production_config_validator.py`
- **Action**: **Resolved**: removed the `is_production` branch; Production-grade validation applies unconditionally.
- **Status**: Resolved

### ADR-004-D3-non-required-continuation-test-coverage: Decision #18/INV-09 continuation test coverage

- **Summary**: Automated test coverage for startup continuation on non-mandatory availability failure (Decision #18, INV-09)
- **Action**: Recorded as Confirmed in this ADR's `## Verification` section; no new governance Known Issue registered
- **Status**: Resolved

### ADR-004-D4-production-tool-safety-validation-fail-open

- **Summary**: Production tool-safety validation could silently skip checks on registry failure (bare `except Exception:` returning `None` in `_resolve_known_tools()`) and accept unknown security-profile values without rejection
- **Action**: **Resolved**: REQ-001–REQ-005 removed broad exception fallback, added explicit `SecurityProfile` coercion/rejection, injected authoritative known-tools from both call sites. Safety-critical checks remain unconditional across `SecurityProfile.PRODUCTION`.
- **Status**: Resolved

### CI-016: Undefined component criticality treatment relies on a safe default, untested

- **Summary**: No automated test verifies prohibition on continuing startup with undefined mandatoriness (Decision #12, INV-14)
- **Action**: **Resolved**: REQ-001 unit test (`tests/shared/test_mcp_config.py::TestRequiredDefault`) verifies the strict default of `McpServerConfig.required`. Update the automated test if that default changes.
- **Status**: Resolved

Do not unconditionally align the ADR text with the current implementation; manage discrepancies as Known Issues.

## Review Triggers

Re-evaluate when:

- Operational scale/concurrency changes significantly
- Deployment changes from single host to multiple hosts/distributed configuration
- Security/audit requirements change
- Performance targets/resource constraints change
- External protocol/adopted library changed or discontinued
- Failure history shows assumptions no longer valid
- Reasons for rejecting an alternative no longer hold
- Component mandatoriness classification logic changed to be environment-independent
- New Accepted ADR permitting Fallback added

## Approval

### Required Reviewers

- Architect
- Component Owner
- Security Reviewer: when security impact
- Ops Reviewer: when ops/monitoring/recovery affected
- Data Owner: when data/schema/retention affected

### Approval Record

- **Approved By**: Task-level approval decision (repository administrator; individual reviewer names not recorded)
- **Approval Date**: Not recorded (individual approval dates not recorded for task-level approval decision)
- **Approval Reference**: `docs/00_governance/governance_01_documentation-policy.md` ADR Acceptance Evidence Standard

This ADR's `Accepted` status uses the task-level approval decision defined by the governance document above as its acceptance evidence. No formal Approval Record with individual reviewer names and approval dates has been created.

## Related Documents

### Companion Document

- [ADR-004 Supporting Sections](adr_04_failure-handling-supporting-sections.md)

### Related ADRs

- ADR-001: Mandatory Workflow Engine — missing/invalid Workflow → Fail-Fast
- ADR-002: Per-Process Configuration Ownership and Config Isolation — Config Isolation violation → Fail-Fast
- ADR-003: RuntimeToolRegistry as Sole Routing Authority — RuntimeToolRegistry init failure → Fail-Fast; authority for Tool visibility/Routing/Dynamic Health
- ADR-010: In-Process Fallback When External RAG Execution Fails — sole Fallback this ADR permits

### Specifications

- [Deployment Guide](../90_deployment/deployment_01_deployment.md) — workflow validation during deployment
- [MCP Config](../23_agent/agent_08_04_configuration-mcp-approval-obs.md#component-criticality-classification) — record of MCP server mandatory/non-mandatory classification (Decision Group 3)

### Operations

- [Workflow Runbook](../23_agent/agent_10_04_operations-and-observability-validation-and-troubleshooting.md#workflow-deployment-runbook) — incident response procedure

### Known Issues

- [Issue Mgmt](../00_governance/governance_03_issue-and-uncertainty-management.md) — ADR-004-related Known Issue (CI-016)

### Implementation References

- `scripts/agent/startup.py` — `StartupOrchestrator.run()`
- `scripts/shared/mcp_config.py` — `McpServerConfig`
- `scripts/shared/production_config_validator.py` — `ProductionConfigValidator.validate()`
- `scripts/agent/services/mcp_tool_discovery.py` — `McpToolDiscoveryService.discover_all()`
- `scripts/shared/mcp_health.py` — `McpServerHealthRegistry`
- `scripts/agent/services/mcp_health.py` — `check_service_health()`
- `config/agent.toml` — configuration file
- Tests — `tests/agent/shared/test_startup_validation_pipeline.py`, `tests/agent/test_startup.py`

## Completion Checklist

Confirm the following before changing the ADR to Accepted.

- [x] Problem is clear
- [x] Decision is single primary design decision
- [x] Decision uses clear terms (mandatory/prohibited/canonical/Fallback)
- [x] Adoption reasons from non-implementation perspectives
- [x] Alternatives and rejection reasons recorded
- [x] Positive consequences recorded
- [x] Negative consequences recorded
- [x] Invariants defined
- [x] Each Invariant has Verification
- [x] Automatable verification does not rely only on Manual Review
- [x] Relationship with existing ADRs recorded
- [x] ADR does not contradict related Specifications
- [x] Discrepancies registered as Known Issues
- [x] Owner and required Reviewers defined
- [x] Review Triggers recorded
- [ ] ADR registered in index and related Document Guides
