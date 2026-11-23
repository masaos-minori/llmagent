## Goal

Point the Rollback on Failure citation of the implementation prompt at the edge file.

## Scope
**Release unit**: code-implementation-edge-split

In scope: the line `Follow ... Rollback on Failure in full.` (line 85).

## Assumptions

- Verified: the line reads `Follow \`skills/code-implementation/workflow.md\` Rollback on Failure in full.`; the heading stays in the main workflow with a trigger line, and the text now lives in the edge file.

## Design decisions

- Change the path to `skills/code-implementation/workflow-edge.md`, keeping `Rollback on Failure` and `in full`.

## Alternatives considered

N/A: documentation only.

## Implementation
### Target file
`prompts/03_implementation.md`

### Procedure
1. Edit the one line.

### Method
One Edit.

### Details
- No other change.

## Compatibility considerations

N/A: no behavior change.

## Security considerations

N/A: documentation only; no approval text, approver, or date is written.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_skills_references.py`
- `uv run python tools/check_skills_heading_cycles.py`

## Completion criteria

- The prompt names the edge file for Rollback on Failure and the checkers pass.

## Out of Scope

Other prompt text.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261123-162340 | 20261123-162624 | Updated the Rollback on Failure citation |
| 2 | Run the documentation checkers named in `rules/tool-gates.md` for a changed `docs/` file (`uv run python tools/run_validation_gates.py`) | Completed | 20261123-162624 | 20261123-162624 | Reference and heading-cycle checks pass |

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
- **Requirement ID**: `REQ-003` (outside citations name the edge file)
- **Source issue**: issues/20261123-155940_skillsize002_compress-skill-workflows-structure.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-161734_skillsize002_compress-skill-workflows-structure.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-162003
- **Related target files**: `prompts/03_implementation.md`
