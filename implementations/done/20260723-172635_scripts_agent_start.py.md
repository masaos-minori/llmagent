## Goal

Improve fail-open visibility and runtime tool availability handling when MCP servers fail to start in local mode.

## Scope

**In:**
- Startup orchestration module: Add readiness reporting function and startup output
- MCP health tracking module: Expose health status for readiness reporting
- Runtime tool discovery module: Filter out tools from unavailable/degraded MCP servers
- Runtime tool registry construction module: Apply conservative default (exclude degraded server tools)
- CLI status command handler: Expose readiness information via `/mcp status` or similar
- Operations documentation: Update to explain fail-open behavior

**Out:**
- Changing production fail-fast semantics
- Modifying existing MCP health check logic
- Adding new configuration options for fail-open behavior

## Assumptions

1. The `McpToolDiscoveryService.discover_all()` already tracks unreachable servers via `DiscoveryResult.unreachable` — confirmed by reading the code.
2. The `RuntimeToolRegistry` stores tools keyed by server — confirmed by reading the code.
3. The LLM planning context uses `RuntimeToolRegistry.llm_tool_definitions()` — confirmed by reading the code.
4. Production mode already uses stricter fail-fast behavior — confirmed by requirement description.
5. Local mode should allow partial functionality while clearly communicating what's unavailable.

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

`scripts/agent/startup.py`, `scripts/agent/services/mcp_health.py`, `scripts/agent/services/mcp_tool_discovery.py`, `scripts/shared/runtime_tool_registry.py`, CLI status command, operations documentation

### Procedure

1. Create centralized readiness reporting function that aggregates MCP health, workflow readiness, RAG readiness, memory readiness, and capability-level summary
2. Call the readiness function at startup and print the result
3. Write readiness information to logs during startup
4. Modify `McpToolDiscoveryService.discover_all()` to pass unreachable/degraded server keys to `RuntimeToolRegistry`
5. Modify `RuntimeToolRegistry` constructor to accept unavailable/degraded server keys and exclude their tools
6. Ensure `llm_tool_definitions()` only returns tools from healthy servers
7. Search for existing `/health` or `/status` CLI commands
8. Implement or extend the CLI command to expose readiness information
9. Update operations documentation to explain fail-open behavior

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

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/startup.py | Lint | `ruff check scripts/agent/startup.py` | 0 errors |
| scripts/agent/startup.py | Type check | `mypy scripts/agent/startup.py` | no new errors |
| scripts/shared/runtime_tool_registry.py | Lint | `ruff check scripts/shared/runtime_tool_registry.py` | 0 errors |
| scripts/shared/runtime_tool_registry.py | Type check | `mypy scripts/shared/runtime_tool_registry.py` | no new errors |
| scripts/agent/services/mcp_tool_discovery.py | Lint | `ruff check scripts/agent/services/mcp_tool_discovery.py` | 0 errors |
| scripts/agent/services/mcp_tool_discovery.py | Type check | `mypy scripts/agent/services/mcp_tool_discovery.py` | no new errors |
| All modified files | Architecture | `lint-imports` | 0 violations |
| All modified files | Tests | `pytest tests/test_agent/ -k discovery` | all pass |
| All modified files | Tests | `pytest tests/test_shared/ -k registry` | all pass |
| All modified files | Manual test | Simulate MCP server startup failure | Verify readiness report, logs, and CLI command reflect degraded state |

## Out of scope

- Changing production fail-fast semantics
- Modifying existing MCP health check logic
- Adding new configuration options for fail-open behavior

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260723-152456_plan.md
- Source implementation procedure: N/A
- Generated at: 20260723-172635
- Related target files: Implementation-dependent — startup orchestration, MCP health tracking, runtime tool discovery, runtime tool registry construction, CLI status command, operations documentation
