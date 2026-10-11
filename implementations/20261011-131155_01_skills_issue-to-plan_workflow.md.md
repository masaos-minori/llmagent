## Goal
- Implement `REQ-001` to `REQ-004` and `REQ-006` of `plans/20261011-130139_plan.md` in `skills/issue-to-plan/workflow.md`: make Step 5 generate the Plan's `Affected areas` and `Risks` sections, and make Step 8a verify both, by appending text only.

## Scope
- Add two bullets to Step 5 "Generate the Plan" (`REQ-001`: Affected areas generation; `REQ-002`: Risks generation and the Step 5 / Step 6 relationship).
- Add two verification paragraphs to Step 8a (`REQ-003`: Affected areas check; `REQ-004`: Risk-to-Mitigation check), plus one appended sentence to that step's "Completed when" paragraph.
- Keep all existing text, headings, and step numbering unchanged (`REQ-006`).

## Assumptions
- Step 3 of the workflow classifies this work as Path A, so the Path A / Path B rules only describe how a future Plan fills the table; no Path B analysis is run for this change.
- `skills/issue-to-plan/SKILL.md` needs no edit (`REQ-005`); the Output format there already requires the full `templates/plan.md` structure. If review finds an inconsistency, that is an additional target file discovery and the Plan must be amended first.
- The Change values `Modify / Create / Delete` and the Blast Radius levels `Low / Medium / High` from the source issue are used as qualitative labels (Plan Unknowns UNK-01 and UNK-02, both non-blocking); `skills/DESIGN.md` is not edited.
- Verified against current content: Step 5's `Implementation Target Files` / `Reference Files` bullet is followed by the "Every claim must be backed by evidence" bullet, and Step 8a currently has three paragraphs followed by a "Completed when" paragraph.

## Design decisions
- Append, do not rewrite: new bullets and paragraphs are inserted at fixed anchors; no existing sentence is edited except by appending one sentence to Step 8a's "Completed when" paragraph.
- Refer to `templates/plan.md` ("Notes on filling Affected areas") and `skills/DESIGN.md` Change-impact table for column definitions and `deploy.sh Impact` values instead of copying them, so the workflow cannot drift from the canonical definitions.
- State the Risks relationship in Step 5 and point to Step 6, leaving Step 6's text untouched; this restates Step 6's existing rule (separate `risks.md` only for an incompletely mitigated Risk) without changing it.
- Reuse the Plan's own wording for the Path A / Path B split so it matches the existing "Path A: skip ... analysis" paragraphs in Step 5.

## Alternatives considered
- Put the Affected areas instruction in Step 3 or Step 4 instead of Step 5: rejected, because Step 3 is inspection and Step 4 is mapping; Plan generation belongs to Step 5 and the issue asks for Step 5.
- Edit Step 6 to say it refines the inline Risks section: rejected, because the issue constrains the change to appending and Step 6 already describes the separate-file rule; a Step 5 sentence is enough.
- Also edit `templates/plan.md` to restate the generation rules: rejected, because the template already defines both sections and is out of scope.

## Implementation
### Target file
`skills/issue-to-plan/workflow.md`

### Procedure
1. Re-read Step 5 "Generate the Plan" and Step 8a so the anchors below are confirmed against the current file.
2. In Step 5, directly after the bullet that begins "Populate `Implementation Target Files` and `Reference Files`" and before the bullet "Every claim must be backed by evidence", insert the two bullets given under Details (Affected areas, then Risks).
3. In Step 8a, after the paragraph "Verify every Requirement ID is traceable ..." and before the "**Completed when**" paragraph, insert the two paragraphs given under Details.
4. Append the one sentence given under Details to the end of Step 8a's "**Completed when**" paragraph.
5. Check that the diff contains only added lines, that no heading or step number changed, and that `skills/issue-to-plan/SKILL.md` was not edited.

### Method
- Use the Edit tool with an `old_string` that is the unchanged anchor line(s) and a `new_string` that is the same anchor plus the added text, so nothing existing is deleted or reworded.
- Write the added text in English, wrapped near the file's existing line width, in the same bullet and paragraph style as the surrounding steps.
- Do not copy column definitions or value lists; name `templates/plan.md` and `skills/DESIGN.md` instead.

### Details
Bullet 1, inserted in Step 5 (Affected areas):

> - Generate the `Affected areas` table per `templates/plan.md`: one row for every `Implementation Target Files` row, so that the `File` column is a subset of those rows, with all six columns populated (`File`, `Change`, `Blast Radius`, `Churn (30d)`, `Bus Factor`, `deploy.sh Impact`). `Change` is `Modify`, `Create`, or `Delete`; `Blast Radius` is a qualitative `Low`, `Medium`, or `High`; `deploy.sh Impact` always states a value from `skills/DESIGN.md` Change-impact table. Path A: judge `Blast Radius` qualitatively from Step 3's direct verification and mark `Churn (30d)` and `Bus Factor` `N/A`. Path B: take `Blast Radius` from the dependency graphing and `Churn (30d)` and `Bus Factor` from the historical analysis in `workflow-path-b.md`, and mark a column `N/A` when the tool that would fill it is unavailable.

Bullet 2, inserted in Step 5 (Risks):

> - Generate the `Risks` section: extract a potential risk from each Constraint and each repository evidence finding mapped to Risks in Step 4, and write each as `- **Risk**: {description} → **Mitigation**: {description}`. This step writes the Plan's inline `Risks` section; Step 6 refines that same section and files `issues/{timestamp}_risks.md` only for a Risk that still lacks a complete mitigation. A separate file never replaces the inline section.

Paragraph 1, inserted in Step 8a:

> Verify the `Affected areas` table: every row's `File` is one of the `Implementation Target Files` rows, and all six columns (`File`, `Change`, `Blast Radius`, `Churn (30d)`, `Bus Factor`, `deploy.sh Impact`) are populated or marked `N/A`.

Paragraph 2, inserted in Step 8a:

> Verify the `Risks` section: every Risk entry has a corresponding Mitigation.

Sentence appended to Step 8a's "Completed when" paragraph:

> The `Affected areas` and `Risks` checks above must also pass.

## Compatibility considerations
- Step numbers and headings are unchanged, so references by step name in `tools/generate_workitem.py`, `tools/manage_workitem_stage.py`, and `tests/tools/test_generate_workitem.py` comments stay valid; no code parses this file's text.
- `templates/plan.md` is unchanged, so existing Plans and `tools/check_workitem_structure.py` behavior are unaffected.
- The added Step 8a checks apply to Plans generated after this change; already generated Plans are not revalidated here (out of scope).

## Security considerations
N/A: a documentation-only edit to a skill file; no secrets, permissions, or executable behavior change.

## Rollback considerations
- The change is a single-file, additions-only edit; revert it with `git revert` of the implementing commit, or `git checkout -- skills/issue-to-plan/workflow.md` before it is committed.
- No data, configuration, or deployment state is touched, so no further rollback steps are needed.

## Validation plan
- `git diff --stat skills/issue-to-plan/workflow.md` and `git diff skills/issue-to-plan/workflow.md`: only added lines; no changed step number or heading (`REQ-006`).
- `uv run python tools/check_workitem_structure.py --file plans/20261008-163326_plan.md`: reports no findings.
- Manual review of the inserted text against `templates/plan.md` (`Affected areas`, `Risks`, "Notes on filling Affected areas") and `skills/DESIGN.md` Change-impact table (`REQ-001` to `REQ-004`).
- `git diff --stat skills/issue-to-plan/SKILL.md` is empty, or any edit is justified per the Assumptions (`REQ-005`).
- Static analysis (`ruff`, `mypy`, `bandit`, `pytest`) is not applicable: no Python file changes.

## Completion criteria
- Step 5 contains the Affected areas bullet and the Risks bullet, each as specified under Details, and the Risks bullet states that Step 5 writes the inline section and Step 6 refines it.
- Step 8a contains the Affected areas check, the Risk-to-Mitigation check, and the appended "Completed when" sentence.
- The diff of `skills/issue-to-plan/workflow.md` contains only added lines.
- `check_workitem_structure.py --file` on an existing plan reports no findings.
- `skills/issue-to-plan/SKILL.md` and `templates/plan.md` are unmodified.

## Out of scope
- Any change to `templates/plan.md`, `templates/execution-status.md`, `templates/requirement-traceability.md`, or `skills/DESIGN.md`.
- Changing the Path A / Path B criteria, Step 6's text, or Step 8c's re-entry table.
- Fixing already generated non-conformant plans.
- Editing `skills/issue-to-plan/SKILL.md` unless the Plan is first amended.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Insert the Affected areas and Risks bullets into Step 5 | Completed | 20261011-153045 | 20261011-153045 | Done |
| 2 | Insert the two checks and the appended sentence into Step 8a | Completed | 20261011-153045 | 20261011-153045 | Done |
| 3 | Add or update tests per Validation plan | Completed | 20261011-153049 | 20261011-153049 | N/A: no automated test covers skill text; validation is the diff review and structure check |
| 4 | Run the Validation plan checks (additions-only diff, structure check, manual review) | Completed | 20261011-153045 | 20261011-153045 | Additions-only diff, structure check: No findings |
| 5 | Confirm `SKILL.md` consistency and that no documentation outside the target file needs updating | Completed | 20261011-153045 | 20261011-153045 | SKILL.md and templates/plan.md unchanged |

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
- **Requirement ID**: `REQ-001` (Affected areas generation), `REQ-002` (Risks generation), `REQ-003` (Affected areas check), `REQ-004` (Risks check), `REQ-006` (append-only, English-only)
- **Source issue**: issues/20261010-173854_nc020_fix_issue_to_plan_workflow_missing_sections.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261011-130139_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261011-131155
- **Related target files**: skills/issue-to-plan/workflow.md