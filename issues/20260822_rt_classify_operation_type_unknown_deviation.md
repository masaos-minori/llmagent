# Known Issue: classify_operation_type uses static ToolRegistry for UNKNOWN distinction

## Summary

ADR-003 INV-04 states that the static ToolRegistry MUST NOT be used for runtime routing decisions. However, `classify_operation_type()` in `tool_policy.py` uses the static ToolRegistry to distinguish between UNKNOWN and READ operation types. When a tool exists in RuntimeToolRegistry but NOT in the static ToolRegistry, it is classified as UNKNOWN (HIGH risk) instead of READ (LOW risk), creating inconsistent security classification depending on which registry contains the tool.

## Details

| Field | Value |
|-------|-------|
| ID | RT-001 |
| Status | Open |
| Severity | Medium |
| Area | Tool routing / risk classification |
| Related ADR | ADR-003-runtime-tool-registry-routing-authority |
| Conflicting Source | scripts/agent/tool_policy.py:69-71 |
| Expected Design | INV-04: Static ToolRegistry is NOT used for runtime routing, limited to drift validation/tests/doc generation. The RuntimeToolRegistry should be the sole authority for ALL tool-related decisions including risk classification. |
| Observed Implementation | classify_operation_type() uses `get_registry().get_all_tool_names()` (static ToolRegistry) to check if a tool is registered. If absent from static registry, returns OperationType.UNKNOWN. If present, returns OperationType.READ. This means the same tool can have different classifications depending on whether it's in the static registry. |
| Impact | Tools discovered dynamically via MCP that are NOT in the static ToolRegistry will be classified as UNKNOWN (HIGH risk) during risk assessment, even though they may be legitimate tools with READ-only semantics. This creates inconsistent risk classification across the two registries. |
| Recommended Action | Replace the static ToolRegistry lookup with RuntimeToolRegistry lookup, or remove the UNKNOWN distinction entirely and rely on RuntimeToolRegistry's agent_safety_tier field for risk classification. |
| Owner | TBD |
| Resolution Target | Next sprint |
