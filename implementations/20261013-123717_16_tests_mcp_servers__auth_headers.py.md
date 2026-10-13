## Goal
- Provide one shared Authorization header for the tests that call the five authenticated MCP server applications, so the header value is defined once and matches the token `tests/conftest.py` gives the five variables (REQ-005).

## Scope
- In: a new module defining the token constant and the header mapping.
- Out: every test edit (rows 17-28) and `tests/conftest.py`, which stays unchanged.

## Assumptions
- `tests/conftest.py` sets `MCP_SHELL_AUTH_TOKEN`, `MCP_GITHUB_AUTH_TOKEN`, `MCP_FILE_READ_AUTH_TOKEN`, `MCP_FILE_WRITE_AUTH_TOKEN`, and `MCP_FILE_DELETE_AUTH_TOKEN` to `"test-token"` through `os.environ.setdefault` (loop ending at line 46); the helper must use the same value (Plan A-5).
- `tests/mcp_servers/` has no `__init__.py`, and `tests/__init__.py` exists; the namespace import was confirmed in a scratch copy.

## Design decisions
- Two module constants only: the token string and a header mapping built from it; no function, no fixture.
- The module docstring names `tests/conftest.py` as the source of the value, so a drift is easy to trace (Plan Risks).

## Alternatives considered
- A pytest fixture or a `conftest.py` in `tests/mcp_servers/`: rejected — the 43 construction sites are plain `TestClient(...)` calls in module-level fixtures and test bodies, so a constant is the smallest change; a conftest would also alter fixture collection.

## Implementation
### Target file
`tests/mcp_servers/_auth_headers.py` (new)

### Procedure
1. Create the module with the content below.
2. Confirm the import works from a test module (`tests.mcp_servers._auth_headers`).

### Method
- Annotate the mapping as `dict[str, str]` so `TestClient(..., headers=...)` type-checks.
- Keep the file free of imports other than `from __future__ import annotations`.

### Details
New file content (module `tests/mcp_servers/_auth_headers.py`):

```python
"""tests/mcp_servers/_auth_headers.py

Authorization header for tests that call the Bearer-authenticated MCP server
applications (shell, github, file-read, file-write, file-delete).

The token is the value tests/conftest.py assigns to the five
MCP_*_AUTH_TOKEN environment variables; keep the two in step.
"""

from __future__ import annotations

MCP_TEST_TOKEN = "test-token"
MCP_TEST_AUTH_HEADERS: dict[str, str] = {"Authorization": f"Bearer {MCP_TEST_TOKEN}"}
```

## Compatibility considerations
- Additive test-only module; nothing imports it until rows 17-28 are applied.

## Security considerations
- The value is a dummy test token already present in `tests/conftest.py`; no real secret.

## Rollback considerations
- Delete the file (after reverting rows 17-28, which import it).

## Validation plan
- `uv run ruff format tests/mcp_servers/_auth_headers.py`, `uv run ruff check tests/mcp_servers/_auth_headers.py`.
- `uv run python -c "from tests.mcp_servers._auth_headers import MCP_TEST_AUTH_HEADERS; print(MCP_TEST_AUTH_HEADERS)"` from the repository root.

## Completion criteria
- The module exists with `MCP_TEST_TOKEN` (new) and `MCP_TEST_AUTH_HEADERS` (new), the token equals the value in `tests/conftest.py`, and a test module can import it.

## Out of scope
- Editing `tests/conftest.py` or any server code.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create the helper module | Pending | — | — | Plan Step 2; must land before rows 17-28 |
| 2 | Run the validation commands | Pending | — | — |  |

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
- **Requirement ID**: `REQ-005` (existing tests keep passing under authentication: shared header helper)
- **Source issue**: issues/20261013-113008_mcp007_register-bearer-auth-in-shell-github-file-mcp-servers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261013-120538_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261013-123717
- **Related target files**: tests/mcp_servers/_auth_headers.py
