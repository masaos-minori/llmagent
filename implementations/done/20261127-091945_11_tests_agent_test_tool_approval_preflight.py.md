# Implementation Procedure

## Goal

- Update the `github_push_files` dry-run approval pin that stopped passing once the declared
  branch key (REQ-001) escalated a high-risk branch to HIGH, which requires the full word "yes".

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Added to the Plan by amendment 2026-11-27 (class `scope`, owner-approved) after the end-of-batch
  full suite reported this failure; recorded in procedure
  `implementations/20261126-215042_03_scripts_mcp_servers_github_tools_file.py.md` Blocker Log.
- The test's purpose is the dry-run preview enrichment, not the risk level, so the branch value is
  changed instead of the patched answer.

## Design decisions
- Keep the test focused on dry-run enrichment by using a branch outside `approval_high_risk_branches`
  so the tier base stays `medium` and the patched "y" answer is still valid.
- The HIGH path is already pinned by `tests/agent/test_tool_approval_risk.py` (procedure 10), so this
  test does not duplicate it.

## Alternatives considered
- N/A: patching the answer to "yes" would make the test cover two behaviors at once.

## Implementation
### Target file
`tests/agent/test_tool_approval_preflight.py`
### Procedure
Change the branch argument of `TestCheckApprovalDryRun::test_github_tool_triggers_dry_run` from
`main` to a non-high-risk branch and state why in a comment.
### Method
Use `feature/x`; leave the patched approval answer and the dry-run assertions unchanged.
### Details
- Fixture default `approval_high_risk_branches` is `["main"]` (`tests/agent/_config_test_defaults.py:141`).
- HIGH requires the full word "yes" in `_prompt_user_approval()` (`scripts/agent/tool_approval.py`).

## Compatibility considerations
- N/A: test-only change; no production behavior affected.

## Security considerations
- N/A: the test asserts the approval flow; it does not change it.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_tool_approval_preflight.py -q` — 84 passed.
- `uv run ruff format --check`, `uv run ruff check`, `uv run mypy --no-namespace-packages` on the file.
- End-of-batch full suite plus `diff-cover` per `rules/toolchain.md`.

## Completion criteria
- The dry-run pin passes with the branch-key declaration in place, and the full suite is clean.

## Out of Scope
- `scripts/agent/tool_approval.py` and `scripts/agent/tool_policy.py` (Plan reference rows, not modified).
- `tests/agent/test_tool_approval_risk.py` (procedure 10).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261127-091945 | 20261127-091945 | Verified against current source: the failing test at line 705 supplied `branch="main"` with a patched "y" answer; `github_push_files` now declares a branch key (`scripts/mcp_servers/github/tools_file.py:77`), `approval_high_risk_branches` defaults to `["main"]` (`tests/agent/_config_test_defaults.py:141`), and HIGH requires "yes" in `_prompt_user_approval()`. File clean at cycle start. Changed the branch to `feature/x` and added the comment. Changed file: tests/agent/test_tool_approval_preflight.py. |
| 2 | Add or update tests per Validation plan | N/A | — | 20261127-091945 | This cycle is the test cycle; no additional tests beyond the updated pin. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261127-091945 | 20261127-091945 | ruff format --check and ruff check: pass. mypy on the file: no issues. Targeted tests: 84 passed. End-of-batch full suite: 15925 passed / 5 skipped, no failures. diff-cover on changed `scripts/` lines: 100% (test files are outside the coverage source). |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | 20261127-091945 | N/A: documentation is covered by procedure 08; the branch-escalation policy text in `docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md:89` already matches the new behavior, so no docs change is needed. |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | N/A: no blocker recorded at procedure creation | N/A: no blocker recorded | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-001` (branch scope for the github file write tools)
- **Source issue**: issues/20261119-140520_mcpai013_github-resource-scope-refine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/done/20261126-073010_mcpai013_github-resource-scope-refine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-091945
- **Related target files**: `tests/agent/test_tool_approval_preflight.py`
