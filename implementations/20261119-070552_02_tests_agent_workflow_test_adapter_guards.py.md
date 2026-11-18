## Goal

Add an early-exit regression test to `tests/agent/workflow/test_adapter_guards.py` that pins the collapsed `exit_reason` state machine cannot silently drop a task-status write when a fresh exception type is raised after `engine.run` starts (`REQ-005`, Testing Expectations 2 / AC-3).

## Scope
**Release unit**: N/A: not part of a release unit.

## Assumptions

- The test drives `execute_turn` directly with injected mocks, matching the existing pattern in this module (`_adapter_with_engine`, `test_missing_boundary_raises_protocol_error`) — no real store or engine is required.
- The refactor preserves every existing exit-path assertion, so the two existing tests pass unchanged (AC-2).
- The new test asserts the same task-status write the current code produces; it fails on HEAD-style behavior where a post-`engine.run` exception drops the write and passes once the state machine cannot drop it.

## Design decisions

- Follow the existing module convention: construct the adapter with injected `MagicMock`/`AsyncMock` store and engine, and call `await adapter.execute_turn(...)` directly. Make the injected `engine.run` raise a fresh, unhandled exception type after it has performed the terminal status write, so the `finally` block's `_record_exit_status` runs on the resulting `exit_reason`.
- Assert on the store's `update_task_status` call sequence and the returned `(answer, error_kind, is_partial)` tuple — the same two surfaces the existing tests pin — rather than internal strings.

## Alternatives considered

- Raising the exception inside `execute_fn` instead of after `engine.run` starts: covered by the existing `WorkflowHaltError`/`WorkflowStageFailure` guards; the new test specifically targets a *fresh* exception type after `engine.run` begins, which the current six-way `exit_reason` threading is most fragile against.

## Implementation
### Target file
`tests/agent/workflow/test_adapter_guards.py`
### Procedure
Add one regression test that a fresh exception raised after `engine.run` starts still yields the correct task status, then validate the whole adapter suite.
### Method
1. Add `@pytest.mark.asyncio async def test_post_engine_run_exception_still_records_status()` following the existing `_adapter_with_engine` / direct-`execute_turn` pattern.
2. Configure the injected `engine.run` to perform the terminal status write (call `store.update_task_status(task.task_id, <terminal>)`) and then raise a fresh exception type (e.g. a custom `RuntimeError` subclass or `asyncio.TimeoutError` not otherwise handled), so the exception propagates through `execute_turn`'s `finally`.
3. Assert that the task status recorded by the store matches the terminal status the current code writes, and that the returned tuple reflects the failure — pinning that the collapsed state machine cannot drop the write again.
### Details

- Keep the test self-contained: build its own `store`, `task_record` with a `task_id`, and `ctx` via `_make_ctx()` as the existing tests do.
- Do not alter the two existing tests; they must pass unchanged (AC-2).

## Compatibility considerations

N/A: this is a pure test addition; it does not touch production code or the adapter surface.

## Security considerations

N/A: no change to guards, `allowed_tools`, or side-effect semantics.

## Rollback considerations

N/A: revert the commit.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/agent/workflow/test_adapter_guards.py` | Unit: new early-exit regression test passes alongside the two existing guard tests | `uv run pytest tests/agent/workflow/test_adapter_guards.py -v` | All three pass, asserting the same task statuses and returned tuples |

## Completion criteria

- The new regression test passes and fails if the exit-status write is dropped for a post-`engine.run` exception.
- The two existing guard tests in the module pass unchanged (AC-2).
- `uv run ruff format --check` and `uv run ruff check` are clean on the test file.

## Out of Scope

- Any change to `tests/agent/workflow/test_adapter_store_ownership.py` beyond the existing exit-path assertions.
- Changes to production adapter control flow (covered by `scripts/agent/workflow_engine_adapter.py`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the early-exit regression test to `tests/agent/workflow/test_adapter_guards.py` (`tests/agent/workflow/test_adapter_guards.py`, REQ-005) | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-005`
- **Source issue**: `issues/20261118-221314_wfrev001_execute-turn-complexity.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261118-231012_wfrev001_execute-turn-complexity.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-070552
- **Related target files**: `tests/agent/workflow/test_adapter_guards.py`
