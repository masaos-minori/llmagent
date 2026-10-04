---
title: "ADR-004 Supporting Sections: Alternatives Considered and Verification"
area: governance
tags:
  - adr
  - governance
  - failure-handling
  - alternatives
  - verification
related:
  - ADR-004-environment-failure-handling-policy.md
  - adr_00_document-guide.md
---
# ADR-004 Supporting Sections: Alternatives Considered and Verification

## Purpose

Companion to `ADR-004-environment-failure-handling-policy.md` (ADR-004: Failure Handling Policy Across Environments). It holds supporting sections moved out of the ADR to keep the ADR within the documentation size limit. The ADR remains the authority for the decision; the section headings in the ADR link here. This document is not a basis for design decisions.

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
  - **Status**: Confirmed

- **Test**: Unavailability of a mandatory component (such as a required MCP server) aborts startup
  - **Verifies**: INV-08
  - **Type**: Integration
  - **Blocking**: Yes
  - **Status**: Confirmed

- **Test**: An availability failure of a non-mandatory component permits startup to continue and disables that component
  - **Verifies**: INV-09
  - **Type**: Integration
  - **Blocking**: Yes
  - **Status**: Confirmed

- **Test**: Safety/integrity failures not converted to partial availability
  - **Verifies**: INV-10
  - **Type**: Regression
  - **Blocking**: Yes
  - **Status**: Confirmed

- **Test**: Calls to Tools of disabled component → rejected
  - **Verifies**: INV-11, INV-12
  - **Type**: Unit
  - **Blocking**: No
  - **Status**: Confirmed

- **Test**: Fallback only per ADR-010
  - **Verifies**: INV-15, INV-16
  - **Type**: Integration
  - **Blocking**: Yes
  - **Status**: Confirmed

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
- No automated test directly verifies INV-01 (single common failure handling policy)
- INV-14 (no startup continuation with undefined mandatoriness) verified by REQ-001 unit test (`tests/shared/test_mcp_config.py::TestRequiredDefault`)
- INV-15/INV-16 cross-cutting audit (no ADR-004-scope fallback outside ADR-010):
  - **Why not automated**: "fallback" appears throughout production code in defensive patterns (default-value substitution, best-effort cleanup) not Destination substitution; pattern-based detector would produce unmanageable false positives. Only ADR-010 marker uniqueness automated (`TestFallbackMarkerLockGuard`).
  - **Procedure**: search production sources for fallback paths, classify as (a) ADR-010 fallback or (b) ADR-004-scope fallback requiring Accepted ADR (Decision 26); file follow-up issue for paths fitting neither.
  - **Baseline**: ADR-010 sole Accepted ADR defining fallback. Treats HTTP errors (401/403), timeouts, connection errors as fallback conditions; empty results and parse errors as non-fallback.
  - **Resolution (2026-10-03)**: Both paths classified per owner decision (UNK-01):
    - **Path 1** (`orchestrator.py` sentinel-workflow fallback): option (c) — ADR-004-scope fallback contradicting INV-03. Rationale: the path exhibits all six elements of Decision 26 (trigger = loader failure, destination = sentinel degraded workflow, eligibility, restrictions, result semantics = degraded REPL, observability = log + warning); INV-03 mandates abort on missing/invalid Workflow; the Workflow engine is a mandatory component. Requires separate code-change handling.
    - **Path 2** (`retriever.py` vector-to-FTS degradation): option (a) — accepted current behavior. Rationale: vector→FTS is a within-database mode switch (both modes read the same `memories` table), not a Destination substitution; therefore outside ADR-004 scope. No behavioral change required.
  - **Cadence**: at each release review, and whenever a change introduces new fallback or Destination substitution.
  - **Owner**: not yet assigned; cross-cutting ownership decision remains open in `docs/00_governance/governance_03_issue-and-uncertainty-management.md`.

Register any Invariant without Verification as an unverified item in an Issue.

## Known Deviations

Not applicable. Known Deviations are recorded in `ADR-004-environment-failure-handling-policy.md`.

## Related Documents

- `ADR-004-environment-failure-handling-policy.md`
- `adr_00_document-guide.md`

## Keywords

- adr
- supporting-sections
