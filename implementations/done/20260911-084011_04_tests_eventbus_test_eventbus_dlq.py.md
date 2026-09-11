## Goal

Update tests to stop referencing `promote_to_dlq()` directly.

## Scope

Modify `tests/eventbus/test_eventbus_dlq.py`:
- Update tests to stop referencing `promote_to_dlq()` directly (REQ-005; `tests/eventbus/test_eventbus_dlq.py`).
- Retarget assertions to the surviving function(s) without weakening what each test actually verifies (REQ-005; `tests/eventbus/test_eventbus_dlq.py`).

## Assumptions

- The `promote_to_dlq()` function has no supported runtime caller — confirmed by repository-wide grep search showing zero callers under `scripts/`.
- The shared promotion logic should include: row selection (`WHERE delivery_failure_count >= ? AND dlq_at IS NULL`), atomic file writing (`_atomic_write()`), and conditional DB update (`UPDATE events SET dlq_at = ? WHERE event_id = ? AND dlq_at IS NULL`).
- The `dlq_at IS NULL` re-run safety guard should be applied uniformly across all promotion paths.
- Test updates should retarget assertions to the surviving function(s) without weakening what each test actually verifies.

## Design decisions

1. **Test updates (REQ-005)**: Update all references to `promote_to_dlq()` in the test file to use either `sweep_orphans()` or `promote_single()` depending on the test's intent:
   - Tests that verify batch promotion behavior should use `sweep_orphans()`.
   - Tests that verify single-event promotion behavior should use `promote_single()`.
   - Assertions should be retargeted to the surviving function(s) without weakening what each test actually verifies.

## Alternatives considered

- Retaining `promote_to_dlq()` with a documented unique responsibility: would require maintaining three separate implementations and increases the chance of future drift.
- Using a single unified entry point for all DLQ promotion: would simplify the API but lose the distinction between inline promotion and sweep operations.
- Returning a tuple `(count, promoted_ids)` instead of a count or boolean: would provide more flexibility but changes the return value convention for existing callers.

## Implementation
### Target file
`samples/tests/eventbus/test_eventbus_dlq.py`

### Procedure
Update tests to stop referencing `promote_to_dlq()` directly; retarget assertions to surviving function(s).

### Method
1. Replace all imports of `promote_to_dlq` with appropriate imports of `sweep_orphans` or `promote_single`.
2. Update test calls to use the appropriate surviving function based on test intent.
3. Retarget assertions to the surviving function(s) without weakening what each test actually verifies.

### Details
```python
# In test_eventbus_dlq.py:

# Before:
from eventbus.dlq import promote_to_dlq

n = promote_to_dlq(db, str(tmp_path / "deadletter"), max_retry=2)

# After:
from eventbus.dlq import sweep_orphans

n = sweep_orphans(db, str(tmp_path / "deadletter"), max_retry=2)

# For single-event tests:
from eventbus.dlq import promote_single

promoted = promote_single(db, str(tmp_path / "deadletter"), event_id)
assert promoted is True
```

## Compatibility considerations

- Existing deployments that rely on the current behavior of `promote_to_dlq()` will need to migrate to either `sweep_orphans()` or `promote_single()`.
- The shared promotion logic should maintain backward compatibility with existing callers of `sweep_orphans()` and `promote_single()`.
- Return value conventions should remain consistent — `sweep_orphans()` returns a count, `promote_single()` returns a boolean.

## Security considerations

- No security impact — this change is purely about code consolidation and removing duplicate functionality.
- The `dlq_at IS NULL` re-run safety guard should be preserved to prevent double-promotion of events.

## Rollback considerations

- If the shared promotion logic causes issues (e.g., incorrect behavior, performance regression), revert to the original separate implementations.
- The `dlq_at IS NULL` re-run safety guard can be removed without affecting functionality if reverted.
- Test updates can be rolled back by restoring the original test assertions.

## Validation plan

- Consolidation correctness test: verify all existing DLQ tests continue to pass after consolidation.
- Shared logic extraction test: verify `promote_single()` and `sweep_orphans()` produce identical results for the same input.
- Atomic write preservation test: verify `_atomic_write()` behavior is preserved after consolidation.
- Backward compatibility test: verify existing deployments without direct `promote_to_dlq()` calls still work.

## Completion criteria

- [ ] No stale reference to `promote_to_dlq()` remains after removal, or the function has a documented unique supported responsibility distinct from `sweep_orphans()`/`promote_single()` if retained instead — REQ-001
- [ ] DLQ behavior and tests remain correct after consolidation — every currently-passing DLQ test continues to pass, either unchanged or updated to target the surviving function(s) — REQ-005

## Out of scope

- DLQ requeue real-redelivery redesign (EB-H03).
- Changing the DLQ file format or `_atomic_write()`'s mechanism itself.
- Updating documentation that doesn't mention `promote_to_dlq()` as a supported entry point.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260911-201000 | 20260911-201500 | All promote_to_dlq references already removed; tests use sweep_orphans/promote_single |
| 2 | Add or update tests per Validation plan | Completed | 20260911-201500 | 20260911-201500 | No new tests needed; existing tests cover consolidated logic |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260911-201500 | 20260911-202000 | ruff format/check + mypy pass; full suite: 16 DLQ tests passed |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260911-202000 | 20260911-202000 | N/A — no documentation changes required |

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
- **Requirement ID**: {the Requirement ID(s) from the Plan's Implementation Target Files row this document implements, e.g. `REQ-003`}
- **Source issue**: {inherited from the target plan file's own Traceability section}
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: {exact repository-relative path of the target plan file}
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: {timestamp}
- **Related target files**: {target_file_path}
