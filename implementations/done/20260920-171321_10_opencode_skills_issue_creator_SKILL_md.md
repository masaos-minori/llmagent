## Goal
Update `.opencode/skills/issue-creator/SKILL.md`: replace cross-reference `Step 1.5` with `Step 2` in the Issue Filename Generation section.

## Scope
- **In-Scope**: Cross-reference update in `.opencode/skills/issue-creator/SKILL.md`
- **Out-of-Scope**: Modifying workflow.md section headings (handled in separate procedure), modifying SKILL.md Phase overview table (handled in separate procedure), modifying completed/historical files, modifying tool code

## Assumptions
- The workspace counterpart (`skills/issue-to-plan/SKILL.md`) receives identical changes via its own procedure document
- workflow.md section headings are already updated (or will be updated concurrently) before this change is validated

## Design decisions
- Sibling skill cross-references must point to the correct step number after renumbering
- Only the specific cross-reference needs updating — no other content in this file requires changes

## Alternatives considered
- Keeping decimal steps: rejected because inconsistent with project convention and causes cross-reference drift

## Implementation
### Target file
`.opencode/skills/issue-creator/SKILL.md`

### Procedure
1. Read the current file to identify the Step 1.5 cross-reference
2. Update cross-reference: `Step 1.5` → `Step 2`
3. Verify alignment with the referenced skill's own step numbering

### Method
Edit-based update of cross-reference. The cross-reference appears in prose text within the Issue Filename Generation section.

### Details
Current state (verified via repository evidence):
- Line 91: `detection in \`skills/issue-to-plan\` Step 1.5.`

Required changes:
1. Update cross-reference on line 91: `Step 1.5` → `Step 2`

## Compatibility considerations
- This cross-reference points to the `issue-to-plan` skill's step number; it must match after that skill's renumbering
- The workspace counterpart (`skills/issue-creator/SKILL.md`) should receive the same update but is not listed as a target file in this Plan — verify whether it also needs updating

## Security considerations
N/A: documentation-only change, no security impact

## Rollback considerations
Simple revert: restore original content via `git checkout -- .opencode/skills/issue-creator/SKILL.md`. No data loss risk.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| .opencode/skills/issue-creator/SKILL.md | Cross-reference verification | Read file for step number refs | Ref matches new number |

## Completion criteria
- [ ] Cross-reference `Step 1.5` → `Step 2` is updated
- [ ] No orphaned decimal step references remain in the file

## Out of scope
- Updating workflow.md section headings (separate procedure)
- Updating SKILL.md Phase overview table (separate procedure)
- Modifying completed/historical files

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20260920-191700 |  |
| 2 | Add or update tests per Validation plan | Completed | — | 20260920-191700 | Not applicable: documentation-only change |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20260920-191700 | Not applicable: documentation-only change |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20260920-191700 | Not applicable: this IS the documentation change |

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
- **Requirement ID**: REQ-005 (Sibling skill cross-references updated: `.opencode/skills/issue-creator/SKILL.md` references correct step number)
- **Source issue**: issues/20260920-164935_doc001_unify_decimal_step_numbers_to_integers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-170042_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260920-171321
- **Related target files**: .opencode/skills/issue-creator/SKILL.md