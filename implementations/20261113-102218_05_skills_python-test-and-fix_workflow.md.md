## Goal
- State the `repo_scan` operational rule once in Step 10 and add `and not repo_scan` to its `--testmon-forceselect` command only (`REQ-004`).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the `--testmon-forceselect` line of the Step 10 code block and one new paragraph at the end of Step 10.
- Not in scope: the production-safety default sentences, the per-test-path flaky and bisect commands, the `--testmon-noselect` command, the Step 10 full run, Step 11's coverage run, the `--timeout` commands.

## Assumptions
- Step 10 holds the `--testmon-noselect` and `--testmon-forceselect` commands with `-m "not integration and not production_paths_allowed"`; the `--testmon-forceselect` line is the iteration command. The other occurrences are safety defaults, diagnostic per-path commands, or final runs and must keep selecting the marked tests. Falsifier: another iteration command is found; list it and ask.
- Overlap judged sequencing (Plan Step 2): `plans/20261113-093804_testspeed004_adopt-parallel-test-execution.md` edits the `pytest-xdist` row and the Step 10 full-run command of this file, and `plans/20261113-093307_testspeed001_mark-repo-scan-tests.md` (this Plan) edits one command line and adds a paragraph; different lines, compatible. Implement this Plan first and re-read Step 10 afterwards.

## Design decisions
- One statement of the rule, here; `skills/python-test-and-fix/SKILL.md` and `skills/code-implementation/workflow.md` refer to it.
- The rule says what the marker means, which commands exclude it, and where the marked tests still run.

## Alternatives considered
N/A: stating the rule in each of three files would restate it and risk drift.

## Implementation
### Target file
`skills/python-test-and-fix/workflow.md`

### Procedure
1. Change the `--testmon-forceselect` line of the Step 10 code block to `-m "not integration and not production_paths_allowed and not repo_scan"`, keeping its trailing comment.
2. After the paragraph that ends "so it is not a full run.", add one paragraph: the marker `repo_scan` labels tests that scan the whole repository (their result depends on the repository, not on the change under test); iteration runs deselect them with `and not repo_scan`; the final full run above, Step 11's coverage run, pre-commit, and CI still run them; a per-test-path command for flaky investigation or bisect must not carry the exclusion, so the test under investigation is not deselected.
3. Run the two skill checkers.

### Method
Edit Step 10 only. Name the marker in backticks and do not copy the five test names; point to `pyproject.toml` for the marker's registration.

### Details
- Do not change any other command that carries the `-m` expression.
- Keep the wording as intent and boundary, no implementation detail.

## Compatibility considerations
Iteration runs select fewer tests; the final full run, pre-commit, and CI are unchanged, so no verification is removed from the pre-merge path.

## Security considerations
N/A: no security impact.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_skills_references.py` and `uv run python tools/check_skills_heading_cycles.py`.
- `uv run python tools/run_validation_gates.py`.

## Completion criteria
- The `--testmon-forceselect` command carries the exclusion, Step 10 states the rule once, and every other `-m` command is unchanged (`AC-004`).
- Both skill checkers pass.

## Out of Scope
- `--testmon-noselect`, full-run, coverage, flaky, and bisect commands; the other skill files that cite the expression.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — |  |
| 2 | Run the skill checkers named in Validation plan (`routing.md` Tools "When to run which tool") | Pending | — | — |  |

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
- **Requirement ID**: REQ-004 (state the rule once in Step 10)
- **Source issue**: issues/20261112-183738_testspeed001_mark-repo-scan-tests.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261113-093307_testspeed001_mark-repo-scan-tests.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261113-102218
- **Related target files**: `skills/python-test-and-fix/workflow.md`
