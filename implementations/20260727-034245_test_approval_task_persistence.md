## Goal

Add guard tests for approval task ID persistence across turns to establish behavioral baseline before refactoring.

## Scope

**In-Scope:**
- Test pending approval ID clearing — verify `pending_approval_id` cleared after resolution
- Test task ID overwrite detection — verify warning issued on second approval
- Test halted task status rejection — verify error returned instead of continued processing
- Test multiple sequential approvals — verify correct task restoration for each

**Out-of-Scope:**
- Changing the behavior of cmd_workflow or orchestrator itself
- Any changes beyond the test

## Assumptions

1. The approval flow needs characterization tests due to silent overwrites
2. Tests should verify current behavior, not expected future behavior
3. Current behavior likely has NO overwrite detection or halted task rejection

## Unknowns

| ID | Unknown Description | Resolution Path | Blocking? (True/False) |
|---|---|---|---|
| UNK-01 | Whether there's an existing test for approval edge cases | Search for `approval` in tests | False |

## Affected Areas & Tool Evidence

- **Affected Files:**
  - New file: `tests/test_approval_task_persistence.py` — all four gaps

- **Blast Radius:**
  - Low churn — new test file only
  - Very low risk since changes are defensive

- **Deploy Impact:**
  - Existing — no deploy.sh changes needed

## Design

Based on inspection of the approval flow logic:
```python
# Key behaviors:
# - pending_approval_id stored during approval workflow
# - Should be cleared after approval resolution
# - No overwrite detection currently exists
# - Halted tasks may continue processing without rejection
# - Sequential approvals need verification
```

The tests will verify all four gaps: ID clearing, overwrite detection, halted task rejection, and sequential approval handling.

## Implementation

### Target files
- New file: `tests/test_approval_task_persistence.py`

### Procedure
1. Phase 1: Verify no existing approval edge case tests exist
2. Phase 2: Create tests for each gap
3. Phase 3: Verify with lint and tests

### Method
Create characterization tests using real components where possible.

### Details
1. Create `tests/test_approval_task_persistence.py`:
   ```python
   """Characterization tests for approval task ID persistence across turns."""
   
   def test_pending_approval_id_cleared_after_resolution():
       """pending_approval_id should be cleared after approval resolution."""
       ...
   
   def test_task_id_overwrite_detection():
       """Warning should be issued when task ID is overwritten."""
       ...
   
   def test_halted_task_status_rejected():
       """Halted task status should return error, not continue processing."""
       ...
   
   def test_multiple_sequential_approvals():
       """Each sequential approval should restore correct task state."""
       ...
   ```

## Compatibility considerations

N/A — test-only change

## Security considerations

These changes improve reliability by documenting current behavior around approval workflows.

## Rollback considerations

- Simple revert: delete the test file

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/test_approval_task_persistence.py` | Characterization tests document current behavior | `uv run pytest -k "approval" -v` | All tests pass |

## Out of scope

- Changing the behavior of cmd_workflow or orchestrator itself
- Any changes beyond the test

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260726-134126_require.md
- Source plan: plans/20260726-173504_plan.md
- Source implementation procedure: N/A
- Generated at: 20260727-034245
- Related target files: scripts/agent/commands/cmd_workflow.py, scripts/agent/orchestrator.py
