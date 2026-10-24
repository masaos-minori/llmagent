## Goal
- Align the Phase overview rows for Steps 2, 5, and 8 in `skills/issue-to-plan/SKILL.md` with the bounded verification wording of the workflow (`REQ-004`: step summaries consistent with `workflow.md`).

## Scope
- Edit the three Phase overview table rows (lines 43, 46, 49 at time of writing); wording only, no new step reference.

## Assumptions
- Row 2 begins `| 2 | Assess the current Issue |`, row 5 `| 5 | Create the Plan |`, row 8 `| 8 | Validate information completeness |` (read 2026-10-24).
- Overlap: `plans/20261024-232610_lightweight-path-a-plan-template.md` edits the Output format and Routing text of this file, not the Phase overview rows; compatible. Re-anchor on the current file before editing.
- Row `01` (`skills/issue-to-plan/workflow.md`) is applied first so the summarized wording exists.

## Design decisions
- Add one short clause per row: Step 2 notes same-cycle dedup and the depth ceiling, Step 5 notes the `(checked in Step N)` evidence tag, Step 8 notes validation from the recorded checks with all four criteria kept.

## Alternatives considered
N/A: wording-only table edit.

## Implementation
### Target file
`skills/issue-to-plan/SKILL.md`

### Procedure
1. Append the clause to each of the three rows, keeping each row on one line.

### Method
- Edit in place with a unique `old_string` per row.

### Details
- Do not touch Output format or Routing; those belong to the sibling Plan.

## Compatibility considerations
N/A: wording only.

## Security considerations
N/A: instruction text only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_skills_references.py` and `uv run python tools/check_skills_heading_cycles.py` exit 0.

## Completion criteria
- The three rows match the workflow wording and every step reference resolves.

## Out of Scope
- Output format, Routing, and any other file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update Phase overview rows 2, 5, 8 | Completed | — | 20261025-001740 |  |
| 2 | Run both skills checkers | Completed | — | 20261025-001740 |  |

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
- **Requirement ID**: `REQ-004` (step summaries consistent with `workflow.md`)
- **Source issue**: issues/20261024-185557_perf002_bound-adversarial-verification-cost.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261024-220231_bound-adversarial-verification-cost.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-235220
- **Related target files**: `skills/issue-to-plan/SKILL.md`