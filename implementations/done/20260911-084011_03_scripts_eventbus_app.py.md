## Goal

Verify `sweep_orphans()` usage remains correct after consolidation.

## Scope

Read-only verification of `scripts/eventbus/app.py`:
- Verify `sweep_orphans()` usage remains correct after consolidation (REQ-002; `scripts/eventbus/app.py`).
- Confirm no changes needed to `app.py` after DLQ consolidation (REQ-002; `scripts/eventbus/app.py`).

## Assumptions

- The `promote_to_dlq()` function has no supported runtime caller — confirmed by repository-wide grep search showing zero callers under `scripts/`.
- The shared promotion logic should include: row selection (`WHERE delivery_failure_count >= ? AND dlq_at IS NULL`), atomic file writing (`_atomic_write()`), and conditional DB update (`UPDATE events SET dlq_at = ? WHERE event_id = ? AND dlq_at IS NULL`).
- The `dlq_at IS NULL` re-run safety guard should be applied uniformly across all promotion paths.
- Test updates should retarget assertions to the surviving function(s) without weakening what each test actually verifies.

## Design decisions

1. **Read-only verification (REQ-002)**: Since `app.py` only calls `sweep_orphans()` (not `promote_to_dlq()`), no changes are expected to this file after DLQ consolidation. The verification step is to confirm that:
   - `sweep_orphans()` is still used correctly after the shared logic extraction.
   - No new callers of `promote_to_dlq()` have been added since this issue was filed.
   - The return value convention of `sweep_orphans()` (count) is consistent with its usage in `app.py`.

## Alternatives considered

N/A — this is a read-only verification task.

## Implementation
### Target file
`samples/eventbus/app.py`

### Procedure
Verify `sweep_orphans()` usage remains correct after consolidation; confirm no changes needed.

### Method
1. Re-verify that `promote_to_dlq()` has no supported runtime caller (grep for `promote_to_dlq` across `scripts/` before deleting).
2. Confirm that `sweep_orphans()` is still used correctly after the shared logic extraction.
3. Confirm that no new callers of `promote_to_dlq()` have been added since this issue was filed.
4. Confirm that the return value convention of `sweep_orphans()` (count) is consistent with its usage in `app.py`.

### Details
```python
# In app.py:
from eventbus.dlq import sweep_orphans

def _dlq_loop():
    """Periodic DLQ sweep loop."""
    # ... existing logic ...
    
    # This call to sweep_orphans() should remain unchanged after consolidation
    promoted = sweep_orphans(db, deadletter_dir, max_retry)
    
    # ... existing logic ...
```

## Compatibility considerations

- Existing deployments that rely on the current behavior of `sweep_orphans()` should not be affected by DLQ consolidation.
- The return value convention of `sweep_orphans()` (count) should remain consistent.

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

- [ ] Inline promotion (`promote_single`) and sweep (`sweep_orphans`) use consistent persistence rules (shared re-run-safety guard, shared atomic-write/DB-update sequence) — REQ-002, REQ-003
- [ ] DLQ behavior and tests remain correct after consolidation — every currently-passing DLQ test continues to pass, either unchanged or updated to target the surviving function(s) — REQ-005

## Out of scope

- DLQ requeue real-redelivery redesign (EB-H03).
- Changing the DLQ file format or `_atomic_write()`'s mechanism itself.
- Updating documentation that doesn't mention `promote_to_dlq()` as a supported entry point.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260911-195000 | 20260911-195500 | Read-only verification: app.py uses sweep_orphans(db, cfg.deadletter_dir, cfg.max_retry) correctly; no changes needed |
| 2 | Add or update tests per Validation plan | Completed | 20260911-195500 | 20260911-195500 | N/A — read-only verification task |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260911-195500 | 20260911-200000 | ruff format/check + mypy pass; full suite: 16 DLQ tests passed |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260911-200000 | 20260911-200000 | N/A — no documentation changes required |

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
