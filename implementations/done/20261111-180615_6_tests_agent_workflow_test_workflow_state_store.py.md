## Goal
Delete the two retained-database compatibility tests from `tests/agent/workflow/test_workflow_state_store.py` so no test pins pre-current-schema behavior (`REQ-003`, Plan Phase 2).

## Scope
**Release unit**: N/A: not part of a release unit

- **Target file**: `tests/agent/workflow/test_workflow_state_store.py` (frozen-table row 6).

## Assumptions
- A-4 (from the Plan): deleting these two tests loses no current-schema coverage — `test_state_store_create_task_issues_unique_keys` covers nonce uniqueness on the current schema, and the neighboring `TestToolCallStateOps` lifecycle tests (`test_record_duplicate_key_is_ignored`, `test_finalize_moves_state_and_bumps_updated_at`) exercise the same current-shape paths (verified 2026-11-11 against the current file).
- adrrev005 procedure 29 has landed (archived `implementations/done/20261110-164906_29_tests_agent_workflow_test_workflow_state_store_py.md`), and both target tests are still present after it — confirmed 2026-11-11 (locations recorded under Implementation > Details). This document therefore adds no overlap with adrrev005.

## Design decisions
- Delete the tests outright rather than rewrite them against the current schema: their subject matter (a hand-built composite-key row; a hand-created `execution_snapshots` table and `snapshot_id` column) does not exist in the current schema, and `snapshot_id` is absent from `scripts/db/schema_sql.py` and the workflow schema service.
- Reword one adjacent comment (see Details, step 3): `AC-4`'s `rg -n "composite|legacy shape|retained" tests/agent/workflow/test_workflow_state_store.py` gate must return no hit, and line 92's surviving comment `# UUID4, not a composite` is the only remaining match after the two deletions.

## Alternatives considered
- Keep the tests as migration guards — rejected: the project policy is current-schema-only (Issue Decision), retained databases are not supported, and no migration path names these shapes.
- Leave line 92's comment unchanged and treat AC-4's `rg` as intent-only — rejected: AC-4 is a literal completion gate and a comment that re-introduces the deleted concept invites re-addition.

## Implementation
### Target file
`tests/agent/workflow/test_workflow_state_store.py`

### Procedure
1. Delete `test_retained_db_compatibility` (lines 109-124, in `TestCreateTask`).
2. Delete `test_lifecycle_works_on_legacy_shape_with_unused_snapshot_column` (lines 793-821, in `TestToolCallStateOps`).
3. Reword the comment on line 92 from `# UUID4, not a composite` to `# UUID4` so no `composite` match remains (AC-4 gate).

### Method
Whole-test-function deletion; no helper is shared with surviving tests (`store` fixture and module-level imports are used elsewhere and stay). No assertion or fixture changes elsewhere.

### Details
- Test 1 (deleted block, lines 109-124): inserts a task row with `task_nonce = ":0"` (composite-style key) directly via SQL, then checks readability after a normal `create_task`. The composite-nonce behavior it protects is gone; `test_state_store_create_task_issues_unique_keys` immediately after it asserts UUID4 nonces (`!= "X:1"`) on the current schema and remains.
- Test 2 (deleted block, lines 793-821): `CREATE TABLE execution_snapshots ...` plus `ALTER TABLE tool_call_state ADD COLUMN snapshot_id ...`, then a normal record/finalize lifecycle on that legacy shape. Neither object exists in the current schema; the lifecycle itself is covered by `test_finalize_moves_state_and_bumps_updated_at` and `test_record_duplicate_key_is_ignored` (both survive).
- Comment (line 92): `assert uuid.UUID(task.task_nonce)  # UUID4, not a composite` → `assert uuid.UUID(task.task_nonce)  # UUID4`. Assertion unchanged.

## Compatibility considerations
- Ordering: adrrev005 procedure 29 has already landed, so this document edits the post-adrrev005 file state; no conflict with `implementations/done/20261110-164906_29_...` (it removed the legacy-age cases only).
- `tests/agent/workflow/test_state_store.py` (frozen-table row 5) requires no edit: `REQ-002` already landed via adrrev005 procedure 11 (commit `331754c1c`), verified 2026-11-11.
- No production code change; deletion of tests only.

## Security considerations
Not applicable (test deletion only).

## Rollback considerations
Single-commit revert restores the two tests; they rebuild their legacy shapes by hand, so a revert needs no schema or fixture migration.

## Validation plan
- `uv run pytest tests/agent/workflow/test_workflow_state_store.py -v` — pass with the two tests gone (Plan Validation plan row 5).
- `rg -n "composite|legacy shape|retained" tests/agent/workflow/test_workflow_state_store.py` — no hit (AC-4).
- `rg -n "snapshot_id|execution_snapshots" tests/agent/workflow/test_workflow_state_store.py` — no hit.
- `uv run ruff check tests/agent/workflow/test_workflow_state_store.py`; `uv run pytest tests/agent/workflow/ -q` — no new findings, whole workflow test dir green.

## Completion criteria
- Both named tests no longer exist; AC-4 and the Validation plan commands pass; only this target file changed.

## Out of Scope
- `tests/agent/workflow/test_state_store.py` (already satisfied, frozen-table row 5) and `tests/agent/workflow/test_stale_recovery_lease.py` (adrrev005-owned).
- Any production schema or code change (`snapshot_id` already absent from `scripts/db/schema_sql.py`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261111-190303 | 20261111-190406 | two test deletions + one comment reword two tests deleted + comment reworded; changed: tests/agent/workflow/test_workflow_state_store.py; Test-2 block citation corrected to 793-821 |
| 2 | Add or update tests per Validation plan | Completed | 20261111-190406 | 20261111-191518 | no new tests; deletions only 40 targeted + 206 workflow-dir tests pass; deletions only |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261111-191518 | ruff pass; AC-4 rg gates no hit; full suite 12109 passed, 9 skipped; diff-cover 100% |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261111-191518 | N/A: no documentation in scope for this row N/A: no documentation in scope for this row |

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
- **Requirement ID**: `REQ-003` (Plan row AC-4)
- **Source issue**: issues/20261111-163923_compat009_workflow-legacy-compat-removal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-170504_compat009_workflow-legacy-compat-removal.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261111-180615
- **Related target files**: `tests/agent/workflow/test_workflow_state_store.py`