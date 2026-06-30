## Goal
- Document MCP tool routing authority and fallback priority across 3 doc files

## Findings
- `04_mcp_03_routing_lifecycle_and_execution.md`: "Routing Source of Truth" section already has 4-layer priority definition (L75-L91). "Adding a New Tool Safely" section exists with clear steps (L136-L148).
- `05_agent_06_tool-execution-and-approval.md`: dispatch priority block (L15-L25) missing routing authority reference to 04_mcp_03.
- `05_agent_13_reference-api.md`: ToolRouteResolver mentioned as callee of ToolExecutor but no dedicated entry exists.

## Changes Made
1. Added routing authority note to `05_agent_06:L21`: "routing authority; see 04_mcp_03 §Routing Source of Truth"
2. Added ToolRouteResolver entry to `05_agent_13:L79-L89` (after ToolExecutor entry): Role, Primary API, Callers, Callees, Config, Failure, Full details link
3. Added recommended procedure note to `04_mcp_03:L149`: Priority ordering for new tool addition; static fallback NOT recommended as primary mechanism

## Conclusion
Code changes already complete. Documentation improvements applied across 3 files.
