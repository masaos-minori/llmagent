## Goal
- Update `skills/python-lint-typecheck/workflow.md` so its scope sentences and mypy commands include `tools` (`REQ-003`: the same scope in the skills text).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the scope sentence (line 38), the `tools/`-or-`tests/` paragraph (lines 41-46), the Step 6 table command (line 55), and the Step 6 command block (line 173).
- Plan: `plans/20261105-105442_toolmypy001_add-tools-to-mypy-scope.md`, Plan step 2 (Phase 2). Not listed in the source Issue; found in Plan Step 3.

## Assumptions
- Line 38 says mypy "also covers `tests/eventbus`"; lines 43-46 say mypy's `files` covers `scripts/` and `tests/eventbus` and that a bare run says nothing about `tools/`; lines 55 and 173 carry the command (verified 2026-11-05).
- After the change, the "bare run says nothing about `tools/`" claim stays true for `ruff` and `bandit` only (CI runs both on `scripts/` only), not for mypy.
- Plan overlap: no other open Plan targets this file.

## Design decisions
- Keep the paragraph's structure; split the claim so it says mypy covers `tools/` while `ruff` and `bandit` do not, and keep the pointer to `routing.md` "Adding a new tool" for those.
- Leave line 174 (`mypy ... scripts/<file>.py`, a single-file form) alone.

## Alternatives considered
N/A: wording alignment only.

## Implementation
### Target file
`skills/python-lint-typecheck/workflow.md`

### Procedure
1. Line 38: "mypy also covers `tests/eventbus` and `tools`".
2. Lines 41-46: rewrite the mypy sentence to name `scripts/`, `tests/eventbus`, and `tools` (the pre-commit hook uses the same `files`); keep the `ruff`/`bandit` remark for `tools/` and the other `tests/` directories.
3. Line 55 and line 173: add `tools` to the commands (`uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, the latter with `--show-error-codes` kept).

### Method
- Four text edits; no heading changes.

### Details
- Do not change the Step numbering or the table's other rows.

## Compatibility considerations
N/A: documentation; wording only.

## Security considerations
N/A: documentation.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_skills_references.py` and `uv run python tools/check_skills_heading_cycles.py` report no finding.
- `rg -n "tests/eventbus" skills/python-lint-typecheck/workflow.md` shows only commands and sentences that also name `tools`.

## Completion criteria
- Every mypy scope statement and command in the file names `tools`, and the checkers are clean.

## Out of Scope
- The `ruff`/`bandit` scope, and other Steps of the workflow.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the scope sentences and the two commands | Completed | 20261105-151330 | 20261105-151701 | Stale check clean. Changed: skills/python-lint-typecheck/workflow.md (scope sentence, tools/ paragraph, Step 6 table command, Step 6 command block) |
| 2 | Run the documentation checkers named in `routing.md` "When to run which tool" | Completed | 20261105-151330 | 20261105-151701 | check_skills_references and check_skills_heading_cycles: no issues; run_validation_gates exit 0; full suite 11607 passed (-n 8); docs N/A: skills file, no docs/00_index.md row |

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
- **Related target files**: `skills/python-lint-typecheck/workflow.md`