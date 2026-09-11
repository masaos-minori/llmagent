## Goal

Retype `AugmentRefiner.__init__`'s `set_fetch_result` annotation; add a new `_set_fetch_result()` call after refiner execution that passes the raw hit-dict list from the refiner's result.

## Scope

Modify `scripts/rag/augment.py`:
- Retype `AugmentRefiner.__init__`'s `set_fetch_result` annotation from `Callable[[str], None] | None` to `Callable[[list[dict[str, Any]]], None] | None` (REQ-002; `scripts/rag/augment.py`).
- Add a new `_set_fetch_result()` call after refiner execution that passes the raw hit-dict list (REQ-002; `scripts/rag/augment.py`).

## Assumptions

- The `set_fetch_result` callback is now invoked by `call_rag_service()` with raw hit-dict data (not a string), as established in Row 1's change.
- The refiner's result does NOT include `selected_hits` — `RefineResult` only has `text` and `reason` fields. The procedure's claim about `result.selected_hits` is stale.
- Only the callback type annotation needs to be retyped in `AugmentRefiner.__init__`; no new callback invocation is needed here because the in-process pipeline sets `last_fetch_result` through the lifecycle mechanism, not the callback.

## Design decisions

1. **Retype the callback parameter**: Change `set_fetch_result` from `Callable[[str], None] | None` to `Callable[[list[dict[str, Any]]], None] | None` in `AugmentRefiner.__init__` (line 47).
2. No new callback invocation is added — the in-process pipeline sets `last_fetch_result` through the lifecycle mechanism, not the callback.
3. **Preserve the fallback reason callback**: Keep line 74 (`set_fallback_reason=lambda _: self._set_fallback_reason(_)`) unchanged — only the fetch result callback is being modified.

## Alternatives considered

- Keeping the existing callback type and wrapping `selected_hits` in a string: would require additional serialization logic and breaks the documented `TwoStageFetchResult` contract.
- Adding a separate callback for fetch metadata: overkill — the existing `_set_fetch_result()` mechanism already serves this purpose.
- Making `_set_fetch_result()` conditional on `selected_hits` presence inside the callback itself: shifts responsibility away from the caller and makes the contract harder to reason about.

## Implementation
### Target file
`scripts/rag/augment.py`

### Procedure
Retype `AugmentRefiner.__init__`'s `set_fetch_result` annotation; add a new `_set_fetch_result()` call after refiner execution that passes the raw hit-dict list.

### Method
1. In `AugmentRefiner.__init__` (line 47), change `set_fetch_result: Callable[[str], None] | None = None` to `set_fetch_result: Callable[[list[dict[str, Any]]], None] | None = None`.
2. Keep lines 73-74 (`set_fallback_reason=lambda _: self._set_fallback_reason(_)`) unchanged.

### Details
```python
# In AugmentRefiner.__init__ (augment.py):

# Before (line 47):
set_fetch_result: Callable[[str], None] | None = None,

# After:
set_fetch_result: Callable[[list[dict[str, Any]]], None] | None = None,

# Lines 73-74 KEPT UNCHANGED:
set_fetch_result=lambda r: self._set_fetch_result(r),
set_fallback_reason=lambda _: self._set_fallback_reason(_),
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
- Full regression: verify all existing tests continue passing.

## Completion criteria

- [ ] `set_fetch_result` type annotation changed to `Callable[[list[dict[str, Any]]], None] | None` — REQ-002
- [ ] All existing tests continue passing (no regression) — REQ-002

## Out of scope

- `/replay` endpoint's own pagination/snapshot-consistency issue (EB-M04).
- Centralizing the currently-hardcoded operational thresholds into validated configuration — tracked separately in this batch.
- Deciding on separate read connections or connection manager — defer until load-test results justify it.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Related target files**: scripts/rag/augment.py
