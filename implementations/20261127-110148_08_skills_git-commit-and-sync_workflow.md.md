## Goal
- Replace the Phase 9 report list of `skills/git-commit-and-sync/workflow.md` with the compact form, its deviation conditions, and a pointer (`REQ-004`, `REQ-005`, `REQ-006`).

## Scope
**Release unit**: N/A: not part of a release unit

- Runs after seq 07. Ceiling 22947 B equals the file size, so the replacement must be shorter than the moved text.

## Assumptions
- Verified in Step 3a: the working tree usually holds other sessions' unrelated untracked or unstaged paths, so "remaining uncommitted changes" is a deviation only for a change this run touched or a file that went missing; unrelated leftovers appear as a count on the status line. `skills/git-commit-and-sync/SKILL.md` row 9 of the Phase overview stays accurate for the full form.

## Design decisions
- A deviation is an unrelated gate failure, another commit published, a change of this run left uncommitted, a stop condition, a warning, or a push that did not proceed.

## Alternatives considered
N/A: the Plan fixes the design (compact default in the workflow, full form verbatim in the edge file).

## Implementation
### Target file
`skills/git-commit-and-sync/workflow.md`

### Procedure
1. Measure `wc -c` (expect 22947).
2. In `## Phase 9: Report` keep the heading and the final `Prohibited behavior` line, delete the moved list, and insert: "Use the compact form when the run had no deviation: no unrelated gate failure, no other commit published, no change of this run left uncommitted, no stop condition, no warning, and the push proceeded. Report: a status line (branch, commit SHA, message subject, sync result, pre-push recheck result, push result, and the count of unrelated uncommitted paths left in the tree); and a validation line (the Phase 4 gates and, after a sync, the post-sync check). Any deviation requires the full report: load `skills/git-commit-and-sync/workflow-edge.md` and follow its "Phase 9: full report" section."
3. Measure again: at most 22947 B.

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
- The file is at most 22947 B.

## Completion criteria
- The compact form and its conditions are stated; the full report is reachable; the file is within its ceiling.

## Out of Scope
- Any other section of this file, the persisted records the report summarizes, and the other three workflows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Measure and replace the report list | Pending | — | — | |
| 2 | Run the skill checks | Pending | — | — | |

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
- **Requirement ID**: `REQ-004`, `REQ-005`, `REQ-006` (compact default, size ceiling)
- **Source issue**: issues/20261126-151444_wfeff009_compact-final-reports.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-104723_wfeff009_compact-final-reports.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-110148
- **Related target files**: `skills/git-commit-and-sync/workflow.md`
