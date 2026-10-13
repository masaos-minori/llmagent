---
title: "ADR-004: Failure Handling Policy Across Environments"
area: governance
tags:
  - system
  - failure-handling
  - environment
related:
  - adr_02_001_workflow-engine-mandatory.md
  - adr_02_002_config-isolation.md
  - adr_02_003_runtime-tool-registry-routing-authority.md
  - adr_02_010_rag-fallback.md
  - deployment_01_deployment.md
  - agent_08_04_configuration-mcp-approval-obs.md
  - agent_10_04_operations-and-observability-validation-and-troubleshooting.md
  - governance_03_issue-and-uncertainty-management.md
  - adr_01_index.md
  - governance_01_documentation-policy.md
---

# ADR-004: Failure Handling Policy Across Environments

## Keywords

- failure handling
- environment policy
- startup validation
- health check

## Status

Accepted

## Summary

Single common failure handling policy for every environment. Environment names do not change startup validation, auth/authz, Allowlist enforcement, approval control, Tool ownership, Routing, resource-scope validation, DB integrity, or Workflow requirements. Failures classified into "safety/integrity failures" and "availability failures"; safety/integrity failures always Fail-Fast/Fail-Closed. Mandatory component unavailability aborts startup; only availability failures of non-mandatory components permit continued startup in partial-availability state. Fallback permitted only when another Accepted ADR explicitly defines trigger, destination, eligibility, restrictions, result semantics, observability. ADR-010 RAG fallback is the only such exception.

## Context

### Problem

Environment names must not change startup validation or Fail-Fast/Fail-Closed boundaries. Treating every dependency uniformly as mandatory lets a temporary unavailability of a peripheral component block startup entirely. Safety/integrity failures must always be Fail-Fast/Fail-Closed; availability failures of components not compromising core safety/integrity may permit continued startup on explicit criteria.

### Constraints

- Execution on a single host with one Agent process and multiple MCP server processes is assumed
- Startup validation of the Agent process runs before the Agent accepts work, so its outcome decides whether the process starts
- Security requirement: safety/integrity failures must never be downgraded to warnings or partial availability
- Operational requirement: the disabled state and reason of a non-mandatory component must be observable
- Safety, validation, authentication, authorization, approval, Routing, and data integrity requirements must not be relaxed by choosing an environment name or changing the configuration

## Assumptions

- Target environment: single host, one Agent process and multiple MCP server processes
- Expected scale: limited concurrency
- Trust boundary: privileges granted only within each process
- External dependencies: MCP servers, the Embedding service, external search and RAG services, and the Observability output destination (classified as mandatory or non-mandatory by the per-server `required` field and its classification table in `agent_08_04` (MCP Configuration))
- Re-evaluate if assumptions no longer hold: multi-host configuration, distributed execution, integration with an external orchestrator or service supervisor

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
12. When a component's mandatoriness is undefined or cannot be determined: do not assume non-mandatory. Do not use undefined classification as grounds for continuing startup. Treat as unresolved design/configuration error.
13. **Division of classification responsibility**: this ADR defines classification criteria and failure handling contract. Approved classification of each MCP server is recorded in the classification table of `agent_08_04`; the `required` field in `config/agent.toml` must match it. Configuration provides effective values only within the range that classification permits. Startup validation verifies effective classification before using it to decide whether startup continues. Configuration alone cannot weaken a mandatory component to non-mandatory without an approved architecture or Specification change.
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
23. Routing decisions based on static `ToolRegistry` or `tool_names`, Routing fallback to static Registry, and Routing by name inference are not reintroduced. The permitted diagnostic use of the static `ToolRegistry` as startup Drift validation input is defined by ADR-003 Decision Detail #15.
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
- Concrete mandatory/non-mandatory assignment of individual components (recorded in the classification table of `agent_08_04`)
- New configuration keys or configuration models
- RuntimeToolRegistry, Routing, availability concepts redesign (ADR-003)
- RAG Fallback changes (ADR-010)

## Rationale

### 1. Primary Reason for Adoption — Security

Safety/integrity failures are always Fail-Fast (at startup) or Fail-Closed (at runtime), preventing Security Controls from being bypassed by the choice of environment name.

### 2. Second Reason for Adoption — Data Integrity

Aborting startup unconditionally when a mandatory component is unavailable prevents processing from proceeding without canonical state or Config Isolation/approval control.

### 3. Third Reason for Adoption — Predictability

A single common policy guarantees the same conditions produce the same results (Fail-Fast/Fail-Closed/continue) in every environment, increasing predictability for operators.

### 4. Availability

Uniformly aborting all of startup even for availability failures of non-mandatory components needlessly stops functions that do not affect core safety and integrity. Permitting partial availability only under explicit criteria secures the necessary availability.

### 5. Operability

Making the reasons for component disabling and partial availability explicitly observable prevents unavailable functions from appearing available and makes incident response easier.

### 6. Non-Persistence of Startup Validation Results

The startup validation results built by `StartupOrchestrator` are an in-memory aggregate rebuilt at every process startup, intentionally not persisted. Keeping a history of past startups is outside the scope of this Decision; only the decision at each startup is valid.

## Alternatives Considered

### Alternative A: Separate failure-handling policies per Environment Profile

#### Description

Define environment-specific failure handling policies (Fail-Fast conditions and the permitted extent of Fail-Open) for Local, Development, Production, and so on.

#### Advantages

- Less friction during development

#### Disadvantages

- Behavioral differences between environments can lead to unintended relaxation of safety
- It becomes hard to predict which guarantees hold in which environment

#### Reason for Rejection

Prioritizing Security and Predictability, a single common policy whose guarantees do not change with the environment name was adopted.

#### Reconsideration Conditions

- Friction during development becomes a serious Availability problem

### Alternative B: Treat every dependency as required

#### Description

Treat every dependency component uniformly as mandatory and always abort startup when any of them is unavailable.

#### Advantages

- Simple rule
- No risk of misclassification

#### Disadvantages

- Even a temporary failure of a peripheral component that does not affect core processing stops startup as a whole
- Operational flexibility is lost

#### Reason for Rejection

Prioritizing Availability, partial availability was permitted under explicit criteria for components that do not affect core safety and integrity.

#### Reconsideration Conditions

- The operational cost of the classification criteria turns out to exceed the actual availability improvement

### Alternative C: Continue startup after any dependency failure

#### Description

Permit startup to continue on any failure, regardless of the kind of dependency component.

#### Advantages

- Startup interruptions are minimized

#### Disadvantages

- It would allow continuing even through safety/integrity failures, which carries a significantly high Security risk

#### Reason for Rejection

Security is the top priority; safety/integrity failures are always Fail-Fast/Fail-Closed.

#### Reconsideration Conditions

- Not applicable (permitting continuation through safety/integrity failures is not reconsidered)

### Alternative D: Allow only explicitly classified non-required components to be disabled

#### Description

The approach adopted by this ADR. Only components explicitly classified as non-mandatory are disabled on an availability failure, and startup is permitted to continue.

#### Advantages

- Because the classification criteria are explicit, arbitrary continuation decisions are prevented
- It can be handled independently of safety/integrity failures

#### Disadvantages

- There is a cost to maintaining the classification of each component
- A misclassification could either prevent a necessary startup abort or needlessly disable an available function

#### Reason for Rejection

Not rejected; this is the approach adopted by this ADR. It is listed for comparison.

### Alternative E: Dynamic failure policy based on real-time risk assessment

#### Description

Change the failure policy dynamically based on real-time risk assessment.

#### Advantages

- More flexible failure response

#### Disadvantages

- Requires a complex implementation
- Risk of misjudgment in real-time assessment
- Unpredictable behavior

#### Reason for Rejection

Rejected to prioritize Predictability and Maintainability, because static classification criteria were judged sufficient.

#### Reconsideration Conditions

- The accuracy of real-time risk assessment is proven and the operational cost exceeds an acceptable level

## Consequences

### Positive Consequences

- Single consistent failure handling policy across all environments
- No safety relaxation through environment names
- Startup and execution boundaries predictable
- Startup can continue when only non-mandatory components unavailable
- Unavailable functions excluded from executable exposure set
- Partial-availability state observable
- Fallback conditions limited to explicit definitions by other Accepted ADRs

### Negative Consequences

- Component mandatoriness must be defined and maintained
- Misclassification can cause unnecessary startup abort or inappropriate disabling of mandatory function
- Partial availability requires support in Diagnostics, Health Checks, and logs
- Startup validation more comprehensive
- Every environment must meet same safety requirements
- Operators must distinguish availability failures from safety/integrity failures when responding

## Invariants

- INV-01: Single common failure handling policy for every environment
- INV-02: Environment names do not relax safety/validation requirements
- INV-03: Missing/invalid Workflow → abort
- INV-04: Duplicate Tool ownership → abort
- INV-05: Required DB connection failure or Schema inconsistency → abort
- INV-06: RuntimeToolRegistry initialization failure → abort
- INV-07: Failures of authentication, authorization, Allowlist, Safety Tier, Config Isolation, or establishing approval control are all Fail-Closed (Fail-Fast) at startup
- INV-08: If a mandatory component is unavailable, startup is aborted
- INV-09: A non-mandatory component can be disabled only in the case of an availability failure; the subprocess spawn path is covered by Exceptions
- INV-10: Safety/integrity failures not converted to partial availability
- INV-11: Tools related to a disabled component are not presented to the LLM as executable
- INV-12: Tools related to a disabled component cannot be executed
- INV-13: The partial-availability state and its reason are observable
- INV-14: If a component's mandatoriness is undefined, startup is not permitted to continue
- INV-15: Fallback is permitted only when another Accepted ADR explicitly defines it
- INV-16: ADR-010 remains the authority for the approved RAG Fallback

### Alignment with INV-01 and INV-02

The strict-default behavior enforces INV-01 and INV-02 at startup time:

1. **INV-01**: the same strict checks run in every environment; for example, a missing required configuration file (`agent.toml`) raises `ConfigMissingError` (Explicit in code — `scripts/shared/config_loader.py`).
2. **INV-02**: `ProductionConfigValidator` rejects a configuration whose strict keys (`tool_definitions_strict`, `routing_drift_strict`) are not true, independent of any environment name (Explicit in code — `scripts/agent/production_config_validator.py`).

## Exceptions

- An Agent-launched MCP subprocess that fails to start after its single retry aborts startup regardless of `required`. This exception holds only while every MCP server with `startup_mode = "subprocess"` is classified required; startup validation rejects a configuration in which such a server sets `required = false`. Before any subprocess server is reclassified non-required, the spawn path must apply `required` to spawn failures, and this exception must be removed.

## Verification

### Automated Tests

- **Test**: Missing/invalid Workflow → abort
  - **Verifies**: INV-03
  - **Type**: Integration
  - **Blocking**: Yes
  - **Status**: Confirmed

- **Test**: Inconsistent DB Schema → abort
  - **Verifies**: INV-05
  - **Type**: Integration
  - **Blocking**: Yes
  - **Status**: Confirmed

- **Test**: Duplicate Tool ownership → abort
  - **Verifies**: INV-04
  - **Type**: Integration
  - **Blocking**: Yes
  - **Status**: Confirmed

- **Test**: Initialization failure of RuntimeToolRegistry, failure of a required DB connection, and failures of authentication/authorization/Allowlist/Safety Tier/Config Isolation/establishing approval control abort startup
  - **Verifies**: INV-06, INV-07
  - **Type**: Integration
  - **Blocking**: Yes
  - **Status**: Partial (see `adr_01_index.md`)

- **Test**: Unavailability of a mandatory component (such as a required MCP server) aborts startup
  - **Verifies**: INV-08
  - **Type**: Integration
  - **Blocking**: Yes
  - **Status**: Confirmed

- **Test**: An availability failure of a non-mandatory component permits startup to continue and disables that component
  - **Verifies**: INV-09
  - **Type**: Integration
  - **Blocking**: Yes
  - **Status**: Confirmed (spawn path: see Exceptions)

- **Test**: Safety/integrity failures not converted to partial availability
  - **Verifies**: INV-10
  - **Type**: Regression
  - **Blocking**: Yes
  - **Status**: Partial (see `adr_01_index.md`)

- **Test**: Calls to Tools of disabled component → rejected
  - **Verifies**: INV-11, INV-12
  - **Type**: Unit
  - **Blocking**: No
  - **Status**: Confirmed

- **Test**: Fallback only per ADR-010
  - **Verifies**: INV-15, INV-16
  - **Type**: Integration
  - **Blocking**: Yes
  - **Status**: Not verified (manual audit only; see Manual Review)

### Startup Validation

- Validation of environment configuration (the same validation items apply regardless of environment name)
- Validation of each component's effective mandatoriness classification
- Decision on whether startup can continue based on failure classification

### Deployment Validation

- Check the failure handling policy configuration before and after deployment
- Confirm that Fail-Fast is effective for mandatory components

### Runtime Monitoring

- Health Check: MCP server health checks
- Metrics: number of disabled components and Tools
- Logs: failure classification results, startup-continuation reasons, disable reasons
- Alert conditions: safety/integrity failures

### Manual Review

- Review of changes to the failure policy
- Review of component mandatoriness classification
- No automated test directly verifies INV-01 (single common failure handling policy); INV-02 and INV-13 have no dedicated entry in the list above
- INV-14 (no startup continuation with undefined mandatoriness) verified by unit test (`tests/shared/test_mcp_config.py::TestRequiredDefault`)
- INV-15/INV-16 cross-cutting audit (no ADR-004-scope fallback outside ADR-010):
  - **Why not automated**: "fallback" appears throughout production code in defensive patterns (default-value substitution, best-effort cleanup) not Destination substitution; pattern-based detector would produce unmanageable false positives. Only ADR-010 marker uniqueness automated (`TestFallbackMarkerLockGuard`).
  - **Procedure**: search production sources for fallback paths, classify as (a) ADR-010 fallback or (b) ADR-004-scope fallback requiring Accepted ADR (Decision #26); file follow-up issue for paths fitting neither.
  - **Baseline**: ADR-010 sole Accepted ADR defining fallback. Treats HTTP errors other than authentication errors (401/403 do not fall back), timeouts, connection errors as fallback conditions; empty results and parse errors as non-fallback.
  - **Classification of known paths**:
    - **Orchestrator workflow loading** (`orchestrator.py`): no fallback exists. A workflow definition that fails to load aborts Orchestrator construction, consistent with INV-03.
    - **Vector-to-FTS degradation** (`retriever.py`): accepted current behavior. Rationale: vector→FTS is a within-database mode switch (both modes read the same `memories` table), not a Destination substitution; therefore outside ADR-004 scope.
    - **augment() HTTP-to-in-process path**: ADR-010 fallback, class (a).
    - **MQE, Rerank, and Refiner degradation**: outside ADR-004 scope; each degrades within the same in-process pipeline (original query, RRF order, raw chunks), not a Destination.
  - **Cadence**: at each release review, and when a change introduces fallback or Destination substitution.
  - **Owner**: Repository owner.

## Implementation Notes

- For the non-persistence of startup validation results, see "6. Non-Persistence of Startup Validation Results" in the Rationale section of this document.
- Retry policy for an unreachable MCP server: live `/v1/tools` discovery (`scripts/agent/services/mcp_tool_discovery.py::fetch_tools()`) does not retry; subprocess startup retries once after a fixed delay (`scripts/agent/startup_mcp_starter.py::McpServerStarter`, through `retry_once_with_delay()`). `HealthChecker.startup_poll()` has no production caller (AGENT-012).
- When a subprocess fails to start after the retry, `retry_once_with_delay()` re-raises the second failure with a `[fatal]` prefix and startup aborts regardless of `required`; the `McpServerStarter` branch that would call `disable_server()` for a non-required server is never reached (Explicit in code — `scripts/agent/startup_mcp_starter.py`, `scripts/agent/shared/retry_helper.py`). This is the spawn-failure exception listed in Exceptions.

## Known Deviations

- **Known Issue**: AGENT-012 — tracked in governance_03 Part 1 (`HealthChecker.startup_poll()` is listed in Implementation References but has no caller under `scripts/`)

## Review Triggers

Re-evaluate when:

- Operational scale/concurrency changes significantly
- Deployment changes from single host to multiple hosts/distributed configuration
- Security/audit requirements change
- Performance targets/resource constraints change
- External protocol/adopted library changed or discontinued
- Failure history shows assumptions no longer valid
- Reasons for rejecting an alternative no longer hold
- Component mandatoriness classification criteria change
- An MCP subprocess server is to be reclassified non-required (the spawn-failure exception must be removed first)
- New Accepted ADR permitting Fallback added

## Approval

### Required Reviewers

- Architecture Owner
- Affected Component Owner
- Security Reviewer: when security impact
- Ops Reviewer: when ops/monitoring/recovery affected
- Data Owner: when data/schema/retention affected

### Approval Record

- **Approved By**: Task-level approval decision (repository owner; individual reviewer names not recorded)
- **Approval Date**: Not recorded (individual approval dates not recorded for task-level approval decision)
- **Approval Reference**: `docs/00_governance/governance_01_documentation-policy.md` ADR Acceptance Evidence Standard
- **Decision Change (2026-10-08)**: Task-level approval decision (repository owner instruction) covering Decision #13; individual reviewer names are not recorded.
- **Decision Change (2026-10-13)**: Task-level approval decision (repository owner instruction) covering INV-09 and the spawn-failure exception; individual reviewer names are not recorded.

This ADR's `Accepted` status uses the task-level approval decision defined by the governance document above as its acceptance evidence. No formal Approval Record with individual reviewer names and approval dates has been created.

## Related ADRs

- ADR-001: Mandatory Workflow Engine — missing/invalid Workflow → Fail-Fast
- ADR-002: Per-Process Configuration Ownership and Config Isolation — Config Isolation violation → Fail-Fast
- ADR-003: RuntimeToolRegistry as the Sole Routing Authority — RuntimeToolRegistry init failure → Fail-Fast; authority for Tool visibility/Routing/Dynamic Health
- ADR-010: In-Process Fallback When External RAG Execution Fails — sole Fallback this ADR permits

## Implementation References

- `scripts/agent/startup.py` — `StartupOrchestrator.run()`
- `scripts/shared/mcp_config.py` — `McpServerConfig`
- `scripts/agent/production_config_validator.py` — `ProductionConfigValidator.validate()`
- `scripts/agent/services/mcp_tool_discovery.py` — `McpToolDiscoveryService.discover_all()`
- `scripts/shared/mcp_health.py` — `McpServerHealthRegistry`
- `scripts/agent/services/mcp_health.py` — `check_service_health()`
- `scripts/agent/startup_mcp_starter.py` — `McpServerStarter`
- `scripts/agent/shared/retry_helper.py` — `retry_once_with_delay()`
- `scripts/agent/http_lifecycle_health_checker.py` — `HealthChecker.startup_poll()`
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
