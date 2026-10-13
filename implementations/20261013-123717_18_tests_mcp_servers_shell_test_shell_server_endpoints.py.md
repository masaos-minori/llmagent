## Goal
- Send the shared Authorization header from the `TestClient` constructions in this file that target the Bearer-authenticated servers, so its tests keep exercising the routes once the servers verify the token (REQ-005).

## Scope
- In: the `client` fixture (one construction).
- Out: any assertion or test logic, and constructions that target other servers.

## Assumptions
- Row 16 (`tests/mcp_servers/_auth_headers.py`) exists.
- Measured in a scratch copy with the servers patched as designed: 9 failures without the header.
- The header is harmless before the servers change (an unauthenticated app ignores it), so this row lands first (Plan Step 2).

## Design decisions
- Pass `headers=MCP_TEST_AUTH_HEADERS` (new) at construction (the pattern of `tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_endpoints.py`); no change to test bodies.
- Leave constructions that target git, cicd, web-search, or rag-pipeline unchanged.

## Alternatives considered
- Per-request `headers=` arguments: rejected (more edits, easy to miss one).

## Implementation
### Target file
`tests/mcp_servers/shell/test_shell_server_endpoints.py`

### Procedure
1. Add the helper import (see Method).
2. Apply the construction changes listed in Details.
3. Run this file's tests and the directory's tests.

### Method
- Add the helper import as its own first-party import block after the third-party imports: `MCP_TEST_AUTH_HEADERS` (new) is imported from the module `tests.mcp_servers._auth_headers` (new). Let `uv run ruff check <file> --fix` (rule `I`) place it; `tests/agent/test_tool_audit.py` imports `tests.agent._config_test_defaults` the same way (a namespace sub-package without `__init__.py`, Explicit in code — `tests/agent/test_tool_audit.py`).
- Anchor for the import: `from fastapi.testclient import TestClient` at line 22.

### Details
One site, the `client` fixture (lines 53-54), Before/After:

```python
# Before:
def client() -> TestClient:
    return TestClient(shell_server.app)
# After:
def client() -> TestClient:
    return TestClient(shell_server.app, headers=MCP_TEST_AUTH_HEADERS)
```

## Compatibility considerations
- Test-only change; no production behavior. Meaningful after the server rows (2, 4, 6, 8, 10) land, harmless before.

## Security considerations
N/A: test code with a dummy token.

## Rollback considerations
- Revert this file; the tests then fail with 401 once the servers verify the token, so revert only together with the server rows.

## Validation plan
- `uv run ruff format tests/mcp_servers/shell/test_shell_server_endpoints.py` and `uv run ruff check tests/mcp_servers/shell/test_shell_server_endpoints.py --fix`.
- `uv run pytest tests/mcp_servers/shell/test_shell_server_endpoints.py -q` (before and after the server rows).
- `uv run pytest tests/mcp_servers -q -rs` — the measured set returns to 2049 passed and 6 skipped.

## Completion criteria
- Every construction listed in Details passes `headers=MCP_TEST_AUTH_HEADERS`.
- The file's tests pass both before and after the server rows are applied.

## Out of scope
- Production code, `tests/conftest.py`, and other test files.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the helper import and the construction changes | Pending | — | — | Plan Step 2 |
| 2 | Run this file's tests and `tests/mcp_servers` | Pending | — | — |  |

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
- **Requirement ID**: `REQ-005` (existing tests keep passing under authentication)
- **Source issue**: issues/20261013-113008_mcp007_register-bearer-auth-in-shell-github-file-mcp-servers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261013-120538_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261013-123717
- **Related target files**: tests/mcp_servers/shell/test_shell_server_endpoints.py
