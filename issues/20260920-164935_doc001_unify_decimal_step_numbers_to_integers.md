# Unify decimal step numbers to integers in code-implementation and issue-to-plan skills

## Priority
Medium

## Summary
Replace all decimal step numbers (Step X.Y) with integer step numbers in the `code-implementation` and `issue-to-plan` skill definitions, ensuring SKILL.md, workflow.md, prompts, and cross-skill references are consistent after renumbering.

## Background
Both `code-implementation` and `issue-to-plan` skills use decimal step numbers for intermediate steps inserted between existing numbered steps:
- `code-implementation`: Step 2.5 (Pre-execution Stale Detection), positioned between Step 2 and Step 3
- `issue-to-plan`: Step 1.5 (Check for Existing Plans), positioned between Step 1 and Step 2

These decimal numbers were introduced as lightweight additions without renumbering subsequent steps. However, decimal step numbering creates inconsistency across the project's workflow documents and makes cross-references harder to maintain.

## Problem
Decimal step numbers cause several problems:
1. Inconsistent numbering conventions across the project (other workflows use integer steps exclusively)
2. Cross-reference drift — every reference to `workflow.md` Step X.Y must be updated alongside the step itself, but SKILL.md, prompts, and other skills also contain these references
3. Phase overview tables in SKILL.md files also contain decimal step entries that must stay synchronized with workflow.md
4. The `.opencode/skills/` directory mirrors the workspace skills and contains identical decimal step references

## Reason for Change
The project has accumulated multiple decimal step references (100+ occurrences across completed files as historical records). While completed files should not be modified per policy, the active skill definitions must be cleaned up to prevent future confusion and reduce maintenance burden for new contributors and AI agents.

## Implementation Intent
For each skill, insert the decimal step into the integer sequence by shifting all subsequent steps +1. Update all cross-references within the skill's own files (SKILL.md + workflow.md) and any sibling skills that reference these steps.

### code-implementation: Step 2.5 → Step 3 (shift Steps 3→4, 4→5, 5→6, 6→7, 7→8)

### issue-to-plan: Step 1.5 → Step 2 (shift Steps 2→3, 3→4, ..., 10→11)

## Target Files or Areas
- `skills/code-implementation/workflow.md`
- `skills/code-implementation/SKILL.md`
- `skills/issue-to-plan/workflow.md`
- `skills/issue-to-plan/SKILL.md`
- `prompts/01_issue-to-plan.md`
- `.opencode/skills/code-implementation/workflow.md`
- `.opencode/skills/code-implementation/SKILL.md`
- `.opencode/skills/issue-to-plan/workflow.md`
- `.opencode/skills/issue-to-plan/SKILL.md`
- `.opencode/skills/issue-creator/SKILL.md`

## Required Changes

### code-implementation skill
1. Renumber Step 2.5 to Step 3; shift Steps 3→4, 4→5, 5→6, 6→7, 7→8 throughout `workflow.md`
2. Update Phase overview table in `SKILL.md`: replace row `2.5 | Pre-execution stale detection` with `3 | Pre-execution stale detection`; shift all subsequent rows +1
3. Update cross-reference in `SKILL.md`: `workflow.md` Step 2.5 → `workflow.md` Step 3
4. Apply same changes to `.opencode/skills/code-implementation/` mirror

### issue-to-plan skill
1. Renumber Step 1.5 to Step 2; shift Steps 2→3, 3→4, 4→5, 5→6, 6→7, 7→8, 8→9, 9→10, 10→11 throughout `workflow.md`
2. Update Phase overview table in `SKILL.md`: replace row `1.5 | Check for Existing Plans` with `2 | Check for Existing Plans`; shift all subsequent rows +1
3. Update cross-reference in `SKILL.md`: `detection via Step 1.5` → `detection via Step 2`
4. Update `prompts/01_issue-to-plan.md`: `#### Step 1.5:` → `#### Step 2:`; `workflow.md` Step 1.5 → `workflow.md` Step 2
5. Update cross-reference in `.opencode/skills/issue-creator/SKILL.md`: `Step 1.5` → `Step 2`
6. Apply same changes to `.opencode/skills/issue-to-plan/` mirror

## Constraints
- Do NOT modify completed/historical files (`plans/done/`, `issues/done/`, `implementations/done/`) — they are historical records
- Tool code (`tools/manage_workitem_stage.py` etc.) does not contain decimal step references and requires no changes
- After renumbering, verify Phase overview tables in both SKILL.md files match their corresponding workflow.md sections exactly
- Verify all internal cross-references within each skill's files are consistent after changes

## Acceptance Criteria
- [ ] No decimal step numbers remain in `skills/code-implementation/` or `skills/issue-to-plan/` directories
- [ ] Phase overview tables in both SKILL.md files have consecutive integer step numbers with no gaps
- [ ] All cross-references within skill files (SKILL.md ↔ workflow.md) are consistent
- [ ] Sibling skill cross-references updated: `.opencode/skills/issue-creator/SKILL.md` references correct step number
- [ ] Prompt file updated: `prompts/01_issue-to-plan.md` references correct step number
- [ ] `.opencode/skills/` mirror matches workspace skills in all step numbers and cross-references

## Testing Expectations
- Manual review of all changed files for numbering consistency
- Verify Phase overview tables in SKILL.md match workflow.md section headings
- Verify no orphaned decimal step references remain in the two skill directories

## Documentation Impact
This issue IS the documentation change. No additional documentation updates required beyond the changes listed here.

## Out of Scope
- Modifying completed/historical files in `plans/done/`, `issues/done/`, `implementations/done/`
- Modifying tool code (no decimal step references exist there)
- Renaming or restructuring the decimal step concept itself (only renumbering, not renaming)

## Dependencies
N/A: none

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Follow these constraints strictly:
1. Only modify files listed under "Target Files or Areas" — do not touch any other files
2. For each skill, apply the full renumbering cascade (insert decimal step into integer sequence, shift all subsequent steps +1) — do not skip any step number update
3. Always update Phase overview tables in SKILL.md simultaneously with workflow.md changes
4. Update cross-references in sibling skills (.opencode/skills/issue-creator/SKILL.md) and prompts (01_issue-to-plan.md)
5. Mirror all workspace changes to .opencode/skills/ counterparts
6. After changes, verify: no decimal step numbers remain in either skill directory, Phase overview tables have consecutive integers, all cross-references are consistent
7. Do not attempt to modify historical files even if they contain old decimal step references

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260920-164935
- **Related target files**: skills/code-implementation/, skills/issue-to-plan/, prompts/01_issue-to-plan.md, .opencode/skills/
