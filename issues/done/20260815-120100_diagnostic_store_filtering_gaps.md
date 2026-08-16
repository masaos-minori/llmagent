# DiagnosticStore._filter_sensitive_fields() may have filtering gaps

## Priority
High

## Summary
DiagnosticStore._filter_sensitive_fields() redacts sensitive fields (artifacts, rag_stage_outcomes) but may miss other sensitive data paths during diagnostic storage.

## Reason for Change
During the adversarial review of the agent startup process, we traced the full diagnostic store flow through diagnostic_store.py. The DiagnosticStore stores data in session_diagnostics table and handles encryption/retention settings via DiagnosticsConfig. The _filter_sensitive_fields() method redacts artifacts and rag_stage_outcomes, but there's no evidence of comprehensive field-level validation against the DiagnosticsConfig schema. If new fields are added to diagnostics without updating _filter_sensitive_fields(), they could leak sensitive information.

## Implementation Intent
The fix should ensure _filter_sensitive_fields() validates against DiagnosticsConfig schema rather than hardcoding field names. Consider adding a schema validation step or making the filter configurable based on DiagnosticsConfig.

## Target Files or Areas
- scripts/agent/services/diagnostic_store.py
- DiagnosticsConfig definition

## Required Changes
- Add schema validation to _filter_sensitive_fields() or make it configurable based on DiagnosticsConfig
- Ensure new fields are automatically covered by the filter
- Document the filtering policy clearly

## Acceptance Criteria
- [ ] All sensitive fields are filtered regardless of how many exist
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
