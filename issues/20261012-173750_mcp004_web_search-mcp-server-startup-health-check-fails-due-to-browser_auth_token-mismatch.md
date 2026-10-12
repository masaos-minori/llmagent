# web_search MCP server startup health check fails due to browser_auth_token mismatch

## Priority
High

## Summary
The web-search MCP subprocess cannot reach a healthy state at startup: its `/health`
endpoint validates the Bearer token against `browser_auth_token`, but the agent's
lifecycle health checker authenticates with the server's main `auth_token`
(`MCP_WEB_SEARCH_AUTH_TOKEN`). Because these are distinct credentials, the health poll
always receives `401`, and the agent aborts startup after `startup_timeout_sec` with
`RuntimeError: MCP subprocess 'web_search' failed to start after retry`, even when every
token is configured correctly.

## Background
HTTP MCP servers run as agent-managed subprocesses and must pass a startup health check
against their `/health` endpoint before the agent treats them as ready
(`scripts/agent/http_lifecycle.py`). The health checker sends the server's configured
`auth_token` via `McpServerConfig.auth_headers()`, which returns
`{"Authorization": "Bearer {self.auth_token}"}`.

The web-search server attaches bearer-token auth middleware using
`_cfg.browser_auth_token` (loaded from `config/web_search_mcp_server.toml`), so every
endpoint — including `/health` — is validated against `browser_auth_token`. The
deployment document records `browser_auth_token` as a distinct credential from the
client-facing `auth_token`.

A recent change to `deploy/start_agent.sh` added a startup pre-flight that requires both
`MCP_WEB_SEARCH_AUTH_TOKEN` and `MCP_WEB_SEARCH_BROWSER_AUTH_TOKEN` to be set before
launching. Previously startup aborted earlier on the missing-token check, which masked
this health-check failure. With the pre-flight in place, startup now proceeds far enough
to hit the broken health check.

## Problem
web-search never becomes healthy, so the agent fails to start whenever
`browser_auth_token` differs from the main `auth_token`. This makes the web-search
server unusable in any normal deployment, where the two credentials are intentionally
distinct.

## Reason for Change
The pre-flight now surfaces this code path (previously hidden behind the missing-token
abort). web-search is a core search capability, and its startup failure blocks the whole
agent. This is a correctness/startup bug, not an environment or operator error.

## Implementation Intent
Make the web-search startup health check succeed without weakening its authorization
model. Evaluate the following directions and pick one (this is a design decision):

- Exempt `/health` from bearer auth on loopback for the health-check request only.
- Have the health checker send `browser_auth_token` when the server configuration
  exposes one separately from `auth_token`.
- Align the server-side health-check credential with the client-facing `auth_token`.

Preserve the browser-domain allowlist and `BrowserAuthorization` semantics. Make the
smallest change that fixes web-search and does not alter the health-check contract for
other servers.

## Target Files or Areas
- `scripts/mcp_servers/web_search/web_search_server.py` (the `attach_auth_middleware`
  call and the `/health` endpoint)
- `scripts/agent/http_lifecycle.py` (`_health_poll_until_ready`, `cfg.auth_headers()`)
- `scripts/mcp_servers/server.py` (`attach_auth_middleware`)
- `config/web_search_mcp_server.toml`
- Possibly `scripts/shared/mcp_config.py` (`auth_headers`)

## Required Changes
- Confirm the exact credential each side uses for `/health` against current source.
- Implement a fix so the startup health check passes while preserving authorization.
- Verify the fix does not regress the health checks of other HTTP subprocess servers.
- Add or adjust tests for the health-check authentication path.

## Constraints
- Do not weaken bearer-token auth on protected endpoints.
- Keep the shared health-poll contract in `http_lifecycle.py` intact.
- Leave the `browser_allowed_domains` allowlist and `BrowserAuthorization` behavior
  unchanged.
- Keep `browser_auth_token` distinct from `auth_token` unless the chosen design
  explicitly couples them.

## Acceptance Criteria
- web-search passes its startup `/health` check within `startup_timeout_sec` when both
  tokens are set.
- The agent starts successfully with web-search enabled and both tokens configured.
- `/health` still returns `401` for a request presenting an incorrect or unauthenticated
  token (authorization preserved).
- Other HTTP subprocess servers still pass their startup health checks.

## Testing Expectations
- Unit test for the health-check authentication path: assert which header the checker
  sends versus which credential the server validates.
- Manual/integration: start the agent with web-search enabled and both tokens set, and
  confirm no startup failure.
- Regression: confirm the health checks of the other HTTP subprocess servers still pass.

## Documentation Impact
Yes. Update `docs/22_mcp/mcp_06_14_mcp-authentication-setup.md` and
`docs/90_deployment/deployment_01_deployment.md` section 2.5 to record that web-search
additionally requires `MCP_WEB_SEARCH_BROWSER_AUTH_TOKEN`, and to document the resolved
issue (or a Known Issues note if unresolved). Point to canonical sources; do not dump
implementation detail.

## Out of Scope
- Changing the auth model for non-web-search servers.
- Revisiting the pre-flight logic in `deploy/start_agent.sh` (already implemented).
- Altering `browser_allowed_domains` allowlist behavior.

## Dependencies
Related to the `deploy/start_agent.sh` `.env`/pre-flight change already committed;
re-verify the health check against current source, since the pre-flight is what now
exposes this path.

## Unresolved Questions
- Which fix direction is preferred: exempt `/health` on loopback, have the health
  checker send `browser_auth_token`, or align the server-side health credential with the
  main `auth_token`?
- Should `browser_auth_token` remain a distinct credential, or is the health check
  supposed to use it deliberately?
- Is the mismatch intentional by design or an oversight?

## AI Implementation Instruction
Confirm the root cause against current source before changing anything: the health
checker sends `cfg.auth_headers()` (the main `auth_token`) while
`web_search_server.py` protects `/health` with `browser_auth_token`. Do not rewrite
unrelated servers. Prefer the minimal change that preserves the authorization model. If
the intended design is unclear, stop and report rather than guessing. Do not alter the
`browser_allowed_domains` allowlist or `BrowserAuthorization` handling.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261012-173750
- **Related target files**: `scripts/mcp_servers/web_search/web_search_server.py`,
  `scripts/agent/http_lifecycle.py`, `scripts/mcp_servers/server.py`,
  `config/web_search_mcp_server.toml`
