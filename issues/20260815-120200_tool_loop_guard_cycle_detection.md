# ToolLoopGuard cycle detection may have infinite loop risk

## Priority
High

## Summary
ToolLoopGuard encapsulates per-turn mutable state and guard rules applied each time LLM returns tool_calls. The cycle detection logic might not handle edge cases properly, potentially leading to infinite loops.

## Reason for Change
During the adversarial review of the agent startup process, we traced the full turn orchestration flow through orchestrator.py → llm_turn_runner.py → tool_loop_guard.py. The ToolLoopGuard handles duplicate call detection, cycle detection, retry suppression, and consecutive error limiting. However, there's no evidence of comprehensive testing for the cycle detection edge cases where the LLM might return tool_calls that don't make progress but also don't trigger the existing guards.

## Implementation Intent
The fix should ensure cycle detection handles all possible edge cases. Consider adding a maximum iteration limit as a safety net beyond the existing guard rules.

## Target Files or Areas
- scripts/agent/tool_loop_guard.py
- scripts/agent/orchestrator.py

## Required Changes
- Add maximum iteration limit to prevent infinite loops
- Ensure cycle detection handles all possible edge cases
- Document the guard rules clearly

## Acceptance Criteria
- [ ] Cycle detection prevents infinite loops under all conditions
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
