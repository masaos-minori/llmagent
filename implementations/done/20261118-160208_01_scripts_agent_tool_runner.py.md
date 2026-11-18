## Goal

Skip the best-effort round completion in `execute_all_tool_calls` when the current task is
being cancelled, so a graceful shutdown is not slowed by the round-completion writes and a
second `CancelledError` cannot replace the original unwinding exception.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Cancellation is detected by the exception being handled, not by `Task.cancelled()`: a
  `CancelledError` reaching the handler is caught by a dedicated `except asyncio.CancelledError`
  clause and skips completion; any other `BaseException` runs best-effort completion.
- `asyncio` is already imported at the top of `scripts/agent/tool_runner.py` (line 14), so
  `asyncio.CancelledError` is available without a new import.
- `Task.cancelled()` is deliberately NOT used as the predicate: it is only `True` once the
  `CancelledError` has propagated out of the coroutine, so inside the internal `except
  BaseException` handler it is still `False` and could not distinguish cancellation from a
  genuine failure (verified empirically during adversarial verification).
- `execute_all_tool_calls` has a single production caller (`llm_turn_runner.py:160`), which
  relies only on the AC-5 propagation contract.

## Design decisions
- Add `except asyncio.CancelledError: raise` BEFORE the existing `except BaseException:` clause
  in `execute_all_tool_calls`, so a cancellation re-raises immediately without awaiting
  `finish()`, while any other `BaseException` still runs `await finish(ToolCallStopReason.ROUND_NOT_COMPLETED)`.
- Keep the surrounding `try:` / `except Exception` guard and the final bare `raise` verbatim.

## Alternatives considered
- `if not asyncio.current_task().cancelled(): await finish(...)` guard — rejected: proven a
  no-op for the in-flight cancellation case (see Assumptions).
- Bound `finish()` with `asyncio.wait_for(finish(...), timeout=...)` — both satisfy AC-2, but
  the hard skip is simpler, needs no timeout tuning, and cannot itself be interrupted mid-write
  by the in-flight cancellation.

## Implementation
### Target file
`scripts/agent/tool_runner.py`

### Procedure
1. Locate the `except BaseException:` handler in `execute_all_tool_calls` (currently line 550).
2. Insert an `except asyncio.CancelledError: raise` clause immediately BEFORE that handler.
3. Leave the rest of the handler (`try:` / `await finish(...)` / `except Exception` / bare
   `raise`) unchanged.

### Method
The handler currently reads:

    except BaseException:
        try:
            await finish(ToolCallStopReason.ROUND_NOT_COMPLETED)
        except Exception:  # noqa: BLE001 — completion must never replace the round's own exception
            logger.exception("tool round completion failed")
        raise

Replace it with:

    except asyncio.CancelledError:
        raise
    except BaseException:
        try:
            await finish(ToolCallStopReason.ROUND_NOT_COMPLETED)
        except Exception:  # noqa: BLE001 — completion must never replace the round's own exception
            logger.exception("tool round completion failed")
        raise

`asyncio.CancelledError` is a `BaseException`, so the dedicated clause MUST come first; otherwise
it would be shadowed by `except BaseException`.

### Details
- On cancellation: the `CancelledError` is caught by the new clause and re-raised immediately;
  `finish()` (and thus `complete_round`) is not awaited, so no history/persistence writes run
  and no second `CancelledError` can escape the `except Exception` guard.
- On a genuine mid-round failure (any other `BaseException`): control falls through to the
  existing `except BaseException` clause, so best-effort completion still runs.
- The final bare `raise` still re-raises whatever unwinds the round, so AC-5 holds.

## Compatibility considerations
The only behavior change is that a cancelled round no longer runs best-effort completion. A
non-cancelled round completes exactly as before. AC-5 (`CancelledError`/`BaseException`
propagates out of `execute_all_tool_calls`) is preserved, so propagation-contract tests are
unaffected. Existing tests that assert synthesized rows written DURING a cancelled round
(`test_call_in_flight_at_cancellation_gets_the_outcome_unknown_hint`,
`test_cancellation_before_any_dispatch_answers_all_as_not_executed` in
`tests/agent/test_tool_runner.py`) must be updated — see the companion test file.

## Security considerations
N/A: control-flow change only; no new data access or privilege path.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- Format + lint: `uv run ruff format --check scripts/agent/tool_runner.py` &&
  `uv run ruff check scripts/agent/tool_runner.py`.
- Type check: `uv run mypy --no-namespace-packages scripts/agent/tool_runner.py`.
- Unit: `uv run pytest tests/agent/test_tool_runner.py` — new cancellation/non-cancellation
  assertions pass; existing propagation-contract tests pass unchanged; the two cancelled-round
  synthesis tests updated per the companion test file.

## Completion criteria
- `tool_runner.py` has `except asyncio.CancelledError: raise` before `except BaseException`.
- A round interrupted by `asyncio.CancelledError` re-raises the same `CancelledError` type and
  does not await `complete_round`/`finish`.
- A round interrupted by a plain `Exception` still attempts best-effort completion and re-raises
  the original exception.
- `ruff format --check`, `ruff check`, and `mypy` are clean; `test_tool_runner.py` passes.

## Out of Scope
`complete_round` internals, the per-call `Exception`-to-error-row conversion in
`_recorded_call`, DAG scheduling, stale-pending cleanup of cancelled tool-call state rows, and
the `CancelledError` propagation contract (AC-5).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `except asyncio.CancelledError: raise` before `except BaseException` in `execute_all_tool_calls` (`scripts/agent/tool_runner.py`, REQ-002, REQ-003) | Completed | 20261118-161946 | 20261118-161946 |  |
| 2 | Add/update tests per Validation plan | Completed | 20261118-161946 | 20261118-161946 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261118-161946 | 20261118-161946 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261118-161946 | 20261118-161946 | N/A: no doc names the cancellation completion contract N/A: no doc names the cancellation completion contract |

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
- **Requirement ID**: `REQ-002` (skip/bound completion on cancellation), `REQ-003` (bare `raise` still propagates; AC-5)
- **Source issue**: issues/20261118-141420_toolrun001_round-completion-cancellation-window.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-144453_toolrun001_round-completion-cancellation-window.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-160208
- **Related target files**: scripts/agent/tool_runner.py