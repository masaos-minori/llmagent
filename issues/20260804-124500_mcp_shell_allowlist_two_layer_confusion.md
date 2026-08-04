# Split the conflated Agent-layer / MCP-server-layer allowlist warning descriptions in docs/04_mcp_*.md (shell-mcp)

## Priority
Medium

## Target files
- `docs/04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md`
- `docs/04_mcp_05_05_mdq-enforcement-and-lockdown.md`

## Background
Similar to the `cicd-mcp` `workflow_allowlist` case, there is a conflation between the Agent-layer warning and the shell-mcp server-layer warning regarding `command_allowlist` and `shell_cwd_allowed_dirs`.

Specifically:
1. **Agent layer** — `scripts/agent/repl_health.py`, function `audit_security_defaults()` logs a warning if `shell.command_allowlist` or `shell_cwd_allowed_dirs` is empty.
2. **shell-mcp layer** — `scripts/mcp_servers/shell/shell_service.py` independently logs warnings if these allowlists are empty.

Currently, some documentation files describe these as a single combined warning or omit the server-layer component.

## Problem
Documentation accuracy affects incident-response speed. An operator might miss the server-layer warning if they only monitor the agent REPL output, or vice versa.

## Implementation intent
(To be detailed in the issue-to-requirement phase)
