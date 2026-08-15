# SessionMessageRepository role validation might miss edge cases

## Priority
Medium

## Summary
SessionMessageRepository validates roles against frozenset {"user", "assistant", "tool", "system"} but might miss edge cases where invalid roles could slip through due to type coercion or unexpected input formats.

## Reason for Change
During the adversarial review of the agent startup process, we traced the full session/message persistence flow through session_message_repo.py. The repository normalizes content before insert (None stored as "") and tracks stat_skipped_no_session and stat_skipped_invalid_role counters. However, there's no evidence of comprehensive testing for edge cases where invalid roles might slip through due to type coercion or unexpected input formats.

## Implementation Intent
The fix should ensure role validation covers all possible edge cases. Consider adding more robust type checking or input sanitization.

## Target Files or Areas
- scripts/agent/session_message_repo.py
- Role validation logic

## Required Changes
- Add more robust type checking for role validation
- Ensure role validation covers all possible edge cases
- Document the role validation policy clearly

## Acceptance Criteria
- [ ] Role validation covers all possible edge cases
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
