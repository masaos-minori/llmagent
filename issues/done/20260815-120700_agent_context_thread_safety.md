# AgentContext shared mutable state thread safety concerns

## Priority
Medium

## Summary
AgentContext composes ConversationState, TurnState, RuntimeStats, AppServices as shared mutable runtime state. The shared mutable state might have thread safety concerns when accessed concurrently from multiple sources.

## Reason for Change
During the adversarial review of the agent startup process, we traced the full context injection flow through context.py. The AgentContext is injected into AgentREPL and CommandRegistry via dependency injection. However, there's no evidence of comprehensive thread safety analysis for edge cases where concurrent access might occur from multiple sources.

## Implementation Intent
The fix should ensure thread safety for all possible access patterns. Consider adding synchronization mechanisms or making the state immutable where appropriate.

## Target Files or Areas
- scripts/agent/context.py
- AgentContext definition

## Required Changes
- Add synchronization mechanisms where needed
- Ensure thread safety for all possible access patterns
- Document the thread safety policy clearly

## Acceptance Criteria
- [ ] Thread safety is ensured for all possible access patterns
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
