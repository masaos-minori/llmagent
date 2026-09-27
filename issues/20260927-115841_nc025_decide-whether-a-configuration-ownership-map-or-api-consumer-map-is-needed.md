# Decide whether a Configuration Ownership Map or API Consumer Map is needed

## Priority
Low

## Summary
Obtain an owner decision on whether the existing Decision Target Canonical Source Matrix is sufficiently precise for configuration/API change-impact scoping, or whether a dedicated Configuration Ownership Map / API Consumer Map should be built, closing Needs Confirmation item NC-025.

## Background
`docs/00_governance/governance_01_documentation-policy.md`'s Change Impact Rule routes configuration/API changes to the existing Decision Target Canonical Source Matrix rather than a dedicated map. NC-025 records that no such dedicated map exists anywhere in the repository, and questions whether one is needed.

## Problem
This is a scoping/tooling-investment decision, not a fact that can be resolved by further code investigation — the existing matrix already functions today; the open question is whether it remains adequate as configuration/API surface grows.

## Reason for Change
Without an explicit decision, this question resurfaces every time someone notices its absence (as it has here), consuming review time on an already-considered trade-off. Recording the decision once, with its rationale, prevents repeated re-litigation.

## Implementation Intent
Present the owner with the trade-off: the existing general-purpose matrix has low maintenance cost but coarse granularity; a dedicated map would give per-config-key/per-endpoint ownership traceability at the cost of a new artifact to keep in sync. Do not build the map speculatively — only if the owner confirms current configuration/API change volume justifies it.

## Target Files or Areas
- `docs/00_governance/governance_01_documentation-policy.md` (Change Impact Rule, Decision Target Canonical Source Matrix)
- `docs/00_governance/governance_03_issue-and-uncertainty-management.md` (NC-025 entry)
- `config/documentation_canonical_sources.toml` (existing registry, for reference — a dedicated map, if built, would likely extend this rather than duplicate it)

## Required Changes
- Present the owner with the current state and the trade-off above.
- Record the owner's decision (build a dedicated map, or keep using the existing matrix) directly in `governance_01_documentation-policy.md`'s Change Impact Rule section, with the stated rationale.
- If the owner decides to build a dedicated map, file a new, separate issue for that implementation work — do not build it as part of resolving this decision issue.
- Remove NC-025 from Active Items once the decision is recorded.

## Constraints
N/A: this issue itself is a decision-recording task; any resulting map-building work is a separate, larger issue.

## Acceptance Criteria
- The owner's decision (build vs. keep current matrix) is recorded in `docs/00_governance/governance_01_documentation-policy.md`'s Change Impact Rule section, with rationale.
- NC-025 is removed from `docs/00_governance/governance_03_issue-and-uncertainty-management.md`'s Active Items.

## Testing Expectations
Not required: documentation/decision task, no behavior change.

## Documentation Impact
Update `docs/00_governance/governance_01_documentation-policy.md`'s Change Impact Rule section to record the decision and rationale. Remove the NC-025 entry from `docs/00_governance/governance_03_issue-and-uncertainty-management.md` once resolved.

## Out of Scope
- Building a Configuration Ownership Map or API Consumer Map — that is separate follow-up work if the owner decides it is warranted, not this issue's own scope.
- Any change to the existing Decision Target Canonical Source Matrix's content.

## Dependencies
N/A: none

## Unresolved Questions
N/A: none — the decision itself is this issue's entire content; there is no further investigation to perform first.

## AI Implementation Instruction
Do not build a Configuration Ownership Map or API Consumer Map as part of this issue, even if it seems like a reasonable next step — the owner's decision must come first. Record whichever decision is given, with its stated rationale, and stop there.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260927-115841
- **Related target files**: docs/00_governance/governance_01_documentation-policy.md
