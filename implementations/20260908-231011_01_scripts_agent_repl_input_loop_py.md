## Goal

Fix `_read_input()`'s `shutdown_event is not None` branch so `KeyboardInterrupt` raised during input reading is caught and treated as a graceful end-of-input signal, matching the behavior of the `else` branch.

## Scope

Modify only `scripts/agent/repl_input_loop.py` to prevent `KeyboardInterrupt` from escaping past the `except KeyboardInterrupt:` clause at line 154.

## Assumptions

- **Corrected 2026-09-09, per Step 3a adversarial verification**: CPython's Task
  machinery special-cases `(KeyboardInterrupt, SystemExit)` — when a Task's own
  coroutine step raises one of these, `Task.__step()` calls `super().set_exception(exc)`
  **and then re-raises it immediately**, inside the event loop's own callback-stepping
  code, *before* control ever returns to whatever coroutine is awaiting that Task (e.g.
  via `asyncio.wait(...)`). This was verified two ways: (1) direct inspection of
  `/usr/lib/python3.13/asyncio/tasks.py`'s `Task.__step_run_and_handle_result`, which
  contains `except (KeyboardInterrupt, SystemExit) as exc: super().set_exception(exc);
  raise`; (2) a minimal standalone `asyncio.run()` reproduction (not pytest) mirroring
  this file's exact structure — `current_buggy_structure()` in the reproduction script —
  which showed the `KeyboardInterrupt` escaping `asyncio.run(main())` **entirely, as an
  unretrieved-Task-exception warning surfacing after `main()` had already returned**, not
  as an exception raised at the `input_coro.result()` call site inside `_read_input()`.
- Consequently, **no `except` clause added around `input_coro.result()` at line 146—156,
  no matter how it is structured or which exception types it lists, can reliably catch
  this** — the exception frequently never reaches that call site's frame at all. This
  invalidates this document's original Design decision (see below) and Alternative #2's
  original dismissal.
- The **correct** boundary is inside `_input_task()`'s own coroutine body — catching
  `(KeyboardInterrupt, SystemExit)` there, before the coroutine step completes, means
  `Task.__step()` never observes a raw `(KeyboardInterrupt, SystemExit)` escaping that
  step, so its special-case re-raise branch is never triggered. This was empirically
  confirmed via the same reproduction script's `fix_a_catch_inside_input_task()` and
  `fix_final_sentinel_exception()`: both completed and returned normally with no
  escape, once `KeyboardInterrupt` was caught inside `_input_task()` itself.
- The `else` branch (line 157-162) already handles `KeyboardInterrupt` correctly via
  `(EOFError, KeyboardInterrupt)` — it is not wrapped in a separate `ensure_future()`
  Task, so the exception propagates through the current coroutine's own frame via
  normal Python exception unwinding, not through `Task.__step()`'s special-cased path.
  This asymmetry between the two branches is the actual root cause of the bug, not a
  detail to preserve unexamined.

## Design decisions

- **Corrected 2026-09-09**: Catch `(KeyboardInterrupt, SystemExit)` **inside
  `_input_task()`'s own body** (wrapping only the `await loop.run_in_executor(...)`
  call), and re-raise as a new, module-scoped plain `Exception` subclass,
  `_InputAborted` — a regular `Exception` is not special-cased by `Task.__step()`, so it
  propagates normally to `input_coro.result()` at the existing call site.
- Replace the existing `except KeyboardInterrupt:` clause (line 154-156) with
  `except _InputAborted:` — the old clause is now unreachable dead code once the
  conversion happens inside `_input_task()`, since a raw `KeyboardInterrupt` can no
  longer reach `input_coro.result()` through this path.
- This is still a minimal change scoped to `scripts/agent/repl_input_loop.py`: one new
  private exception class, one `try/except` inside `_input_task()`, and one renamed
  `except` clause.

## Alternatives considered

1. **Replace `input_coro.result()` with `await input_coro`** — Would propagate the
   exception through await machinery instead of `result()`, but CPython still
   special-cases `(KeyboardInterrupt, SystemExit)` the same way regardless of `.result()`
   vs. `await` — not effective, confirmed by the same reproduction mechanism.
2. **Catch the exception inside `_input_task()`** — *(Corrected 2026-09-09: this
   document originally dismissed this option on the mistaken premise that "the exception
   is raised after the Task completes, not during execution." This is factually wrong —
   the traceback shows it raised at the `await loop.run_in_executor(...)` line, inside
   `_input_task()`'s own body, i.e. during its execution. This is in fact the correct,
   empirically-verified fix — see Design decisions above.)*
3. **Use `asyncio.wait_for()` with timeout** — Same issue as alternative 1; the exception
   propagation mechanism is unchanged by adding a timeout.
4. **Cancel the task and retry** — Complex and introduces race conditions; unnecessary
   given the simpler, now-confirmed approach above.
5. **Wrap `input_coro.result()`'s call site in a broader `except` (any combination of
   `KeyboardInterrupt`/`SystemExit`/bare `Exception`)** — *(Corrected 2026-09-09: this
   was this document's original Design decision. Empirically disproven — see
   Assumptions above. Removed as the chosen approach; Alternative #2 replaces it.)*

## Implementation

### Target file

`scripts/agent/repl_input_loop.py`

### Procedure

1. Add a module-level private exception class `_InputAborted(Exception)` near the top
   of the file (alongside `_REPL_RESERVED_COMMANDS`).
2. Wrap `_input_task()`'s body (`return await loop.run_in_executor(None, lambda: input("> "))`)
   in a `try/except (KeyboardInterrupt, SystemExit) as exc:` that raises
   `_InputAborted from exc`.
3. Replace the `except KeyboardInterrupt:` clause at line 154-156 with
   `except _InputAborted:`, keeping the same body (`self._abort_input(); return None`).

### Method

Add near the top of the file, after `_REPL_RESERVED_COMMANDS`:

```python
class _InputAborted(Exception):
    """Internal sentinel: input reading was interrupted by Ctrl-C/SystemExit.

    CPython's Task.__step() re-raises a raw (KeyboardInterrupt, SystemExit) through
    the event loop's own callback machinery instead of storing it as a normal,
    retrievable Task exception — catching it here, inside _input_task()'s own
    coroutine step, and converting it to a plain Exception subclass avoids that
    special-cased escape path entirely.
    """
```

Change `_input_task()` from:

```python
            async def _input_task() -> str:
                """Read one line of user input via executor."""
                return await loop.run_in_executor(None, lambda: input("> "))
```

to:

```python
            async def _input_task() -> str:
                """Read one line of user input via executor."""
                try:
                    return await loop.run_in_executor(None, lambda: input("> "))
                except (KeyboardInterrupt, SystemExit) as exc:
                    raise _InputAborted from exc
```

Change the `input_coro.result()` except clauses from:

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

to:

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
            except _InputAborted:
                self._abort_input()
                return None
```

### Details

CPython's Task machinery treats `(KeyboardInterrupt, SystemExit)` specially: when a
Task's own coroutine step raises one of these, `Task.__step()` re-raises it directly
through the event loop's callback machinery, bypassing any `except` clause an awaiting
caller (like `_read_input()`) might have around `input_coro.result()` — the exception
frequently never reaches that call site at all, instead surfacing later as an
unretrieved-Task-exception warning once the surrounding `async def` has already
returned. Catching `(KeyboardInterrupt, SystemExit)` *inside* `_input_task()`'s own
coroutine step, before it exits, and converting it into a plain `Exception` subclass
(`_InputAborted`) avoids the special case entirely — a regular `Exception` is not
subject to `Task.__step()`'s re-raise branch, so it flows through `input_coro.result()`
exactly like `EOFError` already does today.

## Compatibility considerations

- The `else` branch (line 157-162) already handles `KeyboardInterrupt` via `(EOFError, KeyboardInterrupt)`, so no compatibility issues there.
- The fix only affects the `shutdown_event is not None` branch, which is the buggy branch.
- No public API changes.

## Security considerations

- `SystemExit` is included alongside `KeyboardInterrupt` because CPython's Task machinery treats both specially. Catching `SystemExit` here is safe because it only occurs in the context of input reading, not application exit.
- The fix does not introduce any new security risks.

## Rollback considerations

- Simple revert: remove the `_InputAborted` class, restore `_input_task()`'s body to a
  bare `return await loop.run_in_executor(...)`, and restore the `except
  KeyboardInterrupt:` clause in place of `except _InputAborted:`.
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
| 1 | Fix `_read_input()`'s `shutdown_event is not None` branch so KeyboardInterrupt is caught | Completed | 20260909-105920 | 20260909-122726 | Step 3a adversarial verification found the original Design decision (wrap `input_coro.result()`'s except clauses) empirically does not work — corrected 2026-09-09 to catch inside `_input_task()` instead (new `_InputAborted` sentinel exception); see Assumptions/Design decisions. Verified via a standalone `asyncio.run()` reproduction script before applying to source. |
| 2 | Confirm else branch still works | Completed | 20260909-105920 | 20260909-122726 | Unmodified; `else` branch's existing `(EOFError, KeyboardInterrupt)` handling untouched. |
| 3 | Run validation sequence (`rules/toolchain.md`) | Completed | 20260909-105920 | 20260909-122726 | ruff format/check, mypy: clean. `lint-imports` broken contract (`shared.production_config_validator` -> `agent.*`) and `bandit` B101 assert finding (line ~250) are pre-existing and unrelated to this change — not fixed, out of scope. `tests/agent/test_repl.py` (55 items): 47 passed, 8 failed — all 8 pre-existing/unrelated (banner workflow status, session-diagnostics warning logging, sqlite error message path, sigterm handler, an unrelated timing test); `test_keyboard_interrupt_breaks_loop` now passes. Full suite `uv run pytest tests/ -q` completed cleanly (7154 collected, 590 failed/6545 passed/16 skipped/3 errors) with zero `KeyboardInterrupt` session aborts — first clean completion this session. Diff coverage: 100% (6/6 changed lines). No `docs/00_index.md` task-scope row matches `repl_input_loop.py` — Step 5/6 skipped per that Step's own no-mapping rule. |

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
