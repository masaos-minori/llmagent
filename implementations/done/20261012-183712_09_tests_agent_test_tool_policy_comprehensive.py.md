## Goal
- Set the web-search authentication variable locally in the one test(s) that build the real agent configuration (`REQ-004`)

## Scope
- The one test(s) in `tests/agent/test_tool_policy_comprehensive.py` that call `build_agent_config` after setting the git and cicd variables.

## Assumptions
- The agent configuration requires a non-empty web-search token, and procedure 04 makes the shared default empty (measured: exactly these tests fail otherwise).

## Design decisions
- Follow the existing pattern: set the variable with `monkeypatch.setenv` next to the git and cicd variables; keep the explanatory comment accurate.

## Alternatives considered
N/A: the Plan Design section already fixed the approach for this row.

## Implementation
### Target file
`tests/agent/test_tool_policy_comprehensive.py`

### Procedure
1. In each of the one test(s), add a `monkeypatch.setenv` call for MCP_WEB_SEARCH_AUTH_TOKEN with the value test-token, right after the git and cicd calls.
2. Extend the nearby comment to say web-search follows the same pattern.

### Method
- Edit only the lines next to the existing setenv calls.

### Details
- Do not change the tests' assertions.

## Compatibility considerations
Test-only change.

## Security considerations
N/A: no input handling, credentials, or trust boundary is touched.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_tool_policy_comprehensive.py -q`; `uv run ruff format --check tests/agent/test_tool_policy_comprehensive.py` and `uv run ruff check tests/agent/test_tool_policy_comprehensive.py`.
- Execution order for the whole plan: tests first (procedures 05, 06, 07, 08, 09, 04), then the code (01, 02, 03), then the documentation (10 to 15); the new tests must be seen failing before the code is edited.

## Completion criteria
- The tests pass with the empty shared default from procedure 04.

## Out of scope
- Other tests in the file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Set the web-search variable in the tests that build the real agent configuration | Completed | 20261012-184531 | 20261012-184531 | stale_detector clean; changed: tests/agent/test_tool_policy_comprehensive.py (web-search variable set in the one test) |
| 2 | Run the validation sequence (`rules/toolchain.md`) for the touched file | Completed | 20261012-184531 | 20261012-184531 | ruff pass; file passes |

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
- **Requirement ID**: `REQ-004`
- **Source issue**: issues/done/20261012-182600_mcp005_web-search-tool-calls-return-401-when-browser_auth_token-differs-from-auth_token.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/done/20261012-183348_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-183712
- **Related target files**: tests/agent/test_tool_policy_comprehensive.py