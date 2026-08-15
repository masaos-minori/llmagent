# McpStatusService._resolve_health_state() returns UNKNOWN when registry is None

## Priority
Medium

## Summary
McpStatusService._resolve_health_state() falls back to UNKNOWN when McpServerHealthRegistry is None, which can mask MCP server health issues during startup or shutdown.

## Reason for Change
During the adversarial review of the agent startup process, we traced the full startup sequence through factory.py → build_agent_context() → AgentContext assembly. The McpStatusService probes all MCP servers and formats status table, but _resolve_health_state() has a fallback to UNKNOWN when registry is None. This means that during startup/shutdown phases where the registry might not be fully initialized, the service will report UNKNOWN instead of a more informative state like "unavailable" or "initializing".

## Implementation Intent
The fix should provide a more informative fallback state than UNKNOWN when the registry is None. Consider using a dedicated state like "initializing" or "unavailable" that clearly indicates the registry is not yet available rather than just unknown.

## Target Files or Areas
- scripts/agent/services/mcp_status.py

## Required Changes
- Replace UNKNOWN fallback in _resolve_health_state() with a more informative state when registry is None
- Ensure the new state is documented in the McpAvailability enum or similar

## Acceptance Criteria
- [ ] When registry is None, _resolve_health_state() returns a state other than UNKNOWN
- [ ] The new state clearly indicates the registry is unavailable rather than just unknown
- [ ] No regressions in normal operation when registry is available

## Testing Expectations
- Unit test for _resolve_health_state() with registry=None
- Integration test verifying status table display during startup/shutdown

## Documentation Impact
If McpAvailability enum is extended, update documentation to reflect the new state.

## Out of Scope
- Changing the registry initialization order
- Adding retry logic for health checks

## AI Implementation Instruction
Modify only _resolve_health_state() in mcp_status.py. Add a new state to McpAvailability enum if needed. Update the fallback logic to use the new state instead of UNKNOWN when registry is None.
