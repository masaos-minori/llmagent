# Implementation Procedure: Resolve external-behavior canonical source conflict in governance_01

## Goal

Resolve the conflicting canonical-source definitions for the `external-behavior` claim type between the Resolution Matrix and the Decision Target Canonical Source Matrix in `governance_01_documentation-policy.md`.

## Scope

- Modify `governance_01_documentation-policy.md` to eliminate the duplicate canonical-source definition for `external-behavior`.
- If the Decision Target matrix's merging of "Requirements" and "External Behavior" is intentional, add explicit language stating this so the two matrices are not read as competing definitions.
- If the two matrices are meant to agree, correct the non-intended row.

## Assumptions

- The `### external-behavior` subsection definition ("Observable behavior of the system as experienced by external consumers") supports the Resolution Matrix interpretation (canonical source = Specification + Integration Test).
- The Decision Target matrix's merging of "Requirements" and "External Behavior" into one row may be intentional, but this needs confirmation from the governance owner.
- No additional files need modification beyond what is listed in the Plan's Implementation Target Files.

## Design decisions

- Prefer Approach 1 (correct the non-intended row) if the governance owner can confirm intent. The `### external-behavior` subsection text suggests the Resolution Matrix is closer to the intended definition.
- Use Approach 2 (add explicit language) if the Decision Target matrix is intentionally coarser. Add a note in the Policy clarifying this intent.
- Use Approach 3 (register a Canonical Source Conflict) as fallback if the governance owner's intent cannot be determined.

## Alternatives considered

- Leave both rows unchanged and rely on the `### external-behavior` subsection to resolve ambiguity — rejected because the Plan's Reason for change states that two conflicting definitions prevent deterministic resolution.
- Merge the two matrices into one unified table — rejected because out-of-scope per the Plan.

## Implementation

### Target file

`docs/00_governance/governance_01_documentation-policy.md`

### Procedure

1. Determine which approach to take based on available evidence:
   - Review git history of `governance_01_documentation-policy.md` to determine if the Decision Target matrix's merging of "Requirements" and "External Behavior" was intentional (UNK-01).
   - Review any related discussions or decisions that inform the governance owner's intent regarding Integration Test as canonical vs. auxiliary evidence for external-behavior (UNK-02).
2. Apply the chosen fix:
   - **Approach 1**: Correct the non-intended row in either the Resolution Matrix or the Decision Target Canonical Source Matrix.
   - **Approach 2**: Add explicit language in the Policy stating that the Decision Target matrix is intentionally coarser (merging Requirements and External Behavior).
   - **Approach 3**: Skip this file and defer to governance_03 Part 3 registration.
3. Verify both matrices are consistent after the edit — no remaining conflicts for `external-behavior`.

### Method

- Run `git log --oneline --diff-filter=M -- docs/00_governance/governance_01_documentation-policy.md` to identify commits that modified the Decision Target matrix.
- Cross-check against the `### external-behavior` subsection definition (line 72): "Observable behavior of the system as experienced by external consumers — inputs, outputs, side effects, and timing characteristics."
- Compare against the Resolution Matrix (line 122): canonical source kind = "Specification + Integration Test", auxiliary evidence = "Runtime Log, Test".
- Compare against the Decision Target Canonical Source Matrix (line 152): canonical = `docs/{area}_*_specification.md`, auxiliary evidence = "Acceptance Test".

### Details

The conflict is between:

| Location | Canonical source kind / Canonical | Auxiliary evidence |
|----------|-----------------------------------|---------------------|
| Resolution Matrix (line 122) | Specification + Integration Test | Runtime Log, Test |
| Decision Target Canonical Source Matrix (line 152) | `docs/{area}_*_specification.md` | Acceptance Test |

The `### external-behavior` subsection (line 72) defines external-behavior as "Observable behavior of the system as experienced by external consumers — inputs, outputs, side effects, and timing characteristics." This aligns more closely with the Resolution Matrix interpretation (Specification + Integration Test) than with the Decision Target matrix's merged "Requirements, External Behavior" row.

**Approach 1 — Correct the non-intended row:**
If the two matrices are meant to agree, identify which row is incorrect and fix it. Based on the `### external-behavior` subsection text, the Resolution Matrix appears closer to the intended definition. The Decision Target matrix row should be corrected to match, OR the Decision Target matrix should be split into separate "Requirements" and "External Behavior" rows.

**Approach 2 — Add explicit language:**
If the Decision Target matrix is intentionally coarser (merging Requirements and External Behavior), add a note in the Policy near the Decision Target Canonical Source Matrix header (around line 144-145) stating: "This matrix intentionally merges 'Requirements' and 'External Behavior' into a single row. For the authoritative canonical source for external-behavior claims, see the Resolution Matrix below."

**Approach 3 — Register a Canonical Source Conflict:**
If undecided, skip this file and register a Canonical Source Conflict in `governance_03` Part 3 following the format defined there (REQ-003; `docs/00_governance/governance_03_issue-and-uncertainty-management.md`).

## Compatibility considerations

N/A: documentation-only change. The change affects only the canonical-source definitions within the same Policy document.

## Security considerations

N/A: documentation-only change.

## Rollback considerations

Reverting the correction would restore the conflicting state. If an approach was incorrectly applied, revert the specific row or added language and re-evaluate the unknowns before applying a different approach.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/00_governance/governance_01_documentation-policy.md | Manual review of both matrices | Read both matrices side-by-side | No conflicting canonical-source definitions for `external-behavior` remain |

## Completion criteria

- One definitive canonical source definition for `external-behavior` exists across both matrices (AC-001).
- If the Decision Target matrix is intentionally coarser, the Policy explicitly states this (AC-002).
- Both matrices are consistent after the edit — no remaining conflicts for `external-behavior`.

## Out of scope

- Resolving conflicts for other claim types (architecture-decision, api-contract, etc.).
- Renaming or restructuring either matrix.
- Changing the scope of any other claim type's canonical source.
- Modifying `governance_03_issue-and-uncertainty-management.md` (covered by a separate row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Investigate git history and governance owner intent for UNK-01 and UNK-02 | Done | — | — | No evidence of intentional merge; Resolution Matrix closer to spec text |
| 2 | Apply the chosen fix (Approach 1, 2, or 3) | Done | — | — | Approach 1: split merged row |
| 3 | Verify both matrices are consistent after the edit | Done | — | — | Both matrices now have separate Requirements and External Behavior rows |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability

- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: issues/20261003-081533_gov001_resolve_external_behavior_canonical_source_conflict.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261003-145930_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261004-074833
- **Related target files**: docs/00_governance/governance_01_documentation-policy.md
