# Resolve external-behavior canonical source conflict between Resolution Matrix and Decision Target Canonical Source Matrix

## Priority
Medium

## Summary
The `governance_01_documentation-policy.md` Policy contains two normative matrices that define conflicting canonical sources for the `external-behavior` claim type. The Resolution Matrix lists Integration Test as part of the canonical source, while the Decision Target Canonical Source Matrix lists Specification only and demotes Integration Test to auxiliary evidence. One decision target has two different canonical-source definitions, which violates the Policy's own Routing Rules ("multiple normative sources").

## Background
In `docs/00_governance/governance_01_documentation-policy.md`, the external-behavior claim type has different values in the two matrices:
- In `### Resolution Matrix` (line ~122), the canonical source kind is "Specification + Integration Test" and the auxiliary evidence is "Runtime Log, Test".
- In `### Decision Target Canonical Source Matrix` (line ~152), the "Requirements, External Behavior" row has canonical `docs/{area}_*_specification.md` and auxiliary evidence "Acceptance Test".

Both matrices are normative within the same Policy, so one Decision Target has two different canonical-source definitions. That is the condition the Policy's own Routing Rules call a "multiple normative sources" conflict. The `docsize001` Plan deliberately left both rows unchanged because neither row was directly edited.

The `### external-behavior` subsection definition ("Specification documents and integration tests") agrees with the Resolution Matrix, not with the Decision Target matrix. No ADR, Specification, or registry entry settles which definition is intended. The Decision Target matrix row also merges functional requirements and external behavior into one target, so it may be intentionally coarser rather than conflicting.

## Problem
A single claim type (`external-behavior`) has two competing canonical-source definitions within the same Policy document. This creates ambiguity for AI agents and humans who rely on these matrices to determine authoritative sources for external behavior claims.

## Reason for Change
When AI agents or developers encounter a discrepancy between observed external behavior and the specification, they need a clear answer about which artifact is authoritative. Two conflicting definitions prevent deterministic resolution.

## Implementation Intent
Determine which matrix row represents the intended definition for `external-behavior` canonical source. If the Decision Target matrix is intentionally coarser (merging Requirements and External Behavior), state that explicitly in the Policy so the two are not read as competing definitions. If the two matrices are meant to agree, correct the non-intended row.

## Target Files or Areas
- `docs/00_governance/governance_01_documentation-policy.md`
- `docs/00_governance/governance_03_issue-and-uncertainty-management.md` Part 3 (if registering a Canonical Source Conflict)

## Required Changes
- Determine whether Integration Test is part of the canonical source for external behavior, or only auxiliary evidence
- Correct the non-intended row if the two matrices are meant to agree
- If the Decision Target matrix is intentionally coarser, state that explicitly in the Policy
- If undecided, register a Canonical Source Conflict in `governance_03` Part 3 per the Policy's Routing Rules

## Constraints
- Do not change any other claim types or decision targets
- Preserve the existing table structure and column semantics
- Any correction must be consistent with the `### external-behavior` subsection definition

## Acceptance Criteria
- [ ] One definitive canonical source definition for `external-behavior` exists across both matrices
- [ ] If the Decision Target matrix is intentionally coarser, the Policy explicitly states this
- [ ] If a Canonical Source Conflict is registered, it follows the format defined in `governance_03` Part 3

## Testing Expectations
Not required — this is a documentation-only change. Manual review of both matrices after editing confirms consistency.

## Documentation Impact
This issue itself resolves a documentation inconsistency. After resolution, the Policy will have a single authoritative definition for the `external-behavior` claim type.

## Out of Scope
- Resolving conflicts for other claim types (architecture-decision, api-contract, etc.)
- Renaming or restructuring either matrix
- Changing the scope of any other claim type's canonical source

## Dependencies
- None — this is a self-contained documentation clarification task

## Unresolved Questions
- Is the Decision Target matrix's merging of "Requirements" and "External Behavior" intentional? If so, should the Policy explicitly state this?
- Does the governance owner consider Integration Test to be part of the canonical source for external behavior, or only auxiliary evidence?

## AI Implementation Instruction
1. Read both matrices in `governance_01_documentation-policy.md` (Resolution Matrix line ~122, Decision Target Canonical Source Matrix line ~152).
2. Identify which row defines the canonical source for `external-behavior` in each matrix.
3. Determine the intended definition based on the `### external-behavior` subsection text.
4. Apply the fix: either correct the non-intended row OR add explicit language stating the Decision Target matrix is intentionally coarser.
5. If undecided, register a Canonical Source Conflict in `governance_03` Part 3.
6. Do not modify any other claim types or matrix rows.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/done/20261001-112149_plan.md
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261003-081533
- **Related target files**: docs/00_governance/governance_01_documentation-policy.md, docs/00_governance/governance_03_issue-and-uncertainty-management.md
