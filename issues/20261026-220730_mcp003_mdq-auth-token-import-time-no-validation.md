# MDQ server reads auth_token at import time without validation before attaching middleware

## Priority
Medium

## Summary
The MDQ server loads `_AUTH_TOKEN` at module import time via `_load_auth_token()` and attaches the auth middleware unconditionally, even though the token value is not validated for non-empty status until after the middleware is attached.

## Background
The MDQ server module (`mdq_server.py`) defines `_load_auth_token()` at lines 72-78, which reads `auth_token` from `mdq_mcp_server.toml` and returns an empty string when the config is missing or the key is absent. The module-level assignment `_AUTH_TOKEN: str = _load_auth_token()` (line 81) runs at import time. The auth middleware is attached at line 471 via `attach_auth_middleware(cast(_FastAPIApp, app), _AUTH_TOKEN)`. The non-empty check (lines 466-470) raises `RuntimeError` only if `_AUTH_TOKEN` is empty, but this check happens AFTER the middleware attachment.

## Problem
If `_AUTH_TOKEN` is empty, the middleware is attached with an empty token value before the `RuntimeError` is raised. This means:
1. The FastAPI app has a middleware layer that checks for a Bearer token, but the token value is empty — the middleware may accept any request or reject all requests depending on its internal logic.
2. The `RuntimeError` is raised after the middleware is attached, so the middleware is partially configured.
3. If the middleware's `require_auth_token` function uses the empty token as a comparison value, it will reject ALL requests (including health checks), making the server appear healthy but non-functional.

Additionally, the import-time execution order is fragile:
- `_AUTH_TOKEN` is loaded at line 81
- `_service` is instantiated at line 82
- Dependencies are collected at lines 88-96
- Posture is built at lines 97-99
- Middleware is attached at line 471
- Non-empty check is at lines 466-470

The middleware attachment at line 471 depends on `_AUTH_TOKEN` being set, but the non-empty validation at lines 466-470 is a separate guard that fires after the middleware is already attached.

## Reason for Change
The current ordering creates a window where the middleware is attached with an invalid (empty) token, which could lead to unexpected behavior: either rejecting all requests or accepting all requests depending on the middleware's implementation.

## Implementation Intent
Move the non-empty auth token check to execute BEFORE the middleware is attached. This ensures the middleware is only attached when a valid token is available.

## Target Files or Areas
- `scripts/mcp_servers/mdq/mdq_server.py` — `_AUTH_TOKEN` loading (line 81), middleware attachment (line 471), non-empty check (lines 466-470)

## Required Changes
- Move the non-empty auth token check (lines 466-470) to execute before the middleware attachment (line 471)
- Alternatively, have `_load_auth_token()` raise `RuntimeError` when the token is empty, eliminating the need for a separate check
- Ensure the middleware is never attached with an empty token value

## Constraints
- Must not change the existing posture-gate semantics
- Must preserve the current error message format for the empty token case

## Acceptance Criteria
- Middleware is never attached with an empty `_AUTH_TOKEN`
- Empty token still raises `RuntimeError` with the same message
- Health endpoint is unreachable when auth_token is empty (not just non-functional)

## Testing Expectations
- Unit test: verify middleware is not attached when `_AUTH_TOKEN` is empty
- Integration test: verify `RuntimeError` is raised before middleware attachment
- Regression test: ensure existing empty-token error message is preserved

## Documentation Impact
Update `_load_auth_token()` docstring to document the empty-token behavior.

## Out of Scope
- Changes to the middleware attachment mechanism itself
- Changes to how `_AUTH_TOKEN` is read from the config file

## Dependencies
N/A: none

## Unresolved Questions
- Does `attach_auth_middleware` with an empty token value reject all requests or accept all requests?
- Is there a similar pattern in other MCP servers (file/delete, git)?

## AI Implementation Instruction
In `scripts/mcp_servers/mdq/mdq_server.py`, move the non-empty auth token check (lines 466-470) to execute before the middleware attachment (line 471). Do not modify any other MCP server's auth flow.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261026-220730
- **Related target files**: scripts/mcp_servers/mdq/mdq_server.py
