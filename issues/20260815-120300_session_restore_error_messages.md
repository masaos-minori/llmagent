# SessionRestoreService.restore_session() insufficient error message when session doesn't exist

## Priority
Medium

## Summary
SessionRestoreService.restore_session() raises SessionNotFoundError when session doesn't exist or has no messages, but the error message might not provide enough context for users to understand what went wrong.

## Reason for Change
During the adversarial review of the agent startup process, we traced the full session restoration flow through session_restore.py. The restore_session() method rebuilds history, switches session ID, and resets stats. However, there's no evidence of comprehensive error handling for edge cases where the session might exist but have no messages, or where the session might be corrupted.

## Implementation Intent
The fix should ensure error messages provide enough context for users to understand what went wrong. Consider adding more specific error messages based on the failure mode.

## Target Files or Areas
- scripts/agent/services/session_restore.py
- SessionNotFoundError definition

## Required Changes
- Add more specific error messages based on failure mode
- Ensure error messages are user-friendly and actionable
- Document the error handling policy clearly

## Acceptance Criteria
- [ ] Error messages provide enough context for users to understand what went wrong
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
