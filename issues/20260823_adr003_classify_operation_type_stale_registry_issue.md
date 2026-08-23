# ADR-003: classify_operation_type uses static ToolRegistry instead of RuntimeToolRegistry

## Status
Open

## Severity
Medium

## Area
Tool Routing / Security Classification

## Related ADR
ADR-003: RuntimeToolRegistry as Sole Routing Authority

## Conflicting Source
- **Design**: ADR-003 INV-04 states "RuntimeToolRegistry is the sole authority for all runtime tool decisions"
- **Implementation**: `scripts/agent/tool_policy.py:69` — `classify_operation_type()` uses `get_registry().get_all_tool_names()` which references the static `ToolRegistry`, not `RuntimeToolRegistry`

## Expected Design
```python
def classify_operation_type(tool_name: str) -> OperationType:
    # Should use RuntimeToolRegistry as the sole authority
    if tool_name not in RuntimeToolRegistry.get_all_tool_names():
        return OperationType.UNKNOWN
    return OperationType.READ
```

## Observed Implementation
```python
def classify_operation_type(tool_name: str) -> OperationType:
    if tool_name in _ALL_WRITE_TOOLS:
        return OperationType.WRITE
    if tool_name in DELETE_TOOLS:
        return OperationType.DELETE
    if tool_name in _EXEC_TOOLS:
        return OperationType.EXECUTE
    if tool_name in _GITHUB_MUTATION_TOOLS:
        return OperationType.API_WRITE
    if tool_name not in get_registry().get_all_tool_names():  # ← Static ToolRegistry
        return OperationType.UNKNOWN
    return OperationType.READ
```

The same tool could have different classifications depending on whether it's registered in the static ToolRegistry:
- Tool exists in RuntimeToolRegistry but NOT in static ToolRegistry → classified as UNKNOWN (HIGH risk)
- Tool exists in BOTH registries → classified as READ (MEDIUM risk)

This creates inconsistent security behavior based on registration state rather than actual tool capabilities.

## Impact
- Tools added dynamically at startup via MCP discovery may be misclassified as UNKNOWN (higher risk) even though they are legitimate runtime tools
- This contradicts ADR-003's design intent of using RuntimeToolRegistry as the sole authority
- Could cause false-positive security escalations for newly discovered tools

## Recommended Action
1. Replace `get_registry().get_all_tool_names()` with `RuntimeToolRegistry.get_all_tool_names()` in `classify_operation_type()`
2. Ensure the change doesn't break existing tests
3. Add regression test coverage for dynamic tool classification scenarios

## Owner
Unassigned

## Resolution Target
Next maintenance cycle
