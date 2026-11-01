# Agent-side path policy ignores list-valued and unlisted path arguments

## Priority
Medium

## Summary
The agent's `allowed_root` check and its protected-path risk escalation read only string values stored under five configured argument names (`path`, `file_path`, `directory_path`, `source`, `destination`). A tool that takes its paths as a list (`read_multiple_files` uses `paths`) or under another name (the git tools use `repo_path`) is not checked at all: such a call passes the policy preflight and, for read-only tools, is auto-approved. The MCP servers enforce their own directory limits, so this is a missing layer rather than an open door, but the agent-side policy does not do what its configuration says. Derive the checked argument names from the tool metadata and handle list values.

## Background
Found during an adversarial review (`python-code-review`) of the agent's MCP call path.
- `tool_policy.check_allowed_root` and `_escalate_for_path` take the key list from `approval_resource_keys.path_keys` in `config/agent.toml` and iterate it with `_iter_string_arg_values`, which yields a value only when it is a non-empty `str`.
- `check_approval` runs `check_preflight` for every prepared call, so the preflight applies to read tools as well as write tools; the gap is in what it inspects, not in which tools it covers.
- Tool metadata already names the relevant arguments: `mcp_servers/file/read_tools.py` declares `resource_scope_keys` of `["paths"]` for `read_multiple_files`, and `mcp_servers/git/git_tools.py` declares `["repo_path"]` for the git tools. `shared/resource_scope.resolve_resource_scopes` uses these keys for scheduling.
- Server side: the file read server resolves paths against its allowed directories (`FileAuthorizationError`, HTTP 403) and the git server has `allowed_repo_paths`. `read_multiple_files` applies the jail to each listed path inside `read_single_file` (`Explicit in code`).
- `classify_risk` returns no risk immediately for tools whose tier is `READ_ONLY` or `WRITE_SAFE`, so the protected-path escalation never applies to them even for the listed keys; only the `allowed_root` denial does.

## Problem
Reproduction (throwaway script, not committed): the real `approval_resource_keys`, `allowed_tools`, `tool_safety_tiers` and protected paths from `config/agent.toml`, a temporary directory as `allowed_root`, and `check_preflight` plus `classify_risk` called directly. No tool was executed. Observed: `read_text_file` with `path=/etc/shadow` is denied (`denied_root_jail`), while `read_multiple_files` with `paths=["/etc/shadow", ...]` and `git_diff` with `repo_path=/etc` are allowed by the preflight and classified as no risk, so no prompt is shown.

Effects:
- The configured jail and protected paths do not apply to list-valued paths or to the git tools' repository path; a reviewer reading the configuration would assume they do.
- The agent-side layer, the approval prompt, and the audit `resource_scope` (also built from the same five keys) are blind to the paths these calls touch.
- Safety then rests entirely on each server's own enforcement.

## Reason for Change
A policy that silently covers only some argument shapes gives false assurance, and the omission is invisible in the configuration. Any new tool with a differently named path argument is unprotected until someone remembers to extend a global list.

## Implementation Intent
Make the path policy follow the tool's declared resource arguments: take the argument names from the tool metadata (`resource_scope_keys`) in addition to the configured keys, and treat list values by checking each string element. A path-like argument whose value is neither a string nor a list of strings should fail closed. Keep the configured key list as an additional source, not the only one. Apply the same extraction to the audit `resource_scope`.

## Target Files or Areas
- `scripts/agent/tool_policy.py` (`check_allowed_root`, `_escalate_for_path`, `_iter_string_arg_values`)
- `scripts/agent/tool_audit.py` (`_extract_resource_scope`)
- `scripts/shared/resource_scope.py` and `scripts/shared/runtime_tool.py` (read-only reference for the declared scope keys)
- `config/agent.toml` (`approval_resource_keys`)
- `tests/agent/test_tool_policy.py`

## Required Changes
- Resolve the checked argument names for a call from the registered tool's declared scope keys plus the configured keys.
- Check every string element of a list-valued argument; fail closed on an unexpected value type.
- Apply the same names to the audit resource scope.
- Add tests: `read_multiple_files` with one path outside `allowed_root` is denied; `git_diff` with a `repo_path` outside `allowed_root` is denied; a list with all paths inside is allowed; behavior for the five existing keys is unchanged.

## Constraints
- Keep the existing five-key behavior and denial codes.
- Do not change server-side enforcement.
- Do not add a registry lookup that fails open when the tool is unknown (an unknown tool is already rejected earlier in preparation).
- Tests must not touch real paths beyond temporary directories.

## Acceptance Criteria
- A call whose list-valued or `repo_path` argument contains a path outside `allowed_root` is denied by the preflight.
- The audit `resource_scope` for such calls lists those paths.
- Calls using the five existing keys behave as before.
- The new tests fail on the current code and pass after the change.

## Testing Expectations
- Unit tests of `check_preflight`, `classify_risk` and `_extract_resource_scope` with a stub registry that declares the scope keys.
- Regression: run the tool policy, approval and audit tests; run `ruff` and `mypy --no-namespace-packages` on touched files.

## Documentation Impact
Needs confirmation: check whether the approval documentation describes `approval_resource_keys`. If it does, state that the checked arguments come from tool metadata as well as configuration, and that list values are checked element by element.

## Out of Scope
- Shell command path handling (see `issues/20261101-073644_shellprefix001_safe-prefix-approves-code.md` and `issues/20261003-180337_shellrisk001_shell-risk-check-misses-flag-paths.md`).
- Changing which tiers skip protected-path escalation.
- Resolving relative paths against the server's working directory instead of the agent's.

## Dependencies
- Related to `issues/20261101-073644_shellprefix001_safe-prefix-approves-code.md`: both edit `tool_policy.py` and its tests; they are independent in behavior and can be done in either order.

## Unresolved Questions
- Confirmed (`Explicit in code`): `ReadBusiness.read_single_file` resolves each listed path against the allowed directories, and the git service enforces `allowed_repo_paths`, so this issue is defense in depth only.
- `index_paths` (the `mdq` tool) with `paths=["/etc"]` was also allowed with no risk in the same reproduction, so it is a third confirmed example. Other tools with other names or shapes: `Needs confirmation`; the metadata-driven approach covers them only if they declare scope keys.
- Whether `READ_ONLY` and `WRITE_SAFE` tools should still escalate on protected paths: a policy decision; this issue keeps the current behavior.
- `allowed_root` is resolved against the agent's working directory for relative paths, while the server resolves them against its own: `Needs confirmation` whether this can differ in production.

## AI Implementation Instruction
Write the failing tests first. Change only path-argument extraction in the policy and the audit scope, plus tests. Keep the five-key behavior and fail closed on unexpected shapes. Do not change tiers or server code. Stop and report if the tool metadata does not carry scope keys for a tool that needs them.

## Traceability
- **Workflow phase**: python-code-review -> issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261101-073742
- **Related target files**: scripts/agent/tool_policy.py, scripts/agent/tool_audit.py, scripts/shared/resource_scope.py, scripts/shared/runtime_tool.py, config/agent.toml, tests/agent/test_tool_policy.py
