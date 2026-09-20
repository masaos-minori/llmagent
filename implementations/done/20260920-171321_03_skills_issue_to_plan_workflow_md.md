## Goal
Replace decimal step number Step 1.5 with integer Step 2 in the `issue-to-plan` skill's workflow.md, shifting all subsequent steps +1 (Steps 2→3 through 10→11).

## Scope
- **In-Scope**: Renumbering Step 1.5 → Step 2 and shifting Steps 2→3 through 10→11 throughout `skills/issue-to-plan/workflow.md`
- **Out-of-Scope**: Modifying SKILL.md Phase overview table (handled in separate procedure), modifying completed/historical files, modifying tool code

## Assumptions
- The `.opencode/skills/` mirror will receive identical changes via a separate procedure document
- No other files outside the listed target files contain references requiring updates within this single-file change

## Design decisions
- Insert the decimal step into the integer sequence by shifting all subsequent steps +1, maintaining sequential numbering without gaps
- This is a mechanical renaming task — no behavioral or architectural implications

## Alternatives considered
- Keeping decimal steps: rejected because inconsistent with project convention and causes cross-reference drift
- Adding a new intermediate step between existing integers: would still leave decimal numbering inconsistency

## Implementation
### Target file
`skills/issue-to-plan/workflow.md`

### Procedure
1. Read the current file to identify all step headings and cross-references
2. Apply renumbering cascade: Step 1.5 → Step 2, Step 2 → Step 3, Step 3 → Step 4, Step 4 → Step 5, Step 5 → Step 6, Step 6 → Step 7, Step 7 → Step 8, Step 8 → Step 9, Step 9 → Step 10, Step 10 → Step 11
3. Update all internal cross-references to step numbers within the file
4. Verify Phase overview table alignment (if present in this file)

### Method
Edit-based renumbering of section headings and cross-references. Each heading `## Step X:` must be updated to `## Step Y:` where Y = X+1 for X >= 2, and `## Step 1.5:` becomes `## Step 2:`. All prose references to step numbers (e.g., "see workflow.md Step 2") must also be updated.

### Details
Current state (verified via repository evidence):
- Line 101: `## Step 1.5: Check for Existing Plans`
- Lines 123+: `## Step 2:` through `## Step 10:` headings exist
- Cross-references to step numbers appear in prose throughout the file

Required changes:
1. Rename `## Step 1.5: Check for Existing Plans` → `## Step 2: Check for Existing Plans`
2. Rename `## Step 2: Assess the Current Issue` → `## Step 3: Assess the Current Issue`
3. Rename `## Step 3: Inspect related files` → `## Step 4: Inspect related files`
4. Rename `## Step 4: Map Issue information to Plan information` → `## Step 5: Map Issue information to Plan information`
5. Rename `## Step 5: Create the Plan` → `## Step 6: Create the Plan`
6. Rename `## Step 6: Analyze Unknowns and Risks` → `## Step 7: Analyze Unknowns and Risks`
7. Rename `## Step 7: Add Traceability` → `## Step 8: Add Traceability`
8. Rename `## Step 8: Validate information completeness` → `## Step 9: Validate information completeness`
9. Rename `## Step 9: Final validation` → `## Step 10: Final validation`
10. Rename `## Step 10: Move the Issue` → `## Step 11: Move the Issue`
11. Update all internal cross-references in descending order to prevent cascading: "Step 10" → "Step 11", "Step 9" → "Step 10", ..., "Step 2" → "Step 3", "Step 1.5" → "Step 2"
12. Update sub-step references in descending order: e.g., "Step 10a" → "Step 11a", ..., "Step 2a" → "Step 3a", "Step 1.5" → "Step 2"
13. Update Execution Status table row numbers (if present)
14. Update any remaining step number references in prose text

## Compatibility considerations
- Downstream consumers of this skill (`issue-to-plan` workflow) will read step numbers from this file; all references must be consistent after changes
- The Phase overview table in `SKILL.md` is handled separately but must remain aligned
- Prompt file `prompts/01_issue-to-plan.md` is handled separately but must remain aligned

## Security considerations
N/A: documentation-only change, no security impact

## Rollback considerations
Simple revert: restore original step numbers via `git checkout -- skills/issue-to-plan/workflow.md`. No data loss risk.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| skills/issue-to-plan/workflow.md | Manual review of numbering consistency | `rg "Step [0-9]+\.[0-9]+" skills/issue-to-plan/workflow.md` | Zero decimal step matches |
| skills/issue-to-plan/workflow.md | Phase overview table alignment | Read file Phase overview table if present | Consecutive integers 2–11, no gaps |
| skills/issue-to-plan/workflow.md | Cross-reference consistency | Read file prose for step number refs | All refs match new numbers |

## Completion criteria
- [ ] No decimal step numbers remain in `skills/issue-to-plan/workflow.md`
- [ ] Phase overview table has consecutive integers starting from 2 (no gap at 1→2 transition)
- [ ] All cross-references within the file are consistent with new numbering
- [ ] Execution Status table rows reflect new step numbers

## Out of scope
- Updating SKILL.md Phase overview table (separate procedure)
- Updating `.opencode/skills/` mirror (separate procedure)
- Updating sibling skill cross-references (separate procedure)
- Updating prompt file (separate procedure)
- Modifying completed/historical files

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20260920-190933 |  |
| 2 | Add or update tests per Validation plan | Completed | — | 20260920-190933 | Not applicable: documentation-only change |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20260920-190933 | Not applicable: documentation-only change |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20260920-190933 | Not applicable: this IS the documentation change |

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
- **Requirement ID**: REQ-002 (No decimal step numbers remain in `skills/issue-to-plan/` directory); REQ-003 (Phase overview tables have consecutive integer step numbers with no gaps)
- **Source issue**: issues/20260920-164935_doc001_unify_decimal_step_numbers_to_integers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-170042_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260920-171321
- **Related target files**: skills/issue-to-plan/workflow.md