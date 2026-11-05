## Goal
- Remove the two statements in `skills/python-code-review/workflow.md` that mypy does not cover `tools/`, which are false once the scope includes `tools` (`REQ-003`: the same scope in the skills text).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the parenthetical at line 41 ("a bare `uv run mypy` does not cover `tools/`") and the example at line 156 ("`mypy`'s configured `files` scope omits `tools/`").
- Plan: `plans/20261105-105442_toolmypy001_add-tools-to-mypy-scope.md`, Plan step 2 (Phase 2). Added to the Plan by amendment (class fallout) in Step 3a.

## Assumptions
- Both quotations are verbatim from the file as of 2026-11-05.
- The line 156 sentence is an example of a CI gate-coverage gap; after the change a true example is that CI's `ruff` and `bandit` steps run on `scripts/` only (`.github/workflows/ci.yml` runs `ruff check scripts/` and `bandit -r scripts/`, verified 2026-11-05).
- Plan overlap: no other open Plan targets this file.

## Design decisions
- Line 41: keep "pass touched files explicitly", and drop the claim about `tools/`.
- Line 156: replace the example with the `ruff`/`bandit` scope gap, which stays true.

## Alternatives considered
N/A: two-sentence correction.

## Implementation
### Target file
`skills/python-code-review/workflow.md`

### Procedure
1. Line 41: change "pass touched files explicitly (a bare `uv run mypy` does not cover `tools/`)" to a parenthetical that is true (touched files give the narrowest check).
2. Line 156: change "(for example, `mypy`'s configured `files` scope omits `tools/`)" to "(for example, CI's `ruff` and `bandit` steps run on `scripts/` only)".

### Method
- Two sentence edits; headings and the "Completed when" line stay.

### Details
- Do not change the rest of the bullet at line 153.

## Compatibility considerations
N/A: documentation; the review procedure is unchanged.

## Security considerations
N/A: documentation.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_skills_references.py` and `uv run python tools/check_skills_heading_cycles.py` report no finding.
- `rg -n "omits .tools|does not cover .tools" skills/python-code-review/workflow.md` returns nothing.

## Completion criteria
- Both false claims are gone and the checkers are clean.

## Out of Scope
- Other Phases of the workflow.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the two stale statements | Completed | 20261105-153420 | 20261105-154210 | Stale check clean. Changed: skills/python-code-review/workflow.md (two stale tools/ mypy statements) |
| 2 | Run the documentation checkers named in `routing.md` "When to run which tool" | Completed | 20261105-153420 | 20261105-154210 | check_skills_references, check_skills_heading_cycles: no issues; repo-wide search for the 'does not cover tools/' phrasing finds nothing; run_validation_gates exit 0; full suite 11607 passed (-n 8; first run hit the xdist collection mismatch, rerun passed); docs N/A: skills file, no docs/00_index.md row |

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
- **Related target files**: `skills/python-code-review/workflow.md`