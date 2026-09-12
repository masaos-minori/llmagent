## Goal

Retype `HttpAugment.__init__`'s `set_fetch_result` annotation; remove the incorrect direct `self._set_fetch_result(result)` call at the end of `run()`.

## Scope

Modify `scripts/rag/http_augment.py`:
- Retype `HttpAugment.__init__`'s `set_fetch_result` annotation from `Callable[[str], None] | None` to `Callable[[list[dict[str, Any]]], None] | None` (REQ-003; `scripts/rag/http_augment.py`).
- Remove the incorrect direct `self._set_fetch_result(result)` call at lines 120-121 that passes the augmented context string (REQ-003; `scripts/rag/http_augment.py`).

## Assumptions

- The `set_fetch_result` callback is now invoked by `call_rag_service()` with raw hit-dict data (not a string), as established in Row 1's change.
- The removed call site was added by commit `cd59f3792` (2026-09-02) as part of the string-flattening refactor — it did not exist before that commit.
- Removing the call does not break any downstream consumer because `last_fetch_result` should receive a `TwoStageFetchResult`, not a plain string.

## Design decisions

1. **Retype the callback parameter**: Change `set_fetch_result` from `Callable[[str], None] | None` to `Callable[[list[dict[str, Any]]], None] | None` in `HttpAugment.__init__` (line 66).
2. **Remove the incorrect call site**: Delete lines 120-121 (`if result is not None: self._set_fetch_result(result)`) — this call passes the augmented context *string*, which conflicts with `last_fetch_result`'s documented type contract (`TwoStageFetchResult | None`).
3. **Preserve the fallback reason callback**: Keep line 122-123 (`elif result is None: self._set_fallback_reason(http_fallback_reason)`) unchanged — only the fetch result callback is being removed.

## Alternatives considered

- Keeping the call but wrapping `result` in a `TwoStageFetchResult`: would require access to `RagConfig` (min_score/max_chunks) which `HttpAugment` doesn't hold — that responsibility belongs to `AugmentRefiner`.
- Adding a no-op lambda instead of removing the call: would silently discard metadata without any observable effect, making debugging harder.
- Changing the callback type back to `Callable[[Any], None]`: too permissive — loses the type safety benefit of narrowing to `list[dict[str, Any]]`.

## Implementation
### Target file
`scripts/rag/http_augment.py`

### Procedure
Retype `HttpAugment.__init__`'s `set_fetch_result` annotation; remove the incorrect direct `self._set_fetch_result(result)` call at the end of `run()`.

### Method
1. In `HttpAugment.__init__` (line 66), change `set_fetch_result: Callable[[str], None] | None = None` to `set_fetch_result: Callable[[list[dict[str, Any]]], None] | None = None`.
2. Delete lines 119-121 (the `# Call user-provided callbacks after determining result` comment and the `if result is not None:` block containing `self._set_fetch_result(result)`).
3. Keep lines 122-123 (`elif result is None: self._set_fallback_reason(http_fallback_reason)`) unchanged.

### Details
```python
# In HttpAugment.__init__ (http_augment.py):

# Before (line 66):
set_fetch_result: Callable[[str], None] | None = None,

# After:
set_fetch_result: Callable[[list[dict[str, Any]]], None] | None = None,

# Lines 119-121 REMOVED:
# # Call user-provided callbacks after determining result
# if result is not None:
#     self._set_fetch_result(result)

# Lines 122-123 KEPT UNCHANGED:
elif result is None:
    self._set_fallback_reason(http_fallback_reason)
```

## Compatibility considerations

- Existing deployments that pass a `set_fetch_result` callback expecting a `str` argument will break under the new type annotation — however, repo-wide `rg` confirms no such caller exists outside the 7 test files enumerated in the Plan's Reference Files.
- The removed call site means `last_fetch_result` will no longer be set from HTTP mode via this path — but it will be set correctly by `AugmentRefiner` (Row 3's change) instead.

## Security considerations

- No security impact — this change removes an incorrect callback invocation rather than adding new functionality.

## Rollback considerations

- If the removed call site causes issues (e.g., missing `last_fetch_result` before Row 3's fix is deployed), revert the deletion while keeping the type annotation change.
- The type annotation change can be reverted without affecting functionality if reverted.

## Validation plan

- Callback type regression test: verify no callers expect a `str` argument to the callback.
- Missing-call-site preservation test: verify `last_fetch_result` is still populated via `AugmentRefiner` after Row 3's change.
- Full regression: verify all existing tests continue passing.

## Completion criteria

- [ ] `set_fetch_result` type annotation changed to `Callable[[list[dict[str, Any]]], None] | None` — REQ-003
- [ ] Incorrect `self._set_fetch_result(result)` call removed from `run()` — REQ-003
- [ ] All existing tests continue passing (no regression) — REQ-003

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
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-09-12T08:59:00Z | 2026-09-12T08:59:30Z | ruff format/lint OK, mypy OK, bandit OK (pre-existing Low B107 on default ""), 28 HttpAugment tests PASS |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | no docs/00_index.md task-scope mapping for scripts/rag/http_augment.py |

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
- **Requirement ID**: REQ-003
- **Source issue**: issues/20260911-132739_raghits01_http-mode-selected-hits-unparsed.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260911-205352_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260911-215854
- **Related target files**: scripts/rag/http_augment.py
