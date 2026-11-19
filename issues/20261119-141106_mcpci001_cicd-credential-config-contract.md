# Unify CI/CD GitHub credential, configuration, schema, and HTTP client lifecycle

## Priority
High

## Summary
Create one effective GitHub credential contract used by service construction, startup posture, and health; generate strict CI/CD schemas from Pydantic models; canonicalize workflow identifiers; validate configuration before bind; and manage the shared HTTP client through the FastAPI lifespan.

## Background
Source: consolidated Web Search and CI/CD MCP backlog (`memo-issue.md`, Issue 5). Related archived work: `issues/done/20261007-154047_cicdallow01_unify-cicd-mcp-workflow_allowlist-to-file-name-form.md` and `issues/done/20261023-114044_mcpstart003_four-mcp-servers-start-without-authentication-when-auth_token-is-empty.md` (re-verify against them).

Evidence (`Explicit in code`, by `rg`): `cicd_service_init.py:26-31` selects `os.environ.get("GITHUB_TOKEN", cfg.github_token)`, only warns when no token exists ("API rate limit will be 60 req/hr"), and creates `httpx.AsyncClient(timeout=30.0)` at service init; `cicd_server.py:194-196` health reads only the environment variable. The schema, identifier, and allowlist claims are from the backlog and `Needs confirmation`.

## Problem
Service and health can disagree about the credential; a tokenless write-capable server starts although Actions writes need authentication; tool schemas omit runtime constraints; workflow identifiers are inconsistently file names or numeric ids and are put into URL paths without a canonicalization contract; allowlists are checked only as lists; and the shared client has no clear shutdown lifecycle.

## Reason for Change
Security-sensitive startup and credential behavior; it blocks workflow-dispatch reconciliation (`issues/20261119-141109_mcpci002_cicd-dispatch-reconciliation.md`) and log retrieval (`issues/20261119-141110_mcpci003_cicd-log-streaming-bounds.md`).

## Implementation Intent
One centralized effective-token selection with documented precedence, used everywhere. Strict request models are the source of published schemas. Identifiers are canonicalized identically for requests and allowlists and encoded as a single path segment. Configuration errors fail before bind. The HTTP client is created and closed in lifespan while still injectable in tests.

## Target Files or Areas
- `scripts/mcp_servers/cicd/cicd_service_init.py`, `cicd_server.py`, `cicd_models.py`, `cicd_tools.py`, `cicd_service_guards.py`
- CI/CD health and posture code; `config/cicd_mcp_server.toml`
- `tests/mcp_servers/cicd/` model, schema, health, and lifecycle tests
- The MCP design document (`22_mcp_all.md` is named by the backlog but is not a tracked file; location `不明`)

## Required Changes
- Centralize effective-token selection and enforce documented environment-versus-configuration precedence for service, posture, and health; refuse startup for write-capable mode without a token.
- Probe token validity and API reachability; distinguish Actions read permission from workflow-dispatch permission; report permission and rate-limit status without exposing the token.
- Generate tool input schemas from Pydantic request models with `extra="forbid"`; publish `run_id >= 1`, `limit` 1 to 50, and non-empty repository, workflow, and ref.
- Define the workflow identifier as a validated file name or a positive numeric id; canonicalize request and allowlist values identically; URL-encode as one path segment.
- Validate repository allowlist entries as non-empty `owner/repo`; reject blank, non-string, duplicate, wildcard, malformed, and oversized values; require `max_log_size_kb >= 1` with a hard maximum.
- Create and close `httpx.AsyncClient` in lifespan; remove import-time construction and keep test injection.

## Constraints
- Tokens never appear in logs, health details, or errors.
- Empty allowlists remain a pre-bind startup failure with runtime deny-all kept as defense in depth.
- Stricter validation changes accepted inputs; list the newly rejected inputs in the change.

## Acceptance Criteria
- [ ] Service and health use the same effective credential; tokenless write-capable startup fails closed.
- [ ] Invalid or insufficiently privileged tokens are reported accurately without exposing them.
- [ ] Public schemas and runtime models enforce the same contract.
- [ ] Numeric workflow ids and file names are handled consistently; path construction cannot be altered by separators or unsafe encoding.
- [ ] Malformed configuration fails before bind.
- [ ] Application shutdown closes the shared HTTP client.

## Testing Expectations
- Environment-only, configuration-only, both, and neither credential cases; invalid, read-only, Actions-write, rate-limited, and timeout probe cases.
- Model and schema parity; file-name, numeric-id, separator, percent-encoding, wildcard, duplicate, blank, and invalid-repository cases.
- FastAPI lifespan startup and shutdown and repeated-construction tests.
- Run ruff, mypy, and the full test suite.

## Documentation Impact
Yes. Credential precedence and required GitHub Actions permissions; empty allowlist behavior; `workflow identifier` terminology and both identifier forms; module layout including composite and job backends.

## Out of Scope
- Dispatch reconciliation (`issues/20261119-141109_mcpci002_cicd-dispatch-reconciliation.md`), log streaming (`issues/20261119-141110_mcpci003_cicd-log-streaming-bounds.md`), error and audit mapping (`issues/20261119-141111_mcpci004_cicd-error-audit-coverage.md`).

## Dependencies
- Blocks `issues/20261119-141109_mcpci002_cicd-dispatch-reconciliation.md`, `issues/20261119-141110_mcpci003_cicd-log-streaming-bounds.md`, and the final state of `issues/20261119-141111_mcpci004_cicd-error-audit-coverage.md`.
- No dependency on other open issues; sibling check found no open issue or plan on the CI/CD files.

## Unresolved Questions
- `不明`: environment-versus-configuration precedence (which wins).
- `不明`: how a token's Actions permissions can be probed without side effects.
- `不明`: hard maximum for `max_log_size_kb` and allowlist size.

## AI Implementation Instruction
Introduce the token-selection function and the lifespan client first, with tests. Do not weaken deny-all behavior. Stop and report the precedence question before choosing silently.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261119-141106
- **Related target files**: `scripts/mcp_servers/cicd/cicd_service_init.py`, `scripts/mcp_servers/cicd/cicd_server.py`, `scripts/mcp_servers/cicd/cicd_models.py`, `scripts/mcp_servers/cicd/cicd_tools.py`, `scripts/mcp_servers/cicd/cicd_service_guards.py`, `config/cicd_mcp_server.toml`
