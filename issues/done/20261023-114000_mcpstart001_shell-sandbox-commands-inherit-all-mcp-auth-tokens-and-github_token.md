# Shell sandbox commands inherit all MCP auth tokens and GITHUB_TOKEN

## Priority
High

## Summary
Commands run by shell-mcp (including `python` and `python3`, which are in the shipped allowlist) start with a full copy of the shell server's own environment. That environment contains every `MCP_*_AUTH_TOKEN` and `GITHUB_TOKEN`, so any LLM-issued command can read the Bearer tokens of all other MCP servers and the GitHub credential. Review severity: Critical (security exposure).

## Background
The Agent launches each MCP subprocess with an environment built by the command validator's `filter_env()`. Its default allowlist (`_DEFAULT_ALLOWED_ENV_VARS` in `scripts/agent/http_lifecycle_command_validator.py`) deliberately passes `MCP_*_AUTH_TOKEN` and `GITHUB_TOKEN` to every subprocess server. shell-mcp then builds the environment of each sandboxed command in `ShellService.run_command()` (`scripts/mcp_servers/shell/shell_service.py`) as `os.environ.copy() | {"PATH": ...} | filtered_env`. The sandbox wrapper (`firejail --private --net=none --noroot`) isolates filesystem and network but does not scrub environment variables. The existing `env_allowlist` / `env_denylist` settings only filter keys supplied by the caller in `req.env`, not the inherited environment.

## Problem
Confirmed by a probe (evidence label: Confirmed by execution, confidence High). With `MCP_GITHUB_AUTH_TOKEN`, `GITHUB_TOKEN` and `MCP_SHELL_AUTH_TOKEN` set in the shell server process, running the allowlisted command `python3 -c "import os; print(sorted(k for k in os.environ if 'TOKEN' in k))"` through `ShellService.run_command()` with the default firejail backend returned `GITHUB_TOKEN`, `MCP_GITHUB_AUTH_TOKEN` and `MCP_SHELL_AUTH_TOKEN` in the command's stdout. A prompt-injected or misbehaving model can therefore exfiltrate those secrets into the tool result, and from there into conversation history and logs. The tokens of file-write, file-delete, git, and cicd servers are exposed the same way, which defeats the per-server token separation.

Verification (issue-to-plan Step 2, 2026-10-23, adversarial): the claim holds, with these refinements. (1) The shell subprocess does receive the tokens: `McpServerConfig.env` defaults to an empty dict, so `filter_env()` applies its default allowlist (it never returns `None` for a configured server), and that allowlist contains `MCP_*_AUTH_TOKEN` and `GITHUB_TOKEN`; `[mcp_servers.shell]` in `config/agent.toml` sets no `env` key. (2) The probe ran inside another sandbox (firejail printed that it was nested), so the firejail isolation itself was not exercised, but firejail does not clear the environment, and the variables reached the command. (3) Existing tests do not assert environment inheritance, so no test pins the current behavior. (4) A narrower Agent-side filter is feasible: each server reads only its own `MCP_<KEY>_AUTH_TOKEN` through its config, and only github-mcp and cicd-mcp read `GITHUB_TOKEN`.

## Reason for Change
Security exposure at a trust boundary: the shell tool is the one server designed to run model-chosen code, yet it receives the credentials of every higher-privilege server. The blast radius is every write-capable MCP server plus the GitHub account.

## Implementation Intent
Build the command environment from an explicit allowlist of runtime basics (for example `PATH`, `HOME`, `LANG`, `LC_*`, `TMPDIR`) instead of copying the process environment, and drop all secret-shaped variables unconditionally. Keep the caller-supplied `req.env` filtering as is. Separately, narrow what the Agent passes to each subprocess so a server only receives its own token; this defense in depth is a follow-up decision, not a prerequisite for the shell fix.

## Target Files or Areas
- `scripts/mcp_servers/shell/shell_service.py` (`run_command` environment construction)
- `scripts/mcp_servers/shell/shell_models.py` (policy fields for the environment, if a new setting is needed)
- `config/shell_mcp_server.toml` (documented environment settings)
- `scripts/agent/http_lifecycle_command_validator.py` (only if the per-server token narrowing is taken up)
- `tests/mcp_servers/shell/`

## Required Changes
- Replace `os.environ.copy()` with a minimal base environment built from an explicit allowlist.
- Never forward `MCP_*_AUTH_TOKEN`, `GITHUB_TOKEN`, or any variable matching a secret-shaped pattern, even when named in `req.env` or an allowlist.
- Keep `PATH` pinned to the configured value.
- Document the resulting environment contract in the shell server configuration comments.

## Constraints
- Existing allowlisted workflows (`pytest`, `ruff`, `mypy`, `git`) must still find their interpreter and locale settings.
- Do not weaken the existing `env_denylist` / `env_allowlist` handling of `req.env`.
- No secret values may appear in logs, test output, or the issue text.

## Acceptance Criteria
- A command run through shell-mcp cannot observe any `MCP_*_AUTH_TOKEN` or `GITHUB_TOKEN` variable that was present in the server process, verified with `python3 -c` printing matching environment keys.
- The commands in the shipped allowlist still run successfully in the test environment.
- The environment contract is described in `config/shell_mcp_server.toml` comments.

## Testing Expectations
- Unit test: with token variables set in the server process, `run_command` for a `python3` command that prints environment keys returns none of them.
- Regression test: `req.env` entries are still filtered by the allowlist/denylist, and `PATH` is still the configured value.
- Run `ruff`, `mypy`, `bandit` on the touched files and `pytest tests/mcp_servers/shell`.

## Documentation Impact
Update the shell MCP documentation to state which environment variables a sandboxed command receives and that secret-shaped variables are never forwarded (boundaries, failure behavior). Run the documentation checkers named in `routing.md` for any edited `docs/` file.

## Out of Scope
- Changing the firejail options or the sandbox backend choice.
- Redesigning the Agent-side environment filter for all servers (tracked as a possible follow-up).
- The posture gate bypass and other startup findings (separate issues).

## Dependencies
- N/A: none. Open issues under `issues/` concern Agent tool-call and turn handling and do not touch these files.

## Unresolved Questions
- Should the Agent stop passing `MCP_*_AUTH_TOKEN` of other servers to each subprocess as well? The shell fix is sufficient to close the exposure to model-chosen code, but other servers keep tokens they do not need.

## AI Implementation Instruction
Keep the change limited to the shell command environment. Do not touch unrelated servers. Do not print or log token values in tests; use obviously fake values. Stop and report if a shipped allowlisted command fails because of the reduced environment.

## Traceability
- **Workflow phase**: python-code-review (adversarial review of MCP server startup), converted by issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261023-114000
- **Related target files**: `scripts/mcp_servers/shell/shell_service.py`, `scripts/mcp_servers/shell/shell_models.py`, `config/shell_mcp_server.toml`, `scripts/agent/http_lifecycle_command_validator.py`
