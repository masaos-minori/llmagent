## Goal

Remove `promote_to_dlq()`; extract shared promotion logic; align `dlq_at IS NULL` guard.

## Scope

Modify `scripts/eventbus/dlq.py`:
- Remove `promote_to_dlq()` if it has no supported caller after re-verification at implementation time (REQ-001; `scripts/eventbus/dlq.py`).
- Extract shared promotion logic used by the inline (`promote_single`) and sweep (`sweep_orphans`) paths where appropriate (REQ-002; `scripts/eventbus/dlq.py`).
- Align `sweep_orphans()`'s safer `dlq_at IS NULL` re-run guard into whatever shared helper is extracted (REQ-003; `scripts/eventbus/dlq.py`).
- Preserve atomic file creation (`_atomic_write()`) and conditional database update behavior (REQ-004; `scripts/eventbus/dlq.py`).

## Assumptions

- The `promote_to_dlq()` function has no supported runtime caller — confirmed by repository-wide grep search showing zero callers under `scripts/`.
- The shared promotion logic should include: row selection (`WHERE delivery_failure_count >= ? AND dlq_at IS NULL`), atomic file writing (`_atomic_write()`), and conditional DB update (`UPDATE events SET dlq_at = ? WHERE event_id = ? AND dlq_at IS NULL`).
- The `dlq_at IS NULL` re-run safety guard should be applied uniformly across all promotion paths.
- Test updates should retarget assertions to the surviving function(s) without weakening what each test actually verifies.

## Design decisions

1. **Remove `promote_to_dlq()` (REQ-001)**: Confirm that `promote_to_dlq()` has no supported runtime caller (already done for this issue, but re-verify at implementation time), and remove it if so. This eliminates duplicate code and prevents future drift between the three overlapping implementations.

2. **Extract shared promotion logic (REQ-002)**: Extract the following common logic from `sweep_orphans()` and `promote_single()` into one internal helper:
   - Row selection (`WHERE delivery_failure_count >= ? AND dlq_at IS NULL`).
   - Atomic file writing (`_atomic_write()`).
   - Conditional DB update (`UPDATE events SET dlq_at = ? WHERE event_id = ? AND dlq_at IS NULL`).

3. **Align `dlq_at IS NULL` guard (REQ-003)**: Apply the `dlq_at IS NULL` re-run safety guard uniformly across all promotion paths. This ensures that `promote_single()` also benefits from the same re-run safety that `sweep_orphans()` has.

4. **Preserve atomic write behavior (REQ-004)**: Ensure that `_atomic_write()` is called before the DB update in all paths, preserving the consistency guarantee that if the file write fails, the DB row is not updated.

## Alternatives considered

- Retaining `promote_to_dlq()` with a documented unique responsibility: would require maintaining three separate implementations and increases the chance of future drift.
- Using a single unified entry point for all DLQ promotion: would simplify the API but lose the distinction between inline promotion and sweep operations.
- Returning a tuple `(count, promoted_ids)` instead of a count or boolean: would provide more flexibility but changes the return value convention for existing callers.

## Implementation
### Target file
`samples/eventbus/dlq.py`

### Procedure
Remove `promote_to_dlq()`; extract shared promotion logic; align `dlq_at IS NULL` guard; preserve atomic write behavior.

### Method
1. Re-verify that `promote_to_dlq()` has no supported runtime caller (grep for `promote_to_dlq` across `scripts/` before deleting).
2. Remove `promote_to_dlq()` function definition.
3. Extract shared promotion logic from `sweep_orphans()` and `promote_single()` into one internal helper.
4. Apply `dlq_at IS NULL` re-run safety guard uniformly across all promotion paths.
5. Preserve atomic write behavior — ensure `_atomic_write()` is called before the DB update in all paths.

### Details
```python
# In dlq.py:

def _shared_promote(db, deadletter_dir, max_retry):
    """Shared promotion logic for sweep and inline paths."""
    now = now_iso()
    rows = db.execute(
        "SELECT seq, event_id, topic, payload, producer, published_at, delivery_failure_count"
        " FROM events WHERE delivery_failure_count >= ? AND dlq_at IS NULL",
        (max_retry,),
    ).fetchall()
    
    promoted = 0
    for row in rows:
        event_id = row["event_id"]
        record = _build_dlq_record(row, now)
        _atomic_write(deadletter_dir, event_id, record)
        cur = db.execute(
            "UPDATE events SET dlq_at = ? WHERE event_id = ? AND dlq_at IS NULL",
            (now, event_id),
        )
        db.commit()
        if cur.rowcount:
            promoted += 1
    
    return promoted

def _shared_promote_single(db, deadletter_dir, event_id):
    """Shared promotion logic for single inline promotion."""
    now = now_iso()
    row = db.execute(
        "SELECT seq, event_id, topic, payload, producer, published_at, delivery_failure_count"
        " FROM events WHERE event_id = ? AND dlq_at IS NULL",
        (event_id,),
    ).fetchone()
    if not row:
        return False
    
    record = _build_dlq_record(row, now)
    _atomic_write(deadletter_dir, event_id, record)
    cur = db.execute(
        "UPDATE events SET dlq_at = ? WHERE event_id = ? AND dlq_at IS NULL",
        (now, event_id),
    )
    db.commit()
    if cur.rowcount:
        logger.warning(
            "dlq inline promoted event_id=%s delivery_failure_count=%d",
            event_id,
            row["delivery_failure_count"],
        )
        return True
    return False

# Remove promote_to_dlq() entirely.
# Update sweep_orphans() to call _shared_promote().
# Update promote_single() to call _shared_promote_single().
```

## Compatibility considerations

- Existing deployments that call `promote_to_dlq()` directly will need to migrate to either `sweep_orphans()` or `promote_single()`.
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
- **Requirement ID**: {the Requirement ID(s) from the Plan's Implementation Target Files row this document implements, e.g. `REQ-003`}
- **Source issue**: {inherited from the target plan file's own Traceability section}
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: {exact repository-relative path of the target plan file}
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: {timestamp}
- **Related target files**: {target_file_path}
