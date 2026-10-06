# Enable security strict mode and configure allowed tools

## Summary

Security defaults are not enforced: `tool_definitions_strict=false` (explicit in config), `routing_drift_strict=false` (default value), and `allowed_tools=[]` (empty = all tools allowed). These should be tightened for production.

## Background

The agent has three security-related configuration knobs that control strictness:
- `tool_definitions_strict` — validates tool definitions against the schema
- `routing_drift_strict` — validates routing configuration against expected state
- `allowed_tools` — restricts which tools can be called (empty = all allowed)

All three are set to permissive values.

## Problem

Startup output includes:
```
[local/development] tool_definitions_strict=false — strict mode is required in production
[local/development] routing_drift_strict=false — strict mode is required in production
[local/development] allowed_tools=[] (all tools allowed; use allowlist to restrict)
```

## Reason for Change

Permissive security defaults increase attack surface. Enabling strict mode catches configuration drift early. Restricting allowed tools limits the blast radius of any single tool compromise.

## Implementation Intent

Enable both strict modes and configure an explicit tool allowlist. This is a configuration change only — no code modifications required.

## Target Files or Areas

- `/opt/llm/config/agent.toml` — security defaults

## Required Changes

### Enable strict modes
```toml
tool_definitions_strict = true
routing_drift_strict = true
```

Note: `routing_drift_strict` must be added to the config (currently absent, using default `False`).

### Configure allowed tools
```toml
allowed_tools = ["file_read", "file_write", "git", "github", "shell", "web_search"]
```

## Constraints

- Do not remove tools from the allowlist without confirming they are needed
- Preserve existing tool concurrency limits and other settings

## Out of Scope

- Adding new security controls
- Changing the strict mode validation logic
- Modifying the tool registry

## Dependencies

- N/A: none

## Acceptance Criteria

- [ ] No strict mode warnings during startup
- [ ] Only configured tools are available
- [ ] Existing tool calls continue to work

## Testing Expectations

- Run `bash /opt/llm/start_agent.sh` and verify no strict mode warnings
- Test tool calls for configured tools to confirm they work

## Documentation Impact

Update deployment documentation to document required security posture settings.

## Unresolved Questions

- What is the correct `allowed_tools` list? (currently assumed based on available tools)

## Evidence

- Startup output: 3 security default warnings
- Source: `/opt/llm/config/agent.toml` (`tool_definitions_strict = false` at line 51, `allowed_tools = []` at line 139)
- Note: `routing_drift_strict` is absent from config; default value is `False` (per `scripts/agent/config_dataclasses.py:188`)

## Priority

Medium
