# web-search tool calls return 401 when browser_auth_token differs from auth_token

## Priority
High

## Summary
The web-search MCP server validates every endpoint except `/health` against `browser_auth_token`, while the agent sends the server's main `auth_token` on every tool call. When the two credentials differ, which the deployment documents as the normal case, the agent now starts (the startup health check was fixed by plan mcp004) but every `search_web` and `browser_fetch` call is rejected with 401. Decide which credential authenticates tool calls and make the server and the agent agree.

## Background
- Plan `plans/done/20261012-175600_plan.md` (mcp004) fixed only the startup `/health` check, by an opt-in loopback admission on the shared Bearer-auth middleware. The plan recorded this gap as `UNK-03` (a Plan Gap found while generating the implementation procedures) and, by decision, left it to a separate issue.
- `docs/22_mcp/mcp_04_01_web-search-file-read-github.md` describes `browser_auth_token` as the "Bearer token for `browser_fetch` calls only (independent of `search_web`)". `docs/90_deployment/deployment_01_deployment.md` and `config/web_search_mcp_server.toml` call it a credential distinct from the client-facing `auth_token`.
- No open issue under `issues/` covers this (checked: the open items are the legacy design memos only).

## Problem
- Evidence (`Verified by run`): with `MCP_WEB_SEARCH_AUTH_TOKEN=main-secret` and `MCP_WEB_SEARCH_BROWSER_AUTH_TOKEN=browser-secret` set, the real web-search app (loaded in-process, client address 127.0.0.1) returns: `/health` with the main token 200 (after mcp004); `/v1/tools` with the main token 401; `/v1/call_tool` with the main token 401; `/v1/tools` with the browser token 200.
- Evidence (`Explicit in code`): the server registers one global middleware with `_cfg.browser_auth_token`, so no route other than `/health` (and only from loopback) accepts the main token. The agent's `HttpTransport` sends `Authorization: Bearer {cfg.auth_token}` (the main token) for tool calls, and the lifecycle manager sends the same header on health probes.
- Evidence (`Explicit in code`): documentation and code disagree. The configuration reference says the browser token applies to `browser_fetch` only, but the middleware applies it to `search_web` and every other endpoint as well.
- Not reproduced end to end through a running agent: the agent-side header was confirmed by reading `scripts/shared/http_transport.py`, not by a live session. The server-side rejection was run.
- Consequence: after mcp004 the agent starts with web-search enabled and both tokens set to different values, but web-search is unusable. With equal values it works, which makes the second token pointless in practice.

## Reason for Change
- web-search is a core capability; a deployment that follows the documented setup (two distinct tokens) reaches an apparently healthy server that rejects every tool call, a failure that the health check cannot reveal.
- The mcp004 fix made startup succeed, so this failure is now the next one an operator meets.

## Implementation Intent
- Decide the credential model first (see Unresolved Questions), then make server and agent consistent with it, so that one credential per call path is sent by the agent and accepted by the server.
- Keep the protection of `browser_fetch`'s own purpose (a separate credential for the browser tool, if that is still wanted) explicit rather than accidental.
- Keep the mcp004 behavior (loopback `/health` admission) unless the chosen model makes it unnecessary.
- Preserve the allowlist and authorization behavior of `browser_fetch`.

## Target Files or Areas
- `scripts/mcp_servers/web_search/web_search_server.py` (which token the middleware validates, per route)
- `scripts/mcp_servers/server.py` (shared middleware, only if the model needs per-route or multi-token validation)
- `scripts/mcp_servers/web_search/web_search_models.py` and `config/web_search_mcp_server.toml` (the `browser_auth_token` setting), if the model changes it
- `scripts/shared/http_transport.py` and `scripts/shared/mcp_config.py`, only if the agent must send a different credential per tool
- Tests: `tests/mcp_servers/web_search/` and `tests/agent/` health and transport tests
- Docs: `docs/22_mcp/mcp_04_01_web-search-file-read-github.md`, `docs/22_mcp/mcp_06_14_mcp-authentication-setup.md`, `docs/90_deployment/deployment_01_deployment.md`, `docs/91_security/security_01_architecture-and-trust-boundaries.md`

## Required Changes
- Choose and record the credential model.
- Change the server and, if needed, the agent so that a tool call carrying the credential the agent sends is accepted, and one carrying any other credential is rejected.
- Add a test that runs the real web-search app with two distinct tokens and calls a tool endpoint with the credential the agent sends.
- Update the documents that describe the browser token so they match the chosen model.

## Constraints
- Do not weaken authentication: a missing or wrong token on a protected route must still return 401, from loopback as well as from any other address.
- Do not change the other servers' behavior (git, rag-pipeline, cicd, mdq).
- Keep secrets out of logs, tests, and documentation.
- Keep the `browser_allowed_domains` allowlist and `BrowserAuthorization` behavior unchanged.

## Acceptance Criteria
- With two distinct tokens configured, a `search_web` call and a `browser_fetch` call made the way the agent makes them succeed (or `browser_fetch` is rejected by its allowlist, not by authentication).
- A request with a missing or wrong token to a protected route is rejected with 401 from a loopback client.
- The startup health check still passes (mcp004 behavior preserved or replaced by an equivalent).
- The documents above state the same credential model as the code.
- A test using the real application object with two distinct tokens covers the tool path.

## Testing Expectations
- Unit and regression tests in `tests/mcp_servers/web_search/` that load the real app with two distinct token values (as the reproduction above does) and call `/v1/tools` and `/v1/call_tool`.
- A transport-level test that the credential sent for web-search tool calls is the one the server accepts.
- `uv run pytest`, `uv run ruff check`, `uv run mypy --no-namespace-packages scripts/`, and the documentation checkers for the edited docs.
- Manual verification: start the agent with web-search enabled and two distinct tokens, and run one `search_web` call.

## Documentation Impact
- Yes. Document the chosen credential model, which token each path uses, and the operator setup (one or two secrets). Resolve the current contradiction between the "`browser_fetch` only" description and the whole-server enforcement. Update the Known Issues or setup notes touched by mcp004.

## Out of Scope
- The startup `/health` admission already done in mcp004.
- Authentication of the other MCP servers, the eventbus, and the `browser_allowed_domains` allowlist.
- Changing how secrets are loaded from the environment.

## Dependencies
- Follows plan `plans/done/20261012-175600_plan.md` (mcp004), which it extends; it assumes that change is deployed or merged.
- The mcp004 code is committed but not yet deployed to `/opt/llm/`; deploy ordering is a separate concern.
- Sibling-issue check: no open issue under `issues/` touches the same files.

## Unresolved Questions
- Which credential model is intended? Candidates: (a) the server validates the main `auth_token` on every route and `browser_auth_token` is dropped or reserved for browser-specific use; (b) the agent sends the browser token for `browser_fetch` and the main token for `search_web`, and the server accepts each on its own routes; (c) the server accepts either token on protected routes; (d) document that both variables must hold the same value. This is a design decision for the maintainer.
- Is `browser_auth_token` meant to protect `browser_fetch` only, as `mcp_04_01` says, or the whole server, as the middleware does today? The code and the document disagree.
- Does the agent have any mechanism today to send a per-tool credential? Not confirmed beyond `HttpTransport`'s single token per server.
- The reproduction ran the server in-process; whether the live agent hits the same 401 on a tool call is expected from the code but not observed.

## AI Implementation Instruction
- Stop and report the Unresolved Questions to the maintainer before choosing a credential model; do not pick one silently.
- Change only the files listed under Target Files or Areas, and keep every protected route authenticated.
- Do not touch the other servers' middleware calls.
- Add the two-token test before the fix and see it fail first.
- Keep the loopback `/health` admission unless the chosen model replaces it with a tested equivalent.

## Traceability
- **Workflow phase**: plan-to-implementation-procedure (Plan Gap found while generating procedures for mcp004), filed through issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/done/20261012-175600_plan.md
- **Source implementation procedure**: implementations/done/20261012-181104_01_scripts_mcp_servers_server.py.md
- **Generated at**: 20261012-182600
- **Related target files**: scripts/mcp_servers/web_search/web_search_server.py, scripts/mcp_servers/server.py, scripts/mcp_servers/web_search/web_search_models.py, config/web_search_mcp_server.toml, scripts/shared/http_transport.py, scripts/shared/mcp_config.py, docs/22_mcp/mcp_04_01_web-search-file-read-github.md, docs/22_mcp/mcp_06_14_mcp-authentication-setup.md, docs/90_deployment/deployment_01_deployment.md, docs/91_security/security_01_architecture-and-trust-boundaries.md
