# Register Bearer-token authentication in the shell, github, and file MCP servers

## Priority
High

## Summary
The shell, github, file-read, file-write, and file-delete MCP servers never register the shared Bearer-token authentication middleware, so they answer every request without credentials. ADR-007 INV-09 requires every MCP server (except the documented exceptions) to reject a request whose Bearer token does not match. Register the middleware in these five servers, give each a server-side `auth_token` setting, and align the tests and documentation. Known Issue MCP-001 records the discrepancy and is removed once this is done.

## Background
- Known Issue MCP-001 (`docs/00_governance/governance_03_issue-and-uncertainty-management.md`) was registered after a documentation review found no `attach_auth_middleware()` call in these servers. A follow-up in-process check confirmed it at runtime.
- The Agent already treats these servers as authenticated: its startup validation rejects an empty `auth_token` for every MCP server (including these five), it sends the token on tool calls, and its post-startup health check sends the Bearer token (closed issue `mcphealthauth01`).
- The servers that are protected today (cicd, git, rag-pipeline, web-search) read an `auth_token` from their own `config/*_mcp_server.toml`, which is resolved from the same environment variable the Agent configuration uses. mdq-mcp is the documented exception and passes an empty token.
- Related closed work: `mcp005` and `mcp006` moved web-search to the shared `auth_token` and removed the loopback health admission. The implementation procedures for `mcp006` are generated but not yet implemented (see Dependencies).
- No open issue under `issues/` covers this (the open items are the legacy design memos only).

## Problem
- Evidence (`Verified by run`): requests made in-process to each server's application without any Authorization header returned 200 on `/v1/tools` for shell, github, file-read, file-write, and file-delete. The same request to the git server, which registers the middleware, returned 401 without a token and 200 with the correct Bearer token.
- Evidence (`Explicit in code`): `attach_auth_middleware()` is called by the cicd, git, rag-pipeline, web-search, and mdq servers only. The five affected servers create their FastAPI application without it and contain no other Bearer verification.
- Evidence (`Explicit in code`): the server-side configuration files for the shell, github, and the three file servers define no `auth_token`, while the cicd, git, rag-pipeline, and web-search ones do.
- Consequence: the Agent-side token requirement gives these servers no protection. Any local process that can reach the loopback port can call tools that read, write, delete, or run commands. Exposure is limited by the loopback-only bind, but the documented authentication boundary does not hold.

## Reason for Change
- ADR-007 INV-09 and the MCP security chapter state that every MCP server except mdq-mcp verifies the Bearer token. The shell and file-write/delete servers expose the most dangerous tools, so they are the ones whose missing check matters most.
- The fix aligns the code with the adopted design instead of weakening the ADR, and removes the open High-severity Known Issue.

## Implementation Intent
- Follow the existing pattern used by the git and cicd servers: a server-side `auth_token` field in each server's configuration model, resolved from the environment variable that the Agent configuration already names for that server, and one `attach_auth_middleware()` call right after the application is created.
- Keep `/health` behind the same token (no new exemption). The Agent's health poll already sends the server token.
- Keep the change minimal and uniform across the five servers; do not refactor the shared middleware or the server base code.
- Preserve fail-closed behavior: a server whose configured token is empty should not silently run unauthenticated unless that is the documented mdq-mcp exception. Decide and document how an empty value is handled (see Unresolved Questions).

## Target Files or Areas
- `scripts/mcp_servers/shell/` (server module and configuration model)
- `scripts/mcp_servers/github/` (server module and configuration model)
- `scripts/mcp_servers/file/` (read, write, and delete server modules and their configuration model)
- `config/shell_mcp_server.toml`, `config/github_mcp_server.toml`, `config/file_read_mcp_server.toml`, `config/file_write_mcp_server.toml`, `config/file_delete_mcp_server.toml`
- `tests/mcp_servers/` (authentication tests for these servers)
- `docs/10_adr/adr_02_007_http-mcp-adoption-and-stdio-non-support.md`, `docs/22_mcp/mcp_05_02_auth-profiles-and-sandboxing.md`, `docs/22_mcp/mcp_06_14*` (authentication setup), `docs/91_security/security_01_architecture-and-trust-boundaries.md`, `docs/00_governance/governance_03_issue-and-uncertainty-management.md` (MCP-001), `docs/00_governance/governance_01_documentation-policy.md` only if the Known Issue reference needs updating

## Required Changes
- Add an `auth_token` field to the configuration models of the shell, github, and file servers, loaded the same way as the git server's field.
- Add `auth_token = "${ENV:...}"` to each of the five server-side configuration files, using the same environment variable names that `config/agent.toml` uses for the matching server, with the explanatory comment used in the git configuration file.
- Call `attach_auth_middleware()` in each of the five servers, passing the configured token.
- Add tests for each server: a request without a token is rejected with 401, a request with a wrong token is rejected, and a request with the correct token succeeds (including `/health`).
- Confirm that the Agent's startup, health polling, and tool calls still succeed against the protected servers (existing Agent-side tests plus a manual or integration check).
- Remove Known Issue MCP-001 and its ADR-007 Known Deviations reference once the servers verify the token; update the security chapter's authentication table so it matches the implementation.

## Constraints
- Do not change the Agent-side token handling; it already sends the token to these servers.
- Do not add an authentication exception for any of these servers; the only documented exceptions stay mdq-mcp and the web-search behavior defined by the `mcp006` work.
- Environment variable names must match those already defined in `config/agent.toml`; no new secret names or values are introduced, and no secret values are written to the repository.
- Deployment: the servers are started by the Agent and inherit its environment, which already contains these variables because Agent startup requires them to be non-empty (Needs confirmation for the production launcher; see Unresolved Questions).
- Coordinate with `mcp006` on the shared middleware module so the two changes do not conflict.

## Acceptance Criteria
- For each of the five servers, an unauthenticated request to a tool route and to `/health` returns 401, and a request with the correct Bearer token succeeds.
- The five server-side configuration files define `auth_token` and the configuration models load it; startup behavior with an unset or empty value matches the decision recorded under Unresolved Questions and is covered by a test.
- Existing tests for these servers pass, with fixtures updated to send the token where needed.
- The Agent can start, poll health, and call a tool on each protected server (verified by existing Agent tests and one manual or integration check).
- ADR-007 INV-09 verification in `docs/10_adr/adr_01_index.md` can be marked Confirmed, and Known Issue MCP-001 and its references are removed.
- `uv run ruff check`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports`, and `uv run pytest` pass; the `docs/` checkers listed in `routing.md` pass.

## Testing Expectations
- Unit tests per server for 401 without a token, 401 with a wrong token, and success with the correct token, following the style of the existing git and cicd server tests under `tests/mcp_servers/`.
- A regression test for the configuration models (field loaded from the environment-resolved value; empty value handling).
- Run the Agent-side MCP startup and health tests, and `tests/mcp_servers/` in full.
- Manual verification: start the Agent against the protected servers and confirm startup, health polling, and one tool call per server.
- Documentation consistency: `check_docs_quality`, `check_docs_structure`, `check_docs_content_policy`, `check_adr_invariant_matrix`, `check_known_deviation_sync`, `check_issue_inventory_conformance`, and `check_docs_consistency --domain mcp`.

## Documentation Impact
- Update: ADR-007 Known Deviations and the INV-09 verification row in `adr_01_index.md` (remove the MCP-001 reference and mark the row Confirmed), `mcp_05_02` and `mcp_06_14` (per-server authentication setup), and `security_01` (authentication table, which already states the intended behavior).
- Remove Known Issue MCP-001 from `governance_03` (resolved items are not retained). Record any deployment finding as a Known Issue or Needs Confirmation item with the required fields.
- Document intent, boundaries, and failure behavior (empty token handling); do not copy configuration values.

## Out of Scope
- Changing the shared `attach_auth_middleware()` implementation, the loopback health admission (covered by `mcp006`), or token comparison logic.
- Per-tool authorization, role-based tokens, or token rotation.
- The mdq-mcp exception and the EventBus authentication model.
- Agent-side configuration or startup validation changes.
- Plan-mode tool blocking and the workflow status display (tracked separately).

## Dependencies
- `mcp006` (closed issue `issues/done/20261012-185047_mcp006_remove-the-loopback-health-admission-from-the-shared-auth-middleware.md`; its implementation procedures under `implementations/20261012-185934_*` are not yet implemented): it edits the shared middleware module and its tests. Implement `mcp006` first, or coordinate the two so the shared module changes are not conflicting; this issue does not need to modify the shared module.
- `mcphealthauth01` (closed): the Agent's post-startup health check already sends the Bearer token, which this issue relies on.
- No open issue under `issues/` overlaps (sibling-issue check done: only legacy design memos are open).

## Unresolved Questions
- How should a server behave when its configured `auth_token` is empty or the environment variable is unset: refuse to start (fail closed, as the config loader does for an unset referenced variable) or run unauthenticated? Assumption: fail closed, consistent with ADR-007 and the git server's behavior.
- Are the `MCP_*_AUTH_TOKEN` variables for these five servers present in the environment of the production launcher that starts the Agent (and therefore the servers)? Needs confirmation against `deploy/start_agent.sh` and the production `.env` handling.
- Is there any consumer other than the Agent (a script, a probe, or a test harness) that calls these servers without a token? None was found by repository search; confirm before enforcing.

## AI Implementation Instruction
- Follow `skills/python-implementation` and the validation sequence in `rules/toolchain.md`.
- Mirror the git and cicd servers' pattern exactly; do not refactor the shared middleware or unrelated server code, and keep the diff small and uniform across the five servers.
- Do not add exemptions, do not weaken or remove existing checks, and do not write secret values anywhere.
- Update tests and documentation named in Required Changes in the same change; remove MCP-001 only after the tests prove the servers reject unauthenticated requests.
- If the empty-token behavior or the production environment question cannot be settled from the repository, stop and report it instead of choosing silently.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261013-113008
- **Related target files**: scripts/mcp_servers/shell/, scripts/mcp_servers/github/, scripts/mcp_servers/file/, config/shell_mcp_server.toml, config/github_mcp_server.toml, config/file_read_mcp_server.toml, config/file_write_mcp_server.toml, config/file_delete_mcp_server.toml, tests/mcp_servers/, docs/10_adr/adr_02_007_http-mcp-adoption-and-stdio-non-support.md, docs/22_mcp/mcp_05_02_auth-profiles-and-sandboxing.md, docs/91_security/security_01_architecture-and-trust-boundaries.md, docs/00_governance/governance_03_issue-and-uncertainty-management.md
