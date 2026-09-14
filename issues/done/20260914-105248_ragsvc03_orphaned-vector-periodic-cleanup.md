# Implement periodic cleanup for orphaned sqlite-vec embedding vectors

## Priority
Low

## Summary
`sqlite-vec` has no foreign-key enforcement, so `chunks_vec` entries can become orphaned when their source document/chunk is deleted outside the normal deletion path; `scripts/db/rag_consistency.py` already detects and reports orphaned vector counts, but no cleanup mechanism removes them — this issue implements the periodic cleanup half of `RAG-005`'s Recommended Action.

## Background
`docs/00_governance_03_issue-and-uncertainty-management.md` `RAG-005` ("sqlite-vec does not enforce foreign key constraints on embedding vectors", Status: open, Severity: Low) already tracks this exact gap, explicitly noting it as "a known, accepted architectural limitation mitigated by deletion ordering, not an active defect being worked." `docs/adr/ADR-005-rag-source-derived-index-relationships.md` Decision Details establish the correct deletion order (delete `chunks_vec` before `documents`) as the primary mitigation — this issue addresses the residual case where that order is bypassed or interrupted (e.g. a crash mid-deletion, or a direct DB operation outside `DocumentManager`).

## Problem
Confirmed by direct inspection: `check_rag_consistency()` (`scripts/db/rag_consistency.py`) computes and reports `orphan_vec_count` as part of its consistency report, and logs a `[CRITICAL]` message when the count is non-zero — but no function in `scripts/rag/` or `scripts/db/` actually deletes the orphaned `chunks_vec` rows the check detects. `scripts/rag/maintenance.py` (`RagMaintenanceService`) currently implements only `rebuild_fts()`, with no equivalent orphan-vector cleanup method.

## Reason for Change
Per `RAG-005`'s own stated Impact: the vector index grows over time with orphaned entries, increasing memory usage and potentially degrading search performance, if no periodic cleanup exists to bound this growth between the rare cases where the deletion-order mitigation is bypassed.

## Implementation Intent
Add a periodic (or on-demand, operator-triggered) cleanup routine that removes `chunks_vec` rows already identified as orphaned by `check_rag_consistency()`'s existing detection logic — reuse that detection, do not reimplement orphan identification separately. Per `RAG-005`'s own accepted-limitation framing, this is a mitigation for a known architectural gap, not a fix to `sqlite-vec` itself (which cannot enforce FK constraints).

## Target Files or Areas
- `scripts/rag/maintenance.py`
- `scripts/db/rag_consistency.py`
- `docs/00_governance_03_issue-and-uncertainty-management.md`
- `docs/adr/ADR-005-rag-source-derived-index-relationships.md`

## Required Changes
- Add an orphan-vector cleanup method to `RagMaintenanceService` (or an equivalent shared location), reusing `check_rag_consistency()`'s existing `orphan_vec_count`/identification logic rather than duplicating it.
- Decide and implement the cleanup's trigger: a periodic scheduled task, an operator-invoked maintenance command, or both — confirm which invocation model fits this codebase's existing maintenance patterns (e.g. how `rebuild_fts()` is currently invoked) before adding a new one.
- Add tests confirming the cleanup removes only genuinely orphaned `chunks_vec` rows and leaves all correctly-referenced rows untouched.
- Update `RAG-005` in `docs/00_governance_03_issue-and-uncertainty-management.md` to reflect that periodic cleanup is now implemented, once verified.

## Constraints
This issue implements the "periodic cleanup" branch of `RAG-005`'s Recommended Action, not the "migrate to a vector store that supports FK constraints" branch — that migration, if ever pursued, is a separate, much larger issue and is explicitly out of scope here.

## Acceptance Criteria
- A cleanup routine exists that removes orphaned `chunks_vec` rows identified by the existing consistency-check logic.
- The cleanup is invocable through the same operational pattern as `rebuild_fts()` (or a documented, deliberate deviation from it).
- Tests confirm orphaned rows are removed and non-orphaned rows are preserved.
- `RAG-005` is updated (not necessarily removed, since the underlying `sqlite-vec` FK limitation remains architecturally accepted) to note that periodic cleanup is implemented.

## Testing Expectations
Add unit/integration tests that create a known orphaned `chunks_vec` row (e.g. by deleting a document's primary rows without going through the vec-deletion step) and confirm the new cleanup routine removes exactly that row. Run the relevant test suite, static analysis, and type checks.

## Documentation Impact
Update `RAG-005`'s entry in `docs/00_governance_03_issue-and-uncertainty-management.md` to describe the implemented cleanup mechanism, once verified — the entry itself may remain open (documenting the accepted `sqlite-vec` FK limitation) with an updated `Recommended Action`/mitigation note, rather than being removed outright, since the underlying architectural limitation is unchanged.

## Out of Scope
- Migrating to a vector store that supports FK constraints.
- Changing `ADR-005`'s established deletion-order invariant — this issue adds a safety net for when that order is bypassed, it does not replace it.

## Dependencies
N/A: none.

## Unresolved Questions
Whether cleanup should run automatically on a schedule or only on operator request — resolve during implementation by checking how `rebuild_fts()` is currently invoked and following the same operational pattern unless a reason to diverge is confirmed. Non-blocking.

## AI Implementation Instruction
Reuse `check_rag_consistency()`'s existing orphan-detection logic rather than reimplementing it; keep changes scoped to adding a cleanup routine and its invocation path. Do not weaken or bypass `ADR-005`'s deletion-order invariant as a shortcut — this issue is an additional safety net, not a replacement for correct deletion ordering. Confirm the cleanup only removes rows the existing detection logic actually flags as orphaned.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260914-105248
- **Related target files**: scripts/rag/maintenance.py, scripts/db/rag_consistency.py, docs/00_governance_03_issue-and-uncertainty-management.md, docs/adr/ADR-005-rag-source-derived-index-relationships.md
