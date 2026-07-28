## Goal

Add guard tests for stampede protection cascading failure behavior to establish behavioral baseline before refactoring.

## Scope

**In-Scope:**
- Test concurrent request exception propagation — verify all waiting requests receive same exception
- Test server health registry update — verify failure recorded in server health registry
- Test retry policy application — verify retry behavior for transient errors
- Test partial success scenario — verify correct handling of mixed results

**Out-of-Scope:**
- Changing the behavior of tool_executor itself
- Any changes beyond the test

## Assumptions

1. The stampede protection needs characterization tests due to cascading failure risk
2. Tests should verify current behavior, not expected future behavior
3. Current behavior likely has NO per-request isolation for exceptions

## Unknowns

| ID | Unknown Description | Resolution Path | Blocking? (True/False) |
|---|---|---|---|
| UNK-01 | Whether there's an existing test for stampede protection edge cases | Search for `stampede` in tests | False |

## Affected Areas & Tool Evidence

- **Affected Files:**
  - New file: `tests/test_stampede_protection_cascade.py` — all four gaps

- **Blast Radius:**
  - Low churn — new test file only
  - Very low risk since changes are defensive

- **Deploy Impact:**
  - Existing — no deploy.sh changes needed

## Design

Based on inspection of the tool_executor stampede protection logic:
```python
# Key behaviors:
# - Concurrent requests share a single execution path during stampede
# - First failure propagates to all waiting requests
# - Server health registry tracks failures for circuit breaker
# - Retry policy applies to transient errors
# - Partial success scenarios need verification
```

The tests will verify all four gaps: exception propagation, health registry updates, retry policies, and partial success handling.

## Implementation

### Target files
- New file: `tests/test_stampede_protection_cascade.py`

### Procedure
1. Phase 1: Verify no existing stampede protection edge case tests exist
2. Phase 2: Create tests for each gap
3. Phase 3: Verify with lint and tests

### Method
Create characterization tests using real components where possible.

### Details
1. Create `tests/test_stampede_protection_cascade.py`:
   ```python
   """Characterization tests for stampede protection cascading failure behavior."""
   
   @pytest.mark.asyncio
   async def test_concurrent_request_exception_propagation():
       """All waiting requests should receive the same exception."""
       ...
   
   @pytest.mark.asyncio
   async def test_server_health_registry_updated_on_failure():
       """Failure should be recorded in server health registry."""
       ...
   
   @pytest.mark.asyncio
   async def test_retry_policy_applied_for_transient_errors():
       """Retry policy should apply for transient errors."""
       ...
   
   @pytest.mark.asyncio
   async def test_partial_success_scenario_handled_correctly():
       """Mixed results should be handled correctly."""
       ...
   ```

## Compatibility considerations

N/A — test-only change

## Security considerations

These changes improve reliability by documenting current behavior around cascading failures.

## Rollback considerations

- Simple revert: delete the test file

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/test_stampede_protection_cascade.py` | Characterization tests document current behavior | `uv run pytest -k "stampede" -v` | All tests pass |

## Out of scope

- Changing the behavior of tool_executor itself
- Any changes beyond the test

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260726-134033_require.md
- Source plan: plans/20260726-173412_plan.md
- Source implementation procedure: N/A
- Generated at: 20260727-034245
- Related target files: scripts/shared/tool_executor.py
