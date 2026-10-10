# Fix issue-to-plan workflow: add missing Affected areas and Risks section generation instructions

## Priority
High

## Summary
The `issue-to-plan` workflow does not instruct the AI to generate two mandatory Plan sections (`Affected areas` and `Risks`), causing 4 of 6 generated plans to be structurally non-conformant. This issue adds the missing generation instructions and validation checks to the workflow.

## Background
Investigation of `plans/20261008-*_plan.md` revealed that 4 of 6 plans were missing `Affected areas` and `Risks` sections. Root cause analysis traced the gap to the `issue-to-plan` workflow: neither section has a generation instruction in Step 5 ("Create the Plan"), and `Affected areas` is absent from Step 8a's completeness verification list entirely.

## Problem
- `Affected areas`: No generation instruction in any workflow step; no validation in Step 8a. Path B analysis tools (`git churn`, `git-fame`, `pydeps`) exist but their results are never used to populate this table.
- `Risks`: Mapped in Step 4 but no explicit generation instruction in Step 5. Step 6 mentions Risk analysis but does not clarify whether it writes to the Plan's inline Risks section or a separate file.
- Result: 4 of 6 plans from 2026-10-08 are structurally non-conformant.

## Reason for Change
Plans that omit required sections cannot be reliably consumed by downstream phases (`plan-to-implementation-procedure`, `code-implementation`). The gap is a workflow defect, not an AI behavior problem — the AI follows the instructions given.

## Implementation Intent
Add generation instructions for both sections to Step 5, add validation for both to Step 8a, and clarify the relationship between Step 5 and Step 6 for Risks. Keep changes minimal — only add what is missing, do not restructure existing content.

## Target Files or Areas
- `skills/issue-to-plan/workflow.md` — Step 5 (Create the Plan) and Step 8a (Validate Information Completeness)
- `skills/issue-to-plan/SKILL.md` — Output format section (verify consistency)

## Required Changes
- Add `Affected areas` table generation instruction to Step 5:
  - For each Implementation Target Files row, assess: Change (Modify/Create/Delete), Blast Radius (Low/Medium/High), Churn (30d), Bus Factor, deploy.sh Impact
  - Path B: use `git-churn`, `git-fame`, `pydeps` results where available; mark N/A if tool unavailable
  - Path A: qualitative Blast Radius only; Churn/Bus Factor as N/A
- Add `Risks` section generation instruction to Step 5:
  - For each constraint and repository evidence finding, extract potential risks and pair with mitigations
  - Clarify that Step 5 generates the Risks section framework and Step 6 refines it (not a separate file)
- Add `Affected areas` to Step 8a's verification list:
  - Confirm each row's File is a subset of Implementation Target Files rows
  - Confirm all six columns (File, Change, Blast Radius, Churn (30d), Bus Factor, deploy.sh Impact) are populated or marked N/A
- Add `Risks` structural validation to Step 8a:
  - Confirm each Risk entry has a corresponding Mitigation
- Update SKILL.md Output format section if needed to reflect the same changes

## Constraints
- Do not restructure existing workflow steps — only append generation/validation instructions
- Do not change the template (`templates/plan.md`) — the template already defines these sections correctly
- Preserve existing Path A/B distinction — Path A gets qualitative assessment only
- Keep changes English-only (per issue-creator skill rules)

## Acceptance Criteria
- All 6 required columns in Affected areas table are generated for each Implementation Target Files row
- Each Risk entry in the Risks section has a corresponding Mitigation
- Step 8a verification list includes both Affected areas and Risks
- Generated plans conform to `templates/plan.md` for all required sections

## Testing Expectations
- Run `uv run python tools/check_workitem_structure.py --file <path>` against generated plans to verify structural conformance
- Manual review of generated plan to confirm all sections present

## Documentation Impact
- `skills/issue-to-plan/workflow.md` — updated with new generation/validation instructions
- `skills/issue-to-plan/SKILL.md` — may need minor update if Output format section references the workflow

## Out of Scope
- Adding new sections to `templates/plan.md`
- Changing the Path A/B classification criteria
- Modifying `templates/execution-status.md` or `templates/requirement-traceability.md`
- Fixing the 4 already-generated non-conformant plans (separate issue)

## Dependencies
- None — this is a standalone workflow fix

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Constrain changes to appending instructions only — do not rewrite existing text. Verify each addition against `templates/plan.md` to ensure alignment. After editing, run `uv run python tools/check_workitem_structure.py --file <any existing plan>` to confirm the tool still passes (it should, since the template hasn't changed).

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261010-173854
- **Related target files**: `skills/issue-to-plan/workflow.md`, `skills/issue-to-plan/SKILL.md`
