## Goal

Add an integration test in `tests/agent/services/test_rag_index_integrity.py` that creates a deliberately orphaned `chunks_vec` row and confirms `RagMaintenanceService.rebuild_vec()` removes it while preserving correctly-referenced rows. Per REQ-004.

## Scope

- Add exactly one integration test method to `tests/agent/services/test_rag_index_integrity.py`
- Test that `rebuild_vec()` removes orphaned `chunks_vec` rows (no matching source in `chunks`)
- Test that valid `chunks_vec` rows are preserved
- Out-of-scope: modifying the `_FakeSQLiteHelper` fixture or schema

## Assumptions

- The existing `_FakeSQLiteHelper` fixture (lines 77-103) provides the SQLite connection pattern to reuse
- The existing `_insert_doc()` and `_insert_chunk()` helper functions provide the data insertion pattern
- The existing `test_rebuild_fts_uses_coalesce` test (line 146) demonstrates how to patch `SQLiteHelper` — same pattern applies here
- The schema already includes `chunks_vec` table (line 44-46): `CREATE TABLE IF NOT EXISTS chunks_vec (chunk_id INTEGER PRIMARY KEY)`
- `rebuild_vec()` deletes all `chunks_vec` rows and re-inserts from `chunks WHERE embedding IS NOT NULL` — confirmed via `rag_maintenance_service.py:66-78`

## Design decisions

1. Place the new test in the existing file alongside other `RagMaintenanceService` integration tests — consistent with the Plan's recommendation
2. Use the existing `_FakeSQLiteHelper` fixture rather than creating a new one — reduces duplication
3. Create an orphaned `chunks_vec` row by inserting a `chunk_id` into `chunks_vec` without a corresponding entry in `chunks` — this is the simplest way to produce an orphan

## Alternatives considered

1. Creating a separate test file for RAG index integrity tests: rejected — the existing file already imports `RagMaintenanceService` and exercises its methods
2. Using a real SQLite database instead of the in-memory fixture: rejected — the existing tests use `_FakeSQLiteHelper`; consistency within the file is preferred

## Implementation

### Target file

`tests/agent/services/test_rag_index_integrity.py`

### Procedure

1. Read the existing test structure (lines 1-129) to confirm current content
2. Add new test section after the last existing test (after line 339)
3. Add `test_rebuild_vec_removes_orphaned_chunks_vec_rows` test method
4. Verify the test follows the same fixture/patching pattern as existing tests

### Method

1. Read `test_rag_index_integrity.py` lines 1-129 to confirm the exact test structure
2. Insert new test after line 339 using the same indentation style
3. Each test follows the same pattern: use fixture, insert test data, call service method, assert on results

### Details

**Step 1 — Read existing test structure:**

Current file ends at line 339. The existing pattern for integration tests:
- Uses `@pytest.fixture` `db` providing `_FakeSQLiteHelper` with in-memory SQLite
- Patches `SQLiteHelper` to inject the fake database
- Calls `RagMaintenanceService()` methods directly

**Step 2 — Add new test after line 339:**

```python
# ── REBUILD_VEC: orphaned chunks_vec removal ──────────────────────────────────


def test_rebuild_vec_removes_orphaned_chunks_vec_rows(db: _FakeSQLiteHelper) -> None:
    """rebuild_vec() must remove orphaned chunks_vec rows while preserving valid ones."""
    conn = db._conn
    # Insert a valid chunk with embedding (will survive rebuild)
    doc_id = _insert_doc(conn, url="http://valid.example.com")
    _insert_chunk_with_embedding(conn, doc_id, "valid content", b"\x00\x01\x02\x03")

    # Insert an orphaned chunks_vec row (chunk_id that does NOT exist in chunks)
    orphan_chunk_id = 9999
    db.execute(
        "INSERT OR IGNORE INTO chunks_vec(chunk_id) VALUES(?)",
        (orphan_chunk_id,),
    )
    db.commit()

    # Verify orphan exists before rebuild
    orphan_before = db.fetchall(
        "SELECT * FROM chunks_vec WHERE chunk_id = ?", (orphan_chunk_id,)
    )
    assert len(orphan_before) == 1

    # Verify valid row exists before rebuild
    valid_before = db.fetchall(
        "SELECT * FROM chunks_vec WHERE chunk_id = ?", (1,)
    )
    assert len(valid_before) == 1

    # Rebuild vec
    with patch(
        "agent.services.rag_maintenance_service.SQLiteHelper"
    ) as mock_helper_cls:
        mock_helper_cls.return_value.open.return_value.__enter__.return_value = db
        mock_helper_cls.return_value.open.return_value.__exit__ = lambda *_: None
        count = RagMaintenanceService().rebuild_vec()

    # Orphan must be removed
    orphan_after = db.fetchall(
        "SELECT * FROM chunks_vec WHERE chunk_id = ?", (orphan_chunk_id,)
    )
    assert len(orphan_after) == 0

    # Valid row must be preserved
    valid_after = db.fetchall(
        "SELECT * FROM chunks_vec WHERE chunk_id = ?", (1,)
    )
    assert len(valid_after) == 1

    # Row count must match the number of chunks with embeddings
    expected_count = len(db.fetchall(
        "SELECT chunk_id FROM chunks WHERE embedding IS NOT NULL"
    ))
    assert count == expected_count
```

Rationale: mirrors the existing `test_rebuild_fts_uses_coalesce` test's patching pattern exactly. Creates both an orphaned row (via direct INSERT into `chunks_vec` bypassing the FK constraint) and a valid row, then verifies the rebuild removes only the orphan.

Reference files read (must NOT be modified):
- `scripts/agent/services/rag_maintenance_service.py:66-78` — confirms `rebuild_vec()` logic
- `tests/agent/services/test_rag_index_integrity.py:1-339` — confirms existing test pattern

## Compatibility considerations

- No public API changes; only adds new test method
- Test isolation preserved: each test uses its own fixture instance
- Existing tests unaffected by the addition

## Security considerations

N/A — test-only change, no security-sensitive operations introduced.

## Rollback considerations

- Revert the added test method to restore original state
- No data loss risk — only test code changes

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tests/agent/services/test_rag_index_integrity.py | Integration — verify orphan removal works | `uv run pytest tests/agent/services/test_rag_index_integrity.py -k rebuild_vec -q` | New test passes |
| tests/agent/services/test_rag_index_integrity.py | Regression — verify existing tests still pass | `uv run pytest tests/agent/services/test_rag_index_integrity.py -q` | Existing tests unaffected |

## Completion criteria

- [ ] `test_rebuild_vec_removes_orphaned_chunks_vec_rows` added and passes
- [ ] Test creates both an orphaned `chunks_vec` row and a valid one
- [ ] Test asserts orphan is removed after `rebuild_vec()`
- [ ] Test asserts valid row is preserved after `rebuild_vec()`
- [ ] Test asserts row count matches `chunks WHERE embedding IS NOT NULL`
- [ ] Existing tests still pass without regression

## Out of scope

- Modifying the `_FakeSQLiteHelper` fixture or schema
- Adding a scheduled cleanup mechanism
- Changing the existing `rag-maintenance-service` behavior
- Testing edge cases like concurrent access or transaction rollback

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: existing tests cover regression |
| 3 | Run the validation sequence (rules/toolchain.md) | Pending | — | — | N/A: documentation-only change |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: docstring already describes delegation |

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
- **Requirement ID**: REQ-004
- **Source issue**: issues/20260914-105248_ragsvc03_orphaned-vector-periodic-cleanup.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-145915_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-161952
- **Related target files**: tests/agent/services/test_rag_index_integrity.py
