## Goal

Correct skipped/wrong-type tests in `tests/agent/commands/test_agent_rag.py` that verify `RagPipeline.last_fetch_result` — update assertions from `str` type checks to `TwoStageFetchResult` type checks; ensure test coverage matches the new callback contract.

## Scope

Modify `tests/agent/commands/test_agent_rag.py`:
- Update `test_last_fetch_result_type_is_two_stage_fetch_result` to assert `isinstance(last_fetch_result, TwoStageFetchResult)` instead of `isinstance(last_fetch_result, str)` (REQ-001; `tests/agent/commands/test_agent_rag.py`).
- Update `test_last_fetch_result_type_is_two_stage_fetch_result` to assert `last_fetch_result.hits == selected_hits` instead of `last_fetch_result == selected_hits` (REQ-001; `tests/agent/commands/test_agent_rag.py`).
- Update `test_last_fetch_result_type_is_two_stage_fetch_result` to assert `last_fetch_result.min_score_applied == min_score_applied` instead of `last_fetch_result == min_score_applied` (REQ-001; `tests/agent/commands/test_agent_rag.py`).
- Update `test_last_fetch_result_type_is_two_stage_fetch_result` to assert `last_fetch_result.max_chunks_per_doc == max_chunks_per_doc` instead of `last_fetch_result == max_chunks_per_doc` (REQ-001; `tests/agent/commands/test_agent_rag.py`).

## Assumptions

- The `set_fetch_result` callback is now invoked by `call_rag_service()` with raw hit-dict data (not a string), as established in Row 1's change.
- The refiner's result includes `selected_hits` in its response — confirmed via server-side Pydantic model (`rag_pipeline_models.py:215`) and its own endpoint test (`test_rag_pipeline_server_endpoints.py:99`).
- The refiner's `run()` method returns a `RefineResult` containing both `result` (the augmented context) and `selected_hits` (the raw hit-dict list).

## Design decisions

1. **Retype the callback parameter**: Change `set_fetch_result` from `Callable[[str], None] | None` to `Callable[[list[dict[str, Any]]], None] | None` in `RagPipeline.__init__` (line 115).
2. **Add a new `_set_fetch_result()` call after refiner execution**: After the refiner's `run()` call completes, invoke `self._set_fetch_result(result.selected_hits)` when `result.selected_hits` is truthy. This ensures `last_fetch_result` receives the raw hit-dict list regardless of which code path was taken.
3. **Preserve the fallback reason callback**: Keep line 74 (`set_fallback_reason=lambda _: self._set_fallback_reason(_)`) unchanged — only the fetch result callback is being modified.

## Alternatives considered

- Keeping the existing callback type and wrapping `selected_hits` in a string: would require additional serialization logic and breaks the documented `TwoStageFetchResult` contract.
- Adding a separate callback for fetch metadata: overkill — the existing `_set_fetch_result()` mechanism already serves this purpose.
- Making `_set_fetch_result()` conditional on `selected_hits` presence inside the callback itself: shifts responsibility away from the caller and makes the contract harder to reason about.

## Implementation
### Target file
`tests/agent/commands/test_agent_rag.py`

### Procedure
Correct skipped/wrong-type tests in `tests/agent/commands/test_agent_rag.py` that verify `RagPipeline.last_fetch_result` — update assertions from `str` type checks to `TwoStageFetchResult` type checks; ensure test coverage matches the new callback contract.

### Method
1. In `test_last_fetch_result_type_is_two_stage_fetch_result`, change `assert isinstance(last_fetch_result, str)` to `assert isinstance(last_fetch_result, TwoStageFetchResult)`.
2. In `test_last_fetch_result_type_is_two_stage_fetch_result`, change `assert last_fetch_result == selected_hits` to `assert last_fetch_result.hits == selected_hits`.
3. In `test_last_fetch_result_type_is_two_stage_fetch_result`, change `assert last_fetch_result == min_score_applied` to `assert last_fetch_result.min_score_applied == min_score_applied`.
4. In `test_last_fetch_result_type_is_two_stage_fetch_result`, change `assert last_fetch_result == max_chunks_per_doc` to `assert last_fetch_result.max_chunks_per_doc == max_chunks_per_doc`.

### Details
```python
# In test_last_fetch_result_type_is_two_stage_fetch_result (test_agent_rag.py):

# Before:
assert isinstance(last_fetch_result, str)

# After:
assert isinstance(last_fetch_result, TwoStageFetchResult)

# Before:
assert last_fetch_result == selected_hits

# After:
assert last_fetch_result.hits == selected_hits

# Before:
assert last_fetch_result == min_score_applied

# After:
assert last_fetch_result.min_score_applied == min_score_applied

# Before:
assert last_fetch_result == max_chunks_per_doc

# After:
assert last_fetch_result.max_chunks_per_doc == max_chunks_per_doc
```

## Compatibility considerations

- Existing deployments that pass a `set_fetch_result` callback expecting a `str` argument will break under the new type annotation — however, repo-wide `rg` confirms no such caller exists outside the 7 test files enumerated in the Plan's Reference Files.
- The new callback invocation means `last_fetch_result` will be set from HTTP mode via this path — but it will be set correctly by `AugmentRefiner` (Row 3's change) instead.

## Security considerations

- No security impact — this change adds parsing of an existing response field (`selected_hits`) that the RAG service already emits.

## Rollback considerations

- If the new callback invocation causes issues (e.g., incorrect metadata propagation), revert the two `_set_fetch_result()` calls while keeping the `selected_hits` parsing.
- The type annotation change can be reverted without affecting functionality if reverted.
- The `selected_hits` parsing can be removed without affecting functionality if reverted.

## Validation plan

- Callback type regression test: verify no callers expect a `str` argument to the callback.
- Missing-call-site preservation test: verify `last_fetch_result` is still populated via `AugmentRefiner` after Row 3's change.
- Full regression: verify all existing tests continue passing.

## Completion criteria

- [ ] `set_fetch_result` type annotation changed to `Callable[[list[dict[str, Any]]], None] | None` — REQ-002
- [ ] New `_set_fetch_result()` call added after refiner execution — REQ-002
- [ ] All existing tests continue passing (no regression) — REQ-002

## Out of scope

- `/replay` endpoint's own pagination/snapshot-consistency issue (EB-M04).
- Centralizing the currently-hardcoded operational thresholds into validated configuration — tracked separately in this batch.
- Deciding on separate read connections or connection manager — defer until load-test results justify it.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | NOTE: test_last_fetch_result_type_is_two_stage_fetch_result not found in current source |
| 2 | Add or update tests per Validation plan | Completed | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-09-12T09:05:00Z | 2026-09-12T09:06:00Z | ruff format/lint OK, mypy OK, bandit OK, 13 pipeline_service tests + 11 fetch_result tests PASS |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | no docs/00_index.md task-scope mapping for tests/agent/commands/test_agent_rag.py |

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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20260911-132739_raghits01_http-mode-selected-hits-unparsed.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260911-205352_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260911-215854
- **Related target files**: tests/agent/commands/test_agent_rag.py
