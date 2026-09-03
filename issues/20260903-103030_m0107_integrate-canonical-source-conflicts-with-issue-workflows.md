# Integrate canonical-source conflicts with issue-management workflows

## Priority
Medium

## Summary
Define and implement deterministic routing from canonical-source analysis to Known Issues, Configuration Drift, Needs Confirmation, Canonical Source Conflict, or design-gap tracking.

## Background
Selecting a canonical source does not by itself resolve a discrepancy.

## Problem
A difference may represent an implementation bug, an intentional but undocumented deviation, configuration drift, missing design ownership, or unresolved intent. Without explicit routing rules, the same discrepancy may be duplicated across inventories or incorrectly resolved by editing a non-canonical document.

## Reason for Change
`M-01-01` through `M-01-06` establish how to identify a canonical source and detect a conflict, but not what happens after detection — without explicit routing, a detected conflict has no deterministic destination and risks silent suppression or duplicate tracking.

## Implementation Intent
Connect the canonical resolution model to the existing issue and uncertainty lifecycle without allowing silent conflict suppression or duplicate active records.

### Required routing rules

Implement and document at least the following routing:

- Adopted design differs from current code: Known Issue
- Canonical functional requirement differs from implementation: Known Issue
- Canonical Specification differs from its acceptance test: blocking Canonical Source Conflict or verification conflict
- Deployed configuration differs from approved operational configuration: Configuration Drift
- Claim intent cannot be determined: Needs Confirmation
- No canonical source exists for a required target and claim type: design or governance gap
- Multiple normative canonical sources exist for the same target and claim type: blocking Canonical Source Conflict
- Non-canonical document contains stale wording only: documentation correction task

## Target Files or Areas
- `docs/00_governance_01_documentation-policy.md`
- `docs/00_governance_03_issue-and-uncertainty-management.md`
- `docs/00_governance_04_documentation-checks.md`
- Known Issue templates
- Needs Confirmation templates
- Configuration Drift documentation or tracker integration
- Canonical Source Registry validator
- Pull request templates and merge checks

## Required Changes
1. Define each conflict category and its entry criteria.
2. Define one destination for each conflict category.
3. Prevent the same discrepancy from being independently active in multiple inventories.
4. Permit cross-references without duplicating the full issue.
5. Define severity and blocking behavior for Canonical Source Conflicts.
6. Define resolution criteria for each category.
7. Require evidence before a discrepancy is reclassified or removed.
8. Prevent documentation-only edits from closing design-versus-code conflicts unless required implementation evidence exists.
9. Align the workflow with the Current-Specification-Only policy for resolved items.
10. Update templates and validation rules.

### Required conflict record fields

For canonical conflicts, include at least:

- Conflict ID
- Decision target
- Claim type
- Canonical source
- Conflicting source or evidence
- Conflict category
- Impact
- Severity
- Blocking status
- Required action
- Owner
- Validation evidence

### Resolution rules

- A Known Issue is resolved only when implementation and adopted design agree, or when the adopted design is formally changed.
- Configuration Drift is resolved only when the deployed value and approved operational value agree, or when the approved value is formally changed.
- Needs Confirmation is removed only after evidence establishes the intended claim and the canonical source is updated.
- Canonical Source Conflict is resolved only when exactly one normative source remains registered for the target and claim type.
- A documentation correction is complete only when validation shows no stale conflicting statement remains.

## Constraints
Do not permit the same discrepancy to be independently active in more than one inventory (Known Issues, Needs Confirmation, Configuration Drift, Canonical Source Conflict) simultaneously — cross-reference instead of duplicating.

## Acceptance Criteria
- [ ] Every required conflict category has one defined destination.
- [ ] Design-versus-code differences route to Known Issues.
- [ ] Production-value differences route to Configuration Drift.
- [ ] Unknown intent routes to Needs Confirmation.
- [ ] Duplicate normative sources route to a blocking Canonical Source Conflict.
- [ ] Missing canonical ownership routes to a design or governance gap.
- [ ] Duplicate active records are prohibited or detected.
- [ ] Resolution criteria require evidence.
- [ ] Documentation-only changes cannot improperly close implementation conflicts.
- [ ] Resolved-item handling complies with the Current-Specification-Only policy.
- [ ] Templates and validators are updated.
- [ ] Workflow tests cover every required routing outcome.
- [ ] Documentation validation tests pass.

## Testing Expectations
Add workflow tests covering every required routing outcome listed above (8 categories); run `uv run python tools/check_docs_quality.py` and `uv run python tools/check_needs_confirmation_inventory.py` against updated templates.

## Documentation Impact
Yes — this issue's entire scope is the governance, Known Issue, Needs Confirmation, and PR-template documents listed in Target Files or Areas.

## Out of Scope
- Do not resolve all existing discrepancies in this issue.
- Do not introduce a new external issue tracker unless the repository already requires one.
- Do not change application runtime behavior.

## Dependencies
Depends on `M-01-01` through `M-01-06`.

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Confirm `M-01-01` through `M-01-06` have landed before implementing routing — this issue's categories reference the claim-type taxonomy, resolution algorithm, and registry validator those issues establish. Reuse the existing Known Issue and Needs Confirmation lifecycle definitions in `docs/00_governance_03_issue-and-uncertainty-management.md` rather than introducing a parallel tracking mechanism. Do not resolve any existing discrepancy as part of this issue — it defines routing rules only. Do not introduce a new external issue tracker unless the repository already requires one.
