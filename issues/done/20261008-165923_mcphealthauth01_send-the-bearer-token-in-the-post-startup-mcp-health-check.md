# Send the Bearer token in the post-startup MCP health check

## Priority
High

## Summary
The Agent's post-startup health check calls `GET <server>/health` without an `Authorization` header, but every MCP server that attaches `attach_auth_middleware()` with a non-empty token answers 401 on `/health`; the check then fails and startup aborts with a FATAL message.

## Background
Found while implementing the rag-pipeline inbound authentication (plans/20261008-095953_plan.md, REQ-001). Attaching the middleware to rag-pipeline-mcp made its `/health` return 401, which exposed that the probe never sends a token.

## Problem
- `McpServerStarter.verify_health()` and `_verify_single_health()` call `client.get(url + "/health")` with no headers and raise `RuntimeError("HTTP 401")` on any non-200 status (Explicit in code — `scripts/agent/startup_mcp_starter.py` lines 136-139 and 175-179).
- `attach_auth_middleware()` has no path exemption, so `/health` requires the Bearer token when the token is non-empty (Explicit in code — `scripts/mcp_servers/server.py`; verified: with `MCP_GIT_AUTH_TOKEN=abc`, `GET /health` on the git app returns 401).
- `port_is_responding()` in `scripts/mcp_launcher.py` treats any status below 500 as "up", so it is not affected.
- Agent startup validation rejects an empty `auth_token` for Agent-managed servers, so every subprocess server in `config/agent.toml` is subject to this (Explicit in code — `scripts/agent/startup_validation.py`, as described in the docstring of `attach_auth_middleware`).
- Whether production startup currently passes through another path is unknown; no deployment was inspected.

## Reason for Change
- A health probe that cannot authenticate either fails startup or hides real failures behind a 401.

## Implementation Intent
- Make the probe send the server's configured Bearer token, or decide that `/health` is intentionally unauthenticated and exempt it in `attach_auth_middleware()`.

## Target Files or Areas
- `scripts/agent/startup_mcp_starter.py`; `scripts/mcp_servers/server.py` (only if `/health` is exempted); `tests/agent/` startup tests (to be read)

## Required Changes
- Choose one approach (see Unresolved Questions) and implement it for all subprocess servers.
- Add a test that a server with a non-empty token passes the post-startup health check.

## Constraints
- Do not log the token; a `/health` exemption must not expose tool data.

## Acceptance Criteria
- With non-empty tokens configured for all subprocess servers, `verify_health()` succeeds against running servers.
- A wrong token still fails the check.

## Testing Expectations
- Unit tests with a mocked or in-process server; ruff, mypy, targeted pytest.

## Documentation Impact
Update the health-check description in the agent startup documents and `docs/91_security/security_01_architecture-and-trust-boundaries.md` if `/health` becomes exempt.

## Out of Scope
- Changing `port_is_responding()` and the circuit-breaker logic.

## Dependencies
N/A: none

## Unresolved Questions
- Is `/health` meant to be unauthenticated (monitoring role) or authenticated? `docs/91_security/security_01_architecture-and-trust-boundaries.md` lists a Monitoring row for GET health; its intent was not confirmed.
- Does production currently pass the post-startup check (for example through a different configuration)? Unknown.

## AI Implementation Instruction
Confirm the intended `/health` policy with the owner before choosing the approach. Keep the change in one place for all servers.

## Traceability
- **Workflow phase**: manually filed
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261008-095953_plan.md
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261008-165923
- **Related target files**: `scripts/agent/startup_mcp_starter.py`, `scripts/mcp_servers/server.py`
