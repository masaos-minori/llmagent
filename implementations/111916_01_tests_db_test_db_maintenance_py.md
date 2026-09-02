# Implementation Procedure: Add UNKNOWN classification test to test_db_maintenance.py

## Goal

Add a unit test asserting that an Unknown classification does not call `_restore_from_backup()` and leaves the target database unmodified, per REQ-001 and REQ-005.

## Scope

**In-Scope**: Add a single new test method to `tests/db/test_db_maintenance.py` that verifies UNKNOWN handling preserves the target database.

**Out-of-Scope**: Modify any other test methods; add integration tests; change existing test fixtures or helpers; modify `scripts/db/recovery.py`.

## Assumptions

- The fix in `scripts/db/recovery.py` (separate implementation procedure) has been implemented and validated before this test addition.
- The test should use the existing `_make_db_cfg` helper and mock infrastructure already present in the file.
- The test should follow the same style as existing `TestRecoverCorruption` tests.

## Design decisions

- Add a new test class `TestRecoverCorruptionUnknown` alongside the existing `TestRecoverCorruption` class.
- Use `unittest.mock.patch` to verify `_restore_from_backup` is NOT called when condition is UNKNOWN.
- Verify the target database file is NOT modified after recovery.
- Mock `_classify_error` to return `(DbCondition.UNKNOWN, "test unknown error")`.

## Alternatives considered

- **Alternative 1: Add the test to the existing `TestRecoverCorruption` class.** Rejected: keeps the class focused; UNKNOWN is a distinct classification requiring separate assertion logic.
- **Alternative 2: Use a real corrupted database fixture like the integration tests.** Rejected: unit test scope; mocking is sufficient and faster.
- **Alternative 3: Test via `_run_integrity_check` directly.** Rejected: the contract is at the `recover_corruption()` level — the test must exercise the full function.

## Implementation

### Target file

`tests/db/test_db_maintenance.py`

### Procedure

1. Locate the end of the existing `TestRecoverCorruption` class (around line ~900).
2. Add a new test class `TestRecoverCorruptionUnknown` immediately after it.
3. Implement a single test method `test_unknown_does_not_restore` that:
   - Creates a temporary database file.
   - Mocks `_classify_error` to return `(DbCondition.UNKNOWN, "unknown integrity error")`.
   - Calls `recover_corruption(cfg, "rag")`.
   - Asserts `_restore_from_backup` was NOT called.
   - Asserts the result `action` indicates preservation (not restoration).
   - Asserts the target database file is unchanged.

### Method

Create the following test class:

```python
class TestRecoverCorruptionUnknown:
    """Tests for DbCondition.UNKNOWN handling in recover_corruption()."""

    @pytest.fixture
    def tmp_rag_db(self, tmp_path: Path) -> Path:
        """Return a temporary rag.sqlite file for UNKNOWN tests."""
        db_path = tmp_path / "rag_unknown.sqlite"
        # Create a valid minimal SQLite file
        conn = sqlite3.connect(str(db_path))
        conn.execute("CREATE TABLE IF NOT EXISTS test_table (id INTEGER PRIMARY KEY)")
        conn.execute("INSERT INTO test_table VALUES (1)")
        conn.commit()
        conn.close()
        return db_path

    def test_unknown_does_not_restore_rag_db(
        self,
        tmp_rag_db: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Verify UNKNOWN classification preserves the target database and does not trigger restore.

        REQ-001: recover_corruption() MUST distinguish DbCondition.UNKNOWN from CORRUPTION
                 and NOT trigger automatic backup-restore for UNKNOWN conditions on rag targets.
        REQ-005: Tests MUST assert that an Unknown classification does not call
                 _restore_from_backup() and leaves the target database unmodified.
        """
        from unittest.mock import patch, MagicMock

        from db.recovery import (
            DbCondition,
            recover_corruption,
        )

        # Create a config pointing to our temp DB
        cfg = MagicMock(spec=DbConfig)
        cfg.rag_db_path = str(tmp_rag_db)
        cfg.session_db_path = str(tmp_rag_db)
        cfg.workflow_db_path = str(tmp_rag_db)
        cfg.eventbus_db_path = str(tmp_rag_db)
        cfg.sqlite_vec_so = "/opt/llm/sqlite-vec/vec0.so"
        cfg.sqlite_timeout = 1
        cfg.sqlite_busy_timeout_ms = 500
        cfg.embed_url = "http://127.0.0.1:8081/embedding"

        # Record original file content for comparison
        original_content = tmp_rag_db.read_bytes()

        # Patch _classify_error to return UNKNOWN
        with patch("db.recovery._classify_error") as mock_classify, \
             patch("db.recovery._restore_from_backup") as mock_restore:
            mock_classify.return_value = (DbCondition.UNKNOWN, "unknown integrity error")

            result = recover_corruption(cfg, "rag")

            # REQ-001: _restore_from_backup MUST NOT be called for UNKNOWN
            mock_restore.assert_not_called()

            # REQ-002: action must indicate preservation, not restoration
            assert result.action != "restored"

            # REQ-005: target database must be unmodified
            current_content = tmp_rag_db.read_bytes()
            assert current_content == original_content

            # REQ-002: success should be False (intervention required)
            assert result.success is False
```

### Details

- Line reference: Insert after the closing brace of `TestRecoverCorruption` class (approximately line ~900 in the current file).
- Follow the existing test naming convention (`test_*`).
- Use `pytest.MonkeyPatch` fixture already available in the file's test methods.
- Import `DbConfig` from `db.config` (already imported at module level).
- Import `DbCondition` from `db.recovery` (needs to be added if not already imported).

## Compatibility considerations

- This is a test-only change. No production code impact.
- The test depends on the UNKNOWN branch being implemented in `recovery.py` — it will fail until that fix is applied.
- The test uses `tmp_path` fixture — standard pytest fixture, no compatibility concerns.

## Security considerations

- No security implications. This is a test addition only.
- Uses temporary files in `tmp_path` — no risk of overwriting real databases.

## Rollback considerations

- To rollback: delete the added test class from the file.
- No operational risk — test changes are always reversible.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tests/db/test_db_maintenance.py::TestRecoverCorruptionUnknown::test_unknown_does_not_restore_rag_db | Unit test execution | `uv run pytest tests/db/test_db_maintenance.py::TestRecoverCorruptionUnknown::test_unknown_does_not_restore_rag_db -v` | Test passes (after recovery.py fix is applied) |
| tests/db/test_db_maintenance.py | Full test suite sanity check | `uv run pytest tests/db/test_db_maintenance.py -v` | All existing tests still pass |

## Completion criteria

- [ ] New test class `TestRecoverCorruptionUnknown` added to `tests/db/test_db_maintenance.py`.
- [ ] Test method `test_unknown_does_not_restore_rag_db` asserts `_restore_from_backup` is NOT called.
- [ ] Test method asserts target database file is unchanged after UNKNOWN recovery.
- [ ] Test method asserts `result.action` is not "restored".
- [ ] Test method asserts `result.success` is False.
- [ ] Existing tests in `test_db_maintenance.py` continue to pass.

## Out of scope

- Adding tests for workflow/eventbus UNKNOWN handling.
- Adding integration tests for UNKNOWN on session DB (covered by separate implementation procedure).
- Modifying existing `TestRecoverCorruption` tests.
- Changing test fixtures or helpers used by other tests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add TestRecoverCorruptionUnknown class with test_unknown_does_not_restore_rag_db method | Pending | — | — | |
| 2 | Validate all existing tests in test_db_maintenance.py still pass | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-005
- **Source issue**: issues/20260831-181721_adr008_01_recover_corruption_unknown_classification_gap.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260901-111916_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260901-111916
- **Related target files**: tests/db/test_db_maintenance.py
