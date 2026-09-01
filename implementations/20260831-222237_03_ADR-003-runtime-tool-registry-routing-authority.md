# Implementation Procedure: ADR-003 Read-only Check

## Goal

Confirm that `docs/adr/ADR-003-runtime-tool-registry-routing-authority.md` does not contain `Migration and Rollout` or `Change History` sections. No modification required if confirmed.

## Scope

- Verify ADR-003 conforms to the current 14-section ADR standard by confirming absence of deprecated sections

## Assumptions

- The rg search result ("neither section found via rg") is accurate and complete
- If neither section exists, no further action is needed for this ADR

## Design decisions

- Read-only verification approach since the plan's Implementation Target Files table marks this as "Read-only check"
- No content relocation needed if sections are absent

## Alternatives considered

- Could read the entire ADR file to verify full section structure, but the plan scope is limited to checking for two specific deprecated sections

## Implementation

### Target file

`docs/adr/ADR-003-runtime-tool-registry-routing-authority.md`

### Procedure

**Phase 1: Verification**

1. Read `docs/adr/ADR-003-runtime-tool-registry-routing-authority.md` in full
2. Search for `Migration and Rollout` section header — confirm none exists
3. Search for `Change History` section header — confirm none exists
4. If either section is found, proceed with removal and content relocation per Phase 2 below; if neither is found, mark as conformant and move on

**Phase 2: Content relocation (only if deprecated sections are found)**

5. For any content under `Migration and Rollout`: decide whether it states a still-applicable requirement, constraint, invariant, rationale, or verification rule (relocate to appropriate current section) or is purely historical narrative (delete)
6. For any content under `Change History`: decide whether it states a still-applicable requirement, constraint, invariant, rationale, or verification rule (relocate to appropriate current section) or is purely historical narrative (delete)
7. Remove the section headers and any purely historical content
8. Reorder remaining sections to match the current 14-section standard where they are out of order

### Method

Document-only read-only verification. If deprecated sections are found, apply the same modification procedure as other ADRs requiring changes.

### Details

- Use exact string matching for section headers: `Migration and Rollout` (not just `Migration`) and `Change History`
- When relocating content, preserve the three duplicate notes required across all ADRs exactly as currently worded
- Do not alter the substance of the Decision, Rationale, Invariants, or Verification sections beyond section placement changes
- Record per-ADR outcome explicitly (nothing lost / relocated / not applicable)

## Compatibility considerations

- None applicable; documentation-only change
- No behavioral changes; structural alignment with governance policy

## Security considerations

- None applicable; documentation-only change

## Rollback considerations

- All changes are reversible via git revert if issues arise
- No data loss risk since no content is deleted without careful review

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/adr/ADR-003-runtime-tool-registry-routing-authority.md` | Manual grep for deprecated sections | `rg 'Migration and Rollout' docs/adr/ADR-003-runtime-tool-registry-routing-authority.md` | No matches found |
| `docs/adr/ADR-003-runtime-tool-registry-routing-authority.md` | Manual grep for deprecated sections | `rg 'Change History' docs/adr/ADR-003-runtime-tool-registry-routing-authority.md` | No matches found |

## Completion criteria

- Confirmed that neither `Migration and Rollout` nor `Change History` section headers exist in ADR-003
- If either was found and corrected, verified that no requirement content was lost during relocation

## Out of scope

- Modifying any ADR's Decision, Rationale, Invariants, or Verification substance beyond section relocation
- Deleting, merging, or superseding any ADR
- Changing ADR Status values
- Modifying the four governance-policy documents themselves

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Verification | Pending | — | — | |
| 2 | Phase 2: Content relocation (if needed) | Pending | — | — | |

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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20260831-162016_adr001_section_standardization_update.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260831-222237_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260831-222237
- **Related target files**: docs/adr/ADR-003-runtime-tool-registry-routing-authority.md
