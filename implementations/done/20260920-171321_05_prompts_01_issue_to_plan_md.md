## Goal
Update `prompts/01_issue-to-plan.md`: replace `#### Step 1.5:` heading with `#### Step 2:`, and update cross-reference `workflow.md` Step 1.5 → `workflow.md` Step 2.

## Scope
- **In-Scope**: Heading and cross-reference update in `prompts/01_issue-to-plan.md`
- **Out-of-Scope**: Modifying workflow.md section headings (handled in separate procedure), modifying SKILL.md Phase overview table (handled in separate procedure), modifying completed/historical files, modifying tool code

## Assumptions
- The `.opencode/skills/` mirror does not contain a copy of this prompt file (it is not under `.opencode/skills/`)
- workflow.md section headings are already updated (or will be updated concurrently) before this change is validated

## Design decisions
- Prompt file must stay aligned with the skill's own step numbering
- Both the heading and the prose cross-reference must be updated together

## Alternatives considered
- Keeping decimal steps: rejected because inconsistent with project convention and causes cross-reference drift

## Implementation
### Target file
`prompts/01_issue-to-plan.md`

### Procedure
1. Read the current file to identify the Step 1.5 heading and cross-references
2. Update heading: `#### Step 1.5: Check for existing plans` → `#### Step 2: Check for existing plans`
3. Update cross-reference: `workflow.md` Step 1.5 → `workflow.md` Step 2
4. Verify alignment with skill's own step numbering

### Method
Edit-based update of heading and cross-reference. The prompt file uses Markdown heading format.

### Details
Current state (verified via repository evidence):
- Line 65: `#### Step 1.5: Check for existing plans`
- Line 67: `Follow \`skills/issue-to-plan/workflow.md\` Step 1.5 in full.`

Required changes:
1. Rename heading: `#### Step 1.5: Check for existing plans` → `#### Step 2: Check for existing plans`
2. Update cross-reference on line 67: `workflow.md` Step 1.5 → `workflow.md` Step 2

## Compatibility considerations
- This prompt file is consumed by AI agents during issue-to-plan execution; step numbers must match the skill's own numbering
- The skill's SKILL.md and workflow.md are updated separately but must remain aligned

## Security considerations
N/A: documentation-only change, no security impact

## Rollback considerations
Simple revert: restore original content via `git checkout -- prompts/01_issue-to-plan.md`. No data loss risk.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| prompts/01_issue-to-plan.md | Heading verification | Read file for step heading | Step 2 heading present, no Step 1.5 |
| prompts/01_issue-to-plan.md | Cross-reference consistency | Read file for step number refs | Ref matches new number |

## Completion criteria
- [ ] Heading `#### Step 2: Check for existing plans` replaces the old `#### Step 1.5:` heading
- [ ] Cross-reference `workflow.md` Step 1.5 → `workflow.md` Step 2 is updated
- [ ] No orphaned decimal step references remain in the file

## Out of scope
- Updating workflow.md section headings (separate procedure)
- Updating SKILL.md Phase overview table (separate procedure)
- Updating `.opencode/skills/` mirror (not applicable — not under that directory)
- Modifying completed/historical files

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20260920-191057 |  |
| 2 | Add or update tests per Validation plan | Completed | — | 20260920-191057 | Not applicable: documentation-only change |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20260920-191057 | Not applicable: documentation-only change |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20260920-191057 | Not applicable: this IS the documentation change |

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
- **Requirement ID**: REQ-006 (Prompt file updated: `prompts/01_issue-to-plan.md` references correct step number)
- **Source issue**: issues/20260920-164935_doc001_unify_decimal_step_numbers_to_integers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-170042_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260920-171321
- **Related target files**: prompts/01_issue-to-plan.md