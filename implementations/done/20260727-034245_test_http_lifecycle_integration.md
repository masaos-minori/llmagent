## Goal

Add guard tests for http_lifecycle.py before refactoring to establish behavioral baseline for signal handling, subprocess lifecycle, and shutdown sequence.

## Scope

**In-Scope:**
- Create `tests/test_http_lifecycle_integration.py` with tests for:
  - Signal handling: signal handlers registered and restored correctly
  - Subprocess lifecycle: subprocesses start, run, and stop correctly
  - Shutdown sequence: shutdown_all works correctly under various conditions
  - Error recovery: failed starts don't prevent subsequent attempts

**Out-of-Scope:**
- Changing the behavior of http_lifecycle or factory modules
- Any changes beyond the test

## Assumptions

1. The lifecycle module needs characterization tests due to dense OS/signal/subprocess side effects
2. Some tests require real processes for signal testing; others can use mocking
3. Tests should verify current behavior, not expected future behavior

## Unknowns

| ID | Unknown Description | Resolution Path | Blocking? (True/False) |
|---|---|---|---|
| UNK-01 | Whether there's an existing test for http lifecycle edge cases | Search for `lifecycle` in tests | False |

## Affected Areas & Tool Evidence

- **Affected Files:**
  - New file: `tests/test_http_lifecycle_integration.py`

- **Blast Radius:**
  - Test-only change — no production code affected

- **Deploy Impact:**
  - Existing — no deploy.sh changes needed

## Design

Based on inspection of `http_lifecycle.py`:
```python
# Key behaviors:
# - startup(): registers SIGINT handler, starts HTTP servers
# - shutdown_all(): unregisters SIGINT handler, stops all subprocesses
# - _absorb_sigint_during_shutdown(): temporary signal handler during shutdown
# - restart(): stops one server and starts it again
```

The test will verify signal handling, subprocess lifecycle, shutdown sequence, and error recovery.

## Implementation

### Target file
New file: `tests/test_http_lifecycle_integration.py`

### Procedure
1. Create new test file `tests/test_http_lifecycle_integration.py`
2. Write tests for signal handling
3. Write tests for subprocess lifecycle
4. Write tests for shutdown sequence
5. Write tests for error recovery
6. Save the file

### Method
Create integration tests using real processes where needed and mocking where appropriate.

### Details
1. Create `tests/test_http_lifecycle_integration.py`:
   ```python
   """Integration tests for HttpLifecycle."""
   
   import asyncio
   import signal
   import pytest
   
   @pytest.mark.asyncio
   async def test_signal_handlers_registered_on_startup():
       """Signal handlers are registered when starting HTTP servers."""
       ...
   
   @pytest.mark.asyncio
   async def test_signal_handlers_restored_after_shutdown():
       """Original signal handlers are restored after shutdown."""
       ...
   
   @pytest.mark.asyncio
   async def test_subprocess_start_stop_lifecycle():
       """Subprocesses start, run, and stop correctly."""
       ...
   
   @pytest.mark.asyncio
   async def test_shutdown_all_under_various_conditions():
       """shutdown_all works correctly under various conditions."""
       ...
   
   @pytest.mark.asyncio
   async def test_failed_start_doesnt_block_subsequent_attempts():
       """Failed server starts don't prevent subsequent attempts."""
       ...
   ```

## Compatibility considerations

N/A — test-only change

## Security considerations

N/A — this test documents current behavior

## Rollback considerations

- Simple revert: delete the test file

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/test_http_lifecycle_integration.py` | Integration tests document current behavior | `uv run pytest -k "lifecycle" -v` | All tests pass |

## Out of scope

- Changing the behavior of http_lifecycle or factory modules
- Any changes beyond the test

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260726-130228_require.md
- Source plan: plans/20260726-172535_plan.md
- Source implementation procedure: N/A
- Generated at: 20260727-034245
- Related target files: scripts/agent/http_lifecycle.py, scripts/agent/factory.py, tests/test_http_lifecycle_integration.py
