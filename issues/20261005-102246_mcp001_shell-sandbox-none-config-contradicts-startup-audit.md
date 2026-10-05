# Shell MCP: checked-in config uses sandbox backend "none", which the startup audit rejects

## Priority
High

## Summary
`config/shell_mcp_server.toml` sets `shell_sandbox_backend = "none"` and its comment says this yields a WARNING at startup. The agent startup security audit raises `RuntimeError` for `none` regardless of environment, which is reported as a FATAL startup outcome. The config value, its comment and the check disagree.

## Background
- `config/shell_mcp_server.toml` (and the deployed copy under `/opt/llm/config/`, which has the same value and comment) sets `shell_sandbox_backend = "none"`, with the comment "Development: none - unsandboxed execution, WARNING at startup" and a production note to use `firejail`.
- `audit_security_defaults()` in `scripts/agent/services/security_audit.py` loads the shell config through `scripts/agent/security_audit_config.py` (`load_shell_audit_config`, which reads `ShellConfig` from `shell_mcp_server.toml` via `ConfigLoader`). When `sandbox_backend == "none"` it raises `RuntimeError("shell_sandbox_backend=none is not permitted regardless of environment")`. Other unknown values only produce a warning; `firejail` without the binary raises.
- `scripts/agent/startup_validation.py` (`check_services`) catches that `RuntimeError` and records a FATAL outcome for `security_audit` with the remediation "Fix MCP server auth_token or sandbox config.", so agent startup fails.
- The shell server itself (`shell_service_static_helpers.init_sandbox`) only validates `firejail`; it logs no WARNING for `none`. `ShellConfig.shell_sandbox_backend` also defaults to `none` when the key is absent, so an omitted key hits the same fatal check.
- Documents: `docs/22_mcp/mcp_04_02_file-write-file-delete-shell.md` and `docs/22_mcp/mcp_05_02_auth-profiles-and-sandboxing.md` state that `none` raises `RuntimeError` regardless of environment, while still listing `none` as "local development only" in places.

## Problem
Evidence (confirmed by code reading; not verified by running the agent):
- With the checked-in config the agent startup should fail at the security audit (FATAL), unless the shell MCP server is not installed or `firejail` is configured instead. This contradicts the config comment (WARNING only) and the "Development" use case.
- The code default for the key is also `none`, which is rejected, so the default configuration is not startable.
- The documents contain mixed messages ("Local development only" versus "Not permitted in any environment").
- Whether the checked-in value is meant as a development placeholder that is expected to fail, or the audit is meant to allow `none` outside production, is not decided.

## Reason for Change
Config, comment, code default and audit policy are inconsistent; operators following the config comment will get a fatal startup failure, and the documented policy is ambiguous.

## Implementation Intent
Decide the policy first. Options: (A) `none` is never permitted (current audit and mcp_05_02 policy): change the checked-in config to `firejail`, fix the comment, and make the code default consistent (for example fail-fast or default to `firejail`); (B) `none` is permitted for development only: change the audit to warn instead of raise when not in a production profile, and fix the documents; (C) keep the audit and keep `none` in the config as an explicit placeholder, but correct the comment to state that startup fails. Recommended: A, since two documents and the audit already state that `none` is not permitted in any environment.

## Target Files or Areas
- config/shell_mcp_server.toml (and the deployment copy managed separately)
- scripts/agent/services/security_audit.py
- scripts/mcp_servers/shell/shell_models.py (default value)
- tests/agent (security audit and startup validation tests)
- docs/22_mcp/mcp_04_02_file-write-file-delete-shell.md
- docs/22_mcp/mcp_05_02_auth-profiles-and-sandboxing.md

## Required Changes
- Record the policy decision.
- Make the config value, its comment, the model default and the audit consistent with that decision.
- Add or adjust tests covering the checked-in config against the audit.
- Align the two MCP documents; remove the pointer to this issue once resolved.

## Constraints
- Do not weaken the check silently; any relaxation must be an explicit decision.
- Option A requires firejail on the target host; deployment must be coordinated.
- Changing the deployed config is a deployment action and must follow the deploy skill.

## Acceptance Criteria
- Starting the agent with the checked-in `config/shell_mcp_server.toml` behaves as the config comment and the documents describe (no contradiction between comment, audit result and documents).
- A test asserts the audit result for the checked-in shell config.
- The code default for the key is consistent with the audit policy.
- `mcp_04_02` and `mcp_05_02` describe one policy for `none` and no longer point to this issue.

## Testing Expectations
- Unit test for `audit_security_defaults()` with the repository shell config loaded (expected outcome per decision).
- Startup validation test that a `none` backend yields (or does not yield) a FATAL `security_audit` outcome per decision.
- Run `uv run pytest tests/agent tests/mcp_servers/shell`, ruff, mypy, and the MCP docs checkers.

## Documentation Impact
Yes. `docs/22_mcp/mcp_04_02_file-write-file-delete-shell.md` and `docs/22_mcp/mcp_05_02_auth-profiles-and-sandboxing.md` (sandbox table, startup enforcement, use case wording) must state a single policy; both currently carry a pointer to this issue.

## Out of Scope
- Changes to firejail arguments or sandbox implementation.
- Other security audit checks (auth_token, allowlists).
- Enforcement when shell-mcp is started outside the agent startup path.

## Dependencies
N/A: none

## Unresolved Questions
- Is `none` meant to be usable in development (option B) or never (option A)? Unknown; recommended A.
- Is firejail installed on the development host? Unknown.

## AI Implementation Instruction
Do not change code or config before the policy decision is recorded. Keep the change minimal and consistent across config, default, audit and tests. Do not edit the deployed `/opt/llm` copy outside the deploy workflow.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261005-102246
- **Related target files**: config/shell_mcp_server.toml, scripts/agent/services/security_audit.py, scripts/mcp_servers/shell/shell_models.py, docs/22_mcp/mcp_04_02_file-write-file-delete-shell.md, docs/22_mcp/mcp_05_02_auth-profiles-and-sandboxing.md
