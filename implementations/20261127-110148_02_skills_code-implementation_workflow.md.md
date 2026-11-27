## Goal
- Replace the Final Report body of `skills/code-implementation/workflow.md` with the compact form, its deviation conditions, and a pointer to the full form (`REQ-001`, `REQ-005`, `REQ-006`).

## Scope
**Release unit**: N/A: not part of a release unit

- Runs after seq 01. Ceiling 42118 B (file 42112 B).

## Assumptions
- Verified in Step 3a: `## Final Report` starts with the completion paragraph (`This cycle is complete when, and only when ...`), which stays; two other sentences refer to the report: Progress recording (`the Final Report's seven-row table records them`) and Question policy (`the Final Report's \`Next steps\``); neither tool nor skill parses the report text.

## Design decisions
- The one-line traceability summary stays in every form because this workflow names it the cycle's traceability record; the other facts stay in the procedure's Execution Status Notes, the Plan, and the archived procedure.

## Alternatives considered
N/A: the Plan fixes the design (compact default in the workflow, full form verbatim in the edge file).

## Implementation
### Target file
`skills/code-implementation/workflow.md`

### Procedure
1. Measure `wc -c` (expect 42112).
2. In `## Final Report` keep the heading and the completion paragraph, delete the region moved by seq 01, and insert: "Use the compact form when the cycle had no deviation: none of `Blocked`, an Attempt Limit retry, a Rollback, a non-blocking `Needs confirmation`, a question asked of the user, an unrelated failure reported, or a failed Plan Execution Status update. Report three lines: the one-line traceability summary (`Source: ... | Completed: ...`, always required, values as in the full form); `Validation:` the stale check, the validators, the targeted tests and the full-suite or documentation-only result, and the documentation outcome; and `Next steps:` the commit through `git-commit-and-sync` (mention `deploy` when `scripts/` files were added, removed, or renamed). Every other fact stays in its persisted place. Any deviation requires the full form: load `skills/code-implementation/workflow-edge.md` and follow its "Final Report: full form" section."
3. In Progress recording replace `the Final Report's seven-row table records them` with `the full-form Final Report's seven-row table records them`.
4. Measure again: at most 42118 B.

### Method
- Copy moved text exactly (whitespace included); edit with exact-string replacements and check each anchor occurs once with `rg -c` first.

### Details
- Plain ASCII punctuation as in the neighboring sections; a heading must be unique in its file.

## Compatibility considerations
N/A: procedure text only; `tools/check_skills_references.py` and `tools/check_skills_heading_cycles.py` must still pass.

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_skill_size.py`, `uv run python tools/check_skills_references.py`, and `uv run python tools/check_skills_heading_cycles.py` exit 0.
- The file is at most 42118 B; `rg -n "Final Report" skills/code-implementation/workflow.md` shows no reference that the compact form contradicts.

## Completion criteria
- The compact form and its conditions are stated; the full form is reachable; the file is within its ceiling; the skill checks pass.

## Out of Scope
- Any other section of this file, the persisted records the report summarizes, and the other three workflows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Measure, replace the body, and adjust the Progress recording sentence | Pending | — | — | |
| 2 | Run the skill size, reference, and heading-cycle checks | Pending | — | — | |

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
- **Requirement ID**: `REQ-001`, `REQ-005`, `REQ-006` (compact default, size ceiling)
- **Source issue**: issues/20261126-151444_wfeff009_compact-final-reports.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-104723_wfeff009_compact-final-reports.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-110148
- **Related target files**: `skills/code-implementation/workflow.md`
