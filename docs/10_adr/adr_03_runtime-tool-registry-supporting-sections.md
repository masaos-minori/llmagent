---
title: "ADR-003 Supporting Sections: Alternatives Considered and Verification"
area: governance
tags:
  - adr
  - governance
  - runtime-tool-registry
  - alternatives
  - verification
related:
  - ADR-003-runtime-tool-registry-routing-authority.md
  - adr_00_document-guide.md
---
# ADR-003 Supporting Sections: Alternatives Considered and Verification

## Purpose

Companion to `ADR-003-runtime-tool-registry-routing-authority.md` (ADR-003: RuntimeToolRegistry as the Sole Routing Authority). It holds supporting sections moved out of the ADR to keep the ADR within the documentation size limit. The ADR remains the authority for the decision; the section headings in the ADR link here. This document is not a basis for design decisions.

## Alternatives Considered

### Alternative A: Dual routing authority (ToolRegistry + RuntimeToolRegistry)

#### Description

Reference both the static `ToolRegistry` and `RuntimeToolRegistry`, and fall back to static definitions when there are no Discovery results.

#### Advantages

- Redundancy when Discovery fails
- Continued support for the legacy specification

#### Disadvantages

- Possible ownership conflicts
- Unexpected routing due to mismatches between configuration and Discovery results
- Reduced safety for unregistered Tools
- Inconsistent Safety Tier and Write attributes

#### Reason for Rejection

Rejected to prioritize Security and reject execution of unregistered Tools Fail-Closed.

#### Reconsideration Conditions

- The reliability of the Discovery mechanism improves significantly
- Consistency between static definitions and Discovery results is guaranteed

### Alternative B: Dynamic tool registration at runtime

#### Description

Add and remove Tools dynamically while updating RuntimeToolRegistry.

#### Advantages

- Flexible Tool management
- Tools can be added at runtime

#### Disadvantages

- Difficulty keeping consistency with Tools being executed
- More complex Security Controls
- Risk of approval state becoming stale

#### Reason for Rejection

Rejected to prioritize Data Integrity and guarantee consistency with Tools being executed.

#### Reconsideration Conditions

- Adding Tools at runtime becomes necessary
- Dynamic updates of approval state become necessary

### Alternative C: No static definition at all

#### Description

Abolish static definitions entirely and use only Discovery results.

#### Advantages

- Simple structure
- Low complexity

#### Disadvantages

- No expected values for tests and Drift validation
- No seed data for documentation generation
- New Tools cannot be pre-registered

#### Reason for Rejection

Rejected to prioritize Operability, because expected values are needed for tests.

#### Reconsideration Conditions

- Discovery results alone allow sufficient verification
- Test automation is sufficiently advanced

### Alternative D: Unify static availability and dynamic health into one `enabled` signal

#### Description

Merge static availability and Dynamic Health into a single `enabled` signal.

#### Advantages

- Simple mental model
- Only one flag to check

#### Disadvantages

- The list of LLM-visible Tools changes every time a Circuit Breaker trips, so temporary network trouble destabilizes Tool availability as seen by the LLM
- The impact is far larger than that of a runtime error

#### Reason for Rejection

The current separation is the safer design.

#### Reconsideration Conditions

- A new requirement arises that changes in Dynamic Health should be reflected in LLM visibility

### Alternative E: Represent approval-required as a disabled state

#### Description

Represent the approval-required state as part of the disabled-Tool mechanism.

#### Advantages

- The existing disabled-Tool mechanism can be reused

#### Disadvantages

- Approval is a per-call decision involving Risk Escalation based on arguments (for example, a path or a Branch) and cannot be expressed as a static per-Tool disable flag
- Merging the two would make Approval-target Tools invisible even where they should be visible to the LLM, making the design of gating at runtime impossible

#### Reason for Rejection

Confuses call-time Policy decisions with per-Tool availability flags.

## Verification

### Automated Tests

- **Test**: Startup fails on duplicate Tool name ownership
  - **Verifies**: INV-01
  - **Type**: Integration
  - **Blocking**: Yes

- **Test**: Unregistered Tools are not executed
  - **Verifies**: INV-02
  - **Type**: Unit
  - **Blocking**: Yes

- **Test**: There is no Fallback to the static ToolRegistry
  - **Verifies**: INV-04
  - **Type**: Regression
  - **Blocking**: Yes

- **Test**: Startup Drift validation (config/live comparison) uses the static `ToolRegistry` as input and does not change the `RuntimeToolRegistry`-based Routing decision itself
  - **Verifies**: INV-04 (Decision Detail #15)
  - **Type**: Integration
  - **Blocking**: No (warning only; in strict mode startup is aborted, but the Routing decision itself is not affected)
  - **Test files**: `tests/agent/shared/test_startup_validation_pipeline.py`, `tests/mcp_servers/cicd/test_tool_server_layer_consistency.py`, `tests/shared/test_tool_registry.py`, `tests/shared/test_tool_safety_tiers.py`

- **Test**: Routing, approval, and auditing reference the same Safety Tier
  - **Verifies**: INV-03
  - **Type**: Integration
  - **Blocking**: Yes

- **Test**: A statically disabled Tool is not included in `llm_tool_definitions()`
  - **Verifies**: INV-06
  - **Type**: Regression
  - **Blocking**: Yes

- **Test**: Tools belonging to a Circuit-Open server remain in `llm_tool_definitions()`
  - **Verifies**: INV-07
  - **Type**: Integration
  - **Blocking**: Yes

### Startup Validation

- Routing is determined at startup based on Discovery results
- Startup is aborted when Discovery fails for a required MCP server; when a non-mandatory MCP server is unavailable, its Tools are disabled and startup continues (ADR-004 Decision 18)

### Deployment Validation

- Check the Discovery results before and after deployment
- Check Schema, configuration, Artifacts, Checksums, and so on

### Runtime Monitoring

- Health Check
- Metrics
- Logs
- Alert conditions: when Discovery fails
- Degraded condition: Not applicable

### Manual Review

- Confirm that a future PR does not re-merge static availability and Dynamic Health by writing to `enabled_for_llm` from a Dynamic Health-driven code path.

## Known Deviations

Not applicable. Known Deviations are recorded in `ADR-003-runtime-tool-registry-routing-authority.md`.

## Related Documents

- `ADR-003-runtime-tool-registry-routing-authority.md`
- `adr_00_document-guide.md`

## Keywords

- adr
- supporting-sections
