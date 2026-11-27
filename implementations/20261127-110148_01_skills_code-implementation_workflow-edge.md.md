## Goal
- Add `## Final Report: full form` to `skills/code-implementation/workflow-edge.md`, holding the current full Final Report text verbatim (`REQ-001`, `REQ-006`).

## Scope
**Release unit**: N/A: not part of a release unit

- Runs before seq 02, so the full form exists here before the workflow text is replaced.

## Assumptions
- Verified in Step 3a: the file is 12258 B (limit 16384 B, no baseline entry); the region to move is in `skills/code-implementation/workflow.md` from the line `Include the following in the final report:` up to (not including) `## Output format` (the one-line traceability summary, Execution Status, Questions asked, Next steps, Blocker Log, and Work Items Created subsections, about 3 KB).

## Design decisions
- Append at the end of the file as a level-2 heading, the level of the existing `## Rollback on Failure`; the loading form in `workflow.md` names the heading exactly.

## Alternatives considered
N/A: the Plan fixes the design (compact default in the workflow, full form verbatim in the edge file).

## Implementation
### Target file
`skills/code-implementation/workflow-edge.md`

### Procedure
1. Append `## Final Report: full form` and an introductory sentence: "Use this form when the cycle had any deviation named in `workflow.md` Final Report."
2. Under it copy the region described under Assumptions verbatim, keeping its `###` subheadings.

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
- The copied text equals the original region (whitespace-normalized comparison against `git show HEAD:skills/code-implementation/workflow.md`).

## Completion criteria
- The section exists with the full text unchanged; the file is under 16384 B; the skill checks pass.

## Out of Scope
- Any other section of this file, the persisted records the report summarizes, and the other three workflows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Append the heading and the verbatim region | Pending | — | — | |
| 2 | Run the skill size, reference, and heading-cycle checks and the text comparison | Pending | — | — | |

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
- **Requirement ID**: `REQ-001`, `REQ-006` (full form kept verbatim)
- **Source issue**: issues/20261126-151444_wfeff009_compact-final-reports.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-104723_wfeff009_compact-final-reports.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-110148
- **Related target files**: `skills/code-implementation/workflow-edge.md`
