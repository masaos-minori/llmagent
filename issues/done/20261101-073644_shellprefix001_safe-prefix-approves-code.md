# Shell safe-prefix auto-approval covers interpreters and mutating git subcommands

## Priority
High

## Summary
`shell_run` is configured with a base risk of high, but a command whose executable matches `approval_shell_safe_prefixes` is lowered to no risk and runs without any prompt. The shipped list contains `python`, `pytest`, `uv run`, and `git branch`. The match looks only at the executable (and subcommand) name, so `python -c <code>`, `pytest -p <plugin>`, `uv run <anything>`, `git branch -D <name>`, and `git diff --output=<file>` are auto-approved with arbitrary arguments whenever the positional-path check passes. Narrow the auto-approval to commands whose whole argument vector is known to be read-only.

## Background
Found during an adversarial review (`python-code-review`) of the agent's MCP call path.
- `tool_policy._special_case_risk` handles `shell_run`: any shell metacharacter gives high; otherwise the parsed command is matched by `_match_executable_identity` against the configured prefixes (basename of the first token, plus the following tokens for multi-word prefixes). A match returns no risk after `_check_positional_args` and `_unsafe_flag_denylist`. This override replaces the base risk, including the explicit `shell_run = "high"` rule in `config/agent.toml`.
- `_check_positional_args` escalates only when a non-flag argument starts with a protected path or resolves outside `allowed_root`. Relative paths are resolved against the agent process's current directory, and a code string or branch name passed as a positional argument is treated as a path.
- `_unsafe_flag_denylist` knows flags only for `find`, `cat`, and `grep`, and looks the executable up by the first token as written.
- The documentation describes the behavior: `docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md` ("`shell_run` and `command` starts with any of `approval_shell_safe_prefixes` -> `none`") and `docs/91_security/security_02_high-risk-tool-common-policy.md`. It does not say which commands count as safe.
- The shell MCP server has its own `command_allowlist` in `config/shell_mcp_server.toml` (`pytest`, `python`, `python3`, `git`, `ruff`, `mypy`, matched on the basename) and runs commands in a sandbox with a restricted working directory (`shell_cwd_allowed_dirs`, `shell_sandbox_backend`). Entries such as `ls`, `cat`, `find`, `grep`, `echo`, `uv` in the agent-side list are not in the server allowlist; the server is expected to reject them (`Needs confirmation`: the server's matching code was not read). The reachable auto-approved set today is therefore `python`/`python3`, `pytest`, and `git`.
- Plan mode blocks `shell_run` entirely (`plan_blocked_tools`), so only normal mode is affected.

## Problem
Reproduction (throwaway script, not committed): the real values of `approval_shell_safe_prefixes`, `approval_protected_paths`, `approval_risk_rules` and `tool_safety_tiers` from `config/agent.toml`, a temporary directory as `allowed_root`, and `classify_risk` called for `shell_run`. No command was executed. With the agent's current directory inside `allowed_root`: `python -c "__import__('shutil').rmtree('data')"`, `git branch -D feature`, `git diff --output=report.txt`, `pytest -p some_plugin`, and `uv run python build.py` all returned no risk (no prompt). With the current directory outside `allowed_root`, the first two returned high, so the outcome depends on the agent's working directory.

Also observed: `/usr/bin/find . -delete` returned no risk although `-delete` is in the denylist, because the denylist is looked up with the unnormalized first token while the prefix match uses the basename. Today the server allowlist should make this unreachable (`find` is not in it), but the two checks disagree.

Effects:
- The model can run arbitrary Python, or delete branches, inside the sandbox without the user seeing or approving the command. The sandbox limits the blast radius, but its filesystem and network scope was not reviewed here (`Needs confirmation`).
- The human-in-the-loop guarantee of a high-risk tool is bypassed by a name match.

## Reason for Change
Auto-approval is a security decision: it removes the only interactive check on `shell_run`. A prefix name does not describe what a command does: interpreters execute their argument, test runners import repository code, and `git branch` can delete or rename branches. The shipped configuration makes this reachable by default.

## Implementation Intent
Auto-approve only command shapes that are read-only by construction, expressed as an explicit, deny-by-default rule per executable (allowed subcommands and flags, no free-form code argument). Move interpreters and test runners out of the auto-approved set so they follow the normal high-risk prompt, or require an explicit operator opt-in with the risk stated in the configuration comments. Resolve the executable name once and use the same normalized name for matching and for the flag checks.

## Target Files or Areas
- `scripts/agent/tool_policy.py` (`_special_case_risk`, `_match_executable_identity`, `_check_positional_args`, `_unsafe_flag_denylist`)
- `config/agent.toml` (`approval_shell_safe_prefixes` and its comment)
- `docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md`, `docs/91_security/security_02_high-risk-tool-common-policy.md`
- `config/shell_mcp_server.toml` (read-only reference for the server allowlist)
- `tests/agent/test_tool_policy.py`

## Required Changes
- Replace prefix-only matching with a per-executable rule that fixes the permitted subcommands and arguments; anything outside it is high.
- Remove `python`, `pytest`, `uv run`, and bare `git branch` from automatic approval (or restrict them to read-only forms such as `git branch --list`), unless the owner records an explicit decision to keep them.
- Use one normalized executable name for prefix matching and for flag checks.
- Align the agent-side list with the server allowlist, or document why they differ.
- Add tests with the real shipped values: each command in the reproduction above must be at least medium (high for code execution and branch deletion), while `git status`, `git log`, and `git diff` without output flags stay automatic.

## Constraints
- Keep the metacharacter and parse-failure rules (fail closed).
- Do not weaken the protected-path and `allowed_root` checks.
- Do not change the shell server's own allowlist or sandbox in this issue.
- Tests must not execute any command.

## Acceptance Criteria
- `python -c ...`, `pytest ...`, `uv run ...`, `git branch -D ...`, and `git diff --output=...` are not auto-approved, regardless of the agent's working directory.
- Read-only forms of `git status`, `git log`, `git diff`, and `git show` remain automatic.
- The prefix match and the flag denylist use the same executable name.
- The documentation lists which command shapes are auto-approved and why.
- The new tests fail on the current code and pass after the change.

## Testing Expectations
- Unit tests of `classify_risk` for `shell_run` using the shipped configuration values, in a working directory inside and outside `allowed_root`.
- Regression: run the tool policy, approval and config tests; run `ruff` and `mypy --no-namespace-packages` on touched files; run the documentation checks for changed docs.

## Documentation Impact
Update the two documents above to state which `shell_run` command shapes are auto-approved, the reason (read-only by construction), and that interpreters and test runners always prompt. Describe intent and boundaries only; do not copy the full prefix list.

## Out of Scope
- The sandbox, the server command allowlist, and `shell_cwd_allowed_dirs`.
- Parsing of `--flag=value` and extension of the flag denylist to more executables (tracked in `issues/20261003-180337_shellrisk001_shell-risk-check-misses-flag-paths.md`).
- Risk classification of tools other than `shell_run`.

## Dependencies
- Related to `issues/20261003-180337_shellrisk001_shell-risk-check-misses-flag-paths.md`: both change `_check_positional_args` and `_unsafe_flag_denylist`. Decide this issue's prefix policy first; it may make part of that issue's denylist generalization unnecessary, and its tests should be reconciled with this issue's.

## Unresolved Questions
- Whether `python`, `pytest`, `uv run`, and `git branch` were accepted deliberately as safe: `Needs confirmation`; the documents describe prefix auto-approval but do not list safe commands.
- The agent's working directory in production relative to `allowed_root`: `Needs confirmation`; it decides whether the positional-path check blocks the code-string case.
- What the sandbox allows (filesystem writes, network): `Needs confirmation`; it sets the real impact.
- How the shell server matches its allowlist (basename of the first token): `Needs confirmation`; it decides whether the unreachable entries are really rejected.

## AI Implementation Instruction
Write the failing tests first, using the shipped configuration values. Change only the shell risk classification, the related configuration comment, and the matching documentation. Keep every fail-closed branch. Do not run any shell command in tests. Stop and report if the owner has not decided whether interpreters stay auto-approved.

## Traceability
- **Workflow phase**: python-code-review -> issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261101-073644
- **Related target files**: scripts/agent/tool_policy.py, config/agent.toml, docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md, docs/91_security/security_02_high-risk-tool-common-policy.md, config/shell_mcp_server.toml, tests/agent/test_tool_policy.py
