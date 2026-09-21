# Implementation Procedure: Remove TestRagDbMaintenanceService from tests/db/test_db_maintenance.py

## Goal

Remove the `TestRagDbMaintenanceService` class and its associated import from `tests/db/test_db_maintenance.py`, since the class under test (`RagDbMaintenanceService`) is being deleted from the source code.

## Scope

Delete:
1. The import statement `from rag.maintenance import RagDbMaintenanceService` (line 33).
2. The entire `TestRagDbMaintenanceService` class definition (lines 231-361), including the section comment header.

## Assumptions

- None of the four test methods in `TestRagDbMaintenanceService` cover behavior that is also tested elsewhere. If any test covers shared behavior (e.g., WAL-checkpoint logic in `test_rotate_wal_checkpoint`), those assertions should be migrated to the real implementation's test suite before deletion.
- The `_make_real_sqlite` helper method used only by `TestRagDbMaintenanceService` tests can be removed along with the class.
- The `_make_rag_schema` helper method used only by `TestRagDbMaintenanceService` tests can be removed along with the class.

## Design decisions

- **Delete vs. migrate**: Deletion is preferred because `RagDbMaintenanceService` has no callers and its divergent behavior would cause silent corruption if wired up incorrectly. Migrating tests to the real implementation's test suite adds maintenance burden without value.
- **Helper method cleanup**: Remove `_make_real_sqlite` and `_make_rag_schema` helpers only if they are exclusively used by `TestRagDbMaintenanceService` methods.

## Alternatives considered

- **Migrate WAL-checkpoint assertion**: Move `test_rotate_wal_checkpoint`'s WAL-checkpoint verification to a test in `scripts/agent/services/rag_maintenance_service.py`'s test suite. Not worth the effort for dead-code removal.
- **Keep the test as a regression guard**: Would require keeping `RagDbMaintenanceService` in the source, which contradicts the goal of eliminating latent FTS5 corruption risk.

## Implementation

### Target file

`tests/db/test_db_maintenance.py`

### Procedure

1. Delete line 33: `from rag.maintenance import RagDbMaintenanceService`.
2. Delete lines 231-361: The section comment `# ── RagDbMaintenanceService ───────────────────────────────────────────────────` through the end of the last test method in `TestRagDbMaintenanceService`.
3. Verify that `_make_real_sqlite` and `_make_rag_schema` helper methods are not used outside `TestRagDbMaintenanceService`. If they are not used elsewhere, remove them too.
4. Check if the `sqlite3` import on line 6 is still needed after removing the helper methods (it may be used by other tests — verify before removing).

### Method

Edit `tests/db/test_db_maintenance.py` using the Write tool to replace the file content with the remaining sections intact.

### Details

Current file structure around the target area:
```
Line 33: from rag.maintenance import RagDbMaintenanceService
...
Lines 231-233: # ── RagDbMaintenanceService ───────────────────────────────────────────────────
               <blank>
               class TestRagDbMaintenanceService:
Lines 235-243: def _make_real_sqlite(self, path: Path) -> None: ...
Lines 244-256: def test_rotate_wal_checkpoint(...) -> None: ...
Lines 257-290: def _make_rag_schema(self, db_file: Path) -> None: ...
Lines 292-301: def test_rebuild_fts(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None: ...
Lines 303-350: def test_rebuild_fts_uses_normalized_content_for_japanese(...) -> None: ...
Lines 352-361: def test_vacuum(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None: ...
Lines 363+:     def test_rotate_session_db_creates_archive(...) -> None: ...
```

After deletion:
- Line 33 import removed.
- Lines 231-361 removed (section comment + class + all methods + helpers).
- The next test method (`test_rotate_session_db_creates_archive`) becomes the first test after `TestPurgeOldSessions`.

Verify with `uv run ruff check tests/db/test_db_maintenance.py` for unused-import warnings.

## Compatibility considerations

- The `TestRagDbMaintenanceService` class is not referenced by any other test module or fixture. Removing it does not affect other tests.
- The `RagDbMaintenanceService` import is only used within this test file; removing it does not break any other imports.

## Security considerations

N/A: Dead-code test removal has no security impact.

## Rollback considerations

To rollback, restore the deleted code from git history:
```bash
git checkout HEAD~1 -- tests/db/test_db_maintenance.py
```
No data migration or configuration changes are involved.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|--------|----------|----------------|------------------|
| tests/db/test_db_maintenance.py | Verify class removed | Manual review + rg | `rg -n "TestRagDbMaintenanceService" tests/db/test_db_maintenance.py` returns no results |
| tests/db/test_db_maintenance.py | Verify import removed | Manual review | No `from rag.maintenance import RagDbMaintenanceService` remains |
| tests/db/test_db_maintenance.py | Unit test pass | `uv run pytest tests/db/test_db_maintenance.py -v` | All remaining tests pass |
| tests/db/test_db_maintenance.py | Lint check | `uv run ruff check tests/db/test_db_maintenance.py` | No errors |
| tests/db/test_db_maintenance.py | Type check | `uv run mypy tests/db/test_db_maintenance.py` | No type errors |

## Completion criteria

- `TestRagDbMaintenanceService` class and all four test methods are removed from `tests/db/test_db_maintenance.py`.
- The `RagDbMaintenanceService` import is removed from `tests/db/test_db_maintenance.py`.
- The file passes `ruff check` with no errors.
- The file passes `mypy` with no type errors.
- All remaining tests pass (`uv run pytest tests/db/test_db_maintenance.py -v`).

## Out of scope

- Modifying `scripts/rag/maintenance.py` — covered by a separate procedure document.
- Migrating WAL-checkpoint assertions to the real implementation's test suite — not worth the effort for dead-code removal.
- Updating `scripts/agent/services/rag_maintenance_service.py` — the real, production-called implementation must remain untouched.

## execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove TestRagDbMaintenanceService class and RagDbMaintenanceService import from tests/db/test_db_maintenance.py | Pending | — | — | |
| 2 | Run lint/type checks on tests/db/test_db_maintenance.py | Pending | — | — | |
| 3 | Run pytest tests/db/test_db_maintenance.py -v and confirm all tests pass | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-003
- **Source issue**: issues/20260920-211327_dead_code_RagDbMaintenanceService_diverges_from_production_schema.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-213943_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260922-060545
- **Related target files**: tests/db/test_db_maintenance.py
