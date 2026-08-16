# HTTP subprocess MCP server lifecycle manager StartupFailure dataclass insufficient error context

## Priority
Medium

## Summary
HTTP subprocess MCP server lifecycle manager uses StartupFailure dataclass to record stderr output and reason. The dataclass might not provide enough context for debugging startup failures.

## Reason for Change
During the adversarial review of the agent startup process, we traced the full HTTP subprocess lifecycle through http_lifecycle.py. The HttpServerLifecycleManager handles startup, health-poll, restart, shutdown with StartupFailure dataclass recording stderr output and reason. However, there's no evidence of comprehensive error handling for edge cases where the startup failure might require more context for debugging.

## Implementation Intent
The fix should ensure error context is sufficient for debugging. Consider adding more fields to StartupFailure dataclass or improving the error message formatting.

## Target Files or Areas
- scripts/agent/http_lifecycle.py
- StartupFailure dataclass definition

## Required Changes
- Add more fields to StartupFailure dataclass where needed
- Ensure error context is sufficient for debugging
- Document the error reporting policy clearly

## Acceptance Criteria
- [ ] Error context is sufficient for debugging
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
