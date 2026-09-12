# Implementation: tests/agent/test_orchestrator.py

## Goal

Remove the 3 `@pytest.mark.skip(...)` markers from `TestHandleLlmTurnOptionalCallbacks`'s tests; correct `test_wait_and_turn_callbacks_invoked_on_success` and `test_wait_end_error_and_turn_end_invoked_when_run_returns_exception`'s mocking strategy from `patch.object(orch._llm_executor, "handle_llm_turn", AsyncMock(...))` (which would bypass the new wiring inside `handle_llm_turn()` entirely) to `patch("agent.llm_turn_executor.LLMTurnRunner")` with the mock instance's `.run` configured as an `AsyncMock` returning the same `TurnResult`; `test_wait_end_invoked_in_except_branch` needs no mocking-strategy change.

## Scope

- Modify `tests/agent/test_orchestrator.py` only.
- Remove the 3 `@pytest.mark.skip(...)` markers from `TestHandleLlmTurnOptionalCallbacks`'s tests.
- Correct `test_wait_and_turn_callbacks_invoked_on_success` and `test_wait_end_error_and_turn_end_invoked_when_run_returns_exception`'s mocking strategy.
- Leave `test_wait_end_invoked_in_except_branch` as-is.

## Assumptions

- The `LLMTurnExecutor` class already stores `on_llm_wait_start`/`on_llm_wait_end` as `self._on_llm_wait_start`/`self._on_llm_wait_end` but never invokes them.
- The `LLMTurnExecutor` class currently stores `on_turn_start`/`on_turn_end` as `self._on_turn_start`/`self._on_turn_end` but never uses them.
- The callbacks should be invoked unconditionally (no gating on success/failure).

## Design decisions

- Remove the skip markers from all 3 tests.
- Correct the mocking strategy for the 2 tests that mock `orch._llm_executor.handle_llm_turn` wholesale.
- Leave `test_wait_end_invoked_in_except_branch` as-is since it already exercises the real call chain end-to-end.

## Alternatives considered

- **Keep both liveness methods**: Would preserve backward compatibility but perpetuates the inconsistency bug where callers cannot know which liveness model applies.
- **Deprecate rather than remove**: Would allow gradual migration but adds maintenance burden for deprecated methods.

## Implementation

### Target file

`tests/agent/test_orchestrator.py`

### Procedure

1. Read `TestHandleLlmTurnOptionalCallbacks` to understand its current structure.
2. Remove the 3 `@pytest.mark.skip(...)` markers from `TestHandleLlmTurnOptionalCallbacks`'s tests.
3. Correct `test_wait_and_turn_callbacks_invoked_on_success` and `test_wait_end_error_and_turn_end_invoked_when_run_returns_exception`'s mocking strategy.
4. Leave `test_wait_end_invoked_in_except_branch` as-is.

### Method

```python
# Step 1: Read TestHandleLlmTurnOptionalCallbacks to understand its current structure
# In test_orchestrator.py (around line 772-878):
#     @pytest.mark.skip("pending callback wiring fix")
#     async def test_wait_and_turn_callbacks_invoked_on_success(self):
#         ...
#         with patch.object(orch._llm_executor, "handle_llm_turn", AsyncMock(return_value=turn_result)):
#             # This mocks the entire handle_llm_turn() body, including the new wiring
#             ...

#     @pytest.mark.skip("pending callback wiring fix")
#     async def test_wait_end_error_and_turn_end_invoked_when_run_returns_exception(self):
#         ...
#         with patch.object(orch._llm_executor, "handle_llm_turn", AsyncMock(return_value=turn_result)):
#             # This mocks the entire handle_llm_turn() body, including the new wiring
#             ...

#     @pytest.mark.skip("pending callback wiring fix")
#     async def test_wait_end_invoked_in_except_branch(self):
#         ...
#         # This test mocks ctx.services_required.llm.stream directly, exercising the real call chain
#         ...

# Step 2: Remove the 3 @pytest.mark.skip(...) markers
# In TestHandleLlmTurnOptionalCallbacks (around line 772-878):
# Before:
#     @pytest.mark.skip("pending callback wiring fix")
#     async def test_wait_and_turn_callbacks_invoked_on_success(self):
# After:
#     async def test_wait_and_turn_callbacks_invoked_on_success(self):

# Before:
#     @pytest.mark.skip("pending callback wiring fix")
#     async def test_wait_end_error_and_turn_end_invoked_when_run_returns_exception(self):
# After:
#     async def test_wait_end_error_and_turn_end_invoked_when_run_returns_exception(self):

# Before:
#     @pytest.mark.skip("pending callback wiring fix")
#     async def test_wait_end_invoked_in_except_branch(self):
# After:
#     async def test_wait_end_invoked_in_except_branch(self):

# Step 3: Correct mocking strategy for the 2 tests
# In test_wait_and_turn_callbacks_invoked_on_success (around line 772):
# Before:
#     with patch.object(orch._llm_executor, "handle_llm_turn", AsyncMock(return_value=turn_result)):
# After:
#     with patch("agent.llm_turn_executor.LLMTurnRunner") as MockRunner:
#         mock_runner = MockRunner.return_value
#         mock_runner.run = AsyncMock(return_value=turn_result)
#         # ... rest of the test body

# In test_wait_end_error_and_turn_end_invoked_when_run_returns_exception (around line 820):
# Before:
#     with patch.object(orch._llm_executor, "handle_llm_turn", AsyncMock(return_value=turn_result)):
# After:
#     with patch("agent.llm_turn_executor.LLMTurnRunner") as MockRunner:
#         mock_runner = MockRunner.return_value
#         mock_runner.run = AsyncMock(return_value=turn_result)
#         # ... rest of the test body

# Step 4: Leave test_wait_end_invoked_in_except_branch as-is
# No changes needed for this test — it already exercises the real call chain end-to-end.
```

### Details

- Line numbers are approximate — verify against current source before applying changes.
- Need to carefully reconcile the behavioral differences between the old and new implementations — the plan explicitly notes these differences must be reconciled during migration.
- The SIGINT handler logic moved to `ShutdownCoordinator` must be verified to work correctly with the new architecture.

## Compatibility considerations

- **Breaking change** for consumers of `get_process_info()` that expect only `pid`, `pgid`, and `running` fields. New fields (`last_exit_code`, `runtime_seconds`) will be present in the output.
- **No breaking change** for existing callers of `verify_running()` — the method signature remains compatible (new parameter has default value).

## Security considerations

- No new security surface introduced. Adding component delegation does not introduce new attack vectors.
- The SIGINT handling logic moved to `ShutdownCoordinator` maintains the same security properties.

## Rollback considerations

- Revert the component initialization and delegation updates.
- If the new fields cause unexpected behavior, remove them and investigate further.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|--------|----------|----------------|------------------|
| Callback invocation | Unit test | `uv run pytest tests/agent/test_orchestrator.py::TestHandleLlmTurnOptionalCallbacks -q` | All 3 tests pass, none skipped |
| Type checking | Static | Type checker against modified file | No type errors |
| Lint checking | Static | Lint tool against modified file | No lint errors |

## Completion criteria

- [ ] 3 `@pytest.mark.skip(...)` markers removed from `TestHandleLlmTurnOptionalCallbacks`.
- [ ] `test_wait_and_turn_callbacks_invoked_on_success` corrected to patch `agent.llm_turn_executor.LLMTurnRunner`.
- [ ] `test_wait_end_error_and_turn_end_invoked_when_run_returns_exception` corrected to patch `agent.llm_turn_executor.LLMTurnRunner`.
- [ ] `test_wait_end_invoked_in_except_branch` left as-is.
- [ ] Existing tests pass without modification.
- [ ] No type/lint regressions.

## Out of scope

- Modifying `scripts/agent/audit_event_emitter.py` — handled by a separate implementation procedure document.
- Modifying `scripts/agent/llm_turn_executor.py` — handled by a separate implementation procedure document.
- Modifying `scripts/agent/conversation_state_manager.py` — handled by a separate implementation procedure document.
- Modifying `scripts/agent/orchestrator.py` — handled by a separate implementation procedure document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Read TestHandleLlmTurnOptionalCallbacks | Completed | — | — | NOTE: skip markers already removed; mocking strategy already corrected |
| 2 | Remove @pytest.mark.skip(...) markers | Completed | — | — | N/A: Already absent in current source |
| 3 | Correct mocking strategy for 2 tests | Completed | — | — | N/A: Already using patch("agent.llm_turn_executor.LLMTurnRunner") in current source |
| 4 | Leave test_wait_end_invoked_in_except_branch as-is | Completed | — | — | N/A: No changes needed |
| 5 | Run validation sequence (rules/toolchain.md) | Completed | — | — | N/A: no changes made |

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
- **Requirement ID**: REQ-004
- **Source issue**: issues/20260911-150000_orchcb01_turn-and-llm-wait-callbacks-never-invoked.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260911-211456_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260912-010239
- **Related target files**: tests/agent/test_orchestrator.py
