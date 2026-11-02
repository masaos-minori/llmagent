## Goal
- Add the consumer-scan step to `skills/issue-to-plan/workflow.md` Step 3 so a Plan for a persisted-schema, public-API, or shared-constant change lists indirect consumers before freeze (`REQ-004`: scan step and record rule).

## Scope
- In scope: one new block in Step 3 (Path B inspection) of the one file. Out of scope: Plan Freeze rules, making the scan a gate, the template note (row 04), and the Step 5 line that another Plan adds.

## Assumptions
- Step 3a verification: Step 3 (`## Step 3: Inspect Related Files — Task-Size Classification`) has a Path A bullet and a Path B bullet, followed by a paragraph beginning "Read only the section(s)". `skills/issue-to-plan/SKILL.md` makes a schema change or a public or runtime-facing interface a Path B criterion, so Path B placement covers the three change classes.
- Overlap (Step 2): `skills/issue-to-plan/workflow.md` is also a target of `plans/20261102-080336_flowimp002_plan-release-units.md` (a line in Step 5). Judged compatible: different step; locate by heading, not line number. Source plan A9 records it.
- This block refers to the tool (row 01) and its routing row (row 06); a reference to `tools/scan_change_consumers.py` (new, row 01) is acceptable because it exists when this procedure runs.

## Design decisions
- Place the block as a new bullet after the Path B bullet, headed by a bold run-in label, not a new heading, so `check_skills_heading_cycles.py` sees no new node.
- The record destination is the Plan's `Design` section; the step states the scan is guidance, not a gate.

## Alternatives considered
- N/A: placement and record format fixed by the Plan Design section.

## Implementation
### Target file
`skills/issue-to-plan/workflow.md`

### Procedure
1. Re-read Step 3 at execution time and locate the Path B bullet by its text.
2. Insert the new block after it and before the paragraph "Read only the section(s)".

### Method
- Text: when the change class is a persisted schema, a public API, or a shared constant, run `uv run python tools/scan_change_consumers.py --seed <seed>` once per seed (the symbol, column or table name, constant, or file being changed) before Step 5, and record every candidate in the Plan's `Design` section as one of: a target row, a reference row, or `not affected: {reason}`.
- State that the report lists candidates only, that a missing consumer is not evidence of absence, that the scan does not block the Plan, and that the testmon state line in the report must be read.
- Reference the record format in `templates/plan.md` by file path (no heading anchor).

### Details
- Keep the block to about six lines in the file's existing imperative style.

## Compatibility considerations
- N/A: additive guidance; no existing step, Freeze rule, or gate changes.

## Security considerations
- N/A: documentation-only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_skills_references.py`
- `uv run python tools/check_skills_heading_cycles.py`

## Completion criteria
- Step 3 contains the scan step for the three change classes with the record rule; both checkers report no findings.

## Out of Scope
- Changing Freeze rules, making the scan blocking, and the Step 5 release-unit line.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Insert the consumer-scan block into Step 3 | Pending | — | — | |
| 2 | Run `check_skills_references.py` and `check_skills_heading_cycles.py` | Pending | — | — | |

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
- **Requirement ID**: `REQ-004` (scan step and record rule)
- **Source issue**: issues/20261030-191006_flowimp001_consumer-impact-scan.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261102-080004_flowimp001_consumer-impact-scan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-085054
- **Related target files**: skills/issue-to-plan/workflow.md
