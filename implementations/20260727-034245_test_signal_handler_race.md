## Goal

Add guard tests for signal handler race condition prevention to establish behavioral baseline before refactoring.

## Scope

**In-Scope:**
- Test turn active flag check — verify `_turn_active` flag is checked/set in signal handler
- Test cross-platform signal handler consistency — verify consistent behavior on Unix vs Windows
- Test shutdown completeness — verify shutdown completes properly even when ctx.services becomes None
- Test shared state modification safety — verify no data corruption under concurrent modifications

**Out-of-Scope:**
- Changing the behavior of repl.py itself
- Any changes beyond the test

## Assumptions

1. The signal handler needs characterization tests due to race condition risk
2. Tests should verify current behavior, not expected future behavior
3. Current behavior likely has NO `_turn_active` flag check in signal handler

## Unknowns

| ID | Unknown Description | Resolution Path | Blocking? (True/False) |
|---|---|---|---|
| UNK-01 | Whether there's an existing test for signal handler edge cases | Search for `signal` in tests | False |

## Affected Areas & Tool Evidence

- **Affected Files:**
  - New file: `tests/test_signal_handler_race.py` — all four gaps

- **Blast Radius:**
  - Low churn — new test file only
  - Very low risk since changes are defensive

- **Deploy Impact:**
  - Existing — no deploy.sh changes needed

## Design

Based on inspection of the repl.py signal handler logic:
```python
# Key behaviors:
# - Signal handler called during turn execution
# - _turn_active flag should be checked before processing
# - Cross-platform differences between Unix and Windows signals
# - ctx.services may become None during shutdown
# - Shared state modifications need thread-safety verification
```

The tests will verify all four gaps: turn active flag, cross-platform consistency, shutdown completeness, and shared state safety.

## Implementation

### Target files
- New file: `tests/test_signal_handler_race.py`

### Procedure
1. Phase 1: Verify no existing signal handler edge case tests exist
2. Phase 2: Create tests for each gap
3. Phase 3: Verify with lint and tests

### Method
Create characterization tests using real components where possible.

### Details
1. Create `tests/test_signal_handler_race.py`:
   ```python
   """Characterization tests for signal handler race condition prevention."""
   
   def test_turn_active_flag_checked_in_signal_handler():
       """_turn_active flag should be checked in signal handler."""
       ...
   
   @pytest.mark.skipif(sys.platform == 'win32', reason="Unix-specific")
   def test_cross_platform_signal_handler_consistency():
       """Signal handler should behave consistently across platforms."""
       ...
   
   def test_shutdown_completes_when_services_become_none():
       """Shutdown should complete even when ctx.services becomes None."""
       ...
   
   def test_shared_state_modification_safety():
       """No data corruption should occur under concurrent modifications."""
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
| `tests/test_signal_handler_race.py` | Characterization tests document current behavior | `uv run pytest -k "signal" -v` | All tests pass |

## Out of scope

- Changing the behavior of repl.py itself
- Any changes beyond the test

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260726-134219_require.md
- Source plan: plans/20260726-173557_plan.md
- Source implementation procedure: N/A
- Generated at: 20260727-034245
- Related target files: scripts/agent/repl.py
