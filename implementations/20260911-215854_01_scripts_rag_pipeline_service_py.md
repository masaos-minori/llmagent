## Goal

Parse `selected_hits` from the RAG service's JSON response in `call_rag_service()` and invoke the existing `_set_fetch_result()` helper with it on both success return paths; retype `set_fetch_result`'s type annotation from `Callable[[str], None]` back to `Callable[[list[dict[str, Any]]], None]`.

## Scope

Modify `scripts/rag/pipeline_service.py`:
- Parse `selected_hits` from the response body in `call_rag_service()` (REQ-001; `scripts/rag/pipeline_service.py`).
- Call the existing `_set_fetch_result()` helper with the raw hit-dict list on both success return paths (REQ-001; `scripts/rag/pipeline_service.py`).
- Change `set_fetch_result`'s type annotation from `Callable[[str], None]` back to `Callable[[list[dict[str, Any]]], None]` (REQ-001; `scripts/rag/pipeline_service.py`).

## Assumptions

- The RAG service's `/v1/call_tool` response for `rag_run_pipeline` already emits `selected_hits` in production — confirmed via server-side Pydantic model (`rag_pipeline_models.py:215`) and its own endpoint test (`test_rag_pipeline_server_endpoints.py:99`).
- Both the empty-`"result"` and non-empty-`"result"` success paths should call `_set_fetch_result()` with `selected_hits` when present.
- When `selected_hits` is absent or empty, `_set_fetch_result()` should not be called (preserving existing behavior where `last_fetch_result` remains unchanged).

## Design decisions

1. **Parse `selected_hits` in `call_rag_service()`**: After parsing the JSON response body at line 134, add `body.get("selected_hits")` before the existing `result_raw` extraction. Only invoke `_set_fetch_result()` when `selected_hits` is truthy (non-empty list).
2. **Invoke `_set_fetch_result()` on both success paths**: Add the callback invocation after the `None` check (line 136-137) and after the string validation (line 142), so both success return paths propagate fetch metadata.
3. **Retype the callback signature**: Change `set_fetch_result` parameter type from `Callable[[str], None]` to `Callable[[list[dict[str, Any]]], None]` across all three files (`pipeline_service.py`, `http_augment.py`, `augment.py`) — this is the narrowest change that restores the original contract without affecting other callers.

## Alternatives considered

- Retaining the `str` type annotation and wrapping `selected_hits` in a string: would require additional serialization logic and breaks the documented `TwoStageFetchResult` contract.
- Adding a separate callback for fetch metadata: overkill — the existing `_set_fetch_result()` mechanism already serves this purpose.
- Making `_set_fetch_result()` conditional on `selected_hits` presence inside the callback itself: shifts responsibility away from the caller and makes the contract harder to reason about.

## Implementation
### Target file
`scripts/rag/pipeline_service.py`

### Procedure
Parse `selected_hits` from the response body in `call_rag_service()`; call the existing `_set_fetch_result()` helper with it on both success return paths; retype `set_fetch_result` from `Callable[[str], None]` to `Callable[[list[dict[str, Any]]], None]`.

### Method
1. In `call_rag_service()`, after `body = parse_http_json(resp)` (line 134), extract `selected_hits = body.get("selected_hits")`.
2. Before the first success return path (line 136-137), add: `if selected_hits: _set_fetch_result(set_fetch_result, selected_hits)`.
3. Before the second success return path (line 142), add: `if selected_hits: _set_fetch_result(set_fetch_result, selected_hits)`.
4. Change `set_fetch_result` parameter type annotation from `Callable[[str], None] | None` to `Callable[[list[dict[str, Any]]], None] | None` in the function signature (line 56).
5. Change `_set_fetch_result`'s parameter type from `Callable[[str], None] | None` to `Callable[[list[dict[str, Any]]], None] | None` (line 41).

### Details
```python
# In call_rag_service() (pipeline_service.py):

# After line 134: body = parse_http_json(resp)
selected_hits = body.get("selected_hits")

# Before line 136-137 (first success path):
if selected_hits:
    _set_fetch_result(set_fetch_result, selected_hits)

# Before line 142 (second success path):
if selected_hits:
    _set_fetch_result(set_fetch_result, selected_hits)

# Return statements remain unchanged:
return "", status_code, elapsed_ms   # line 137
return result_raw, status_code, elapsed_ms  # line 142
```

## Compatibility considerations

- Existing deployments that pass a `set_fetch_result` callback expecting a `str` argument will break under the new type annotation — however, repo-wide `rg` confirms no such caller exists outside the 7 test files enumerated in the Plan's Reference Files.
- The callback invocation only happens when `selected_hits` is truthy, preserving existing behavior where `last_fetch_result` is not overwritten by empty responses.

## Security considerations

- No security impact — this change adds parsing of an existing response field (`selected_hits`) that the RAG service already emits.
- The callback receives raw dict data from the RAG service; downstream consumers are responsible for validating its structure.

## Rollback considerations

- If the new callback invocation causes issues (e.g., incorrect metadata propagation), revert the two `_set_fetch_result()` calls while keeping the `selected_hits` parsing.
- The type annotation change can be reverted without affecting functionality if reverted.
- The `selected_hits` parsing can be removed without affecting functionality if reverted.

## Validation plan

- Fetch result metadata test: verify `_set_fetch_result()` is invoked with `selected_hits` on both success paths.
- Empty-hits preservation test: verify `_set_fetch_result()` is NOT invoked when `selected_hits` is absent or empty.
- Type annotation regression test: verify no callers expect a `str` argument to the callback.
- Full regression: verify all existing tests continue passing.

## Completion criteria

- [ ] `selected_hits` is parsed from the RAG service's JSON response in `call_rag_service()` — REQ-001
- [ ] `_set_fetch_result()` is invoked with the raw hit-dict list on both success return paths when `selected_hits` is present — REQ-001
- [ ] `set_fetch_result` type annotation restored to `Callable[[list[dict[str, Any]]], None]` — REQ-001
- [ ] All existing tests continue passing (no regression) — REQ-001

## Out of scope

- `/replay` endpoint's own pagination/snapshot-consistency issue (EB-M04).
- Centralizing the currently-hardcoded operational thresholds into validated configuration — tracked separately in this batch.
- Deciding on separate read connections or connection manager — defer until load-test results justify it.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | |
| 2 | Add or update tests per Validation plan | Completed | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-09-12T08:55:00Z | 2026-09-12T08:56:00Z | ruff format/lint OK, mypy OK, bandit OK, 13 pipeline_service tests + 11 fetch_result tests PASS |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | no docs/00_index.md task-scope mapping for scripts/rag/pipeline_service.py |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20260911-132739_raghits01_http-mode-selected-hits-unparsed.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260911-205352_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260911-215854
- **Related target files**: scripts/rag/pipeline_service.py
