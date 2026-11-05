## Goal
- Remove the statement in `skills/code-implementation/workflow.md` that a bare `uv run mypy` does not cover `tools/`, which is false once the scope includes `tools` (`REQ-003`: the same scope in the skills text).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the changed-`tools/*.py` note of the validation step, one sentence (`skills/code-implementation/workflow.md:396`).
- Plan: `plans/20261105-105442_toolmypy001_add-tools-to-mypy-scope.md`, Plan step 2 (Phase 2). Added to the Plan by amendment (class fallout) in Step 3a.

## Assumptions
- The sentence reads "pass the file path to `uv run mypy` explicitly, because a bare `uv run mypy` does not cover `tools/`" (verified 2026-11-05).
- Plan overlap: no other open Plan targets this file.

## Design decisions
- Keep the instruction to pass the path, and replace the reason: it is the narrowest check, while a bare run now covers `tools/` and reports every file.

## Alternatives considered
N/A: single-sentence correction.

## Implementation
### Target file
`skills/code-implementation/workflow.md`

### Procedure
1. Replace "because a bare `uv run mypy` does not cover `tools/`" with a reason that is true after the change (narrowest check; a bare run also covers `tools/` but reports every file).

### Method
- One sentence edit; surrounding text and headings stay.

### Details
- Do not change the `routing.md` reference or the `run_validation_gates.py` sentence that follows.

## Compatibility considerations
N/A: documentation; the instruction itself is unchanged.

## Security considerations
N/A: documentation.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_skills_references.py` and `uv run python tools/check_skills_heading_cycles.py` report no finding.
- `rg -n "does not cover" skills/code-implementation/workflow.md` shows no `tools/` claim.

## Completion criteria
- The false claim is gone and the checkers are clean.

## Out of Scope
- Other Steps of the workflow.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the stale sentence | Pending | — | — | |
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
- **Related target files**: `skills/code-implementation/workflow.md`
