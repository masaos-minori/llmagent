# `issues/20260831-173019_adr004_01_...md` is now stale — ADR-004's revised policy re-introduces required/non-required classification

## Priority
High

## Summary
`issues/20260831-173019_adr004_01_mcp_config_failure_model_alignment.md` instructs removing
`McpServerConfig`'s `required_in_local`/`failure_policy` fields entirely and collapsing every
configured component to a single unconditional Fail-Fast behavior. `docs/adr/ADR-004-environment-failure-handling-policy.md`
(the 2026-08-31 full rewrite of ADR-004) now defines the opposite direction: components are
explicitly classified as required or non-required, and a non-required component's availability
failure is permitted to leave it disabled while the system continues with partial availability.
Implementing `adr004_01` as written would now contradict the current ADR-004.

## Background
ADR-004 has gone through two full revisions in this session. The first revision (accepted
2026-08-31) established "Production is the only mode; no required/optional distinction; every
configured component's unavailability is Fail-Fast" — `adr004_01` was written against that
version. The second, current revision (also 2026-08-31, replacing the first) reverses the
required/optional position: components ARE classified as required or non-required (by criteria
independent of environment), and non-required components may be disabled with partial
availability on an availability failure, while safety/integrity failures remain Fail-Fast/
Fail-Closed regardless of classification.

## Problem
(Evidence: Explicit in code and Explicit in the two ADR-004 revisions) `adr004_01`'s
Implementation Intent says: "keep a single required/enabled flag per server... whose
unavailability always causes startup to abort" and its Constraints say "Do not introduce a new
required/optional distinction." The current ADR-004 Decision (Group 3, Group 6, Group 7)
explicitly requires exactly the required/optional distinction `adr004_01` forbids introducing,
just with the classification criteria being environment-independent (not conditioned on
`security_profile`) rather than the old `required_in_production`/`required_in_local` pair.

Separately, during the ADR-004 rewrite, direct code inspection of
`scripts/agent/services/mcp_tool_discovery.py` found that the current classification logic
selects between `cfg.required_in_production` and `cfg.required_in_local` based on
`security_profile == PRODUCTION` — this environment-conditional branching is itself a gap
against the current ADR-004 (Decision Group 1: environment names must not change classification
outcomes), independent of the required/non-required question `adr004_01` addressed.

## Reason for Change
`adr004_01` is currently the only tracked issue for this area, and following its instructions
would actively move the implementation further from the current approved architecture (toward
a single unconditional Fail-Fast model that ADR-004 no longer specifies). Leaving it open and
actionable as-is risks a future implementer executing it and creating a new, larger conformance
gap.

## Implementation Intent
Do not implement `adr004_01` as written. Instead:
1. Retain a required-vs-non-required distinction in `McpServerConfig`, but make the classification
   environment-independent — a single property per component (e.g., a renamed/simplified
   `required: bool`), not a `required_in_production`/`required_in_local` pair selected by
   `security_profile`.
2. Update `scripts/agent/services/mcp_tool_discovery.py`'s classification branch to stop reading
   `security_profile` to choose between two fields; it should read one environment-independent
   value.
3. Decide the fate of `failure_policy` (`FailurePolicy` enum: `fail-fast`/`disable-tool`/
   `degraded`) against the current ADR-004: a required component's unavailability must be
   Fail-Fast (no `disable-tool`/`degraded` outcome), while a non-required component's
   availability failure must always result in disable-and-continue (not a separate
   configurable choice per component) — this suggests `failure_policy` as a per-server override
   is no longer needed at all, with disable-vs-abort determined solely by the required/
   non-required classification. Confirm this with the architecture owner rather than assuming.
4. Ensure no component is classified as required or non-required without evidence per ADR-004's
   classification criteria (Decision Group 3) — since no current Specification records
   per-component classification (see the companion issue on that gap), this implementation
   cannot proceed correctly until that Specification exists or an explicit classification list is
   approved.

## Target Files or Areas
- `scripts/shared/mcp_config.py` — `McpServerConfig`, `FailurePolicy`
- `scripts/agent/services/mcp_tool_discovery.py` — classification branch (`is_prod`/`is_required` logic)
- `config/agent.toml` — any server entries that would need an explicit classification once one exists
- `docs/adr/ADR-004-environment-failure-handling-policy.md` — Known Deviations (update once implementation is aligned)

## Required Changes
- Supersede `issues/20260831-173019_adr004_01_mcp_config_failure_model_alignment.md`: mark it
  stale/do-not-implement, or close it, once this issue is accepted as its replacement.
- Do not remove the required/non-required concept from `McpServerConfig` — instead make it
  environment-independent.
- Resolve the `failure_policy` question (see Implementation Intent #3) with the architecture
  owner before implementing.
- This implementation depends on the missing component-classification Specification (see the
  companion issue) — do not invent per-component classifications without it.

## Constraints
- Do not implement this until the companion Specification-gap issue is resolved, or until an
  explicit, approved per-component classification is otherwise obtained.
- Do not reintroduce environment-conditional branching in any new form.
- Do not modify ADR-004's Decision, Rationale, or Invariants — only its Known Deviations, once
  the implementation is aligned.

## Acceptance Criteria
- `McpServerConfig`'s required/non-required classification no longer depends on
  `security_profile`.
- `adr004_01` is closed or explicitly marked superseded, referencing this issue.
- ADR-004's Known Deviations entry for this gap is updated once implementation lands.

## Testing Expectations
- Add tests for the classification logic that verify identical classification results regardless
  of `security_profile`.
- Add a test for a non-required component's availability failure producing disable-and-continue
  behavior, and for a required component's unavailability producing Fail-Fast — both are
  currently unverified (see ADR-004 Verification section, INV-019/INV-020 gaps).
- Apply the standard validation sequence in `rules/toolchain.md`.

## Documentation Impact
Update ADR-004's Known Deviations (`ADR-004-D1-profile-config-model-still-present`) once this
lands. Close or update `adr004_01`.

## Out of Scope
- Defining which specific MCP servers are required vs. non-required (tracked in the companion
  Specification-gap issue).
- Redesigning MCP server startup retry/backoff behavior.

## Dependencies
Depends on `issues/20260831-192510_adr004_06_missing_component_criticality_specification.md`
(no current Specification defines per-component classification). Supersedes
`issues/20260831-173019_adr004_01_mcp_config_failure_model_alignment.md`.

## Unresolved Questions
- Whether `failure_policy`'s `disable-tool`/`degraded` values should be removed entirely now that
  disable-vs-abort is determined by required/non-required classification alone, or repurposed —
  needs an architecture-owner decision.
- Whether any `config/agent.toml` server entry currently sets `required_in_local` or a non-default
  `failure_policy` — needs confirmation before editing the config file.

## AI Implementation Instruction
Do not implement `adr004_01`'s original Implementation Intent (collapsing to unconditional
Fail-Fast). Read the current `docs/adr/ADR-004-environment-failure-handling-policy.md` Decision
Groups 3, 6, and 7 in full before making any code change here. Stop and ask if the required/
non-required classification for any specific component cannot be determined from an approved
Specification.
