# Dead-code duplicate RagDbMaintenanceService.rebuild_fts() diverges from production schema and could corrupt FTS5 table

## Priority
Medium

## Summary
Delete the dead-code `RagDbMaintenanceService` class from `scripts/rag/maintenance.py` and its associated tests in `tests/db/test_db_maintenance.py::TestRagDbMaintenanceService`, since the class has no production caller and its `rebuild_fts()` method implements a divergent, schema-breaking version of the FTS5 rebuild operation.

## Background
The CI-007 Plan (`plans/20260920-203952_plan.md`) verified INV-07 against the real, called `rebuild_fts()` implementation in `scripts/agent/services/rag_maintenance_service.py::RagMaintenanceService.rebuild_fts()` and treated the dead-code duplicate in `scripts/rag/maintenance.py::RagDbMaintenanceService.rebuild_fts()` as an allow-listed, out-of-scope finding. However, the dead-code duplicate remains in the codebase and poses a latent risk: if ever wired up as a caller (directly, or via a future refactor that consolidates the two `rebuild_fts()` implementations into one and picks the wrong one), it would silently break the FTS5 table's content-mapping and delete/update-side trigger behavior.

## Problem
`scripts/rag/maintenance.py::RagDbMaintenanceService.rebuild_fts()` is a second, unreferenced implementation of the manual FTS5 rebuild operation, functionally divergent from the real, production-called implementation in `scripts/agent/services/rag_maintenance_service.py::RagMaintenanceService.rebuild_fts()`. It drops and recreates `chunks_fts` *without* the `content='chunks', content_rowid='chunk_id'` content-mapping the schema (`scripts/db/schema_sql.py:56-60`) defines, and only recreates the `chunks_ai` trigger — not `chunks_ad`/`chunks_au`. If this class were ever wired up as a caller (directly, or via a future refactor that consolidates the two `rebuild_fts()` implementations into one and picks the wrong one), it would silently break the FTS5 table's content-mapping and delete/update-side trigger behavior.

## Reason for Change
A dead-code duplicate with divergent, schema-breaking behavior creates a latent risk of silent corruption if ever accidentally wired up as a caller. Deleting it eliminates this risk entirely and reduces maintenance burden by removing a confusing, incorrect implementation that could mislead future contributors.

## Implementation Intent
Confirm via repository inspection that `RagDbMaintenanceService` has no production callers today, then delete the whole class (all three methods: `rotate`, `rebuild_fts`, `vacuum`) from `scripts/rag/maintenance.py` and remove or rewrite `tests/db/test_db_maintenance.py::TestRagDbMaintenanceService` to match (removing tests for a deleted class, or migrating any still-relevant assertion — e.g., `rotate()`'s WAL-checkpoint behavior, if not already covered elsewhere — to test the real `scripts/agent/services/rag_maintenance_service.py` implementation instead).

## Target Files or Areas
- `scripts/rag/maintenance.py`
- `tests/db/test_db_maintenance.py`

## Required Changes
1. Confirm via `rg -n "RagDbMaintenanceService"` across the full repository that `tests/db/test_db_maintenance.py` is still the only reference outside the class's own file.
2. Confirm via `uv run vulture scripts/rag/maintenance.py --min-confidence 60` that the class and its methods are still flagged as unused.
3. Delete `RagDbMaintenanceService` (the whole class, all three methods: `rotate`, `rebuild_fts`, `vacuum`) from `scripts/rag/maintenance.py`.
4. Delete or rewrite `tests/db/test_db_maintenance.py::TestRagDbMaintenanceService` to match (removing tests for a deleted class, or migrating any still-relevant assertion — e.g., `rotate()`'s WAL-checkpoint behavior, if not already covered elsewhere — to test the real `scripts/agent/services/rag_maintenance_service.py` implementation instead).

## Constraints
- Do NOT modify `scripts/agent/services/rag_maintenance_service.py` — that is the real, production-called implementation and must remain untouched.
- Do NOT modify `scripts/db/schema_sql.py` — that defines the correct schema.
- If a legitimate future caller is found (contradicting step 1), instead reconcile the two implementations into one correct version and update all callers.

## Acceptance Criteria
- [ ] No references to `RagDbMaintenanceService` remain outside `scripts/rag/maintenance.py` and `tests/db/test_db_maintenance.py`.
- [ ] `RagDbMaintenanceService` class is removed from `scripts/rag/maintenance.py`.
- [ ] `TestRagDbMaintenanceService` class is removed or rewritten in `tests/db/test_db_maintenance.py`.
- [ ] `uv run pytest tests/db/test_db_maintenance.py -v` passes after changes.
- [ ] `uv run ruff check scripts/rag/maintenance.py tests/db/test_db_maintenance.py` reports no errors.
- [ ] `uv run mypy scripts/rag/maintenance.py tests/db/test_db_maintenance.py` reports no type errors.

## Testing Expectations
- Run `uv run pytest tests/db/test_db_maintenance.py -v` to confirm all remaining tests pass.
- Run `uv run ruff check scripts/rag/maintenance.py tests/db/test_db_maintenance.py` and `uv run mypy scripts/rag/maintenance.py tests/db/test_db_maintenance.py` to confirm no lint/type errors.
- Verify that the real `RagMaintenanceService.rebuild_fts()` implementation in `scripts/agent/services/rag_maintenance_service.py` is unaffected.

## Documentation Impact
N/A: this is a dead-code cleanup with no documentation impact.

## Out of Scope
- The real, production-called `RagMaintenanceService.rebuild_fts()` in `scripts/agent/services/rag_maintenance_service.py` — that is the correct implementation and must remain untouched.
- Any other dead-code classes in `scripts/rag/maintenance.py` that are not part of `RagDbMaintenanceService`.
- Reconciling the two `rebuild_fts()` implementations — that is out of scope for this issue; deletion is the preferred approach since the dead-code class has no caller.

## Dependencies
- N/A: none.

## Unresolved Questions
Whether any tests in `TestRagDbMaintenanceService` cover behavior that is also tested elsewhere (e.g., `rotate()`'s WAL-checkpoint behavior) — if so, migration of those assertions to the real implementation's test suite should be considered rather than simple deletion.

## AI Implementation Instruction
Follow these constraints strictly:
1. Only modify files listed under "Target Files or Areas" — do not touch any other files.
2. Before deleting, re-confirm via `rg -n "RagDbMaintenanceService"` that no new callers have appeared since this Issue's filing.
3. Delete the whole `RagDbMaintenanceService` class and all three methods from `scripts/rag/maintenance.py`.
4. Remove `TestRagDbMaintenanceService` from `tests/db/test_db_maintenance.py` unless any of its tests cover behavior that is also tested elsewhere — in that case, migrate those specific assertions to the real implementation's test suite.
5. After changes, verify: `uv run pytest tests/db/test_db_maintenance.py -v` passes, no lint/type errors.
6. Do not attempt to reconcile the two `rebuild_fts()` implementations — deletion is the preferred approach.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-203952_plan.md
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260920-213514
- **Related target files**: scripts/rag/maintenance.py, tests/db/test_db_maintenance.py

</content>
<parameter=filePath>
/home/sugimoto/llmagent/issues/20260920-213514_dead_code_RagDbMaintenanceService_diverges_from_production_schema.md