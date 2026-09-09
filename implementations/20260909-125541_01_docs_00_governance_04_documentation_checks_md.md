# Implementation Procedure: Add exemption decision to GV-021 row

## Goal

Record an explicit, reasoned decision for the auto-generated port/table exemption in `docs/00_governance_04_documentation-checks.md`'s GV-021 row.

## Scope

- **In-Scope**: Add exemption decision text to the GV-021 row in `docs/00_governance_04_documentation-checks.md`
- **Out-of-Scope**: Code changes to `check_docs_content_policy.py`; unit test creation

## Assumptions

- Option (b) is chosen: exempt the auto-generated, guard-commented block specifically while still removing hand-written port mentions elsewhere
- The exemption rationale should match where `docscope3`'s prior decision is already recorded

## Design decisions

- Exempt only the content between `<!-- AUTO-GENERATED -->` / `<!-- END AUTO-GENERATED -->` guard comments — not all tables
- Rationale: mechanically regenerated content is self-correcting; deleting it would break `tools/generate_reference_table.py --type mcp`'s output destination

## Alternatives considered

- Option (a): No exemption — would make `generate_reference_table.py --type mcp` have no valid output destination
- Option (c): Broaden to all tables — too general, conflicts with the narrow exemption principle

## Implementation

### Target file

`docs/00_governance_04_documentation-checks.md`

### Procedure

Add exemption decision text to the GV-021 row describing the auto-generated port table case.

### Method

Find the GV-021 row in `docs/00_governance_04_documentation-checks.md` and append the exemption decision alongside the existing description.

### Details

1. Locate the GV-021 row in `docs/00_governance_04_documentation-checks.md`:
   - Search for `GV-021` to find the governance check entry
   - Expected: Row exists with `check_docs_content_policy.py` entry and report-only/Warning status
2. Append the exemption decision text after the existing GV-021 description:
   - State option (b) choice explicitly
   - Record rationale: auto-generated content is self-correcting; deleting it breaks `generate_reference_table.py --type mcp`'s output destination
   - Note that the exemption is narrowly scoped to guard-commented blocks only
3. Verify the decision is explicit and reasoned (not a repeat of "pending exemption list")

## Compatibility considerations

- Existing governance checks remain unchanged
- The decision text does not alter tool behavior — it documents policy for downstream issues

## Security considerations

N/A: Documentation-only change

## Rollback considerations

- Revert the added text if the decision is revised later
- No code changes to revert

## Validation plan

Manual review: confirm the GV-021 row contains an explicit, reasoned decision for the auto-generated port table case (not "pending exemption list").

## Completion criteria

- GV-021 row in `docs/00_governance_04_documentation-checks.md` states an explicit, reasoned decision for the auto-generated port table case
- Decision includes rationale matching option (b) as stated in the Plan's Design section

## Out of scope

- Code changes to `check_docs_content_policy.py` (separate target file)
- Unit test creation (separate target file)
- Changes to `check_port_drift()`/`check_port_range_claim()` disposition (UNK-01, non-blocking)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Locate GV-021 row in docs/00_governance_04_documentation-checks.md | Pending | — | — | |
| 2 | Add exemption decision text to GV-021 row | Pending | — | — | |
| 3 | Verify decision is explicit and reasoned | Pending | — | — | |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20260905-153715_dcp001_port_number_exemption_policy_decision.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260908-210115_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260909-125541
- **Related target files**: docs/00_governance_04_documentation-checks.md
