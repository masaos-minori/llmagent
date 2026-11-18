## Goal

Cover the new cancellation-skip behavior of `execute_all_tool_calls`: a cancelled round does
not best-effort complete, while a plain-`Exception` round still does. Also update the two
existing cancelled-round tests whose assertions (synthesized rows written during cancellation)
are invalidated by skipping completion on cancellation.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `complete_round` is imported into `scripts/agent/tool_runner.py` (line 45) and called by the
  local `finish` closure, so `patch("agent.tool_runner.complete_round")` intercepts the
  completion call.
- `ctx.turn.persistence_boundary.save_phase_grouped` is called only inside `complete_round`
  (`scripts/agent/tool_round_completion.py:134`), so
  `save_phase_grouped.assert_not_called()` proves completion was skipped.
- A real `task.cancel()` sets the task's cancellation flag; the `CancelledError` is raised at
  the current await point and propagates to the handler.

## Design decisions
- Assert the mechanism directly by patching `complete_round`: on cancellation it must not be
  awaited; on a plain `Exception` it must be awaited once.
- Rewrite the two cancelled-round synthesis tests to assert completion was skipped
  (`save_phase_grouped` not called) plus `CancelledError` propagation, instead of asserting
  synthesized row text.

## Alternatives considered
- Asserting on saved row text (`_saved_text`) for the cancellation path — rejected: with
  completion skipped nothing is written, so there is no synthesized text to assert.

## Implementation
### Target file
`tests/agent/test_tool_runner.py`

### Procedure
1. Add a cancellation-path test to `TestCancellationDispatchState`.
2. Add a plain-`Exception` test to `TestBatchFailureTotality`.
3. Update `test_call_in_flight_at_cancellation_gets_the_outcome_unknown_hint`
   (`TestCancellationDispatchState`).
4. Update `test_cancellation_before_any_dispatch_answers_all_as_not_executed`
   (`TestCancellationDispatchState`).

### Method
Add the two new tests below. Replace the bodies of the two named existing tests with the
updated versions. Keep all other tests unchanged.

New cancellation-path test (add to `TestCancellationDispatchState`):

    @pytest.mark.asyncio
    async def test_cancellation_skips_best_effort_completion(self) -> None:
        ctx = _make_ctx(_cfg(serial_tool_calls=True))
        started = asyncio.Event()
        block = asyncio.Event()

        async def blocking_execute(name: str, args: dict) -> ToolCallResult:
            started.set()
            await block.wait()  # never set: the round is cancelled while here
            return _ok("never-reached")

        ctx.services_required.tools.execute = blocking_execute
        calls = [
            {"id": "c0", "function": {"name": "read_text_file", "arguments": "{}"}},
            {"id": "c1", "function": {"name": "read_text_file", "arguments": "{}"}},
        ]
        with (
            patch("agent.tool_runner.complete_round", new_callable=AsyncMock) as complete_round,
            _approve_all(),
        ):
            task = asyncio.create_task(
                execute_all_tool_calls(ctx, calls, 0, guard=ToolLoopGuard(ctx))
            )
            await started.wait()
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task

        # Completion is skipped on cancellation: complete_round is not awaited.
        complete_round.assert_not_awaited()

New plain-`Exception` test (add to `TestBatchFailureTotality`):

    @pytest.mark.asyncio
    async def test_plain_exception_still_attempts_best_effort_completion(self) -> None:
        ctx = _make_ctx()
        with (
            patch("agent.tool_runner.complete_round", new_callable=AsyncMock) as complete_round,
            patch(
                "agent.tool_approval.run_approval_checks",
                new_callable=AsyncMock,
                side_effect=RuntimeError("approval down"),
            ),
        ):
            with pytest.raises(RuntimeError, match="approval down"):
                await execute_all_tool_calls(
                    ctx, _declared("read_text_file", "list_directory"), 0, guard=ToolLoopGuard(ctx)
                )

        # A non-cancellation BaseException still best-effort completes the round.
        complete_round.assert_awaited_once()

Updated `test_call_in_flight_at_cancellation_gets_the_outcome_unknown_hint`:

    @pytest.mark.asyncio
    async def test_cancellation_skips_completion_no_synthesized_rows(self) -> None:
        ctx = _make_ctx(_cfg(serial_tool_calls=True))
        started = asyncio.Event()
        block = asyncio.Event()

        async def blocking_execute(name: str, args: dict) -> ToolCallResult:
            started.set()
            await block.wait()  # never set: the round is cancelled while here
            return _ok("never-reached")

        ctx.services_required.tools.execute = blocking_execute
        calls = [
            {"id": "c0", "function": {"name": "read_text_file", "arguments": "{}"}},
            {"id": "c1", "function": {"name": "read_text_file", "arguments": "{}"}},
        ]
        task = asyncio.create_task(
            execute_all_tool_calls(ctx, calls, 0, guard=ToolLoopGuard(ctx))
        )
        with _approve_all():
            await started.wait()
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task

        # Completion is skipped on cancellation: nothing is persisted or synthesized.
        ctx.turn.persistence_boundary.save_phase_grouped.assert_not_called()

Updated `test_cancellation_before_any_dispatch_answers_all_as_not_executed`:

    @pytest.mark.asyncio
    async def test_cancellation_before_any_dispatch_skips_completion(self) -> None:
        ctx = _make_ctx(_cfg())
        approval_started = asyncio.Event()
        block = asyncio.Event()

        async def blocking_approval(
            ctx: Any, prepared: list[Any]
        ) -> tuple[list[Any], list[str]]:
            approval_started.set()
            await block.wait()  # cancelled while awaiting approval
            return prepared, []

        calls = [
            {"id": "c0", "function": {"name": "read_text_file", "arguments": "{}"}},
            {"id": "c1", "function": {"name": "read_text_file", "arguments": "{}"}},
        ]
        task = asyncio.create_task(
            execute_all_tool_calls(ctx, calls, 0, guard=ToolLoopGuard(ctx))
        )
        with patch("agent.tool_approval.run_approval_checks", new=blocking_approval):
            await approval_started.wait()
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task

        # No completion runs on cancellation: no rows are persisted or synthesized.
        ctx.turn.persistence_boundary.save_phase_grouped.assert_not_called()

### Details
- `complete_round.assert_not_awaited()` / `save_phase_grouped.assert_not_called()` prove the
  completion was skipped on cancellation.
- `complete_round.assert_awaited_once()` proves best-effort completion still runs for a
  non-cancellation `BaseException`.
- The propagation contract (AC-5) is unchanged: both paths re-raise, so `pytest.raises` still
  holds. Existing `test_cancellation_still_propagates_not_converted` (raises `CancelledError`
  from an execute call) is unaffected and left unchanged.

## Compatibility considerations
The two rewritten tests change their method names and assertions to reflect that completion is
skipped on cancellation. All other tests in the file are untouched.

## Security considerations
N/A: test-only change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_tool_runner.py` — the two new tests pass, the two updated
  tests pass, and the rest of the file passes unchanged.

## Completion criteria
- `test_cancellation_skips_best_effort_completion` (new) passes (complete_round not awaited on
  cancellation, `CancelledError` propagates).
- `test_plain_exception_still_attempts_best_effort_completion` (new) passes (complete_round awaited
  once on a plain `Exception`, original exception propagates).
- The two rewritten cancelled-round tests pass and assert completion was skipped.
- Full `test_tool_runner.py` passes.

## Out of Scope
Tests outside `tests/agent/test_tool_runner.py`; any production caller behavior beyond the
AC-5 propagation contract.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261118-161946 | 20261118-161946 |  |
| 2 | Add/update tests per Validation plan | Completed | 20261118-161946 | 20261118-161946 | add 2 tests, update 2 existing tests |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261118-161946 | 20261118-161946 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261118-161946 | 20261118-161946 | N/A N/A: no doc update required |

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
- **Requirement ID**: `REQ-001` (genuine failure still completes best-effort), `REQ-002`
  (cancellation skips/bounds completion; `CancelledError` propagates), `REQ-003` (bare `raise`
  still propagates; AC-5), `REQ-004` (per-call conversion unchanged)
- **Source issue**: issues/20261118-141420_toolrun001_round-completion-cancellation-window.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-144453_toolrun001_round-completion-cancellation-window.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-160208
- **Related target files**: tests/agent/test_tool_runner.py