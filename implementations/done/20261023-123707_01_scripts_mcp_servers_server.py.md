## Goal
Add one shared helper that raises the standard error when an auth token is empty (`REQ-001`).

## Scope
- Add `require_auth_token()` (new) next to `attach_auth_middleware()`.
- No change to `attach_auth_middleware` behavior (its accept-all fallback stays for standalone testing).

## Assumptions
- The module is 12937 bytes and the posture-gate plan also adds about 700 bytes; the total must stay under 16384.

## Design decisions
- Raise `RuntimeError` with the message format used by shell, github, mdq and the file servers so operators see one error shape.
- Return the token so callers can pass it straight to `attach_auth_middleware`.

## Alternatives considered
- Make `attach_auth_middleware` itself refuse an empty token: rejected, existing base tests use the empty-token path deliberately and the posture flow documents it.

## Implementation
### Target file
`scripts/mcp_servers/server.py`

### Procedure
1. Add `require_auth_token(label: str, env_var: str, token: str | None) -> str` (new) after `attach_auth_middleware` in `scripts/mcp_servers/server.py`.
2. Raise `RuntimeError(f"{label}: auth_token is empty; set {env_var} to a non-empty value (the server does not start without Bearer authentication)")` when `not token`; otherwise return `token`.
3. Give it a docstring that states it never echoes the token.

### Method
- Pure function, no logging, no imports beyond what the module has.

### Details
- Evidence: `server.py:95-133` (`attach_auth_middleware` docstring documents the accept-all fallback); message format from `shell_server.py` and `github_server.py`.

## Compatibility considerations
- Additive; no existing caller changes.

## Security considerations
- Closes a fail-open start path: an empty `auth_token` makes the server refuse to start; no token value is printed or logged (the message names the variable only).

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `tests/mcp_servers/test_require_auth_token.py` and `tests/mcp_servers/test_mcp_server_base.py`.
- `uv run ruff check`, `uv run mypy`, `uv run bandit -r scripts/mcp_servers`, `uv run python tools/check_module_size.py`, `uv run python tools/check_docstrings.py`, `lint-imports`.

## Completion criteria
- The helper raises for `""` and `None` and returns a non-empty token unchanged; the message names the label and variable only.

## Out of Scope
- Changing `attach_auth_middleware`
- Posture contract changes

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement `require_auth_token()` (new) per Implementation > Procedure | Completed | 20261023-130206 | 20261023-130206 | implemented; tests/mcp_servers 2468 passed; one additional test file discovered and added to the Plan (row 25); full suite run at the end of the batch |
| 2 | Add or update tests per Validation plan (`tests/mcp_servers/test_require_auth_token.py`, tracked in its own document) | Completed | 20261023-130206 | 20261023-130206 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261023-130206 | 20261023-130206 |  |

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
- **Requirement ID**: `REQ-001` (shared `require_auth_token()` (new))
- **Source issue**: issues/20261023-114044_mcpstart003_four-mcp-servers-start-without-authentication-when-auth_token-is-empty.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261023-115211_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-123707
- **Related target files**: scripts/mcp_servers/server.py