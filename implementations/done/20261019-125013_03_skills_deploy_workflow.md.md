## Goal
State in Phase 1b of the deploy workflow that the build sets `UV_SYSTEM_CERTS=true` by default and how to override it (`REQ-002`).

## Scope
- One sentence added to Phase 1b; no heading or other text changes.

## Assumptions
- The script behavior is as specified in the sibling procedure.

## Design decisions
- Add the sentence where the build host prerequisites are mentioned, so an operator reading the failure message finds the cause.

## Alternatives considered
N/A: one sentence.

## Implementation
### Target file
`skills/deploy/workflow.md`

### Procedure
1. Insert one sentence in Phase 1b before the line "**Completed when**: `check` lists no stale or unknown binary."
2. Run the skill checkers.

### Method
- Sentence: "The build exports `UV_SYSTEM_CERTS=true` by default so `uv` can fetch nuitka on hosts whose certificates are only in the system store; set `UV_SYSTEM_CERTS=false` to turn it off."
- Keep it in the existing prose paragraph style of Phase 1b.

### Details
- Do not repeat build mechanics already described in Phase 1b.

## Compatibility considerations
N/A: documentation wording only.

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_skills_references.py`
- `uv run python tools/check_skills_heading_cycles.py`

## Completion criteria
- Phase 1b contains the sentence and both skill checkers pass.

## Out of scope
- Other phases
- `docs/90_deployment/deployment_01_deployment.md` (lists no build prerequisites; no change needed)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the sentence to Phase 1b | Completed | 20261019-125830 | 20261019-125830 |  |
| 2 | Run the skill reference and heading-cycle checkers | Completed | 20261019-125830 | 20261019-125830 |  |

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
- **Requirement ID**: `REQ-002` (Phase 1b sentence)
- **Source issue**: issues/20261019-123439_deploybin002_build-script-needs-system-certificates.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261019-124601_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-125013
- **Related target files**: skills/deploy/workflow.md