# Add `uv` to MCP subprocess allowed commands list

## Summary

All 10 MCP subprocesses fail to start because `uv` is not in the allowed commands list. This renders all MCP tools unusable.

## Background

The `CommandValidator` class validates commands before allowing MCP subprocesses to start. The allowed commands list (`_DEFAULT_ALLOWED_COMMANDS`) does not include `uv`, which is required by all MCP servers that use `uv run` to start their subprocesses.

## Problem

AgentREPL startup produces 10 identical warnings:
```
First attempt failed for MCP subprocess 'X': Command 'uv' (resolved to '/usr/bin/uv') is not in the allowed commands list.
```

This affects all MCP servers: shell, git, web_search, file_delete, file_write, file_read, github, cicd, rag_pipeline, mdq.

## Reason for Change

Without `uv` in the allowed commands list, no MCP subprocess can start. This is a correctness issue — the agent cannot use any MCP tools.

## Implementation Intent

Add `"uv"` to the `_DEFAULT_ALLOWED_COMMANDS` frozenset in `http_lifecycle_command_validator.py`. This is a minimal, single-line change that restores MCP subprocess functionality.

## Target Files or Areas

- `scripts/agent/http_lifecycle_command_validator.py` — line 24-26 (`_DEFAULT_ALLOWED_COMMANDS`)
- `scripts/agent/http_lifecycle.py` — line 67-69 (`_ALLOWED_COMMANDS`)

## Required Changes

Add `"uv"` to both frozensets:

### http_lifecycle_command_validator.py
```python
_DEFAULT_ALLOWED_COMMANDS: frozenset[str] = frozenset(
    {"node", "npm", "npx", "uvx", "python", "pipx", "uvicorn", "uv"}
)
```

### http_lifecycle.py
```python
_ALLOWED_COMMANDS: frozenset[str] = frozenset(
    {"node", "npm", "npx", "uvx", "python", "pipx", "uvicorn", "uv"}
)
```

## Constraints

- Do not add other commands not currently used by MCP servers
- Preserve the frozenset type annotation
- Do not modify the protected env vars list

## Out of Scope

- Adding new MCP servers
- Changing the command validation logic
- Modifying the allowed commands list via config

## Dependencies

- N/A: none

## Acceptance Criteria

- [ ] All 10 MCP subprocesses start successfully without "not in the allowed commands list" errors
- [ ] MCP tool discovery succeeds for all configured servers
- [ ] Existing tests pass after the change

## Testing Expectations

- Run `bash /opt/llm/start_agent.sh` and verify no MCP startup failures
- Run `uv run pytest tests/agent/test_context.py::TestAppServicesValidation` to verify no regressions

## Documentation Impact

N/A: no documentation update required

## Unresolved Questions

- N/A: all items are resolved

## Evidence

- Startup output: 10 MCP subprocess failures with "Command 'uv' ... is not in the allowed commands list"
- Source: `scripts/agent/http_lifecycle_command_validator.py:24-26` (_DEFAULT_ALLOWED_COMMANDS)
- Source: `scripts/agent/http_lifecycle.py:67-69` (_ALLOWED_COMMANDS)

## Priority

High
