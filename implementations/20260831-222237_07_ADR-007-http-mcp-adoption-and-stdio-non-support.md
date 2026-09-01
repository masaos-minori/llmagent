# Implementation Procedure: ADR-007 Remove Deprecated Sections and Relocate Valid Requirements

## Goal

Remove `Migration and Rollout` and `Change History` sections from `docs/adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md`, relocate any still-valid requirement content, and reorder remaining sections to match the current 14-section standard.

## Scope

- Remove `Migration and Rollout` section (confirmed at line 330)
- Remove `Change History` section (confirmed at line 459)
- Relocate any still-valid requirements from those sections to appropriate current sections
- Reorder remaining sections to match the 14-section standard

## Assumptions

- The rg search results confirming Migration and Rollout at line 330 and Change History at line 459 are accurate
- Some content under these sections may qualify as still-valid requirements that must be preserved
- The three duplicate notes required across all ADRs are stable and will not change during this task

## Design decisions

- Process each statement under the deprecated sections individually: determine whether it is historical narrative (delete) or still-valid requirement (relocate)
- Relocate valid requirements to the most appropriate current section (Alternatives Considered, Consequences, Known Deviations, or Verification)
- Preserve the three duplicate notes required across all ADRs exactly as currently worded

## Alternatives considered

- Could batch all relocations into a single edit pass, but individual statement-by-statement analysis reduces risk of losing valid requirements
- Could normalize wording when relocating, but the plan requires preserving exact wording of duplicate notes

## Implementation

### Target file

`docs/adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md`

### Procedure

**Phase 1: Preparation**

1. Read `docs/adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md` in full
2. Read `docs/00_governance_01_documentation-policy.md` to know the correct 14-section order
3. Identify `Migration and Rollout` section boundaries (starts at line 330)
4. Identify `Change History` section boundaries (starts at line 459)

**Phase 2: Statement-by-statement analysis of `Migration and Rollout` section**

5. For each statement under `Migration and Rollout`:
   - Is it historical narrative (record of when a decision changed)? → Delete
   - Does it state a still-applicable requirement, constraint, invariant, rationale, or verification rule? → Relocate to appropriate current section (Alternatives Considered, Consequences, Known Deviations, or Verification)
6. Remove the `Migration and Rollout` section header and any purely historical content

**Phase 3: Statement-by-statement analysis of `Change History` section**

7. For each statement under `Change History`:
   - Is it historical narrative (record of when a decision changed)? → Delete
   - Does it state a still-applicable requirement, constraint, invariant, rationale, or verification rule? → Relocate to appropriate current section (Alternatives Considered, Consequences, Known Deviations, or Verification)
8. Remove the `Change History` section header and any purely historical content

**Phase 4: Section reordering**

9. Reorder remaining sections to match the current 14-section standard order: Context, Assumptions, Decision, Rationale, Alternatives Considered, Consequences, Invariants, Verification, Implementation Notes, Known Deviations, Review Triggers, Approval, Related Documents, Completion Checklist
10. Preserve internal reference text exactly; only move section headers and content blocks, not inline references

**Phase 5: Verification**

11. Verify no `Migration and Rollout` or `Change History` section headers remain
12. Verify each section appears in the standard 14-section order
13. Run `uv run python tools/check_docs_quality.py docs/adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md` and resolve errors
14. Run `uv run python tools/check_docs_structure.py docs/adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md` and resolve errors

### Method

Document-only modification: selective deletion of deprecated sections, content relocation, section reordering.

### Details

- Use exact string matching for section headers: `Migration and Rollout` (not just `Migration`) and `Change History`
- When relocating content, record per-ADR outcome explicitly (nothing lost / relocated / not applicable)
- Stop and report if ambiguity between historical narrative and still-valid requirement cannot be resolved
- Preserve the three duplicate notes required across all ADRs exactly as currently worded
- Do not alter the substance of the Decision, Rationale, Invariants, or Verification sections beyond section placement changes

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
| `docs/adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md` | Run documentation quality checks | `uv run python tools/check_docs_quality.py docs/adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md` | Exit code 0, no errors |
| `docs/adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md` | Run documentation structure validation | `uv run python tools/check_docs_structure.py docs/adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md` | Exit code 0, no errors |
| `docs/adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md` | Manual verification of section removal | Grep for `Migration and Rollout` / `Change History` | No matches found |
| `docs/adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md` | Manual verification of section ordering | Compare against 14-section standard | All sections in correct order |

## Completion criteria

- Neither `Migration and Rollout` nor `Change History` section headers exist in ADR-007
- Each section appears in the standard 14-section order
- Any requirement, constraint, invariant, rationale, or verification rule previously recorded under a removed section has been added to the appropriate current section — with the outcome recorded (nothing lost / relocated / not applicable)
- Documentation quality and structure checks pass with no errors

## Out of scope

- Modifying any other ADR file
- Changing any ADR's Decision, Rationale, Invariants, or Verification substance beyond relocating still-valid content
- Deleting, merging, or superseding any ADR
- Changing ADR Status values
- Modifying the four governance-policy documents themselves

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Preparation | Pending | — | — | |
| 2 | Phase 2: Analyze Migration and Rollout section | Pending | — | — | |
| 3 | Phase 3: Analyze Change History section | Pending | — | — | |
| 4 | Phase 4: Section reordering | Pending | — | — | |
| 5 | Phase 5: Verification | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003
- **Source issue**: issues/20260831-162016_adr001_section_standardization_update.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260831-222237_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260831-222237
- **Related target files**: docs/adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md
