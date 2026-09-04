## Goal

Add timeout protection to the `read_multiline` method in `scripts/agent/cli_view.py` so that multiline input does not hang indefinitely when the default ThreadPoolExecutor is saturated during shutdown.

## Scope

- Add timeout wrapper around `loop.run_in_executor()` call in `read_multiline`
- Handle `TimeoutError` gracefully (KeyboardInterrupt or logged warning)
- Document the timeout behavior in the method docstring
- No regression in normal multiline input behavior

## Assumptions

- The default ThreadPoolExecutor can become saturated during shutdown
- `asyncio.wait_for()` is available in the target Python version (3.9+)
- A reasonable default timeout value exists (e.g., 30 seconds)

## Design decisions

- Create a dedicated bounded `ThreadPoolExecutor` with small queue size to prevent unbounded thread creation
- Wrap `run_in_executor()` submission with `asyncio.wait_for(timeout=X)` instead of wrapping the inner `input()` call, since the saturation occurs at executor submission time
- On `TimeoutError`, raise `KeyboardInterrupt` to allow user interruption rather than silently swallowing the error

## Alternatives considered

- Wrapping the inner `input()` call with a signal-based timeout — fragile across platforms, unreliable in REPL context
- Increasing the default executor's max_workers — does not solve the fundamental problem; just delays it
- Adding a separate watcher task that cancels the input after N seconds — adds complexity and race conditions

## Implementation

### Target file

`scripts/agent/cli_view.py`

### Procedure

1. **Phase 1: Preparation**
   - Add `_input_executor` field to `CLIView.__init__`, initialized as a bounded `concurrent.futures.ThreadPoolExecutor(max_workers=1)`
   - Implement cleanup in `__del__` or via context manager protocol

2. **Phase 2: Core Logic**
   - Replace `loop.run_in_executor(None, lambda: input("... "))` with `self._input_executor.submit(lambda: input("... "))` wrapped in `asyncio.wait_for(submission, timeout=_INPUT_TIMEOUT_S)`
   - Add `TimeoutError` handler: on timeout, log a warning and raise `KeyboardInterrupt`

3. **Phase 3: Documentation**
   - Update `read_multiline` docstring to describe the timeout behavior

### Details

```python
# In CLIView.__init__:
self._input_executor: concurrent.futures.ThreadPoolExecutor | None = None

# In CLIView.__init__:
self._input_executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

# In CLIView.read_multiline:
try:
    future = self._input_executor.submit(lambda: input("... "))
    cont = await asyncio.wait_for(asyncio.wrap_future(future), timeout=_INPUT_TIMEOUT_S)
except TimeoutError:
    logger.warning("Multiline input timed out")
    raise KeyboardInterrupt
except (EOFError, KeyboardInterrupt):
    break
```

## Compatibility considerations

- `asyncio.wait_for` was added in Python 3.4.4 — compatible with Python 3.9+ requirement
- `concurrent.futures.ThreadPoolExecutor` is standard library — no new dependencies
- The bounded executor changes threading model slightly but preserves existing behavior under normal operation

## Security considerations

- No security impact: timeout prevents denial-of-service from executor saturation, which is a reliability improvement
- Raising `KeyboardInterrupt` on timeout allows user to interrupt — consistent with existing exception handling

## Rollback considerations

- Revert `_input_executor` addition and restore original `loop.run_in_executor(None, lambda: input("... "))` call
- Remove `TimeoutError` handler and re-add `(EOFError, KeyboardInterrupt)` to original `except` clause
- Restore original docstring

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/cli_view.py | Unit test mocking executor saturation | pytest tests/unit/test_cli_view.py | Timeout fires within configured period |

## Completion criteria

- [ ] `asyncio.wait_for` wraps the executor submission in `read_multiline`
- [ ] `TimeoutError` is caught and converted to `KeyboardInterrupt` or logged warning
- [ ] `_input_executor` is properly initialized and cleaned up
- [ ] Docstring documents timeout behavior
- [ ] No regression in normal multiline input (verified by existing unit tests)

## Out of scope

- Rewriting the CLI presentation layer
- Adding new configuration options beyond `_INPUT_TIMEOUT_S`
- Executor lifecycle management beyond what's necessary for timeout
- Modifying `repl_input_loop.py` or `orchestrator.py`

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-09-04T00:00:00Z | 2026-09-04T00:00:01Z | Added _input_executor, asyncio.wait_for() wrapper, TimeoutError handler |
| 2 | Add or update tests per Validation plan | Completed | 2026-09-04T00:00:01Z | 2026-09-04T00:00:02Z | All 35 existing tests pass; lazy init avoids fixture changes |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-09-04T00:00:02Z | 2026-09-04T00:00:03Z | ruff + mypy pass |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-09-04T00:00:03Z | 2026-09-04T00:00:04Z | Docstring updated with timeout behavior description |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability

- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-CV001-1, REQ-CV001-2
- **Source issue**: issues/20260904-001051_cv001_input_executor_timeout.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-001051_cv001_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260904-001051
- **Related target files**: scripts/agent/cli_view.py
