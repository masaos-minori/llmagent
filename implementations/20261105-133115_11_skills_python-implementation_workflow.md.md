## Goal
- Remove the statement in `skills/python-implementation/workflow.md` that mypy's configured scope omits `tools/`, which is false once the scope includes `tools` (`REQ-003`: the same scope in the skills text).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the trailing comment of the mypy command line at line 330 of the validation command block.
- Plan: `plans/20261105-105442_toolmypy001_add-tools-to-mypy-scope.md`, Plan step 2 (Phase 2). Added to the Plan by amendment (class fallout) in Step 3a.

## Assumptions
- The comment reads `# or pyright; pass paths explicitly (mypy's configured scope omits tools/)` (verified 2026-11-05).
- Plan overlap: no other open Plan targets this file.

## Design decisions
- Keep "pass paths explicitly" (changed files only is the narrowest check) and drop the claim about `tools/`.

## Alternatives considered
N/A: single-comment correction.

## Implementation
### Target file
`skills/python-implementation/workflow.md`

### Procedure
1. Change the comment to `# or pyright; pass the changed paths explicitly (the narrowest check)`.

### Method
- One comment edit inside a fenced block; the command itself is unchanged.

### Details
- Keep the column alignment of the other comments in that block.

## Compatibility considerations
N/A: documentation; the command is unchanged.

## Security considerations
N/A: documentation.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_skills_references.py` and `uv run python tools/check_skills_heading_cycles.py` report no finding.
- `rg -n "omits tools" skills/python-implementation/workflow.md` returns nothing.

## Completion criteria
- The false claim is gone and the checkers are clean.

## Out of Scope
- Other Steps and commands of the workflow.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the stale comment | Pending | — | — | |
| 2 | Run the documentation checkers named in `routing.md` "When to run which tool" | Pending | — | — | |

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
- **Requirement ID**: `REQ-003` (the same scope in the skills text)
- **Source issue**: issues/20261104-152002_toolmypy001_add-tools-to-mypy-scope.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261105-105442_toolmypy001_add-tools-to-mypy-scope.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-133115
- **Related target files**: `skills/python-implementation/workflow.md`
