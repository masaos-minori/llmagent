## Goal
- Create `skills/git-commit-and-sync/workflow-edge.md` with `### Phase 9: full report` holding the current Phase 9 report list verbatim (`REQ-004`, `REQ-006`).

## Scope
**Release unit**: N/A: not part of a release unit

- Runs before seq 08. The skill had no edge file; this follows the pattern of the other three skills.

## Assumptions
- Verified in Step 3a: `skills/git-commit-and-sync/` holds `SKILL.md` and `workflow.md` only; the region to move is in `skills/git-commit-and-sync/workflow.md` `## Phase 9: Report`: the `Report:` line and its nine bullets (about 800 B); the final line `Prohibited behavior: see \`SKILL.md\` Core rules.` stays in `workflow.md`.

## Design decisions
- The new file starts with a one-line title and a sentence that it is loaded only when `workflow.md` Phase 9 requires the full report.

## Alternatives considered
N/A: the Plan fixes the design (compact default in the workflow, full form verbatim in the edge file).

## Implementation
### Target file
`skills/git-commit-and-sync/workflow-edge.md` (new)

### Procedure
1. Create the file with the title `# Git Commit and Sync - Edge Cases` and the sentence above.
2. Add `### Phase 9: full report` and copy the region verbatim under it.

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
- The file exists with the full text unchanged; the skill checks pass.

## Out of Scope
- Any other section of this file, the persisted records the report summarizes, and the other three workflows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create the file with the heading and the verbatim region | Pending | — | — | |
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
- **Requirement ID**: `REQ-004`, `REQ-006` (full report kept verbatim)
- **Source issue**: issues/20261126-151444_wfeff009_compact-final-reports.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-104723_wfeff009_compact-final-reports.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-110148
- **Related target files**: `skills/git-commit-and-sync/workflow-edge.md`
