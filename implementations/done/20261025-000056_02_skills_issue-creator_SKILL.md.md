## Goal
- Reword Phase overview item 10 of `skills/issue-creator/SKILL.md` so it states the same scaffold policy as `workflow.md` Step 10.2 (`REQ-004`: one policy in both files).

## Scope
- Phase overview item 10 only (lines 83-84 at time of writing): `10. Write and Verify the File: scaffold the file, fill every placeholder (including Traceability), run the structure checker, and report to the user`.

## Assumptions
- Text confirmed 2026-10-24.
- Overlap: `implementations/20261024-235959_02_skills_issue-creator_SKILL.md.md` edits items 2 and 4 of the same list (executed first per the Plan fix order); this row touches item 10 only. Sequencing dependency, compatible; re-read and re-anchor immediately before editing.
- Row `01` (`skills/issue-creator/workflow.md`) is applied first so the wording matches Step 10.2.

## Design decisions
- Replace "scaffold the file" with "create the file (scaffold tool by default, or direct write under `workflow.md` Step 10.2's conditions)"; keep the rest of the item and its two-line layout.

## Alternatives considered
N/A: wording-only edit.

## Implementation
### Target file
`skills/issue-creator/SKILL.md`

### Procedure
1. Edit item 10's text as above, keeping it within the numbered-list format.

### Method
- Edit in place with the current item text as `old_string`.

### Details
- Do not change items 1 to 9 or the pointer lines added by the sibling procedure.

## Compatibility considerations
N/A: wording only.

## Security considerations
N/A: instruction text only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_skills_references.py` and `uv run python tools/check_skills_heading_cycles.py` exit 0.
- Read item 10 and `workflow.md` Step 10.2 side by side and confirm one policy.

## Completion criteria
- Item 10 no longer says only "scaffold the file" and matches `workflow.md` Step 10.2; both checkers exit 0.

## Out of Scope
- Other Phase overview items and `workflow.md`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Reword Phase overview item 10 | Completed | — | 20261025-003542 |  |
| 2 | Run both skills checkers and compare with Step 10.2 | Completed | — | 20261025-003542 |  |

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
- **Requirement ID**: `REQ-004` (Phase overview matches the workflow policy)
- **Source issue**: issues/20261024-212657_perf007_align-scaffold-policy-with-practice.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261024-234023_align-scaffold-policy-with-practice.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261025-000056
- **Related target files**: `skills/issue-creator/SKILL.md`