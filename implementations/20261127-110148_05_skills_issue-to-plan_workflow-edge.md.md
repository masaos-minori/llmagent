## Goal
- Add `### Step 9: full report` to `skills/issue-to-plan/workflow-edge.md`, holding the current Step 9 report text verbatim (`REQ-003`, `REQ-006`).

## Scope
**Release unit**: N/A: not part of a release unit

- Runs before seq 06.

## Assumptions
- Verified in Step 3a: the file is 4512 B (no baseline entry); the region to move is in `skills/issue-to-plan/workflow.md` `## Step 9: Final Validation`: the paragraph starting `When no Plan was generated this cycle, report only:` and the paragraph starting `Otherwise report:` (through `(already in the Plan's table).`), about 1.5 KB; the `Per rules/ai-execution.md Progress Reporting (Base)` paragraph and the gate paragraphs stay in `workflow.md`.

## Design decisions
- Append at the end of the file as a level-3 heading, like the existing sections.

## Alternatives considered
N/A: the Plan fixes the design (compact default in the workflow, full form verbatim in the edge file).

## Implementation
### Target file
`skills/issue-to-plan/workflow-edge.md`

### Procedure
1. Append `### Step 9: full report` and an introductory sentence: "Use this report when the cycle had any deviation, was the no-Plan case, or was the existing-Plan case named in `workflow.md` Step 9."
2. Copy the two paragraphs verbatim under it.

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
- The copied text equals the original region (whitespace-normalized comparison).

## Completion criteria
- The section exists with the full text unchanged; the skill checks pass.

## Out of Scope
- Any other section of this file, the persisted records the report summarizes, and the other three workflows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Append the heading and the verbatim paragraphs | Pending | — | — | |
| 2 | Run the skill checks and the text comparison | Pending | — | — | |

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
- **Requirement ID**: `REQ-003`, `REQ-006` (full report kept verbatim)
- **Source issue**: issues/20261126-151444_wfeff009_compact-final-reports.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-104723_wfeff009_compact-final-reports.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-110148
- **Related target files**: `skills/issue-to-plan/workflow-edge.md`
