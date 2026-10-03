# Implementation Procedure: Register Canonical Source Conflict in governance_03

## Goal

Register a Canonical Source Conflict entry in `governance_03_issue-and-uncertainty-management.md` Part 3 if the governance owner's intent cannot be determined and the conflict remains unresolved.

## Scope

- Add a new Canonical Source Conflict entry to Part 3 of `governance_03_issue-and-uncertainty-management.md` documenting the `external-behavior` canonical source conflict between the Resolution Matrix and the Decision Target Canonical Source Matrix in `governance_01_documentation-policy.md`.
- Only required if the governance owner's intent cannot be determined (UNK-01, UNK-02) and Approach 3 is selected.

## Assumptions

- The governance owner's intent regarding the Decision Target matrix's merging of "Requirements" and "External Behavior" cannot be determined from available evidence.
- Adding a Canonical Source Conflict entry to Part 3 is sufficient to track this unresolved conflict.
- No additional files need modification beyond what is listed in the Plan's Implementation Target Files.

## Design decisions

- Follow the existing Part 3 entry template exactly: 12 fields (ID, Decision target, Claim type, Canonical source, Conflicting source or evidence, Conflict category, Impact, Severity, Blocking status, Required action, Owner, Validation evidence).
- Use a sequential ID following the existing pattern in Part 3 (currently empty, so start with CSC-001).
- Set Blocking status to "Non-blocking" since the fallback mechanism (the `### external-behavior` subsection) provides some ambiguity resolution.

## Alternatives considered

- Leave the conflict untracked — rejected because the Plan's Reason for change states that two conflicting definitions prevent deterministic resolution.
- Resolve the conflict without governance owner input — rejected because the unknowns (UNK-01, UNK-02) require governance owner confirmation.

## Implementation

### Target file

`docs/00_governance/governance_03_issue-and-uncertainty-management.md`

### Procedure

1. Determine whether the governance owner's intent can be established (UNK-01, UNK-02). If yes, apply Approaches 1 or 2 instead and skip this file.
2. If the intent cannot be determined, add a new Canonical Source Conflict entry to Part 3:
   - Create a new section under "Active Items" following the Part 3 entry template.
   - Populate all 12 required fields based on the conflict details.
3. Verify the entry follows the Part 3 format definition.

### Method

- Review git history of `governance_01_documentation-policy.md` to determine if the Decision Target matrix's merging of "Requirements" and "External Behavior" was intentional (UNK-01).
- Review any related discussions or decisions that inform the governance owner's intent regarding Integration Test as canonical vs. auxiliary evidence for external-behavior (UNK-02).
- If the intent cannot be determined, construct the Canonical Source Conflict entry using the Part 3 template:

```markdown
#### CSC-001: external-behavior canonical source conflict

**Decision target**: External Behavior
**Claim type**: external-behavior
**Canonical source**: Specification + Integration Test (Resolution Matrix, line 122)
**Conflicting source or evidence**: docs/{area}_*_specification.md (Decision Target Canonical Source Matrix, line 152)
**Conflict category**: Multiple normative sources
**Impact**: Ambiguity for AI agents and humans relying on these matrices to determine authoritative sources for external behavior claims
**Severity**: Medium
**Blocking status**: Non-blocking
**Required action**: Obtain governance owner confirmation on the Decision Target matrix's intent
**Owner**: Unassigned
**Validation evidence**: None yet — pending governance owner response
```

### Details

The conflict is between:

| Location | Canonical source kind / Canonical | Auxiliary evidence |
|----------|-----------------------------------|---------------------|
| Resolution Matrix (line 122) | Specification + Integration Test | Runtime Log, Test |
| Decision Target Canonical Source Matrix (line 152) | `docs/{area}_*_specification.md` | Acceptance Test |

Both matrices are normative within the same Policy, creating a "multiple normative sources" conflict per the Policy's own Routing Rules. The `### external-behavior` subsection definition ("Observable behavior of the system as experienced by external consumers") agrees with the Resolution Matrix but not with the Decision Target matrix.

## Compatibility considerations

N/A: documentation-only change. The change adds a tracking entry to the existing Part 3 inventory.

## Security considerations

N/A: documentation-only change.

## Rollback considerations

Removing the Canonical Source Conflict entry after adding it would lose the tracking record. If the conflict is later resolved through Approaches 1 or 2, remove the entry per the Current-Specification-Only Policy (resolved entries are removed from the active inventory, not retained with a closed-out status).

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/00_governance/governance_03_issue-and-uncertainty-management.md | Format compliance check | Read Part 3 format definition and compare | Canonical Source Conflict entry matches the defined format (all 12 fields present) |

## Completion criteria

- A Canonical Source Conflict entry for `external-behavior` exists in Part 3 of `governance_03` (AC-003).
- All 12 required fields are populated correctly.
- The entry follows the Part 3 format definition.

## Out of scope

- Resolving the conflict itself (covered by the separate row for `governance_01`).
- Modifying the Resolution Matrix or Decision Target Canonical Source Matrix rows (covered by the separate row for `governance_01`).
- Adding entries for other claim types' canonical source conflicts.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm governance owner intent cannot be determined (UNK-01, UNK-02) | Pending | — | — | Prerequisite for this file |
| 2 | Add Canonical Source Conflict entry to Part 3 | Pending | — | — | |
| 3 | Validate format compliance | Pending | — | — | |

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
- **Requirement ID**: REQ-003
- **Source issue**: issues/20261003-081533_gov001_resolve_external_behavior_canonical_source_conflict.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261003-145930_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261004-074833
- **Related target files**: docs/00_governance/governance_03_issue-and-uncertainty-management.md
