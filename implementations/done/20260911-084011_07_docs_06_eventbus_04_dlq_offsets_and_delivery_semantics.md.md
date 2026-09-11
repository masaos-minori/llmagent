## Goal

Update if any describes `promote_to_dlq()` as a supported entry point.

## Scope

Modify `docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md`:
- Update if any describes `promote_to_dlq()` as a supported entry point (REQ-005; `docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md`).
- Retarget assertions to the surviving function(s) without weakening what each test actually verifies (REQ-005; `docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md`).

## Assumptions

- The `promote_to_dlq()` function has no supported runtime caller — confirmed by repository-wide grep search showing zero callers under `scripts/`.
- The shared promotion logic should include: row selection (`WHERE delivery_failure_count >= ? AND dlq_at IS NULL`), atomic file writing (`_atomic_write()`), and conditional DB update (`UPDATE events SET dlq_at = ? WHERE event_id = ? AND dlq_at IS NULL`).
- The `dlq_at IS NULL` re-run safety guard should be applied uniformly across all promotion paths.
- Test updates should retarget assertions to the surviving function(s) without weakening what each test actually verifies.

## Design decisions

1. **Documentation updates (REQ-005)**: Update all references to `promote_to_dlq()` in the documentation to use either `sweep_orphans()` or `promote_single()` depending on the context:
   - Documentation that describes batch promotion behavior should use `sweep_orphans()`.
   - Documentation that describes single-event promotion behavior should use `promote_single()`.
   - Assertions should be retargeted to the surviving function(s) without weakening what each test actually verifies.

## Alternatives considered

- Retaining `promote_to_dlq()` with a documented unique responsibility: would require maintaining three separate implementations and increases the chance of future drift.
- Using a single unified entry point for all DLQ promotion: would simplify the API but lose the distinction between inline promotion and sweep operations.
- Returning a tuple `(count, promoted_ids)` instead of a count or boolean: would provide more flexibility but changes the return value convention for existing callers.

## Implementation
### Target file
`samples/docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md`

### Procedure
Update if any describes `promote_to_dlq()` as a supported entry point.

### Method
1. Replace all references to `promote_to_dlq()` with appropriate references to `sweep_orphans()` or `promote_single()`.
2. Update documentation calls to use the appropriate surviving function based on context.
3. Retarget assertions to the surviving function(s) without weakening what each test actually verifies.

### Details
```markdown
# In docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md:

# Before:
## promote_to_dlq()
Promotes events to the dead-letter queue when they exceed the maximum retry count.

# After:
## sweep_orphans()
Periodically promotes orphaned events to the dead-letter queue.

## promote_single()
Promotes a single event to the dead-letter queue immediately after a nack.
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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260911-211000 | 20260911-211500 | No promote_to_dlq references found in docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md; governance doc and ADR correctly record it as dead code |
| 2 | Add or update tests per Validation plan | Completed | 20260911-211500 | 20260911-211500 | N/A — documentation-only change |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260911-211500 | 20260911-212000 | ruff format/check + mypy pass; full suite: 16 DLQ tests passed |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260911-212000 | 20260911-212000 | No docs edits required — no stale promote_to_dlq references found |
| 5 | Validate documentation updates | Completed | 20260911-212000 | 20260911-212500 | check_docs_quality.py: 0 errors; check_docs_structure.py: 1 pre-existing warning (missing '## Keywords') |

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
