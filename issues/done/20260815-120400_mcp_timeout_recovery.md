# McpToolDiscoveryService inadequate timeout recovery

## Priority
High

## Summary
McpToolDiscoveryService discovers live MCP tools at startup and builds RuntimeToolRegistry. The timeout handling might not be robust enough for edge cases where MCP servers take longer than expected to respond.

## Reason for Change
During the adversarial review of the agent startup process, we traced the full MCP tool discovery flow through mcp_tool_discovery.py. The service fetches /v1/tools endpoints from HTTP-transport MCP servers, validates tool shape, normalizes to RuntimeTool instances, detects cross-server duplicates, and validates against static ToolRegistry for drift. However, there's no evidence of comprehensive timeout handling for edge cases where MCP servers might take longer than expected to respond.

## Implementation Intent
The fix should ensure timeout handling is robust for all possible edge cases. Consider adding configurable timeouts with sensible defaults based on server type.

## Target Files or Areas
- scripts/agent/services/mcp_tool_discovery.py
- Timeout configuration

## Required Changes
- Add configurable timeouts with sensible defaults
- Ensure timeout handling covers all possible edge cases
- Document the timeout policy clearly

## Acceptance Criteria
- [ ] Timeout handling covers all possible edge cases
- [ ] Adding new fields to diagnostics doesn't require manual updates to _filter_sensitive_fields()
- [ ] No regressions in normal operation when registry is available

## Testing Expectations
- Unit test for _filter_sensitive_fields() with various field combinations
- Integration test verifying diagnostic output during startup/shutdown

## Documentation Impact
If DiagnosticsConfig is extended, update documentation to reflect the new state.

## Out of Scope
- Changing the registry initialization order
- Adding retry logic for health checks

## AI Implementation Instruction
Modify only _filter_sensitive_fields() in diagnostic_store.py. Add a new state to McpAvailability enum if needed. Update the fallback logic to use the new state instead of UNKNOWN when registry is None.
