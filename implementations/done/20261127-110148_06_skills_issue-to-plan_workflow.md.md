## Goal
- Replace the Step 9 report text of `skills/issue-to-plan/workflow.md` with the compact form, its deviation conditions, and a pointer, leaving the Step 9 gate text intact (`REQ-003`, `REQ-005`, `REQ-006`).

## Scope
**Release unit**: N/A: not part of a release unit

- Runs after seq 05. Ceiling 42540 B (file 42539 B), so the replacement must be shorter than the moved text.

## Assumptions
- Verified in Step 3a: Step 9 also holds the Progress Reporting read-back paragraph and the two gate paragraphs (`The move to issues/done/ needs no human approval ...`, `If Implementation Target Files is not Frozen ...`); they are unchanged. `rules/workflow-lifecycle.md` Validation Reporting lists five fields (Status, Output, Validation, Unresolved items, Pending move); the compact form carries all five: Status, Output, and Pending move on the status line, Validation and Unresolved items on the validation line.

## Design decisions
- A deviation is any unresolved item, a generated Unknown or Risk file, an overlap, the no-Plan or existing-Plan case, or `Blocked`.

## Alternatives considered
N/A: the Plan fixes the design (compact default in the workflow, full form verbatim in the edge file).

## Implementation
### Target file
`skills/issue-to-plan/workflow.md`

### Procedure
1. Measure `wc -c` (expect 42539).
2. Replace the two moved paragraphs with: "Use the compact form when the cycle had no deviation: no unresolved item, no generated Unknown or Risk file, no overlap with another Frozen Plan, not the no-Plan or existing-Plan case, and not `Blocked`. Report: a status line (generated Plan path, number of Requirements, number of `Implementation Target Files` rows, Path A or B, `Frozen`, the Issue pending move); a validation line (information completeness and traceability results, unresolved items `None`); and the next steps (`git-commit-and-sync` commits the Plan and the staged Issue rename, then `plan-to-implementation-procedure` takes the Plan). Any deviation or either of those cases requires the full report: load `skills/issue-to-plan/workflow-edge.md` and follow its "Step 9: full report" section."
3. Measure again: at most 42540 B.

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
- The file is at most 42540 B and the Step 9 gate paragraphs are unchanged (`git diff` shows only the replaced report paragraphs).

## Completion criteria
- The compact form and its conditions are stated; the gate text is intact; the file is within its ceiling.

## Out of Scope
- Any other section of this file, the persisted records the report summarizes, and the other three workflows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Measure and replace the report paragraphs | Completed | 20261127-111826 | 20261127-111844 | Changed: skills/issue-to-plan/workflow.md 42539 -> 42111 B (ceiling 42540); Step 9 gate paragraphs unchanged; verbatim comparison identical. Edge intro reworded to avoid a heading cycle |
| 2 | Run the skill checks | Completed | 20261127-111844 | 20261127-111844 | skill size, references, heading cycles pass after rewording the edge intro |

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
- **Requirement ID**: `REQ-003`, `REQ-005`, `REQ-006` (compact default, size ceiling)
- **Source issue**: issues/20261126-151444_wfeff009_compact-final-reports.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-104723_wfeff009_compact-final-reports.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-110148
- **Related target files**: `skills/issue-to-plan/workflow.md`