# Four MCP servers start without authentication when auth_token is empty

## Priority
Medium

## Summary
git-mcp, cicd-mcp, rag-pipeline-mcp and web-search-mcp serve every request without a Bearer token when their configured `auth_token` resolves to an empty string, and their security posture still reports `validated = True`. The other six servers (shell, github, mdq, file-read, file-write, file-delete) refuse to import in the same situation. Review severity: Medium after verification (inconsistent fail-open behavior for a standalone start; Agent-managed starts are already protected).

## Background
`attach_auth_middleware()` in `scripts/mcp_servers/server.py` skips authentication when the token is empty; its docstring says this accept-all fallback exists only for standalone testability and relies on Agent startup validation to reject empty tokens. shell, github, mdq and the three file servers add an import-time `RuntimeError` for an empty token. git, cicd, rag_pipeline and web_search only call `attach_auth_middleware(app, token or "")`. The shared startup flow (`check_auth_token_present` in `scripts/shared/security/startup_flow.py`) classifies an empty token as WARNING, not FAILED (documented there as a deliberate Plan decision), so the posture gate cannot stop these servers either. The module docstrings of `git_server.py` and `cicd_server.py` still describe the token as "optional".

## Problem
Confirmed by a probe (evidence label: Confirmed by execution, confidence High). With `MCP_GIT_AUTH_TOKEN`, `MCP_CICD_AUTH_TOKEN`, `MCP_RAG_PIPELINE_AUTH_TOKEN` and `MCP_WEB_SEARCH_AUTH_TOKEN` set to an empty string, importing each server module succeeded, an unauthenticated `GET /v1/tools` returned HTTP 200, and the posture was `validated = True` with only `common.auth_token: WARNING`. The same probe against the other six servers failed at import with the "auth_token is empty" RuntimeError. An unset variable is already rejected by the config loader, so the exposure requires an empty value (for example `export MCP_GIT_AUTH_TOKEN=`, or an empty literal in the TOML file). The Agent validates this only for servers it launches; a server started through `mcp_launcher.py` or by hand has no protection. git-mcp can write when `read_only = false`, and cicd-mcp can trigger workflows, so this is a trust-boundary gap, even though the servers bind to loopback only.

Verification (issue-to-plan Step 2, 2026-10-23, adversarial): the behavior is confirmed, with corrections. (1) The Agent does protect managed starts: `scripts/agent/startup_validation.py` (lines 82-88) rejects any enabled MCP server with an empty `auth_token`, so the exposure needs a standalone start (for example `mcp_launcher.py` or a binary run by hand) with an empty variable; the documentation (`mcp_02_01_endpoints-and-transport.md`) already calls the accept-all path unsupported in production. (2) The accept-all behavior is pinned by tests: `tests/conftest.py` sets `MCP_GIT_AUTH_TOKEN`, `MCP_CICD_AUTH_TOKEN` and `MCP_WEB_SEARCH_AUTH_TOKEN` to an empty string on purpose, and running `tests/mcp_servers/{git,cicd,web_search,rag_pipeline}` with non-empty tokens produced 94 failures across 11 test files (requests sent without an Authorization header). A fix therefore includes a test-suite migration, not only four server modules. (3) rag-pipeline-mcp already runs under a non-empty test token and was unaffected. (4) The posture tests for cicd, rag_pipeline and web_search build the posture directly from a patched config and assert the empty-token WARNING; they stay valid if the posture severity is left unchanged.

## Reason for Change
Authentication policy is inconsistent across servers, and the safe behavior depends on which launcher is used. Loopback binding does not protect against other local processes or users.

## Implementation Intent
Apply one fail-closed rule to all ten servers: an empty token prevents startup. Prefer a shared enforcement point so a new server cannot forget it. Keep the posture contract and the Agent-side validation consistent with the final rule.

## Target Files or Areas
- `scripts/mcp_servers/git/git_server.py`, `cicd/cicd_server.py`, `rag_pipeline/rag_pipeline_server.py`, `web_search/web_search_server.py`
- `scripts/mcp_servers/server.py` (`attach_auth_middleware`)
- `scripts/shared/security/startup_flow.py` (severity of the empty-token check)
- `tests/mcp_servers/*/test_*_health_posture.py`

## Required Changes
- Make an empty token a startup failure for git, cicd, rag_pipeline and web_search, matching the other six servers.
- Prefer a single shared check (in `attach_auth_middleware` or the posture flow) over four more copies of the import-time `RuntimeError`.
- Update the "optional Bearer-token auth" wording in the git and cicd module docstrings.
- Keep existing tests that rely on the accept-all behavior working through an explicit test-only option, or update them.

## Constraints
- Do not log or echo token values.
- Importing server modules in tests must remain possible without real secrets.
- The decision on WARNING versus FAILED in the shared flow was recorded as a Plan decision; changing it needs an explicit note (see Unresolved Questions).

## Acceptance Criteria
- Starting any of the ten servers with an empty `auth_token` fails with a clear message and no unauthenticated request can be served.
- All ten servers behave identically for empty, missing, and valid tokens.
- Existing posture tests still pass, with the empty-token expectation updated consistently.

## Testing Expectations
- Parametrized test over all ten servers: empty token fails at import or startup; a non-empty token serves, and a request without the token returns 401.
- Regression test that `attach_auth_middleware` with a non-empty token still compares in constant time and returns 401 for a missing or wrong header.
- Run `ruff`, `mypy`, `bandit`, and `pytest tests/mcp_servers tests/shared`.

## Documentation Impact
Update the MCP server documentation and the config comments so the empty-token rule is stated once as a startup failure for every server, and remove "optional" wording (boundaries, failure behavior). Run the documentation checkers named in `routing.md` for any edited `docs/` file.

## Out of Scope
- Changing token generation, rotation, or the Agent-side token distribution.
- Authentication for the EventBus service.
- The posture gate bypass (`mcpstart002`).

## Dependencies
- Related: `mcpstart002` (posture gate bypass). Making the empty token FAILED in the posture only helps once the gate is enforced on every launch path; an import-time refusal works independently.
- No open issue under `issues/` covers these files.

## Unresolved Questions
- Should the posture severity of an empty token change from WARNING to FAILED, or should enforcement stay as an import-time refusal? The shared flow documents WARNING as a deliberate choice (Plan UNK-06). Resolution proposed in the plan: keep WARNING and enforce by import-time refusal, since the import fails before the posture is consulted.

## AI Implementation Instruction
Change only authentication startup behavior for the four servers and the shared enforcement point. Do not alter tool behavior or posture checks unrelated to the token. Use obviously fake tokens in tests and never print them. Stop and report if a test depends on unauthenticated access in a way that cannot be expressed through a test-only option.

## Traceability
- **Workflow phase**: python-code-review (adversarial review of MCP server startup), converted by issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261023-114044
- **Related target files**: `scripts/mcp_servers/server.py`, `scripts/mcp_servers/git/git_server.py`, `scripts/mcp_servers/cicd/cicd_server.py`, `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`, `scripts/mcp_servers/web_search/web_search_server.py`, `scripts/shared/security/startup_flow.py`
