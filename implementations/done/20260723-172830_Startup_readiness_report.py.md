## Goal

Make local-mode fail-open state explicit, visible, and operationally safe by adding a startup readiness report, CLI status command, structured logging, and filtering unavailable tools from the runtime tool registry and LLM planning context.

## Scope

**In**:
- Startup readiness report function and print logic
- CLI status command exposing the same readiness information
- Structured logging of MCP health at startup
- Runtime tool registry construction rule: exclude tools from unhealthy MCP servers
- Planning context builder: filter out tools from unavailable MCP servers
- Operations documentation updates

**Out**:
- Production mode behavior changes (fail-fast remains unchanged)
- MCP server health detection logic (assumes existing health tracking data structures)
- New MCP server implementations
- Database schema changes

## Assumptions

1. MCP server health status is already tracked per-server somewhere in the startup module (e.g., a dict mapping server names to health states). If not, this becomes a blocking unknown.
2. The runtime tool registry is constructed after MCP health is known but before the LLM planning context is built.
3. A CLI command pattern already exists for agent REPL commands (e.g., `/health`, `/status`).
4. Structured logging via `structlog` is already used in the project.
5. The LLM planning context is built from the runtime tool registry or a related tool list.

## Design decisions

- Centralize readiness logic in a single function rather than duplicating across startup, CLI, and logging.
- Use conservative default for degraded MCP servers: exclude their tools unless explicit policy allows inclusion.
- Keep production fail-fast behavior unchanged — only affect local mode.
- Report capability-level status (not just service-level) so operators understand user impact.

## Alternatives considered

- Only change startup output without changing tool registration: leaves the LLM with incorrect tool availability info.
- Change tool registration only without adding visibility: operators still can't see what's degraded.
- Add configuration option for degraded-server behavior: adds complexity for a relatively simple problem.

## Implementation

### Target file

Startup orchestration module, MCP health tracking module, Runtime tool registry construction, Planning context builder, CLI command handler, Operations documentation

### Procedure

1. Investigate startup orchestration module for MCP health state tracking
2. Investigate runtime tool registry construction module
3. Investigate planning context builder
4. Investigate existing CLI command patterns
5. Create centralized readiness reporting function aggregating MCP health status
6. Print readiness report at startup
7. Add structured logging of readiness information at startup
8. Implement runtime tool registry exclusion rule: exclude tools from unhealthy MCP servers
9. Filter unavailable tools from LLM planning context
10. Add CLI status command exposing readiness information
11. Reuse existing CLI command pattern
12. Update operations documentation explaining fail-open behavior

### Method

Add readiness reporting function; modify RuntimeToolRegistry to filter tools by server health status; extend CLI status command; update documentation.

### Details

```python
# In RuntimeToolRegistry.__init__():
def __init__(
    self,
    tools: dict[str, RuntimeTool] | None = None,
    unavailable_servers: frozenset[str] | None = None,
    degraded_servers: frozenset[str] | None = None,
) -> None:
    self._unavailable_servers = unavailable_servers or frozenset()
    self._degraded_servers = degraded_servers or frozenset()
    self._tools: dict[str, RuntimeTool] = {}
    if tools:
        for name, tool in tools.items():
            if tool.server_key in self._unavailable_servers:
                continue  # Exclude unavailable server tools
            if tool.server_key in self._degraded_servers:
                continue  # Conservative default: exclude degraded server tools
            self._tools[name] = tool
```

## Compatibility considerations

Medium — affects multiple modules; changes tool availability behavior in local mode only.

## Security considerations

N/A — no security impact; only improves operational visibility for MCP failures.

## Rollback considerations

Revert RuntimeToolRegistry filtering logic and remove readiness reporting function; no data migration or config changes required.

## Validation plan

| Check | Tool | Target |
|---|---|---|
| Lint | `ruff check scripts/` | 0 errors |
| Type check | `mypy scripts/` | no new errors |
| Architecture | `lint-imports` | 0 violations |
| Security | `bandit` | no HIGH unaddressed |
| Unit tests | `pytest` | all pass |
| Pre-commit | `pre-commit run --all-files` | pass |

## Out of scope

- Production mode behavior changes (fail-fast remains unchanged)
- MCP server health detection logic (assumes existing health tracking data structures)
- New MCP server implementations
- Database schema changes

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260723-164756_plan.md
- Source implementation procedure: N/A
- Generated at: 20260723-172830
- Related target files: Implementation-dependent — startup orchestration, MCP health tracking, runtime tool discovery, runtime tool registry construction, CLI status command, operations documentation
