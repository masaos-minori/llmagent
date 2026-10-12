## Goal
- Tell procedure authors to write the marker (new) after the target path when the document creates the file (`REQ-005`).

## Scope
- One added bullet in "Notes on filling sections" of `templates/implementation-procedure.md`, next to the existing note about the Target file.

## Assumptions
- Lightweight fill: a one-bullet documentation change.
- The existing note about the Target file ends with the rule on additional-target-file discovery; the new bullet follows the same list.

## Design decisions
- State the convention and its consequences in one bullet: the marker goes after the backticked path, it skips the existence check, the containing directory must exist, and a file that already exists is reported.

## Alternatives considered
N/A: single-bullet note.

## Implementation
### Target file
`templates/implementation-procedure.md`

### Procedure
1. In "Notes on filling sections", directly after the bullet that describes the Target file, add a bullet: when this document creates its target file, write the marker (new) after the backticked path in the Target file section; the stale detector then skips the existence check for that file, requires its containing directory to exist, reports a file that already exists, and skips line citations that resolve to it. A target without the marker that does not exist is reported as stale.

### Method
- Plain prose in the surrounding style; no change to the fenced template body.

### Details
- Keep the bullet short; the full rules live in the tool description.

## Compatibility considerations
- Existing generated procedures are unaffected; the generator output is unchanged.

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_workitem_structure.py --file` on a current procedure, and `uv run python tools/check_skills_references.py`.
- Execution order for the whole plan: procedure 02 (tests) first, then 01 (code), then 03, 04 and 05 (documentation); the new-policy tests must be seen failing before the code is edited.

## Completion criteria
- The note exists in the template's notes and the structure checker reports no findings.

## Out of scope
- Changing the template body or the generator.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the declared-new target note | Completed | 20261012-174543 | 20261012-174543 | stale_detector clean; changed: templates/implementation-procedure.md (one bullet after the Target file note) |
| 2 | Run the documentation checkers | Completed | 20261012-174543 | 20261012-174543 | check_workitem_structure and check_skills_references pass |

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
- **Related target files**: templates/implementation-procedure.md