## Goal
Make git-mcp refuse to start when its `auth_token` is empty by calling `require_auth_token()` (new) where the auth middleware is attached (`REQ-002`).

## Scope
- Change the `attach_auth_middleware(...)` call at line 177 and the `mcp_servers.server` import list and correct the module docstring line 12 ("Optional Bearer-token auth" becomes a statement that a non-empty token is required).
- No change to tool logic, posture checks or other modules.

## Assumptions
- The module is 14977 bytes, so a few added lines stay under the 16384-byte module-size gate.
- The helper exists in `scripts/mcp_servers/server.py` before this row is implemented (row 01 of this Plan).

## Design decisions
- Pass the label `git-mcp` and the variable name "MCP_GIT_AUTH_TOKEN" so the message matches the six servers that already refuse an empty token.

## Alternatives considered
- Inline `if not _cfg.auth_token: raise RuntimeError(...)` as in shell and github: rejected, it repeats the message in four more places.

## Implementation
### Target file
`scripts/mcp_servers/git/git_server.py`

### Procedure
1. Add `require_auth_token` (new) to the `from mcp_servers.server import (...)` list.
2. Replace `attach_auth_middleware(cast(_FastAPIApp, app), _cfg.auth_token or "")` (line 177) with a call that passes `require_auth_token("git-mcp", "MCP_GIT_AUTH_TOKEN", _cfg.auth_token)` as the token.
3. Edit the module docstring (line 12) so it no longer calls Bearer authentication optional.

### Method
- Keep the call at the same position so the middleware is still attached at import time, before any route is added.

### Details
- Evidence: `scripts/mcp_servers/git/git_server.py` line 177; probe: with the token set to an empty string the module imported and an unauthenticated `GET /v1/tools` returned 200.
- Reference only: `scripts/mcp_servers/shell/shell_server.py` (existing import-time refusal and message format).

## Compatibility considerations
- A server started with an empty token now fails at import instead of serving unauthenticated; Agent-managed starts already reject an empty token, so no supported flow changes.

## Security considerations
- Closes a fail-open start path: an empty `auth_token` makes the server refuse to start; no token value is printed or logged (the message names the variable only).

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `tests/mcp_servers/test_require_auth_token.py` (all-ten refusal test) and the server's own test directory after the test migration rows.
- `uv run ruff check`, `uv run mypy`, `uv run bandit -r scripts/mcp_servers`, `uv run python tools/check_module_size.py`, `uv run python tools/check_docstrings.py`, `lint-imports`.

## Completion criteria
- Importing the module with an empty "MCP_GIT_AUTH_TOKEN" fails with the "auth_token is empty" error; with a non-empty token it imports and requests without the header return 401.
- Module-size and docstring gates pass.

## Out of Scope
- Replacing the inline checks in the other six servers (plan UNK-02)
- Posture severity of an empty token (plan UNK-01)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the import and the middleware call per Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan (`tests/mcp_servers/test_require_auth_token.py`, tracked in its own document) | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-002` (call the shared check before attaching the middleware), `REQ-004` (docstring wording)
- **Source issue**: issues/20261023-114044_mcpstart003_four-mcp-servers-start-without-authentication-when-auth_token-is-empty.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261023-115211_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-123707
- **Related target files**: scripts/mcp_servers/git/git_server.py
