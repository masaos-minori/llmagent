## Goal
Update the `issue-to-plan` skill's SKILL.md: replace Phase overview table row `1.5 | Check for Existing Plans` with `2 | Check for Existing Plans`, shift all subsequent rows +1, and update cross-reference `detection via Step 1.5` → `detection via Step 2`.

## Scope
- **In-Scope**: Phase overview table row update, cross-reference update in `skills/issue-to-plan/SKILL.md`
- **Out-of-Scope**: Modifying workflow.md section headings (handled in separate procedure), modifying completed/historical files, modifying tool code

## Assumptions
- The `.opencode/skills/` mirror will receive identical changes via a separate procedure document
- workflow.md section headings are already updated (or will be updated concurrently) before this change is validated

## Design decisions
- Phase overview table must stay synchronized with workflow.md section headings
- Cross-references within the skill must point to the correct step number after renumbering

## Alternatives considered
- Keeping decimal steps: rejected because inconsistent with project convention and causes cross-reference drift

## Implementation
### Target file
`skills/issue-to-plan/SKILL.md`

### Procedure
1. Read the current file to identify Phase overview table and cross-references
2. Update Phase overview table: replace row `1.5 | Check for Existing Plans` with `2 | Check for Existing Plans`; shift all subsequent rows +1
3. Update cross-reference: `detection via Step 1.5` → `detection via Step 2`
4. Verify alignment with workflow.md section headings

### Method
Edit-based update of Phase overview table row and cross-reference. The Phase overview table uses Markdown table format — each row must maintain proper column alignment.

### Details
Current state (verified via repository evidence):
- Line 32: `detection via Step 1.5.`
- Phase overview table lines ~36-50: contains rows for Steps 0–10
- Routing section references `Step 3's classification` which maps to the old Step 3 (now Step 4)

Required changes:
1. Replace Phase overview table row: `| 1.5 | Check for Existing Plans | ... |` → `| 2 | Check for Existing Plans | ... |`
2. Shift all subsequent Phase overview table rows +1: `| 2 |` → `| 3 |`, `| 3 |` → `| 4 |`, ..., `| 10 |` → `| 11 |`
3. Update cross-reference on line 32: `detection via Step 1.5` → `detection via Step 2`
4. Update Routing section reference: `Step 3's classification` → `Step 4's classification`
5. Update Routing section reference: `Step 3's direct-verification inspection` → `Step 4's direct-verification inspection`
6. Update Routing section reference: `establish the Step 6-equivalent validation quality baseline` → `establish the Step 7-equivalent validation quality baseline`
7. Update Routing section reference: `Steps 6-10 run unconditionally` → `Steps 7-11 run unconditionally`
8. Update Core Execution Rules reference: `see \`workflow.md\` Step 10` → `see \`workflow.md\` Step 11`

## Compatibility considerations
- This file's Phase overview table must align with workflow.md section headings; both are updated as part of the same overall task
- Downstream consumers reading this skill's description will expect consistent step numbering
- The Routing section's step references must also be updated

## Security considerations
N/A: documentation-only change, no security impact

## Rollback considerations
Simple revert: restore original content via `git checkout -- skills/issue-to-plan/SKILL.md`. No data loss risk.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| skills/issue-to-plan/SKILL.md | Phase overview table verification | Read SKILL.md Phase overview table | Consecutive integers 0–11, no gaps |
| skills/issue-to-plan/SKILL.md | Cross-reference consistency | Read SKILL.md for step number refs | All refs match new numbers |

## Completion criteria
- [ ] Phase overview table has consecutive integers 0–11 with no gaps
- [ ] Row `2 | Check for Existing Plans` replaces the old `1.5` row
- [ ] Cross-reference `detection via Step 1.5` → `detection via Step 2` is updated
- [ ] Routing section step references updated (Step 3→4, Step 6→7, Steps 6-10→7-11)
- [ ] Core Execution Rules step reference updated (Step 10→11)
- [ ] Phase overview table alignment with workflow.md section headings confirmed

## Out of scope
- Updating workflow.md section headings (separate procedure)
- Updating `.opencode/skills/` mirror (separate procedure)
- Updating sibling skill cross-references (separate procedure)
- Modifying completed/historical files

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20260920-185120 |  |
| 2 | Add or update tests per Validation plan | Completed | — | 20260920-185120 | Not applicable: documentation-only change |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20260920-185120 | Not applicable: documentation-only change |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20260920-185120 | Not applicable: this IS the documentation change |

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
- **Requirement ID**: REQ-003 (Phase overview tables have consecutive integer step numbers with no gaps); REQ-004 (All cross-references within skill files are consistent after changes)
- **Source issue**: issues/20260920-164935_doc001_unify_decimal_step_numbers_to_integers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-170042_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260920-171321
- **Related target files**: skills/issue-to-plan/SKILL.md