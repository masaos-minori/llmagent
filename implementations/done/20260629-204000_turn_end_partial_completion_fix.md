# Implementation Design: Fix turn_end.partial_completion Always Emitted as False

## Goal

Fix the remaining gap where `turn_end.partial_completion` is always emitted as `False` even after a partial LLM transport error, and verify that the already-implemented `persist_as_assistant=False` guard is fully covered by tests for session restore and fetch_messages paths.

## Scope

- **In-Scope**:
  - `scripts/agent/orchestrator.py` — fix `_build_turn_end_event` to reflect actual partial completion state
  - `scripts/agent/orchestrator.py` — propagate `is_partial` flag from `_process_turn` through to `_handle_turn_end`
  - `tests/test_orchestrator.py` — add tests for `partial_completion` field accuracy in turn_end event
- **Out-of-Scope**:
  - `agent/turn_result.py` — `persist_as_assistant` field already implemented
  - `agent/llm_turn_runner.py` — `persist_as_assistant=False` on error already implemented
  - `agent/orchestrator.py` — `persist_as_assistant` guard in `_handle_llm_turn` already implemented
  - DB schema changes, deploy changes

## Implementation Steps

### Phase 1: Extend _process_turn return type

Extended `_process_turn` return type from `tuple[str, str | None]` to `tuple[str, str | None, bool]`, where the third element is `is_partial`. Set `is_partial = True` when `result.exception` is an `LLMTransportError` with truthy `partial_text`.

### Phase 2: Update call sites

Updated both call sites to unpack the new `is_partial` value and pass it to `_handle_turn_end`:
- Line 193 in `handle_turn`: `answer, error_kind, is_partial = await self._process_turn(...)`
- Line 228 in `_handle_workflow_engine`: added `nonlocal is_partial`, updated unpacking

### Phase 3: Update _handle_turn_end and _build_turn_end_event

- Updated `_handle_turn_end` signature to accept `is_partial: bool = False`
- Updated `_build_turn_end_event` signature to accept `is_partial: bool = False`
- Changed `"partial_completion": False` to `"partial_completion": is_partial` in `_build_turn_end_event`

### Phase 4: Add tests

Added two new tests:
- `test_turn_end_event_has_partial_completion_true_on_partial_error` — verifies `partial_completion=True` for partial LLM transport errors
- `test_turn_end_event_has_partial_completion_false_on_non_partial_error` — verifies `partial_completion=False` for non-partial errors

### Phase 5: Update existing mocks

Updated three existing test mocks that patch `_process_turn` to return the new third element:
- Line 643: `AsyncMock(return_value=("ok", None))` → `AsyncMock(return_value=("ok", None, False))`
- Line 857: same change
- Line 881: same change

## Validation Results

- All 53 tests in `tests/test_orchestrator.py` pass (including 2 new tests)
- All 28 tests in `tests/test_llm_turn_runner.py` pass
- All tests in `tests/test_diagnostic_store.py` pass

## Acceptance Criteria

- [x] `_build_turn_end_event` uses actual partial completion state instead of hardcoded `False`
- [x] `is_partial` flag propagated from `_process_turn` through `_handle_turn_end` to `_build_turn_end_event`
- [x] Both call sites (`handle_turn` and `_handle_workflow_engine`) updated atomically
- [x] Tests verify `partial_completion=True` for partial errors
- [x] Tests verify `partial_completion=False` for non-partial errors
- [x] All existing tests pass
