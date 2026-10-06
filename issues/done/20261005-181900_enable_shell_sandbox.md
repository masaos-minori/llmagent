# Enable shell sandbox backend

## Summary

Shell MCP server runs commands without sandbox isolation (`shell_sandbox_backend=none`). This causes a fatal startup error.

## Background

The shell MCP server supports two sandbox backends:
- `"firejail"` — sandboxed execution via firejail (requires firejail installed)
- `"none"` — unsandboxed execution (fatal error at startup)

Current configuration uses `"none"`.

## Problem

Startup fails with:
```
RuntimeError: shell_sandbox_backend=none is not permitted regardless of environment
```

This is a fatal error — AgentREPL cannot start until the sandbox backend is changed from `"none"`.

## Reason for Change

Unsandboxed shell execution allows arbitrary command execution without resource limits or isolation. Additionally, this is a startup blocker — AgentREPL cannot start with `sandbox_backend="none"`.

## Implementation Intent

Install firejail and switch the sandbox backend to `"firejail"`. This is a configuration change plus a system dependency installation.

## Target Files or Areas

- `/opt/llm/config/shell_mcp_server.toml` — sandbox backend setting

## Required Changes

### Install firejail
```bash
apt-get install -y firejail
```

### Update configuration
```toml
shell_sandbox_backend = "firejail"
```

## Constraints

- firejail must be available in the deployment environment before this change
- If firejail cannot be installed, consider alternative sandbox solutions

## Out of Scope

- Adding new sandbox backends
- Modifying the sandbox enforcement logic
- Changing other MCP server security settings

## Dependencies

- firejail must be installed on the deployment host

## Acceptance Criteria

- [ ] No sandbox backend warning during startup
- [ ] Shell commands execute within sandbox isolation
- [ ] Existing shell tool calls continue to work

## Testing Expectations

- Run `bash /opt/llm/start_agent.sh` and verify no sandbox backend warning
- Test shell tool calls to confirm they work within sandbox

## Documentation Impact

Update deployment documentation to document firejail as a required dependency.

## Unresolved Questions

- Is firejail available in the deployment environment?

## Evidence

- Startup failure: `RuntimeError: shell_sandbox_backend=none is not permitted regardless of environment`
- Source: `/opt/llm/config/shell_mcp_server.toml` (`shell_sandbox_backend = "none"` at line 31)
- Source: `scripts/agent/services/security_audit.py:89-91` (fatal error on sandbox_backend="none")
- Note: `scripts/mcp_servers/shell/shell_service_static_helpers.py:36` warns about missing firejail binary when sandbox_backend="firejail"

## Priority

Medium
