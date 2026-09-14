# Replace unsafe shell command prefix approval with parsed policy enforcement

## Priority
High

## Summary
Shell command risk classification currently authorizes approval-free execution using raw prefix matching (`cmd.startswith(p) for p in cfg.approval.approval_shell_safe_prefixes`, confirmed at `scripts/agent/tool_policy.py` line 138), which does not establish real executable identity or detect compound syntax, redirection, substitution, or unsafe arguments — this issue replaces it with parsed-command authorization that fails closed on ambiguous syntax.

## Background
N/A: covered by Summary — this is an independent security boundary and should not be mixed with the MCP startup work in `mcpagent01`.

## Problem
`_classify_shell_risk()` (or equivalent) in `scripts/agent/tool_policy.py` currently checks `cmd.startswith(p)` against a configured safe-prefix list. A command like `"cat /etc/passwd; rm -rf /"` or one using shell metacharacters (`|`, `&&`, backticks, `$()`) could share a prefix with an approved command and be misclassified as low-risk, since prefix matching does not parse compound syntax, redirection, or substitution.

## Reason for Change
Shell approval currently relies on raw command-prefix matching. This does not establish the executable identity or detect compound syntax, redirection, substitution, unsafe arguments, or path access. The issue is an independent security boundary and should not be mixed with MCP startup work.

## Implementation Intent
Authorize shell commands from a parsed representation and audited argument policy. Ambiguous or compound syntax must fail closed and require high-risk handling.

## Target Files or Areas
- `scripts/agent/tool_policy.py`
- `scripts/mcp_servers/shell/`
- `scripts/agent/tool_approval.py`, `scripts/agent/startup_approval_recovery.py`, `scripts/agent/workflow/approval_ops.py` (Unknown: source review cited a `scripts/agent/approval/` directory, which does not exist — these are the closest existing approval-related files; confirm the exact target(s) before implementation)
- `tests/agent/test_tool_policy.py`
- `tests/mcp_servers/shell/test_shell_mcp_service.py`, `tests/shared/protocols/test_shell_policy.py` (Unknown: source review cited `tests/test_shell_mcp.py`, which does not exist anywhere under `tests/`; these two existing files are the closest candidates — confirm exact target(s) before implementation)

## Required Changes
- Remove raw `startswith()` matching from shell risk classification.
- Parse the command into executable and arguments using the actual shell-execution semantics.
- Classify pipelines, redirection, command substitution, control operators, and multiple commands as high risk.
- Define allowed arguments and path constraints for each approval-free executable.
- Reassess whether `cat`, `find`, `grep`, and similar path-reading commands may ever be `RiskLevel.NONE`.
- Add adversarial tests for prefix collisions and shell metacharacter bypasses.

## Constraints
N/A: none stated in source review.

## Acceptance Criteria
- Only an exact approved executable with approved arguments can receive approval-free classification.
- Compound or ambiguous shell syntax is classified as high risk.
- Path restrictions and protected-path escalation still apply.
- Tests demonstrate that prefix collisions and shell metacharacters cannot bypass approval.

## Testing Expectations
Add or update automated tests for every modified behavior and failure path, including adversarial tests for prefix collisions and metacharacter bypasses (see Acceptance Criteria). Run unit tests, integration tests, static analysis, and type checks.

## Documentation Impact
Update ADRs and the active known-issue inventory only after executable verification is available.

## Out of Scope
- Unrelated refactoring outside the design and implementation boundary described in this issue.

## Dependencies
N/A: none — this issue is independent of the other issues in this batch (deliberately separated from `mcpagent01`'s MCP startup work per Reason for Change).

## Unresolved Questions
Exact file(s) among the existing approval-related and shell-test-related files that correspond to the source review's `scripts/agent/approval/` and `tests/test_shell_mcp.py` references — confirm during implementation. Non-blocking.

## AI Implementation Instruction
Keep changes scoped to shell command risk classification and its approval-free authorization logic; do not modify unrelated MCP startup code (see `mcpagent01`, which is intentionally separate). Confirm the exact approval/test file targets (see Unresolved Questions) before editing rather than guessing. Verify that logs and tool results do not expose credentials, payloads, raw response bodies, or sensitive configuration.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260914-103045
- **Related target files**: scripts/agent/tool_policy.py, scripts/mcp_servers/shell/, scripts/agent/tool_approval.py, scripts/agent/startup_approval_recovery.py, scripts/agent/workflow/approval_ops.py, tests/agent/test_tool_policy.py, tests/mcp_servers/shell/test_shell_mcp_service.py, tests/shared/protocols/test_shell_policy.py
