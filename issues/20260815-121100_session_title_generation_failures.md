# SessionTitleService might have edge cases with LLM title generation failures

## Priority
Medium

## Summary
SessionTitleService generates and persists a session title via LLM using cfg.llm.title_llm_temperature and cfg.llm.title_llm_max_tokens. The service might not handle LLM title generation failures correctly in edge cases where the LLM returns unexpected responses.

## Reason for Change
During the adversarial review of the agent startup process, we traced the full session title generation flow through session_title.py. The service uses cfg.llm.title_llm_temperature and cfg.llm.title_llm_max_tokens for LLM configuration. However, there's no evidence of comprehensive testing for edge cases where the LLM might return unexpected responses or fail entirely.

## Implementation Intent
The fix should ensure LLM title generation failures are handled correctly. Consider adding retry logic or fallback mechanisms for failed title generation.

## Target Files or Areas
- scripts/agent/services/session_title.py
- LLM configuration

## Required Changes
- Add retry logic or fallback mechanisms for failed title generation
- Ensure title generation handles all possible edge cases
- Document the title generation policy clearly

## Acceptance Criteria
- [ ] Title generation handles all possible edge cases
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
