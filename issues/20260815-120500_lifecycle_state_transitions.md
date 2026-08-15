# LifecycleState transition guards unclear source state when invalid transition detected

## Priority
Medium

## Summary
LifecycleState enum has valid transition guards via assert_valid_transition(). When an invalid transition is detected, the error message might not provide enough context about what the source state was.

## Reason for Change
During the adversarial review of the agent startup process, we traced the full lifecycle management flow through lifecycle.py. The LifecycleState transitions from STARTING → RUNNING/FAILED/STOPPED with valid transition guards. However, there's no evidence of comprehensive error handling for edge cases where an invalid transition might occur due to race conditions or unexpected state changes.

## Implementation Intent
The fix should ensure error messages provide enough context for debugging. Consider adding more specific error messages based on the source and target states.

## Target Files or Areas
- scripts/agent/lifecycle.py
- LifecycleState definition

## Required Changes
- Add more specific error messages based on source and target states
- Ensure error messages are actionable for debugging
- Document the transition policy clearly

## Acceptance Criteria
- [ ] Error messages provide enough context for debugging
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
