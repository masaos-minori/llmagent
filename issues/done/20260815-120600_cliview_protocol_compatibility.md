# CLIView Writer/Reader protocols compatibility issues with test doubles

## Priority
Medium

## Summary
CLIView uses Writer and Reader Protocols for testable I/O presentation layer. The protocol definitions might have compatibility issues with test doubles that don't implement all required methods.

## Reason for Change
During the adversarial review of the agent startup process, we traced the full CLI presentation flow through cli_view.py. The Writer and Reader Protocols allow test doubles and alternative I/O backends without touching callers. However, there's no evidence of comprehensive testing for edge cases where test doubles might not implement all required methods correctly.

## Implementation Intent
The fix should ensure protocol definitions are compatible with all possible test double implementations. Consider adding optional methods or default implementations where appropriate.

## Target Files or Areas
- scripts/agent/cli_view.py
- Writer/Reader Protocol definitions

## Required Changes
- Add optional methods or default implementations where appropriate
- Ensure protocol definitions are compatible with all possible test double implementations
- Document the protocol requirements clearly

## Acceptance Criteria
- [ ] Protocol definitions are compatible with all possible test double implementations
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
