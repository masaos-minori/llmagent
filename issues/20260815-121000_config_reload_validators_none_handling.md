# ConfigReloadService typed_validators might have edge cases with None values

## Priority
Medium

## Summary
ConfigReloadService uses typed_validators for field extraction with ConfigReloadValidationError on mismatch. The validators might not handle None values correctly in edge cases where configuration fields are missing or null.

## Reason for Change
During the adversarial review of the agent startup process, we traced the full config reload flow through config_reload.py and typed_validators.py. The service applies reloaded configuration to live service instances using _get_int, _get_float, _get_bool, etc. with ConfigReloadValidationError on mismatch. However, there's no evidence of comprehensive testing for edge cases where configuration fields might be missing or null.

## Implementation Intent
The fix should ensure validators handle None values correctly. Consider adding explicit None checks or default value handling.

## Target Files or Areas
- scripts/agent/services/config_reload.py
- scripts/agent/services/typed_validators.py

## Required Changes
- Add explicit None checks or default value handling in validators
- Ensure validators handle all possible edge cases
- Document the validator policy clearly

## Acceptance Criteria
- [ ] Validators handle None values correctly
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
