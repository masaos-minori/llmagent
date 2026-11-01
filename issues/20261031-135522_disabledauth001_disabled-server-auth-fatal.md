# Startup validation treats a disabled MCP server without auth_token as a fatal error

## Priority
High

## Summary
`StartupValidationPipeline.check_services` reports a FATAL `mcp_auth` outcome for every configured MCP server whose `auth_token` is empty, including servers that are disabled (`startup_mode` is `none`). The configuration layer deliberately accepts an empty token for a disabled server, and the readiness and tool-discovery steps skip disabled servers, but this check does not. One disabled server with an unset token variable therefore aborts the whole agent startup. Make the check consistent with the rest of the pipeline.

## Background
Found during an adversarial review (`python-code-review`) of the agent startup path.
- `McpServerConfig` validation (`_validate_auth_token`) requires a non-empty token only when the server is not disabled, with the comment that disabled servers do not require unused connection credentials.
- `_build_single_server` defaults `startup_mode` to `none` when the key is absent, and resolves the token from an environment reference, so an unset variable yields an empty token.
- The readiness check (`mcp_health`) and tool discovery (`McpToolDiscoveryService`) both skip a server when `is_disabled` is true.

## Problem
In `check_services`, the "MCP authentication check" builds `missing_auth` from all of `ctx.cfg.mcp.mcp_servers` with a bare `not srv.auth_token` test, with no `is_disabled` filter. If any server is disabled and has an empty token, the pipeline records `add_fatal("mcp_auth", ...)`, and `StartupOrchestrator._check_services` raises `RuntimeError("Startup validation failed: ...")`.

Reproduction (throwaway script, not committed): construct a disabled `McpServerConfig` (HTTP transport, `startup_mode=NONE`, empty token), stub the later pipeline steps and the RAG consistency service so no real state is touched, and run `check_services`. Observed: the first outcome is `mcp_auth` with status fatal and the message "MCP server(s) missing auth_token: optional_srv".

For enabled servers the check is redundant: `McpServerConfig` already refuses an empty token for them. In practice the check can only fire for disabled servers.

## Reason for Change
A server the operator has switched off, or has not configured yet, blocks startup of the whole agent, and the remediation text ("set a non-empty auth_token") asks for credentials the config layer says are not needed. This contradicts the documented intent (REQ-004) and the behavior of every other pipeline step.

## Implementation Intent
Exclude disabled servers from the `mcp_auth` check, in line with the readiness and discovery steps, and keep the check fail-closed for enabled servers. Keep the outcome source name and message format so reporting is unchanged.

## Target Files or Areas
- `scripts/agent/startup_validation.py` (`StartupValidationPipeline.check_services`, "MCP authentication check")
- `tests/agent/test_startup_validation.py`

## Required Changes
- Filter disabled servers out of the `missing_auth` computation.
- Add tests: disabled server with empty token yields no `mcp_auth` fatal; an enabled server with an empty token (constructed in a way that bypasses config validation) still yields a fatal; the message lists only enabled offenders.

## Constraints
- Do not weaken the check for enabled servers (ADR-004 Decision 14: safety failures stay unconditional).
- Do not change config-layer validation in `scripts/shared/mcp_config.py`.
- Keep the outcome source (`mcp_auth`) and the remediation wording shape.

## Acceptance Criteria
- A configuration whose only token-less server is disabled passes the `mcp_auth` step.
- An enabled server with an empty token still produces a fatal `mcp_auth` outcome naming that server.
- The new tests fail on the current code and pass after the change.

## Testing Expectations
- Unit tests in `tests/agent/test_startup_validation.py` as above.
- Existing tests in `tests/agent/test_startup_severity_classification.py` (`test_mcp_auth_fatal_*`) use `MagicMock` servers with `auth_token=""`; a filter on `srv.is_disabled` is truthy on a `MagicMock`, so set `is_disabled=False` on them when adding the filter, and correct the comment there that says an empty-token config can no longer be constructed (it can for disabled servers).
- Run `tests/agent/test_startup_validation.py`, `tests/agent/test_startup.py`, `ruff`, and `mypy --no-namespace-packages` on the touched files.

## Documentation Impact
Needs confirmation: check whether the agent startup documentation describes the `mcp_auth` check as applying to every configured server. If it does, state that disabled servers are exempt, consistent with the configuration contract.

## Out of Scope
- Whether the `mcp_auth` check should exist at all for enabled servers.
- Changes to how tokens are resolved from environment references.
- Any other startup validation step.

## Dependencies
- Related to `issues/20261031-135634_validorder001_config-validation-after-spawn.md`: that issue may move the `mcp_auth` check (it reads configuration only) into an earlier stage. The two changes touch the same function; apply this one first or rebase the other on it. No other open issue or in-flight plan targets `scripts/agent/startup_validation.py` for this behavior.

## Unresolved Questions
- `_check_component_mandatoriness` (added to `check_services`) loops over every configured server, disabled ones included, and treats an unknown server as fatal: whether a disabled server needs the same exemption is `Needs confirmation` (separate from this issue's `mcp_auth` filter).
- Whether an enabled server with an empty token can be produced by a path other than `_build_single_server` (for example a config reload or programmatic construction). If it cannot, the check is dead for enabled servers; deciding whether to keep it is a separate question (see Out of Scope). `Needs confirmation`.

## AI Implementation Instruction
Make the smallest change that filters disabled servers in the `mcp_auth` check, plus the tests. Do not refactor the pipeline or alter other steps. Do not copy real token values or environment values into tests or messages.

## Traceability
- **Workflow phase**: python-code-review -> issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261031-135522
- **Related target files**: scripts/agent/startup_validation.py, tests/agent/test_startup_validation.py
