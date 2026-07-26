## Goal

Add guard tests for orchestrator background task failure threshold behavior to establish behavioral baseline before refactoring.

## Scope

**In-Scope:**
- Test consecutive failure counting — verify `_consecutive_bg_failures` increments correctly
- Test threshold reach behavior — verify error log output and agent continues running at 5 failures
- Test _on_error callback exception handling — verify exception logged but not notified to user
- Test cancelled task counter reset — verify `_consecutive_bg_failures` resets to 0

**Out-of-Scope:**
- Changing the behavior of orchestrator itself
- Any changes beyond the test

## Assumptions

1. The orchestrator needs characterization tests due to silent failure behavior
2. Tests should verify current behavior, not expected future behavior
3. Current behavior likely has NO user notification on threshold breach

## Unknowns

| ID | Unknown Description | Resolution Path | Blocking? (True/False) |
|---|---|---|---|
| UNK-01 | Whether there's an existing test for orchestrator edge cases | Search for `orchestrator` in tests | False |

## Affected Areas & Tool Evidence

- **Affected Files:**
  - New file: `tests/test_orchestrator_bg_failure_threshold.py` — all four gaps

- **Blast Radius:**
  - Low churn — new test file only
  - Very low risk since changes are defensive

- **Deploy Impact:**
  - Existing — no deploy.sh changes needed

## Design

Based on inspection of the orchestrator layer:
```python
# Key behaviors:
# - _consecutive_bg_failures: incremented on each bg task failure, reset on success
# - BG_FAILURE_THRESHOLD: when reached, logs error but does NOT notify user
# - _on_error callback: exceptions caught and logged, not propagated to user
# - Cancelled tasks: do NOT increment _consecutive_bg_failures
```

The tests will verify all four gaps: failure counting, threshold behavior, error callback handling, and cancellation logic.

## Implementation

### Target files
- New file: `tests/test_orchestrator_bg_failure_threshold.py`

### Procedure
1. Phase 1: Verify no existing orchestrator edge case tests exist
2. Phase 2: Create tests for each gap
3. Phase 3: Verify with lint and tests

### Method
Create characterization tests using real components where possible.

### Details
1. Create `tests/test_orchestrator_bg_failure_threshold.py`:
   ```python
   """Characterization tests for orchestrator background task failure threshold."""
   
   @pytest.mark.asyncio
   async def test_consecutive_failures_increment():
       """_consecutive_bg_failures should increment on each bg task failure."""
       ...
   
   @pytest.mark.asyncio
   async def test_threshold_reached_logs_error_but_continues():
       """At threshold, error logged but agent continues running."""
       ...
   
   @pytest.mark.asyncio
   async def test_on_error_callback_exception_logged_not_notified():
       """_on_error callback exceptions logged but not notified to user."""
       ...
   
   @pytest.mark.asyncio
   async def test_cancelled_task_resets_counter():
       """Cancelled tasks do NOT increment _consecutive_bg_failures."""
       ...
   ```

## Compatibility considerations

N/A — test-only change

## Security considerations

These changes improve reliability by documenting current behavior.

## Rollback considerations

- Simple revert: delete the test file

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/test_orchestrator_bg_failure_threshold.py` | Characterization tests document current behavior | `uv run pytest -k "orchestrator" -v` | All tests pass |

## Out of scope

- Changing the behavior of orchestrator itself
- Any changes beyond the test

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260726-133855_require.md
- Source plan: plans/20260726-173230_plan.md
- Source implementation procedure: N/A
- Generated at: 20260727-034245
- Related target files: scripts/agent/orchestrator.py
