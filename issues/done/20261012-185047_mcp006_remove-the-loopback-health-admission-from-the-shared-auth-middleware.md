# Remove the loopback health admission from the shared auth middleware

## Priority
Medium

## Summary
Plan mcp004 added an opt-in switch to the shared Bearer-auth middleware that admits `/health` from a loopback client without a token, and web-search opted in. Plan mcp005 then moved web-search to the shared `auth_token`, which is exactly what the agent's health poll sends, so the admission no longer has a purpose. It leaves web-search as the only server whose health endpoint (with provider details and metrics) answers without credentials. Remove the switch, its helper, the web-search opt-in, and the tests and documentation that describe it.

## Background
- mcp004 (`plans/done/20261012-175600_plan.md`) fixed the startup health check while web-search still validated a separate browser token, by admitting the exact health path from loopback regardless of the presented token.
- mcp005 (`plans/done/20261012-183348_plan.md`) retired the browser token: the server now validates the same `auth_token` the agent sends. Both plans recorded the redundancy as `UNK-02` and deferred the removal to a separate issue.
- The two changes are committed but not yet deployed to `/opt/llm/`, and no live agent run has confirmed the mcp005 behavior (mcp005 `UNK-03`).
- No open issue under `issues/` covers this (the open items are the legacy design memos only).

## Problem
- Evidence (`Verified by run`): with `MCP_WEB_SEARCH_AUTH_TOKEN` set, the real web-search app answers `/health` from a loopback client with no token with 200 and a body containing `status`, `ready`, `liveness`, `dependencies`, and `details` (the details include `provider`, `browser_provider`, `metrics`, `browser_metrics`, and `service`). With the shared token it also answers 200. The unauthenticated answer comes only from the admission.
- Evidence (`Explicit in code`): `exempt_health_on_loopback` is passed by exactly one caller, the web-search server; the git, rag-pipeline, cicd, and mdq callers do not pass it.
- Evidence (`Explicit in code`): the agent's health poll and liveness check send the server's `auth_token`, which is the token web-search now validates, so the poll passes through ordinary validation. Tests already show this for a server without the switch (the poll succeeds when the server token equals the main token).
- No other consumer needs an unauthenticated health request: the launcher's port probe treats any response below 500 (including 401) as "responding", and the deploy scripts do not probe the MCP servers' health endpoints (checked by search).
- Consequence: dead, security-relevant code in the shared middleware, and an inconsistency (one server exposes health details without credentials to any local process; the others do not).

## Reason for Change
- The admission was a workaround for a credential mismatch that no longer exists; keeping it widens the unauthenticated surface of one server for no benefit and adds a path that every future change to the middleware must keep correct.
- Removing it restores one rule for every MCP server: all routes, including `/health`, require the server's token.

## Implementation Intent
- Remove the opt-in parameter, its private helper, and the web-search opt-in; keep the middleware's behavior for every other case exactly as it was before mcp004.
- Remove or rewrite the tests whose subject was the admission, keeping the coverage that is still meaningful (the agent poll against a server using the shared token; the real-application test, with its health expectation changed to require the token).
- Update the two documents that mention the admission.
- Do this only after mcp005 is deployed and confirmed against a live agent, so the removal cannot reintroduce a failing startup poll on a host that still has the old configuration.

## Target Files or Areas
- `scripts/mcp_servers/server.py` (the parameter, `_is_loopback_client`, the `ipaddress` import, the docstring)
- `scripts/mcp_servers/web_search/web_search_server.py` (the opt-in keyword)
- `tests/mcp_servers/web_search/test_web_search_health.py` (the loopback tests, the opt-in AST tests, the real-application expectation for `/health`)
- `tests/agent/test_http_lifecycle_health_check.py` (the switch-on poll test and the helper's switch parameter)
- `docs/22_mcp/mcp_06_14_mcp-authentication-setup.md`, `docs/90_deployment/deployment_01_deployment.md` (the sentences that mention the loopback admission)

## Required Changes
- Delete the `exempt_health_on_loopback` parameter and its logic from `attach_auth_middleware`, delete `_is_loopback_client` and the now-unused import, and restore the docstring.
- Remove the opt-in keyword from the web-search call.
- Replace the tests of the admission with one test that an unauthenticated `/health` is rejected with 401 (including from loopback) and one that the shared token is accepted; update the real-application test's health expectation accordingly.
- Remove the two documentation sentences.

## Constraints
- After the change every route of every MCP server, including `/health`, must require the correct token; no new exemption may be introduced.
- Do not change the agent's health poll, `auth_headers`, or any server's token source.
- Do not deploy this before mcp005 is deployed (see Dependencies).
- Keep the loopback-only bind verification in the server runner unchanged.

## Acceptance Criteria
- A request to `/health` without a token, or with a wrong token, is rejected with 401 on web-search and on every other server, including from a loopback client.
- The agent's startup poll and liveness check still succeed against web-search with the shared token.
- `exempt_health_on_loopback` and `_is_loopback_client` no longer exist in the repository, and no test or document refers to them.
- The remaining tests, ruff, mypy (`--no-namespace-packages`), bandit, lint-imports, and the documentation checkers pass.

## Testing Expectations
- `uv run pytest tests/mcp_servers tests/agent -q`, then the full suite once.
- A real-application check (as in the mcp005 tests) that `/health` returns 401 without a token and 200 with the shared token.
- Manual verification after deployment: start the agent with web-search enabled and confirm the startup health check passes.

## Documentation Impact
- Yes: remove the sentences added by mcp004 that say the health endpoint is admitted from a loopback client without a token (the authentication setup guide's troubleshooting solution and the deployment guide's note). No other document describes it.

## Out of Scope
- The token model itself (settled in mcp005), the other servers' authentication, and the server runner's loopback bind check.
- Any new unauthenticated health or readiness endpoint (a separate design if wanted).

## Dependencies
- Depends on mcp005 (`plans/done/20261012-183348_plan.md`) being deployed together with mcp004, and on a live check that the web-search startup poll and a tool call succeed with the shared token (mcp005 `UNK-03`). Deploying this removal first, or onto a host with the old configuration, would bring the startup `401` back.
- Sibling-issue check: no open issue under `issues/` touches the same files.

## Unresolved Questions
- Should the generic capability stay in the shared middleware for a future server that needs an unauthenticated loopback health route? Recommended: no; remove it and design it again if a real need appears.
- Is a live agent run against the deployed mcp005 build available before this is planned? Not confirmed; the dependency above makes it a precondition.

## AI Implementation Instruction
- Change only the files listed under Target Files or Areas.
- Remove the admission completely; do not leave a disabled parameter behind.
- Keep every other middleware behavior and the coverage of the agent poll against a shared-token server.
- Stop and report if the live verification of mcp005 has not happened, rather than assuming it.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/done/20261012-183348_plan.md
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261012-185047
- **Related target files**: scripts/mcp_servers/server.py, scripts/mcp_servers/web_search/web_search_server.py, tests/mcp_servers/web_search/test_web_search_health.py, tests/agent/test_http_lifecycle_health_check.py, docs/22_mcp/mcp_06_14_mcp-authentication-setup.md, docs/90_deployment/deployment_01_deployment.md
