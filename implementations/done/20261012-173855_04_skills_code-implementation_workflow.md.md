## Goal
- State in Step 3 what the stale detector does with a target declared new, and that an unmarked absent target is still a mismatch (`REQ-005`).

## Scope
- One added paragraph in "Stale detection result handling" of `skills/code-implementation/workflow.md`.

## Assumptions
- Lightweight fill: the existing paragraph about symbols and imports marked (new) sits at the start of that section; the new paragraph goes right after it.

## Design decisions
- Keep it to the observable behavior and point to the template notes for authoring, as the existing paragraph does.

## Alternatives considered
N/A: single-paragraph note.

## Implementation
### Target file
`skills/code-implementation/workflow.md`

### Procedure
1. In "Stale detection result handling", right after the paragraph about symbols and imports marked (new), add a paragraph: a target file written with the marker (new) after its path is declared as created by the procedure; the detector skips the existence check, requires the containing directory to exist, reports a file that already exists, checks symbols, imports and code blocks against an empty file, and skips line citations that resolve to it; an unmarked target that does not exist is still a mismatch and aborts the procedure.

### Method
- Plain prose in the surrounding style; do not change the abort rule or the instruction not to correct the procedure and continue.

### Details
- Refer to the procedure template notes for how authors write the marker.

## Compatibility considerations
- No change to the abort policy; the text only describes the detector.

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_skills_references.py`.
- Execution order for the whole plan: procedure 02 (tests) first, then 01 (code), then 03, 04 and 05 (documentation); the new-policy tests must be seen failing before the code is edited.

## Completion criteria
- The paragraph exists and the references checker reports no issues.

## Out of scope
- The abort policy and the other workflow steps.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the declared-new target paragraph | Completed | 20261012-174543 | 20261012-174543 | stale_detector clean; changed: skills/code-implementation/workflow.md (one paragraph in Stale detection result handling) |
| 2 | Run the documentation checkers | Completed | 20261012-174543 | 20261012-174543 | check_skills_references pass |

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
- **Requirement ID**: `REQ-005`
- **Source issue**: issues/done/20261012-172916_stale002_allow-new-target-files-in-stale-detector.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261012-173651_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-173855
- **Related target files**: skills/code-implementation/workflow.md