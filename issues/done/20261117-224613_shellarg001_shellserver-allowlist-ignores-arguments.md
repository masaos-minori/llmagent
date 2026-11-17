# Shell server allowlist ignores command arguments

## Priority
Medium

## Summary
The shell-mcp server validates only the executable name (`argv[0]` basename) against
`command_allowlist` and imposes no constraint on the remaining arguments. Because
`python`, `python3`, `pytest`, and `git` are allowlisted, an authenticated caller can run
arbitrary code (`python -c ...`, `pytest` importing repository code) or destructive git
operations (`git branch -D`, `git push`) with no argument-level check. Tighten the allowlist
to a per-command argument contract, or route code-executing forms through approval.

## Background
- `ShellService._check_command` (`scripts/mcp_servers/shell/shell_service.py`) parses the
  request into `argv`, then accepts it when `os.path.basename(argv[0])` is in
  `self._allowlist`; `argv[1:]` is returned to the runner unchecked. The allowlist is built
  in `__init__` by normalizing `policy.allowed_commands` to basenames. Confirmed by repository
  evidence.
- `config/shell_mcp_server.toml` sets `command_allowlist = ["pytest", "python", "python3",
  "git", "ruff", "mypy"]` with the comment "permitted command names (matched against
  argv[0] basename)". Confirmed by repository evidence.
- ADR-014 makes the MCP server own the technical safety of shell execution (allowlist
  enforcement, cwd/path validation, sandboxed execution); this is not duplicated in the
  Orchestrator/ToolExecutor layers (`shell_service.py` module docstring). Confirmed by
  repository evidence.
- The agent also has a shell allowlist/auto-approval in `scripts/agent/tool_policy.py`. Issue
  `issues/20261101-073644_shellprefix001_safe-prefix-approves-code.md` covers that agent-side
  layer and explicitly lists "the server command allowlist" as Out of Scope, leaving the
  server-side matching an open `Needs confirmation`. This issue addresses that uncovered layer.

## Problem
- Reproduction (no command executed): call `shell_run` with `command="python -c
  __import__('os').system('id')"` or `command="git branch -D feature"`. `_check_command`
  passes because the basenames `python`/`git` are in the allowlist, and the unrestricted
  arguments reach the subprocess runner. Confirmed by reading `_check_command`.
- An allowlisted interpreter entry is functionally "execute any code": the allowlist
  constrains the executable name only, not what the command does. `pytest` imports repository
  code, and `git` can delete or push branches.
- A reviewer reading `command_allowlist` assumes the listed tools' behavior is constrained. It
  is not; the config comment honestly states argv[0]-only matching, so nothing warns that
  `python` means arbitrary code execution.

## Reason for Change
The allowlist is the last technical safety boundary (ADR-014) before execution. A basename-only
match for interpreters and VCS tools degrades to "run whatever name is allowlisted with any
arguments," which defeats the least-privilege intent. The gap is invisible in configuration
because the comment documents argv[0]-only matching without stating the impact of an
interpreter entry, so no operator or reviewer is alerted that code execution is reachable.

## Implementation Intent
Add an argument-shape check to the server's command validation, after the existing basename
allowlist gate. For each allowlisted executable, define the permitted argument shapes as a
deny-by-default contract (allowed subcommands/flags, forbidden patterns such as a free-form
code string for interpreters, or mutating git subcommands). Anything outside the per-command
contract fails closed. Design direction: either restrict interpreters and git to safe/read-only
forms, or route code-executing forms to the human-in-the-loop approval instead of
auto-executing. Keep the basename allowlist as the first gate; add argument validation as the
second. Do not change the agent-side `tool_policy` layer, which is covered by
`shellprefix001`.

## Target Files or Areas
- `scripts/mcp_servers/shell/shell_service.py` (`_check_command`, `ShellService.__init__`
  allowlist build)
- `config/shell_mcp_server.toml` (`command_allowlist` and its comment)
- `scripts/shared/protocols/shell.py` (`ShellPolicy.allowed_commands`) — read-only reference
- `tests/mcp_servers/shell/` — shell server tests

## Required Changes
- Add an argument-shape check after the basename allowlist match in `_check_command`; reject
  `argv` when an interpreter (`python`, `python3`) is invoked with a free-form code argument, or
  when `git` is used with a mutating subcommand, unless a safe form is defined.
- Express the per-command argument contract as a deny-by-default table or configuration, so new
  executables require an explicit decision.
- Fail closed on unrecognized or unexpected argument shapes; never execute before validation.
- Document which argument shapes are permitted for each allowlisted command.

## Constraints
- Keep the existing basename allowlist as the first gate; do not weaken it.
- Preserve `shlex`/`argv` parsing and empty-command rejection.
- Do not change the agent-side `tool_policy.py` auto-approval layer (`shellprefix001`).
- Do not alter the sandbox, resource limits, or env filtering.
- Fail closed: unrecognizable argument shapes are rejected, not executed.

## Acceptance Criteria
- `python -c <code>`, `pytest` importing arbitrary modules, and mutating `git` forms are
  rejected or require approval.
- Read-only / safe forms of the allowlisted commands still execute.
- An unrecognized argument shape for an allowlisted executable fails closed.
- Tests fail on the current code and pass after the change.

## Testing Expectations
- Unit tests of `_check_command` / `run_command` with the shipped allowlist: code-execution and
  mutating-git forms are rejected; safe forms are allowed.
- Regression: run the shell server tests; run `ruff` and `mypy --no-namespace-packages` on
  touched files.
- No command is actually executed in tests (assert rejection before the subprocess launch, or
  use `dry_run`).

## Documentation Impact
Update the `command_allowlist` comment in `config/shell_mcp_server.toml` to state which
argument shapes are permitted for each allowlisted command and that code-executing forms require
approval. State intent and boundaries only; do not enumerate every flag.

## Out of Scope
- Agent-side `tool_policy.py` auto-approval (`shellprefix001`).
- The sandbox, resource limits, and environment filtering.
- Changing which commands appear in `command_allowlist`; that is an operator policy decision to
  document, not remove here.

## Dependencies
- Related to `issues/20261101-073644_shellprefix001_safe-prefix-approves-code.md`: both concern
  the shell command allowlist but at different layers (agent risk classification vs server
  technical safety). Resolve `shellprefix001` first; this issue covers the server layer that
  `shellprefix001` left out of scope.
- Related to `issues/20261003-180337_shellrisk001_shell-risk-check-misses-flag-paths.md`:
  agent-side flag handling; independent layer.

## Unresolved Questions
- Whether `python`/`python3`/`git` in `command_allowlist` were accepted deliberately as
  unconstrained: `Needs confirmation`. The config comment documents argv[0]-only matching but
  does not state that `python` means arbitrary code.
- Which argument shapes should be permitted versus require approval for each command:
  `Needs confirmation`; an operator policy decision.
- Whether the agent-side prompt currently fires for `shell_run` before the server runs it:
  `Needs confirmation`; affects whether this is the only check on arguments.
- Real blast radius of the firejail sandbox (filesystem writes, network egress beyond
  `--net=none`): `Needs confirmation`; sets the actual impact.

## AI Implementation Instruction
Write failing unit tests first, using the shipped `command_allowlist`. Add argument validation
in `shell_service.py::_check_command` (or a helper it calls) and keep the basename allowlist as
the first gate; fail closed and never execute before validation. Do not touch `tool_policy.py`,
the sandbox, resource limits, or env filtering. Do not remove commands from
`command_allowlist`; express permitted shapes as a deny-by-default contract. Stop and report if
the owner has not decided which forms need approval.

## Traceability
- **Workflow phase**: python-code-review -> issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261117-224613
- **Related target files**: scripts/mcp_servers/shell/shell_service.py, config/shell_mcp_server.toml, tests/mcp_servers/shell/
