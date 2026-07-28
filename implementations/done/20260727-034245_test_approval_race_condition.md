## Goal

Add guard tests for approval resolution race condition to establish behavioral baseline before refactoring.

## Scope

**In-Scope:**
- Test concurrent resolution detection — verify only one succeeds on simultaneous resolution attempts
- Test optimistic locking — verify second resolution fails with appropriate error
- Test check-and-resolve atomicity — verify check + resolve within single transaction
- Test already-resolved clarity — verify clear "already resolved" response vs "not found"

**Out-of-Scope:**
- Changing the behavior of cmd_workflow or approval_ops itself
- Any changes beyond the test

## Assumptions

1. The approval flow needs characterization tests due to race condition risk
2. Tests should verify current behavior, not expected future behavior
3. Current behavior likely has NO optimistic locking or double-resolution detection

## Unknowns

| ID | Unknown Description | Resolution Path | Blocking? (True/False) |
|---|---|---|---|
| UNK-01 | Whether there's an existing test for approval edge cases | Search for `approval` in tests | False |

## Affected Areas & Tool Evidence

- **Affected Files:**
  - New file: `tests/test_approval_race_condition.py` — all four gaps

- **Blast Radius:**
  - Low churn — new test file only
  - Very low risk since changes are defensive

- **Deploy Impact:**
  - Existing — no deploy.sh changes needed

## Design

Based on inspection of the approval resolution logic:
```python
# Key behaviors:
# - Concurrent resolutions need detection and prevention
# - Optimistic locking may not exist currently
# - Check-and-resolve should be atomic
# - Already-resolved state should return clear message
```

The tests will verify all four gaps: concurrent detection, optimistic locking, atomicity, and clear status reporting.

## Implementation

### Target files
- New file: `tests/test_approval_race_condition.py`

### Procedure
1. Phase 1: Verify no existing approval edge case tests exist
2. Phase 2: Create tests for each gap
3. Phase 3: Verify with lint and tests

### Method
Create characterization tests using real components where possible.

### Details
1. Create `tests/test_approval_race_condition.py`:
   ```python
   """Characterization tests for approval resolution race condition."""
   
   @pytest.mark.asyncio
   async def test_concurrent_resolution_only_one_succeeds():
       """Only one concurrent resolution should succeed."""
       ...
   
   @pytest.mark.asyncio
   async def test_optimistic_locking_second_fails():
       """Second resolution should fail with appropriate error."""
       ...
   
   @pytest.mark.asyncio
   async def test_check_and_resolve_atomicity():
       """Check + resolve should occur within single transaction."""
       ...
   
   @pytest.mark.asyncio
   async def test_already_resolved_returns_clear_message():
       """Already-resolved should return 'already resolved' not 'not found'."""
       ...
   ```

## Compatibility considerations

N/A — test-only change

## Security considerations

These changes improve reliability by documenting current behavior around race conditions.

## Rollback considerations

- Simple revert: delete the test file

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/test_approval_race_condition.py` | Characterization tests document current behavior | `uv run pytest -k "approval" -v` | All tests pass |

## Out of scope

- Changing the behavior of cmd_workflow or approval_ops itself
- Any changes beyond the test

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260726-134503_require.md
- Source plan: plans/20260726-173841_plan.md
- Source implementation procedure: N/A
- Generated at: 20260727-034245
- Related target files: scripts/agent/commands/cmd_workflow.py, scripts/agent/workflow/approval_ops.py
