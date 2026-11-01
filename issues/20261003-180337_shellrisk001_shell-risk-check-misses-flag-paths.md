# Shell risk check misses flag paths

## Priority
Medium

## Summary
`shell_run` risk-escalation checks inspect only non-flag positional tokens for protected-path and allowed-root violations, so a path supplied as `--flag=value` (for example `grep --file=/etc/shadow pattern`) is skipped. Narrowed scope: the generalization of the unsafe-flag denylist and the executable-name mismatch are tracked in `issues/20261101-073644_shellprefix001_safe-prefix-approves-code.md`; this issue covers the `--flag=value` and flag-value path extraction.

## Background
Found during an adversarial code review (`python-code-review` skill) of the REPL's tool-execution/approval-gating subsystem (`scripts/agent/tool_policy.py`) and re-verified against the current code. The shell MCP server's own allowlist (`config/shell_mcp_server.toml`) is `pytest`, `python`, `python3`, `git`, `ruff` and `mypy` (normalized to basenames), so `grep`, `cat` and `find` are probably unreachable today; the reachable gap is mainly `python`, `pytest` and `git`. The `--flag=value` bypass also depends on `allowed_root` being set and on the agent's working directory, as described in `shellprefix001`. Related, different gap: `issues/20261101-073742_pathkeys001_path-checks-skip-lists.md`.

## Problem
`scripts/agent/tool_policy.py::_check_positional_args()` builds `positional = [a for a in argv[1:] if not a.startswith("-")]` and escalates only on those tokens; any path supplied via `--flag=value` (the whole token starts with `-`) is skipped. `_UNSAFE_FLAGS` still lists only `find` (`-exec`, `-delete`, `-ok`), `grep` (`-r`, `-R`) and `cat` (an empty set), and `_unsafe_flag_denylist` is looked up with the unnormalized first token (see `shellprefix001`).

## Reason for Change
A `shell_run` command using an allowlisted "safe" executable can embed a protected path or a dangerous flag in `--flag=value` form and receive a lower risk classification (potentially `RiskLevel.NONE`, auto-approved with no interactive prompt) than an equivalent space-separated form would. This narrows — but does not eliminate — the protected-path escalation that `_escalate_for_path`/`_check_positional_args` are meant to guarantee for shell commands, and auto-approval of a crafted command bypasses the human-in-the-loop check for what should be a MEDIUM/HIGH-risk operation.

## Implementation Intent
Normalize `--flag=value` tokens into (flag, value) pairs before positional-path classification so that a path after `=` gets the same protected-path and allowed-root checks as a space-separated positional argument. Broader flag-denylist redesign (deny by default per executable) belongs to `shellprefix001`; do not duplicate it here.

## Target Files or Areas
- `scripts/agent/tool_policy.py` (`_check_positional_args()`)

## Required Changes
- Parse `--flag=value` tokens into flag and value parts before applying positional-path and protected-path checks.
- Add tests: a protected path supplied via `--flag=value` escalates like the equivalent space-separated form, using the executables that the server allowlist actually permits.

## Constraints
- Do not change the risk-escalation thresholds themselves, only the token parsing/coverage that feeds them.
- Do not remove or weaken the existing `find`/`cat`/`grep` unsafe-flag entries.

## Acceptance Criteria
- A protected-path value supplied via `--flag=value` escalates risk identically to the same path supplied as a bare positional argument.
- Existing positional-argument behavior is unchanged.

## Testing Expectations
Unit tests for both scenarios above. Run `tests/agent/test_tool_policy.py` after the change, including existing `shell_run` risk-classification tests to confirm no regression in already-covered cases.

## Documentation Impact
N/A: no operator-facing documentation describes the exact token-parsing coverage of this check today.

## Out of Scope
- Generalizing `_UNSAFE_FLAGS` to other executables and normalizing the executable name (see `issues/20261101-073644_shellprefix001_safe-prefix-approves-code.md`).
- `tool_approval.check_approval()`'s own approval-prompt flow.
- Any change to `approval_shell_safe_prefixes`'s configuration format.

## Dependencies
Related to `issues/20261101-073644_shellprefix001_safe-prefix-approves-code.md`: both change `_check_positional_args` and `_unsafe_flag_denylist`. Decide that issue's prefix policy first; it may make part of this issue's tests redundant.

## Unresolved Questions
N/A: none; the `not a.startswith("-")` filter was confirmed in the current code.

## AI Implementation Instruction
Parse `--flag=value` tokens carefully (distinguish `--flag=value` from a bare `--flag` and from a short flag that takes a space-separated value) before extending path checks to cover them. Do not generalize the unsafe-flag denylist here. Add the regression tests described above before considering this done.

## Traceability
- **Workflow phase**: python-code-review -> issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261003-180337
- **Related target files**: scripts/agent/tool_policy.py
