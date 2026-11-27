# Implementation Procedure

## Goal

- Update the REQ-008 pin in the approval-risk test that asserted no shipped github tool
  declares a branch-kind key, which REQ-001 (branch scope for the github file write tools)
  invalidated.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Added to the Plan by amendment 2026-11-27 (class `scope`, owner-approved) after the end-of-batch
  full suite reported this failure; recorded in procedure
  `implementations/20261126-215042_03_scripts_mcp_servers_github_tools_file.py.md` Blocker Log.
- The escalation contract itself is unchanged — `scripts/agent/tool_policy.py:346`
  (`_escalate_for_github_branch()`) already reads the declared branch-kind keys.

## Design decisions
- The pin is rewritten to the actual REQ-008 contract (declared keys are the only key source)
  rather than to the removed assumption that no github tool declares one.
- The original intent is kept by asserting the non-escalating case for a tool with no branch key.

## Alternatives considered
- N/A: the alternative was to revert the REQ-001 branch-key declarations, rejected because it
  would drop AC-2.

## Implementation
### Target file
`tests/agent/test_tool_approval_risk.py`
### Procedure
Rewrite `TestClassifyRisk::test_github_tools_have_no_declared_branch_keys` as
`test_declared_branch_keys_are_the_escalation_source`.
### Method
Assert the declared branch-kind key set equals the three github file write tools; keep the
no-branch-key case for `github_create_pull_request`; add the escalation case for
`github_push_files` on a high-risk branch and the non-escalation case on a normal branch.
### Details
- Fixture default `approval_high_risk_branches` is `["main"]` (`tests/agent/_config_test_defaults.py:141`).
- The old test name asserted the removed assumption, so the name is changed to state the contract.

## Compatibility considerations
- N/A: test-only change; no production behavior affected.

## Security considerations
- N/A: the test asserts the escalation behavior; it does not change it.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_tool_approval_risk.py -q` — 36 passed.
- `uv run ruff format --check`, `uv run ruff check`, `uv run mypy --no-namespace-packages` on the file.
- End-of-batch full suite plus `diff-cover` per `rules/toolchain.md`.

## Completion criteria
- The test pins the declared branch-key set and the HIGH escalation on a high-risk branch while
  the no-branch-key case still resolves to `medium`; the full suite is clean.

## Out of Scope
- `scripts/agent/tool_policy.py` (Plan reference row, not modified).
- `tests/agent/test_tool_approval_preflight.py` (procedure 11).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261127-091945 | 20261127-091945 | Verified against current source: the failing pin at line 225 asserted no `branch` kind in `resource_scope_keys`; `_escalate_for_github_branch()` at `scripts/agent/tool_policy.py:346` reads the declared branch keys; `tests/agent/_config_test_defaults.py:141` defaults `approval_high_risk_branches` to `["main"]`; the only github tools declaring a branch key are the three file write entries (`scripts/mcp_servers/github/tools_file.py:77`). File clean at cycle start. Rewrote the test as described. Changed file: tests/agent/test_tool_approval_risk.py. |
| 2 | Add or update tests per Validation plan | N/A | — | 20261127-091945 | This cycle is the test cycle; no additional tests beyond the rewritten pin. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261127-091945 | 20261127-091945 | ruff format --check and ruff check: pass. mypy on the file: no issues. Targeted tests: 36 passed. End-of-batch full suite: 15925 passed / 5 skipped, no failures. diff-cover on changed `scripts/` lines: 100% (test files are outside the coverage source). |
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
- **Related target files**: `tests/agent/test_tool_approval_risk.py`
