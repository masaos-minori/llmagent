# Replace deprecated UV_NATIVE_TLS with UV_SYSTEM_CERTS

## Summary

The `UV_NATIVE_TLS` environment variable is deprecated in favor of `UV_SYSTEM_CERTS`. All deploy scripts still use the deprecated variable.

## Background

The `uv` package deprecated `UV_NATIVE_TLS` and recommends `UV_SYSTEM_CERTS` instead. The deprecation warning appears during every AgentREPL startup.

## Problem

Startup output includes:
```
warning: The `UV_NATIVE_TLS` environment variable is deprecated and will be removed in a future release. Use `UV_SYSTEM_CERTS` instead.
```

This appears during AgentREPL startup (the workflow validation step does not produce this warning).

## Reason for Change

The deprecated variable will break in future `uv` versions. Replacing it now avoids future breakage.

## Implementation Intent

Replace `UV_NATIVE_TLS=true` with `UV_SYSTEM_CERTS=true` in all deploy scripts. This is a simple find-and-replace across 4 files.

## Target Files or Areas

- `deploy/start_agent.sh` — lines 65, 76
- `deploy/setup_services.sh` — lines 28, 56 (112-114はユーザー向け例示のため省略可)
- `deploy/init_db.sh` — line 28
- `deploy/deploy.sh` — lines 24, 33

## Required Changes

Replace all occurrences of `UV_NATIVE_TLS=true` with `UV_SYSTEM_CERTS=true`:
```bash
# Before:
PYTHONPATH="${PYTHONPATH}" UV_NATIVE_TLS=true uv run python ...

# After:
PYTHONPATH="${PYTHONPATH}" UV_SYSTEM_CERTS=true uv run python ...
```

## Constraints

- Do not remove the variable entirely — `uv` requires one of these to enable TLS
- Preserve the `PYTHONPATH` setting alongside it

## Out of Scope

- Changing TLS behavior (keep the same security posture)
- Modifying the `uv` dependency version

## Dependencies

- N/A: none

## Acceptance Criteria

- [ ] No `UV_NATIVE_TLS` deprecation warnings during startup
- [ ] TLS connections work correctly (no regression)
- [ ] Deploy scripts execute without errors

## Testing Expectations

- Run `bash /opt/llm/start_agent.sh` and verify no deprecation warnings
- Verify MCP server connections still work (TLS)

## Documentation Impact

Update deployment documentation to reference `UV_SYSTEM_CERTS` instead of `UV_NATIVE_TLS`.

## Unresolved Questions

- N/A: the replacement is straightforward

## Evidence

- Startup output: `UV_NATIVE_TLS` deprecation warning during AgentREPL startup
- Source: `deploy/start_agent.sh:65,76`, `deploy/setup_services.sh:28,56`, `deploy/init_db.sh:28`, `deploy/deploy.sh:24,33`
- Note: `setup_services.sh:112-114` are user-facing example commands (not auto-executed)

## Priority

Medium
