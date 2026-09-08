## Goal

Fix `_read_input()`'s `shutdown_event is not None` branch so `KeyboardInterrupt` raised during input reading is caught and treated as a graceful end-of-input signal, matching the behavior of the `else` branch.

## Scope

Modify only `scripts/agent/repl_input_loop.py` to prevent `KeyboardInterrupt` from escaping past the `except KeyboardInterrupt:` clause at line 154.

## Assumptions

- CPython's Task machinery special-cases `(KeyboardInterrupt, SystemExit)` and re-raises them through the event loop's callback machinery when a Task's own coroutine step raises one of these exceptions.
- The `input_coro.result()` call at line 146 propagates the exception before the `except KeyboardInterrupt:` clause at line 154 can catch it.
- The `else` branch (line 157-162) already handles `KeyboardInterrupt` correctly via `(EOFError, KeyboardInterrupt)`.

## Design decisions

- Wrap the entire `try/except` block (lines 145-156) in a try/except that catches `KeyboardInterrupt` and `SystemExit`, then calls `_abort_input()` and returns `None`.
- This approach preserves the existing control flow while adding a safety net for the Task machinery bug.
- Minimal change: only modify the existing code, do not introduce new abstractions.

## Alternatives considered

1. **Replace `input_coro.result()` with `await input_coro`** — Would propagate the exception through await machinery instead of result(), but CPython still re-raises `(KeyboardInterrupt, SystemExit)` through await. Not effective.
2. **Catch the exception inside `_input_task()`** — Would require wrapping the executor call in a try/except inside the Task, but the exception is raised after the Task completes, not during execution.
3. **Use `asyncio.wait_for()` with timeout** — Same issue as alternative 1; the exception propagation mechanism is the same.
4. **Cancel the task and retry** — Complex and introduces race conditions; unnecessary given the simpler approach.

## Implementation

### Target file

`scripts/agent/repl_input_loop.py`

### Procedure

1. After the `input_coro.result()` call at line 146, wrap the subsequent `except` clauses in a try/except that catches `KeyboardInterrupt` and `SystemExit`.
2. When caught, call `self._abort_input()` and return `None`.

### Method

Add a try/except wrapper around the existing `try/except` block (lines 145-156):

```python
            try:
                raw = input_coro.result()
            except asyncio.CancelledError:
                # Input was cancelled by signal handler — treat as shutdown
                self._abort_input()
                return None
            except EOFError:
                self._abort_input()
                return None
            except KeyboardInterrupt:
                self._abort_input()
                return None
```

Change to:

```python
            try:
                raw = input_coro.result()
            except asyncio.CancelledError:
                # Input was cancelled by signal handler — treat as shutdown
                self._abort_input()
                return None
            except EOFError:
                self._abort_input()
                return None
            except KeyboardInterrupt:
                self._abort_input()
                return None
            except (KeyboardInterrupt, SystemExit):
                # Safety net: Task machinery may re-raise these through
                # the event loop's callback machinery even though we
                # just handled KeyboardInterrupt above. This catches
                # the case where the exception propagated out of the
                # Task before our except clause could catch it.
                self._abort_input()
                return None
```

Wait, this would be redundant since we already handle `KeyboardInterrupt` above. The correct approach is different.

The issue is that `input_coro.result()` raises `KeyboardInterrupt` BEFORE the `except KeyboardInterrupt:` clause at line 154 can execute. The exception has already been propagated out of the Task machinery. So the fix needs to wrap the entire `result()` call in a try/except:

```python
            try:
                raw = input_coro.result()
            except asyncio.CancelledError:
                # Input was cancelled by signal handler — treat as shutdown
                self._abort_input()
                return None
            except EOFError:
                self._abort_input()
                return None
            except KeyboardInterrupt:
                self._abort_input()
                return None
            except Exception:
                # Catch any other unexpected exception from result()
                self._abort_input()
                return None
```

But wait, `KeyboardInterrupt` is already caught above. The real issue is that the `KeyboardInterrupt` raised by `input_coro.result()` bypasses the `except KeyboardInterrupt:` clause because the exception has already been propagated out of the Task machinery.

Actually, looking at this more carefully, the `except KeyboardInterrupt:` clause at line 154 SHOULD catch the exception from `input_coro.result()`. The issue described in the source issue is that the exception escapes past this clause entirely.

Let me reconsider. The problem is that `input_coro.result()` raises `KeyboardInterrupt`, but the `except KeyboardInterrupt:` clause at line 154 does NOT catch it because the exception has already been propagated out of the Task machinery.

The correct fix is to wrap the entire `result()` call in a try/except that catches `(KeyboardInterrupt, SystemExit)`:

```python
            try:
                raw = input_coro.result()
            except asyncio.CancelledError:
                # Input was cancelled by signal handler — treat as shutdown
                self._abort_input()
                return None
            except EOFError:
                self._abort_input()
                return None
            except (KeyboardInterrupt, SystemExit):
                # Task machinery may re-raise these through the event loop's
                # callback machinery even though we just handled KeyboardInterrupt
                # above. This catches the case where the exception propagated
                # out of the Task before our except clause could catch it.
                self._abort_input()
                return None
```

This removes the separate `except KeyboardInterrupt:` clause and replaces it with a combined `(KeyboardInterrupt, SystemExit)` clause that catches the exception regardless of whether it came from the Task machinery or directly from `result()`.

### Details

The key insight is that CPython's Task machinery treats `(KeyboardInterrupt, SystemExit)` specially: when a Task's own coroutine step raises one of these exceptions, the machinery re-raises it through the event loop's callback machinery. This means the exception may propagate out of the Task before the `except KeyboardInterrupt:` clause at line 154 can catch it.

By replacing the separate `except KeyboardInterrupt:` clause with a combined `(KeyboardInterrupt, SystemExit)` clause, we ensure that the exception is caught regardless of how it was propagated.

## Compatibility considerations

- The `else` branch (line 157-162) already handles `KeyboardInterrupt` via `(EOFError, KeyboardInterrupt)`, so no compatibility issues there.
- The fix only affects the `shutdown_event is not None` branch, which is the buggy branch.
- No public API changes.

## Security considerations

- `SystemExit` is included alongside `KeyboardInterrupt` because CPython's Task machinery treats both specially. Catching `SystemExit` here is safe because it only occurs in the context of input reading, not application exit.
- The fix does not introduce any new security risks.

## Rollback considerations

- Simple revert: restore the original `except KeyboardInterrupt:` clause and remove the `(KeyboardInterrupt, SystemExit)` clause.
- No data loss risk.

## Validation plan

1. Run the existing test suite: `uv run pytest tests/agent/test_repl.py -q -p no:randomly`
2. Verify that `test_keyboard_interrupt_breaks_loop` passes without an uncaught `KeyboardInterrupt`.
3. Verify that the `else` branch still works correctly (existing tests should cover this).

## Completion criteria

- `test_keyboard_interrupt_breaks_loop` passes without raising an uncaught `KeyboardInterrupt`.
- All existing tests in `tests/agent/test_repl.py` continue to pass.
- The `else` branch (no `shutdown_event`) continues to work correctly.

## Out of scope

- Modifying the `else` branch (it already works correctly).
- Adding new tests beyond verifying the existing `test_keyboard_interrupt_breaks_loop` passes.
- Modifying any other files.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Fix `_read_input()`'s `shutdown_event is not None` branch so KeyboardInterrupt is caught | Pending | — | — | |
| 2 | Confirm else branch still works | Pending | — | — | |
| 3 | Run validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-REPL001B-1, REQ-REPL001B-2
- **Source issue**: issues/20260907-140047_repl001_keyboard_interrupt_not_caught_with_shutdown_event.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260908-071725_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260908-231011
- **Related target files**: scripts/agent/repl_input_loop.py
