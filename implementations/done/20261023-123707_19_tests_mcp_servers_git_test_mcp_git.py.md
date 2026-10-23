## Goal
Make this module pass with non-empty server tokens by sending the shared Authorization header from its `TestClient` sites (1 failures in the verification run) (`REQ-005`).

## Scope
- Update the 1 `TestClient(` construction site(s) at lines 397 to pass `headers=MCP_TEST_AUTH_HEADERS` where the client targets the real server app.
- Leave tests that build their own app, token or explicit `Authorization` header alone.

## Assumptions
- The failures are caused by requests without an Authorization header: the module had 1 failures when the token variables were set to `test-token`.
- `tests/conftest.py` will set `test-token` for all ten servers (row 11 of this Plan), matching `MCP_TEST_AUTH_HEADERS` in `tests/mcp_servers/_auth_headers.py`.

## Design decisions
- Reuse the existing `MCP_TEST_AUTH_HEADERS` constant; do not add a new helper.

## Alternatives considered
- A global autouse client patch: rejected, it would hide tests that check the 401 path.

## Implementation
### Target file
`tests/mcp_servers/git/test_mcp_git.py`

### Procedure
1. Add `from tests.mcp_servers._auth_headers import MCP_TEST_AUTH_HEADERS` if the module does not import it yet.
2. Pass `headers=MCP_TEST_AUTH_HEADERS` to each `TestClient(...)` that targets the real server application (an existing `headers=` argument is merged, not replaced).
3. Run the module with the three tokens set to a non-empty value and fix any remaining site the line list missed.

### Method
- Edit call sites only; do not change assertions except where a test asserted accept-all behavior.

### Details
- Evidence: verification run showed 1 failures in this module; `TestClient(` sites at lines 397.

## Compatibility considerations
- Test-only.

## Security considerations
- Fake token value `test-token` only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/git/test_mcp_git.py` with `MCP_GIT_AUTH_TOKEN=test-token MCP_CICD_AUTH_TOKEN=test-token MCP_WEB_SEARCH_AUTH_TOKEN=test-token` before the conftest row lands, then plain `uv run pytest tests/mcp_servers`; `uv run ruff check`, `uv run mypy`.

## Completion criteria
- The module passes with the non-empty test tokens and with the final conftest.

## Out of Scope
- Other test modules
- Changing what the tests assert about authentication

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the header changes per Implementation > Procedure | Completed | 20261023-130224 | 20261023-130224 | implemented; tests/mcp_servers 2468 passed; one additional test file discovered and added to the Plan (row 25); full suite run at the end of the batch |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261023-130224 | 20261023-130224 |  |

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
- **Requirement ID**: `REQ-005` (test migration to a non-empty test token and the shared header)
- **Source issue**: issues/20261023-114044_mcpstart003_four-mcp-servers-start-without-authentication-when-auth_token-is-empty.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261023-115211_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-123707
- **Related target files**: tests/mcp_servers/git/test_mcp_git.py