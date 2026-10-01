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
---

# ADR-004: Failure Handling Policy Across Environments

## Keywords
<placeholder>

## Status

Accepted

## Summary

This ADR defines a single common failure handling policy for every environment in which the system runs. Environment names (including any name used to distinguish environments, such as Local, Development, Test, or Production) do not change startup validation, authentication, authorization, Allowlist enforcement, approval control, Tool ownership requirements, Routing requirements, resource-scope validation, DB integrity requirements, or Workflow requirements. Failures are classified into "safety/integrity failures" and "availability failures", and safety/integrity failures are always Fail-Fast at startup or Fail-Closed at runtime. Unavailability of a mandatory component aborts startup, but only for an availability failure of a non-mandatory component is startup allowed to continue in a partial-availability state after that component is disabled. Fallback is permitted only when another Accepted ADR explicitly defines the trigger, destination, eligibility, restrictions, result semantics, and observability. The RAG fallback defined by ADR-010 is the only such exception.

## Context

### Problem

Environment names must not change startup validation or the Fail-Fast/Fail-Closed boundaries. On the other hand, treating every dependency component uniformly as mandatory for startup lets a temporary unavailability of a peripheral component that does not affect core processing block startup as a whole. Failures related to safety and integrity must always be reliably Fail-Fast/Fail-Closed, while for availability failures of components that do not compromise core safety and integrity, continuing startup must be permitted on the basis of explicit criteria.

### Constraints

- Execution on a single host in a single process is assumed
- In the deployment environment, the existence of the workflow definition file must be confirmed before startup
- There are no constraints from external protocols, libraries, or services
- Security requirement: every operation with side effects must be traceable
- Data integrity: approval state must persist across process boundaries
- Safety, validation, authentication, authorization, approval, Routing, and data integrity requirements must not be relaxed by choosing an environment name or changing the configuration

### Assumptions

- Target environment: a single host, a single Agent process
- Expected scale: limited concurrency
- Trust boundary: privileges are granted only within the Agent process
- External dependencies: none (the workflow definition is a local file)
- Items to re-evaluate if the assumptions no longer hold: multi-host configuration, distributed execution, integration with an external workflow engine

## Decision

### Group 1: Common Policy Across Environments

1. The system uses a single common failure handling policy for every environment in which it runs. No environment-specific failure handling policies are defined.
2. Target environments: every environment in which the system runs. There are no environment-specific differences in failure handling policy.
3. Environment names change none of the following: startup validation, authentication, authorization, Allowlist enforcement, approval control, Tool ownership requirements, Routing requirements, resource-scope validation, DB integrity requirements, Workflow requirements, Fail-Fast conditions, or Fail-Closed conditions.

### Group 2: Failure Classification

4. Failures are classified into two kinds: "safety/integrity failures" and "availability failures". This classification is used to decide the impact boundary, that is, whether a failure affects startup as a whole or is limited to a specific component; it is not used to relax safety or integrity requirements.
5. Safety/integrity failures include at least the following: duplicate Tool ownership, missing Workflow definition, invalid Workflow definition, inconsistency of the required DB Schema, Config Isolation violations, invalid authentication configuration, invalid authorization configuration, invalid Allowlist configuration, invalid Safety Tier configuration, missing required Secrets, invalid Tool argument Schemas, invalid resource-scope definitions, a state in which approval control cannot be established, initialization failure of RuntimeToolRegistry, a state in which Tool ownership uniqueness cannot be determined, a state in which a safe Routing destination cannot be determined, a state in which execution preconditions cannot be verified, and data integrity failures.
6. Safety/integrity failures must not be converted into any of the following: partial availability, continuing with a warning only, continuing execution after disabling a component, Fallback, or a No-op treated as success.
7. Availability failures may include unavailability of an MCP server, the Embedding service, external search, or an external RAG service, unavailability of an Observability output destination, and other dependency reachability failures.
8. An availability failure alone does not permit startup to continue. Continuing startup is permitted only when all of the following hold: the target component is explicitly classified as non-mandatory, the failure is localized to that component, every affected function can be safely disabled, no safety or integrity control is relaxed, and the resulting partial-availability state is observable.

### Group 3: Component Mandatoriness Classification

9. **Criteria for mandatory components**: a component is classified as mandatory if any of the following applies.
   - It is required to start or complete the system's core processing.
   - It establishes authentication, authorization, approval, Routing, auditability, Config Isolation, persistence, or data integrity.
   - Its absence prevents operations from being safely rejected.
   - Its absence could cause an incorrect success result.
   - It owns canonical state required for core processing.
   - An Accepted ADR explicitly defines it as mandatory.
   - Its failure cannot be safely isolated from other mandatory components.
10. **Criteria for non-mandatory components**: a component may be classified as non-mandatory only if all of the following are true.
    - Its absence does not prevent safe core processing.
    - Its absence bypasses none of the authentication, authorization, approval, Routing, audit, Config Isolation, or data integrity controls.
    - Its failure can be localized to a known set of functions.
    - The related functions and Tools can be reliably disabled.
    - Calls targeting the function can be rejected Fail-Closed.
    - The disabled state and its impact are observable.
    - The other mandatory components remain safe and internally consistent.
    - Any Fallback is explicitly defined by an Accepted ADR.
11. A component must not be treated as non-mandatory merely because startup is technically possible.
12. When a component's mandatoriness is undefined or cannot be determined: do not assume the component is non-mandatory. Do not use an undefined classification as grounds for continuing startup. Treat it as an unresolved design or configuration error. Where applicable, record or reference the current Known Issue.
13. **Division of classification responsibility**: this ADR defines the classification criteria and the failure handling contract. The approved classification of each component is recorded by the applicable Startup, Agent, or MCP Specification. Configuration provides effective values only within the range the approved Specification permits. Startup validation verifies the effective classification before using it to decide whether startup continues. Configuration alone cannot weaken a mandatory component to non-mandatory without an approved architecture or Specification change.

### Group 4: Startup Fail-Fast Boundary

14. The following conditions are Fail-Fast at startup (startup is aborted).
    - Missing Workflow definition
    - Invalid Workflow definition
    - Connection failure of a required DB
    - Inconsistency of the required DB Schema
    - Initialization failure of RuntimeToolRegistry
    - Duplicate Tool ownership (duplicate ownership of a Live Tool)
    - Unavailability of a required MCP server
    - Invalid authentication configuration
    - Invalid authorization configuration
    - Invalid Allowlist configuration
    - Invalid Safety Tier configuration
    - Missing required Secret
    - Config Isolation violation
    - A state in which approval control cannot be established
    - Failure of environment configuration validation
    - A state in which the component mandatoriness that the startup-continuation decision depends on cannot be determined

    Not every dependency failure stops startup. If it is an availability failure and the target component is explicitly classified as non-mandatory, continuing startup may be permitted according to Decision #7. Unless confirmed by the currently approved Specification, not every MCP server is assumed to be mandatory.

### Group 5: Runtime Fail-Closed Boundary

15. The following conditions are Fail-Closed at runtime (the processing is rejected).
    - Unknown Tool
    - Disabled Tool
    - Unavailable Tool
    - Ambiguous Tool ownership
    - Invalid Tool arguments
    - Missing required approval
    - Authentication or authorization failure
    - Resource-scope validation failure
    - Allowlist validation failure
    - A state in which execution preconditions cannot be verified
    - A state in which a safe execution destination cannot be determined
    - A request targeting a disabled non-mandatory component
16. A rejected operation must return a failure or rejection result. It must not be converted into a No-op treated as success. Routing by name inference must not be performed. It must not fall back to the static Registry. Unless an Accepted ADR explicitly permits it, it must not be redirected to another Tool. An observable reason must be recorded.

### Group 6: Behavior of Mandatory Components

17. When a mandatory component is unavailable: abort startup. Make the failure and its reason observable. Do not silently disable the component. Do not perform Fallback unless an Accepted ADR explicitly permits it.

### Group 7: Behavior of Non-Mandatory Components

18. When an availability failure occurs in a non-mandatory component: disable the component. Permit the system to continue startup in a partial-availability state. Exclude the component's Tools and functions from the executable exposure set. Reject new calls targeting those Tools or functions. Report the disabled state. Report the failure reason. Report the affected functions. Report the reason startup was permitted to continue. Expose the state through the currently approved Diagnostics and operational Observability mechanisms. Do not report the system as fully available.
19. If a safety/integrity failure occurs in the same component, continuing startup is prohibited. Being classified as non-mandatory is not an exemption from safety/integrity failures.

### Group 8: Observability of Partial Availability

20. The disabled state, the failure reason, the affected functions, and the startup-continuation decision must be observable through the currently approved Diagnostics, Health Checks, and logs. A system in a partial-availability state must not be reported as fully available.

### Group 9: Tool Visibility and Execution Boundary

21. Tools associated with a disabled component: must not be presented to the LLM as executable; must not be Routable for new calls; must not be executable; and must have an observable disable reason.
22. ADR-003 remains the authority for `RuntimeToolRegistry`, Tool ownership, Routing, static availability, Dynamic Health, LLM visibility, separation of approval state, execution eligibility, and Reload and Rediscovery behavior. This ADR defines only the failure-handling consequences of how these concepts relate to component mandatoriness classification and does not redefine ADR-003's decisions.
23. Drift validation using the static `ToolRegistry` or `tool_names`, Routing fallback to the static Registry, and Routing by name inference are not reintroduced.
24. Distinguish between a component that is unavailable because of its startup classification (disabled due to a non-mandatory availability failure) and one that became dynamically unavailable after startup due to Dynamic Health. The former is a state related to ADR-003's "static availability" and affects LLM visibility and Routing eligibility. The latter is a state related to ADR-003's "Dynamic Health", affects only runtime success or failure, and does not automatically change LLM visibility. This ADR does not merge or collapse this distinction defined by ADR-003.

### Group 10: Fallback Boundary

25. Fallback is prohibited by default.
26. Fallback is permitted only when an Accepted ADR explicitly defines all of the following: the trigger (Failure Trigger), the Fallback destination (Destination), the eligibility conditions (Eligibility Conditions), the restrictions (Restrictions), the result semantics (Result Semantics), and the observability requirements (Observability Requirements).
27. ADR-010 is the sole authority for the approved external-RAG-to-in-process-RAG fallback. ADR-010 permits Fallback only for its RAG-related conditions and does not permit general Fail-Open behavior. An ordinary empty RAG result does not automatically trigger Fallback. A safety/integrity failure must not trigger an availability Fallback. Fallback must not bypass any of the authentication, authorization, approval, Allowlist, Routing, or data integrity controls.

### Scope

- **Target components**: `StartupOrchestrator`, `McpToolDiscoveryService`, `ProductionConfigValidator`, `McpServerHealthRegistry`
- **Target processes**: the entire Agent process
- **Target data**: startup check results, MCP server state, Tool ownership information, approval state
- **Target environments**: every environment in which the system runs. There are no environment-specific differences in failure handling policy.
- **Target APIs or processing paths**: `StartupOrchestrator.run()`, `McpToolDiscoveryService.discover_all()`, `ProductionConfigValidator.validate()`

### Out of Scope

- Details of failure detection for individual MCP servers
- Details of failure detection for OTel output destinations
- The Startup Orchestrator's own precondition checks, such as Health Checks and pre-startup validation
- Removal of the existing StartupCheckStatus (OK/WARNING/FATAL/SKIPPED)
- Removal of the existing pipeline.add_fatal()/add_warning()
- The concrete mandatory/non-mandatory assignment of individual components (defined by the applicable Specification)
- Introduction of new configuration keys or configuration models
- Redesign of RuntimeToolRegistry, Routing, and availability concepts defined by ADR-003
- Changes to the RAG Fallback defined by ADR-010

## Rationale

### 1. Primary Reason for Adoption — Security

Safety/integrity failures are always Fail-Fast (at startup) or Fail-Closed (at runtime), so that Security Controls are not bypassed by the choice of environment name.

### 2. Second Reason for Adoption — Data Integrity

Aborting startup unconditionally when a mandatory component is unavailable prevents processing from proceeding while the owner of canonical state or the component that establishes Config Isolation and approval control is missing.

### 3. Third Reason for Adoption — Predictability

Not having environment-specific failure handling policies guarantees that the same conditions produce the same results (Fail-Fast/Fail-Closed/continue) in every environment, which increases predictability for operators.

### 4. Fourth Reason for Adoption — Availability

Uniformly aborting all of startup even for availability failures of non-mandatory components needlessly stops functions that do not affect core safety and integrity. Permitting partial availability only under explicit criteria secures the necessary availability.

### 5. Fifth Reason for Adoption — Operability

Making the reasons for component disabling and partial availability explicitly observable prevents unavailable functions from appearing available and makes incident response easier.

Do not use "the current code is implemented this way" as the sole reason for adoption.

### 6. Non-Persistence of Startup Validation Results

The startup validation results built by `StartupOrchestrator` are an in-memory aggregate rebuilt at every process startup,
and are intentionally not persisted. Keeping a history of past startups is outside the scope of this Decision; only the
decision at each startup is valid.

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

Security is the top priority, and safety/integrity failures are always Fail-Fast/Fail-Closed.

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

- A single consistent failure handling policy applies to all environments
- No relaxation of safety occurs through environment names
- Startup and execution boundaries become predictable
- When only non-mandatory components are unavailable, startup can continue
- Unavailable functions are explicitly excluded from the executable exposure set
- The partial-availability state becomes observable
- The conditions under which Fallback is permitted are limited to explicit definitions by other Accepted ADRs

### Negative Consequences

- Component mandatoriness must be defined and maintained
- A misclassification can cause either an unnecessary startup abort or inappropriate disabling of a mandatory function
- Achieving partial availability requires support in Diagnostics, Health Checks, and logs
- Startup validation becomes more comprehensive
- Every environment must meet the same safety requirements
- Operators must distinguish availability failures from safety/integrity failures when responding

## Invariants

- INV-01: The system uses a single common failure handling policy for every environment in which it runs.
- INV-02: Environment names do not relax safety or validation requirements.
- INV-03: If the Workflow definition is missing or invalid, startup is aborted.
- INV-04: If duplicate Tool ownership occurs, startup is aborted.
- INV-05: If a required DB connection fails or its Schema is inconsistent, startup is aborted.
- INV-06: If RuntimeToolRegistry initialization fails, startup is aborted.
- INV-07: Failures of authentication, authorization, Allowlist, Safety Tier, Config Isolation, or establishing approval control are all Fail-Closed (Fail-Fast) at startup.
- INV-08: If a mandatory component is unavailable, startup is aborted.
- INV-09: A non-mandatory component can be disabled only in the case of an availability failure.
- INV-10: Safety/integrity failures are not converted into partial availability.
- INV-11: Tools related to a disabled component are not presented to the LLM as executable.
- INV-12: Tools related to a disabled component cannot be executed.
- INV-13: The partial-availability state and its reason are observable.
- INV-14: If a component's mandatoriness is undefined, startup is not permitted to continue.
- INV-15: Fallback is permitted only when another Accepted ADR explicitly defines it.
- INV-16: ADR-010 remains the authority for the approved RAG Fallback.

## Alignment with INV-01/INV-02

With REQ-001's fix (strict-default behavior), the Fail-Fast requirements of INV-01/INV-02 are now enforced at startup time. Specifically:

1. **INV-01**: Missing required config files cause immediate process termination (no silent-continue).
2. **INV-02**: All processes enforce fail-closed behavior regardless of environment.
3. **No environment-based relaxation**: The strict-default applies uniformly across all environments.

## Verification

### Automated Tests

- **Test**: Startup fails when the Workflow definition is missing or invalid (`tests/agent/test_startup.py::test_aborts_on_missing_workflow_definition`, tests related to `check_workflow_definition()` in `tests/agent/test_repl_health.py`)
  - **Verifies**: INV-03
  - **Type**: Integration
  - **Blocking**: Yes
  - **Status**: Confirmed (executed and confirmed to pass)

- **Test**: Startup fails when the required DB Schema is inconsistent (`tests/agent/test_startup.py::test_aborts_on_missing_workflow_schema`)
  - **Verifies**: INV-05
  - **Type**: Integration
  - **Blocking**: Yes
  - **Status**: Confirmed (executed and confirmed to pass)

- **Test**: Startup fails on duplicate Tool ownership (see ADR-003 Verification)
  - **Verifies**: INV-04
  - **Type**: Integration
  - **Blocking**: Yes
  - **Status**: Confirmed (managed and verified on the ADR-003 side)

- **Test**: Initialization failure of RuntimeToolRegistry, failure of a required DB connection, and failures of authentication/authorization/Allowlist/Safety Tier/Config Isolation/establishing approval control abort startup
  - **Verifies**: INV-06, INV-07
  - **Type**: Integration
  - **Blocking**: Yes
   - **Status**: Confirmed — `tests/agent/test_startup.py::test_falsy_own_config_file_raises` verifies Config Isolation fail-closed (REQ-003); `tests/shared/test_config_loader.py::test_unknown_top_level_key_rejected` verifies unknown-key rejection (REQ-004). Note: individual scenario tests for each condition are covered by these new tests rather than the general FATAL/WARNING aggregation test.

- **Test**: Unavailability of a mandatory component (such as a required MCP server) aborts startup
  - **Verifies**: INV-08
  - **Type**: Integration
  - **Blocking**: Yes
   - **Status**: Confirmed (executed and confirmed to pass) — the `TestDiscoverAllUnreachableServers` class in `tests/agent/services/test_mcp_tool_discovery.py` directly verifies the `is_required` branch

- **Test**: An availability failure of a non-mandatory component permits startup to continue and disables that component
  - **Verifies**: INV-09
  - **Type**: Integration
  - **Blocking**: Yes
   - **Status**: Confirmed (executed and confirmed to pass) — the same `TestDiscoverAllUnreachableServers` class directly verifies dedicated scenarios tied to non-mandatory component classification

- **Test**: Safety/integrity failures are not converted into partial availability
  - **Verifies**: INV-10
  - **Type**: Regression
  - **Blocking**: Yes
  - **Status**: Confirmed in code structure (the Workflow/Schema/Tool-ownership checks in `scripts/agent/startup.py` always take the FATAL path without going through the `is_required` branch); no dedicated test directly verifies this structure across the board

- **Test**: Calls to Tools related to a disabled component are rejected (`tests/mcp_servers/file/test_call_tool_validation.py`, a limited verification covering file-mcp only)
  - **Verifies**: INV-11, INV-12
  - **Type**: Unit
  - **Blocking**: No
  - **Status**: Confirmed (file-mcp only)

- **Test**: Fallback does not occur outside the situations defined by ADR-010
  - **Verifies**: INV-15, INV-16
  - **Type**: Integration
  - **Blocking**: Yes
  - **Status**: Needs confirmation (not individually re-run in this task)

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
- No automated test directly verifies INV-01 (a single common failure handling policy)
- INV-14 (no startup continuation with undefined mandatoriness) is verified by automation in the REQ-001 unit test (`tests/shared/test_mcp_config.py::TestRequiredDefault`).

Register any Invariant without Verification as an unverified item in an Issue.

## Implementation Notes

Briefly describe how the current implementation realizes the Decision.

For the non-persistence of startup validation results, see "6. Non-Persistence of Startup Validation Results" in `## Rationale`.

Retry policy when an MCP server is unreachable: the unreachable-handling paths actually taken (`scripts/agent/services/mcp_health.py`,
`scripts/agent/services/mcp_tool_discovery.py::fetch_tools()`, and adjacent files) contain no retry logic,
and the only retry implementation (`scripts/agent/http_lifecycle_health_checker.py::HealthChecker.startup_poll()`)
has no callers. Owner confirmation (2026-09-27): the current no-retry behavior on these paths
is the intended, settled policy.

This chapter is not a basis for design decisions. List detailed APIs, Classes, and Functions in the Implementation References.

Do not record line numbers; reference by File Path and Symbol name.

## Known Deviations

### ADR-004-D1-profile-config-model-still-present: Environment-conditional required/local branching in McpServerConfig

- **Known Issue**: ADR-004-D1-profile-config-model-still-present
- **Type**: Design Deviation (Resolved)
- **Summary**: `McpServerConfig` in `scripts/shared/mcp_config.py` and `scripts/agent/services/mcp_tool_discovery.py` branched on the value of `security_profile` (the environment) to decide whether to reference `required_in_production` or `required_in_local`.
- **Conflicting Source**: Decision Group 3 (mandatoriness decisions should be environment-independent)
- **Expected Design**: Component mandatoriness decisions must be environment-independent (Decision Group 3).
- **Observed Implementation**: Before the fix, a branch existed that referenced either `required_in_production` or `required_in_local` depending on the value of `security_profile`.
- **Impact**: INV-01, INV-02, INV-09, INV-10, INV-14 → resolved.
- **Recommended Action**: **Resolved (confirmed 2026-09-04)**: `plans/done/20260903-091417_plan.md` (`localremoval`) removed `SecurityProfile.LOCAL` itself, and `SecurityProfile` became an enum that holds only `PRODUCTION` (confirmed in `scripts/shared/mcp_config.py`). The environment branch between `required_in_production`/`required_in_local` was resolved, and mandatoriness decisions became environment-independent. Because the very concept of a cross-profile equivalence test became unnecessary with the removal of `SecurityProfile.LOCAL`, the remaining item was resolved as Not Applicable.
- **Owner**: TBD
- **Status**: Resolved (2026-09-04)
- **Resolution Target**: N/A: already resolved

### ADR-004-D2-production-config-validator-severity-downgrade: is_production-gated strict-mode violation downgraded to warning

- **Known Issue**: ADR-004-D2-production-config-validator-severity-downgrade
- **Type**: Design Deviation (Resolved)
- **Summary**: Downgrading strict-mode violations to warnings under the `is_production` condition in `scripts/shared/production_config_validator.py` (a deviation separate from D1, pointed out in `docs/10_adr/adr-index.md` INV-010).
- **Conflicting Source**: `docs/10_adr/adr-index.md` INV-010
- **Expected Design**: Production-grade validation should apply unconditionally in every environment.
- **Observed Implementation**: Before the fix, strict-mode violations were downgraded to warnings under the `is_production` condition.
- **Impact**: It affected the consistency of Production-grade validation.
- **Recommended Action**: **Resolved (confirmed 2026-09-04)**: REQ-004 of `plans/done/20260903-091417_plan.md` removed the `is_production` conditional branch (confirmed in `scripts/shared/production_config_validator.py`; the branch no longer exists), and Production-grade validation now applies unconditionally in every environment.
- **Owner**: TBD
- **Status**: Resolved (2026-09-04)
- **Resolution Target**: N/A: already resolved

### ADR-004-D3-non-required-continuation-test-coverage: Decision #18/INV-09 continuation test coverage

- **Known Issue**: N/A: not registered as a governance Known Issue — see Recommended Action
- **Type**: Resolved Gap
- **Summary**: Status of automated tests that verify startup continuation on an availability failure of a non-mandatory component (Decision #18, INV-09).
- **Conflicting Source**: N/A: not a conflict — this entry records confirmation, not a discrepancy.
- **Expected Design**: An availability failure of a non-mandatory component permits startup to continue only when explicit criteria are met (Decision #18, INV-09).
- **Observed Implementation**: Already verified in `tests/agent/services/test_mcp_tool_discovery.py::TestDiscoverAllUnreachableServers` (see this ADR's `## Verification` section, Status: Confirmed).
- **Impact**: N/A: not an active discrepancy.
- **Recommended Action**: Because this is already recorded as Confirmed in this ADR's own `## Verification` section, no new governance Known Issue is registered.
- **Owner**: N/A: not applicable — no active issue to own
- **Status**: Resolved
- **Resolution Target**: N/A: already resolved

### ADR-004-D4-production-tool-safety-validation-fail-open

- **Known Issue**: N/A: not registered as a governance Known Issue — see Recommended Action
- **Type**: Resolved Gap
- **Summary**: Production tool-safety validation could silently skip checks on registry failure (bare `except Exception:` returning `None` in `_resolve_known_tools()`) and accept unknown security-profile values without rejection. This was addressed by REQ-001–REQ-005: removing the broad exception fallback, adding explicit `SecurityProfile` coercion/rejection, and injecting authoritative known-tools from both runtime call sites. All safety-critical checks remain unconditional across `SecurityProfile.PRODUCTION`.
- **Conflicting Source**: N/A: not a conflict — this entry records confirmation, not a discrepancy.
- **Expected Design**: Production validation cannot succeed without an authoritative tool set; registry failures must produce actionable errors; unknown security profiles must fail during configuration construction.
- **Observed Implementation**: REQ-001–REQ-005 completed: `_resolve_known_tools()` now raises `ValueError`/`ImportError` instead of silently skipping; `validate()` coerces/rejects unknown `SecurityProfile` values; `build_agent_config()` injects `known_tools` explicitly; `audit_security_defaults()` uses specific exception handling.
- **Impact**: N/A: not an active discrepancy.
- **Recommended Action**: Because this is already recorded as Resolved in this ADR's own `## Known Deviations` section, no new governance Known Issue is registered.
- **Owner**: N/A: not applicable — no active issue to own
- **Status**: Resolved
- **Resolution Target**: N/A: already resolved

### CI-016: Undefined component criticality treatment relies on a safe default, untested

- **Known Issue**: CI-016
- **Type**: operational-gap
- **Summary**: No automated test currently verifies the prohibition on continuing startup with undefined mandatoriness (Decision #12, INV-14).
- **Conflicting Source**: This ADR's `## Completion Checklist` (the unchecked item "automatable verification does not rely only on Manual Review") and `## Verification` > `### Manual Review` (which stated that INV-14 was not enforced by the current implementation)
- **Expected Design**: When a component's mandatoriness is undefined or cannot be determined, do not assume it is non-mandatory; treat it as an unresolved design or configuration error (Decision #12, INV-14).
- **Observed Implementation**: `McpServerConfig.required` defaults to `True` (`scripts/shared/mcp_config.py:95`), so unspecified mandatoriness is never implicitly treated as non-mandatory. The REQ-001 unit test (`tests/shared/test_mcp_config.py::TestRequiredDefault`) verifies the safety of this default, so this Known Deviation is resolved.
- **Impact**: Without a test, if the default value of `required` were changed in the future (for example, to `False`), there would be no automated check to detect a violation of INV-14.
- **Recommended Action**: The REQ-001 unit test (`tests/shared/test_mcp_config.py::TestRequiredDefault`) verifies that the default value of `McpServerConfig.required` is `True`. This Known Deviation is resolved. If the default value of `required` is changed in the future, update the automated test that detects violations of INV-14 at the same time.
- **Owner**: Unassigned
- **Status**: Resolved (automated test added)
- **Resolution Target**: Adding unit tests for the default value of `McpServerConfig.required` and for the handling of undefined mandatoriness

Do not unconditionally align the ADR text with the current implementation; manage discrepancies as Known Issues.

**Revision record (2026-09-04)**: Based on the architecture owner's approval on 2026-09-03, the policy of fully removing `SecurityProfile.LOCAL` and making Production-grade validation unconditional for every normal startup was finalized (this ADR was revised directly rather than replaced by a new ADR). After confirming that all four related plans (`plans/done/20260903-091417_plan.md` "localremoval", `plans/done/20260903-091921_plan.md` "loopbackonly", `plans/done/20260903-092407_plan.md` "mcpauth", `plans/done/20260903-092746_plan.md` "localcleanup") were fully implemented, the two corresponding Known Deviations above were updated as resolved. The "single common failure handling policy" wording in Decision Group 1 was already environment-independent before this revision, so the Decision body itself did not need rewriting.

## Review Triggers

Re-evaluate this ADR when any of the following conditions occurs.

- The operational scale or concurrency changes significantly
- The deployment changes from a single host to multiple hosts or a distributed configuration
- Security or audit requirements change
- Performance targets or resource constraints change
- An external protocol or adopted library is changed or discontinued
- Failure history shows that the assumptions are no longer valid
- The reasons for rejecting an alternative no longer hold
- Component mandatoriness classification logic is changed to be environment-independent
- A new Accepted ADR that permits Fallback is added

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
- **Approval Reference**: `docs/governance_01_documentation-policy.md` ADR Acceptance Evidence Standard

This ADR's `Accepted` status uses the task-level approval decision defined by the governance document above as its acceptance evidence. No formal Approval Record with individual reviewer names and approval dates has been created.

## Related Documents

### Related ADRs

- ADR-001: Mandatory Workflow Engine — a missing or invalid Workflow definition is Fail-Fast
- ADR-002: Per-Process Configuration Ownership and Config Isolation — a Config Isolation violation is Fail-Fast
- ADR-003: RuntimeToolRegistry as the Sole Routing Authority — initialization failure of RuntimeToolRegistry is Fail-Fast; authority for Tool visibility, Routing, and Dynamic Health
- ADR-010: In-Process Fallback When External RAG Execution Fails — the only Fallback this ADR permits

### Specifications

- [Deployment Guide](../90_deployment/deployment_01_deployment.md) — workflow validation during deployment
- [MCP Configuration / Approval / Observability](../23_agent/agent_08_04_configuration-mcp-approval-obs.md#component-criticality-classification) — record of MCP server mandatory/non-mandatory classification (Decision Group 3)
<!-- TODO: Document 'agent_03_03_turn-processing-flow-workflow-engine.md' was deleted -->

### Operations

- [Workflow Deployment Runbook](../23_agent/agent_10_04_operations-and-observability-validation-and-troubleshooting.md#workflow-deployment-runbook) — incident response procedure

### Known Issues

- [Issue and Uncertainty Management](../00_governance/governance_03_issue-and-uncertainty-management.md) — ADR-004-related Known Issue (CI-016)

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

- [x] The problem to solve is clear
- [x] The Decision is narrowed to one primary design decision
- [x] The Decision is stated in clear terms such as mandatory, prohibited, canonical, or Fallback conditions
- [x] The reasons for adoption are explained from perspectives other than the current implementation
- [x] Substantive alternatives and the reasons for rejecting them are recorded
- [x] Positive Consequences are recorded
- [x] Negative Consequences are recorded
- [x] Verifiable Invariants are defined
- [x] Each Invariant has a corresponding Verification (some are explicitly marked as Needs confirmation/unverified)
- [x] Automatable verification does not rely only on Manual Review (INV-01 is Confirmed; INV-14 is confirmed by the REQ-001 automated test; INV-08 and INV-09 are Confirmed)
- [x] The relationship with existing ADRs is recorded
- [x] The ADR does not contradict related Specifications (a Specification recording component mandatoriness classification is in place)
- [x] Discrepancies with the current implementation are registered as Known Issues (registered as `CI-016`; see `## Known Deviations`)
- [x] The Owner and required Reviewers are defined (the task-level approval decision defined by `docs/governance_01_documentation-policy.md` ADR Acceptance Evidence Standard is used as acceptance evidence; no individual Approval Record [approver, approval date, approval reference] has been created)
- [x] Review Triggers are recorded
- [ ] The ADR is registered in the ADR index and the Document Guides of related areas (separate confirmation required)
