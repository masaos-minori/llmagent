## Goal
Bound the best-effort round completion in `execute_all_tool_calls` so it neither extends the
shutdown window during a cancellation nor risks replacing the original unwinding exception
with a second `BaseException` raised while completing a cancelled round.

## Priority
Low

## Scope
- **In-Scope**: Guard the `finish()` call in the `except BaseException` branch of
  `execute_all_tool_calls` so completion is skipped (or time-bounded) when the current task
  is cancelled, while preserving the final bare `raise` and best-effort completion for a
  genuine mid-round failure. Add unit tests for both the cancelled and non-cancellation paths.
- **Out-of-Scope**: How cancelled tool-call state rows are cleaned up (stale-pending
  detection), the per-call `Exception`-to-error-row conversion in `_recorded_call`, DAG
  scheduling, `complete_round` internals, and the `CancelledError` propagation contract
  (AC-5).
- **Dependencies**: N/A: none.

## Background
`tool_runner.py::execute_all_tool_calls` wraps DAG execution in `except BaseException:` and
calls `await finish(ToolCallStopReason.ROUND_NOT_COMPLETED)` — which runs `complete_round`
(appends tool results to history and persists them) — before re-raising. This is intentional
best-effort persistence of whatever already ran during a round that did not complete (e.g. an
`asyncio.CancelledError`).

## Problem
Two related concerns:
- During cancellation, awaiting `finish()` performs additional DB/history writes before the
  exception propagates, extending the time before the process can honor a shutdown signal.
- If `finish()` raises a second `BaseException` (e.g. another `CancelledError`), the inner
  `except Exception` guard does not catch it (in Python 3.11+ `CancelledError` is a
  `BaseException`, not an `Exception`); it propagates out of the handler and replaces the
  original exception in the chain. Both are cancellation-related, so the observable outcome
  (turn aborted) is unchanged, but the surfaced exception is no longer the one that started
  the unwind.

## Reason for Change
The current behavior is defensible (best-effort persistence), but a graceful shutdown that
must be fast pays the full round-completion cost, and the exception-replacement edge case
makes debugging the true origin harder. Non-blocking; the fix is optional and gated.

## Implementation Intent
Distinguish cancellation from a genuine failure by the exception being handled, and skip
best-effort completion only for cancellation. Add an `except asyncio.CancelledError: raise`
clause BEFORE the existing `except BaseException:` clause in `execute_all_tool_calls`, so a
cancellation re-raises immediately without awaiting `finish()`, while any other
`BaseException` still runs best-effort completion:

    except asyncio.CancelledError:
        raise
    except BaseException:
        try:
            await finish(ToolCallStopReason.ROUND_NOT_COMPLETED)
        except Exception:  # noqa: BLE001 — completion must never replace the round's own exception
            logger.exception("tool round completion failed")
        raise

This preserves best-effort persistence for a genuine mid-round failure while skipping the
write when the task is being cancelled. Preserve the final bare `raise` so the original
unwinding exception still propagates. Do not change the per-call `Exception`-to-error-row
conversion or the `CancelledError` propagation contract (AC-5).

Note: the originally proposed `if not asyncio.current_task().cancelled():` guard was
rejected during adversarial verification — `Task.cancelled()` is only `True` once the
`CancelledError` has propagated out of the coroutine, so inside the internal `except
BaseException` handler it is still `False` and the guard would run `finish()` even during a
cancellation (a no-op for the goal). Exception-type branching is the mechanism that
actually distinguishes the two cases.

## Requirements
- `REQ-001`: On a genuine mid-round failure (not a cancellation), the round is still
  completed best-effort (`REQ-001` via AC-1).
- `REQ-002`: On cancellation (a `CancelledError` reaches the handler), `finish()` is
  skipped and the original `CancelledError` propagates unchanged
  (`REQ-002` via AC-2).
- `REQ-003`: The final bare `raise` still re-raises the original unwinding exception after
  the guarded completion; AC-5 (a `CancelledError`/`BaseException` propagates out of
  `execute_all_tool_calls`) is preserved.
- `REQ-004`: The per-call `Exception`-to-error-row conversion in `_recorded_call` and the
  `CancelledError` propagation contract are unchanged.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/agent/tool_runner.py` | Modify | In `execute_all_tool_calls`, add `except asyncio.CancelledError: raise` BEFORE the existing `except BaseException` branch (line 550-555) so a cancellation re-raises immediately without awaiting `finish()`; any other `BaseException` still runs `await finish(ToolCallStopReason.ROUND_NOT_COMPLETED)`; keep the final bare `raise` (line 555). Predicate is exception type, NOT `asyncio.current_task().cancelled()` (it is `False` inside the handler during an in-flight cancellation). | REQ-001, REQ-002, REQ-003 | Observed: `except BaseException` at line 550, `try: await finish(...)` / `except Exception` at lines 551-554 (does not catch `BaseException`), bare `raise` at line 555; `asyncio` imported at line 14 (`checked in Step 2/3`) | `tests/agent/test_tool_runner.py` | Verified |
| `tests/agent/test_tool_runner.py` | Modify | Add a test asserting a round interrupted by `CancelledError` skips/bounds `finish()` and re-raises the same exception type; assert a round interrupted by a plain `Exception` still attempts best-effort completion. | REQ-002, REQ-003, REQ-004 | Existing `execute_all_tool_calls` tests exercise the completion path (`checked in Step 3`) | `tests/agent/test_tool_runner.py` | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file
  group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT
  appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as
  its own row when it requires modification — do not fold it into the row for the
  source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be
  `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/agent/tool_round_completion.py` | Defines `complete_round` (the work `finish()` runs); must understand exactly which history/persistence writes are skipped on cancellation to confirm the guard achieves the goal. | `scripts/agent/tool_runner.py` / REQ-002 |
| `scripts/agent/llm_turn_runner.py` | Sole production caller of `execute_all_tool_calls` (line 160); confirm it relies only on the AC-5 propagation contract and gains nothing from completion during a cancellation. | REQ-003, REQ-004 |

## Acceptance Criteria
- On a real mid-round failure (not a cancellation), the round is still completed
  best-effort (`REQ-001`, AC-1).
- On cancellation (a `CancelledError` reaches the handler), `finish()` is skipped and
  the original `CancelledError` propagates unchanged (`REQ-002`, AC-2).
- The final bare `raise` still re-raises the original unwinding exception; AC-5 holds
  (`REQ-003`).
- The per-call `Exception`-to-error-row conversion and `CancelledError` propagation contract
  are unchanged (`REQ-004`).

## Tests
- Unit (`REQ-002`, `REQ-003`): interrupt a round with `asyncio.CancelledError` and assert
  `finish()`/`complete_round` is not awaited (or completes within a bound) and the same
  `CancelledError` type propagates out of `execute_all_tool_calls`.
- Unit (`REQ-001`, `REQ-004`): interrupt a round with a plain `Exception` and assert
  best-effort completion is still attempted; assert `_recorded_call`'s per-call conversion
  is unchanged.
- Static: `uv run ruff format` and `uv run ruff check` on `tool_runner.py`;
  `uv run mypy --no-namespace-packages scripts/agent/tool_runner.py`; existing tool-execution
  tests pass unchanged.

## Documentation Impact
N/A: no doc describes the cancellation/shutdown completion contract; if one does (check the
tool-execution / DAG-scheduling prose per `docs/00_index.md`), note the guarded skip
(drives REQ-002). Not required unless such a doc exists and names the contract.

## Assumptions
- Cancellation is detected by the exception type, not `Task.cancelled()`: a `CancelledError`
  reaching the handler is caught by the dedicated `except asyncio.CancelledError` clause and
  skips completion, while any other `BaseException` falls through to the `except BaseException`
  clause and runs best-effort completion.
- `Task.cancelled()` is NOT used as the predicate: it is only `True` once the `CancelledError`
  has propagated out of the coroutine, so inside the internal handler it is still `False` and
  could not distinguish the two cases (this is why the `current_task().cancelled()` guard was
  rejected in favor of exception-type branching).
- Skipping `finish()` on cancellation does not leave an inconsistent session state that a
  later restore would misread; stale-pending cleanup is explicitly out of scope.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether graceful-shutdown latency from the round-completion writes is ever measurable here (不明) | No profiling of shutdown-time round-completion cost | Non-blocking; the issue gates the change on a confirmed shutdown-time concern; the guard is a pure control-flow narrowing with identical output for non-cancelled rounds | False |
| UNK-02 | Whether `asyncio.wait_for` bounding is preferable to a hard skip on cancellation (both satisfy AC-2) | No shutdown-latency requirement quantified | Implementation-phase choice; hard skip is simpler and fully preserves AC-5; `wait_for` adds a timeout parameter but interacts with in-flight cancellation | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/agent/tool_runner.py` | Modify | Low (control flow inside the `except BaseException` handler; single production caller `llm_turn_runner.py:160`, AC-5 preserved) | 14 | N/A | not applicable (rsynced) |
| `tests/agent/test_tool_runner.py` | Modify | Low (adds cancellation-path assertions) | N/A | N/A | not applicable (rsynced) |

## Design
Path A (single file, no interface change). The change is confined to the control flow of
`execute_all_tool_calls`'s `except BaseException` handler (`tool_runner.py:550-555`); the
public entry-point contract (return value, the AC-5 `BaseException` propagation) is not
touched.

Responsibility and control flow. The handler currently unconditionally runs
`await finish(ToolCallStopReason.ROUND_NOT_COMPLETED)` (best-effort `complete_round`) before
the bare `raise`. The design narrows this by handling cancellation separately, so completion
is skipped only for a `CancelledError`:

    except asyncio.CancelledError:
        raise
    except BaseException:
        try:
            await finish(ToolCallStopReason.ROUND_NOT_COMPLETED)
        except Exception:  # noqa: BLE001 — unchanged: completion must never replace the round's own exception
            logger.exception("tool round completion failed")
        raise

Rationale for each element:
- The dedicated `except asyncio.CancelledError: raise` clause (placed BEFORE `except
  BaseException`, which also matches `CancelledError`) catches a cancellation first and
  re-raises immediately without awaiting `finish()`, shrinking the shutdown window and
  avoiding a second `CancelledError` escaping the `except Exception` guard. Any other
  `BaseException` falls through to the `except BaseException` clause, where best-effort
  completion still runs (preserving persistence for a genuine mid-round failure).
- Exception-type branching is used instead of `asyncio.current_task().cancelled()` because
  `Task.cancelled()` is only `True` once the `CancelledError` has propagated out of the
  coroutine; inside the internal handler it is still `False`, so a `cancelled()` guard would
  run `finish()` even during a cancellation and fail to achieve the goal.
- The final bare `raise` is kept verbatim, so the original unwinding exception propagates
  unchanged and AC-5 holds regardless of the branch taken.
- The existing `except Exception` guard around `finish()` is left intact; it still contains
  ordinary completion failures and still does not (and must not) catch a second
  `BaseException`.

Alternatives considered:
- Bound `finish()` with `asyncio.wait_for(finish(...), timeout=...)` instead of a hard skip.
  Both satisfy AC-2; the hard skip is simpler, needs no timeout tuning, and cannot itself be
  interrupted mid-write by the in-flight cancellation, so it is recommended. `wait_for` is
  the fallback if a bounded partial completion is later deemed desirable.
- Completing the round unconditionally (the current behavior). Rejected only as the thing
  being changed; retained as the non-cancelled branch.

Compatibility: no caller of `execute_all_tool_calls` (`llm_turn_runner.py:160`) observes any
behavior change except the narrowed completion window during cancellation; AC-5 is preserved,
so the propagation contract tests are unaffected.

## Implementation steps
Each step description MUST cite the exact file path(s) it touches by referencing rows
of `Implementation Target Files` above — do not restate file-level detail
independently of that frozen table. A step is a top-level numbered item (a Phase); its
checklist items are sub-tasks, and the Execution Status table has one row per step.
Declare a release unit (see `### Release units` below) when a phase breaks existing callers or
tests until another phase lands (for example a `NOT NULL` column added before its write path):
one line per unit, `**Unit**: {name} | **Phases**: {N, N} | **Reason**: {why the members cannot be
validated alone}`. Phases that land together in one commit cannot be validated alone: declare them
as a unit; `N/A` is only for a Plan whose every phase passes validation alone.

1. **Phase 1: Skip round completion on cancellation (REQ-002, REQ-003; `scripts/agent/tool_runner.py`)**
   - [ ] In `execute_all_tool_calls`, add `except asyncio.CancelledError: raise` BEFORE the existing `except BaseException:` handler so a cancellation re-raises immediately without awaiting `finish()` (skip best-effort completion); any other `BaseException` still runs `finish(ToolCallStopReason.ROUND_NOT_COMPLETED)`. Do NOT use `asyncio.current_task().cancelled()` as the predicate (it is `False` inside the handler during an in-flight cancellation and cannot distinguish the two cases).
   - [ ] Keep the surrounding `try:` / `except Exception` guard and the final bare `raise` unchanged so the original unwinding exception still propagates (AC-5).
2. **Phase 2: Tests for cancelled and non-cancellation paths (REQ-001..REQ-004; `tests/agent/test_tool_runner.py`)**
   - [ ] Add a test interrupting a round with `asyncio.CancelledError`: assert `complete_round`/`finish` is not awaited and the same `CancelledError` type propagates out of `execute_all_tool_calls`.
   - [ ] Add a test interrupting a round with a plain `Exception`: assert best-effort completion is still attempted and `_recorded_call`'s per-call conversion is unchanged.
   - [ ] Update the two existing cancellation tests that assert synthesized rows written during a cancelled round (`test_call_in_flight_at_cancellation_gets_the_outcome_unknown_hint`, `test_cancellation_before_any_dispatch_answers_all_as_not_executed`): under this plan completion is skipped on cancellation, so no 'not executed'/'outcome unknown' row is written — assert completion was skipped and the `CancelledError` propagated instead of asserting saved synthesized text.
3. **Phase 3: Deployment & Verification (REQ-001..REQ-004; `scripts/agent/tool_runner.py`, `tests/agent/test_tool_runner.py`)**
   - [ ] Run `uv run ruff format` and `uv run ruff check` on `scripts/agent/tool_runner.py`.
   - [ ] Run `uv run mypy --no-namespace-packages scripts/agent/tool_runner.py`.
   - [ ] Run `uv run pytest tests/agent/test_tool_runner.py` and confirm existing tool-execution tests pass unchanged.

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/tool_runner.py` | Format + lint | `uv run ruff format --check scripts/agent/tool_runner.py` && `uv run ruff check scripts/agent/tool_runner.py` | Pass (no diff, no lint errors) |
| `scripts/agent/tool_runner.py` | Type check | `uv run mypy --no-namespace-packages scripts/agent/tool_runner.py` | No issues |
| `tests/agent/test_tool_runner.py` | Unit (cancellation + non-cancellation paths) | `uv run pytest tests/agent/test_tool_runner.py` | New assertions pass; existing tool-execution tests pass unchanged |

## Risks
- **Risk**: High 30-day churn on `tool_runner.py` (14 commits) means the surrounding turn
  path may have drifted during implementation, so a rebase may meet conflict. → **Mitigation**:
  the change is a single guarded line inside one handler; the existing cancellation and
  non-cancellation tests pin the behavior, and the edit targets a stable region.
- **Risk**: Skipping `finish()` on cancellation could leave tool-call state rows pending that
  a later restore would treat as stale. → **Mitigation**: stale-pending cleanup is explicitly
  out of scope and already handles pending rows; skipping completion does not create a new
  inconsistent state, only omits the best-effort write that a genuine shutdown would skip
  anyway.
- **Risk**: `asyncio.current_task()` returns `None` outside a running task. → **Mitigation**:
  `execute_all_tool_calls` always runs inside the event loop's current task, so
  `current_task()` is non-None; if defensive coding is desired, guard with
  `(task := asyncio.current_task()) is not None and not task.cancelled()`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Skip `finish()` on cancellation in `execute_all_tool_calls` (exception-type branch) (`scripts/agent/tool_runner.py`, REQ-002, REQ-003) | Completed | 20261118-162059 | 20261118-162059 |  |
| 2 | Cancelled/non-cancellation unit tests (`tests/agent/test_tool_runner.py`, REQ-001..REQ-004) | Completed | 20261118-162059 | 20261118-162059 |  |
| 3 | Format/lint/type-check and run tool-execution tests | Completed | 20261118-162059 | 20261118-162059 |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261118-141420_toolrun001_round-completion-cancellation-window.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261118-144453
- **Related target files**: scripts/agent/tool_runner.py, tests/agent/test_tool_runner.py

### Requirement Traceability
| Requirement ID | Source Issue Section or Evidence | Target File | Implementation Step | Acceptance Criterion | Test / Validation Item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Problem / Reason for Change / AC-1 | `scripts/agent/tool_runner.py` | Step 1 | genuine mid-round failure still completes round best-effort | plain-`Exception` interrupt test; existing completion tests | Confirmed by repository evidence |
| REQ-002 | Problem / Required Changes / AC-2 | `scripts/agent/tool_runner.py` | Step 1 | cancellation skips/bounds `finish()`; original `CancelledError` propagates | `asyncio.CancelledError` interrupt test | Confirmed by repository evidence |
| REQ-003 | Constraints / AC-5 | `scripts/agent/tool_runner.py` | Step 1 | final bare `raise` re-raises original unwinding exception; AC-5 holds | propagation-contract test | Confirmed by repository evidence |
| REQ-004 | Constraints / AC-4 | `scripts/agent/tool_runner.py` | Step 2 | per-call `Exception`-to-error-row conversion unchanged | `_recorded_call` behavior test | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261118-160208 -->