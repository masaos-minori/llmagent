# Implementation Procedure: Add UNKNOWN classification integration test to test_session_recovery.py

## Goal

Add an integration test verifying that UNKNOWN handling on `session.sqlite` preserves the database and requires operator intervention, per REQ-001 and REQ-005.

## Scope

**In-Scope**: Add a single new integration test function to `tests/integration/test_session_recovery.py` that verifies UNKNOWN handling preserves the session database.

**Out-of-Scope**: Modify existing integration tests; add tests for other targets (rag, workflow, eventbus); change the `corrupt_wal_db` fixture or `_patch_db_config` helper.

## Assumptions

- The fix in `scripts/db/recovery.py` (separate implementation procedure) has been implemented and validated before this test addition.
- The test should use the existing `_patch_db_config` helper and `tmp_path` fixture already present in the file.
- The test should follow the same style as existing `test_e*` functions.

## Design decisions

- Add a new test function `test_e06_recover_corruption_unknown_preserves_session_db` following the existing `test_eNN_*` naming convention.
- Use a valid SQLite file (not corrupted) since UNKNOWN arises from unrecognized exceptions during integrity check, not from physical corruption.
- Mock `_classify_error` to return `(DbCondition.UNKNOWN, "unknown integrity error")`.
- Verify the session database file is NOT modified after recovery.

## Alternatives considered

- **Alternative 1: Use the `corrupt_wal_db` fixture.** Rejected: physical corruption triggers different code paths; UNKNOWN specifically requires an exception that bypasses both OperationalError and DatabaseError classifiers.
- **Alternative 2: Create a mock-based unit test instead.** Rejected: integration test scope requires exercising the full function including path resolution via `build_db_config`.
- **Alternative 3: Test via `AgentSession.start()` flow.** Rejected: the contract is at the `recover_corruption()` level — direct invocation is cleaner and more focused.

## Implementation

### Target file

`tests/integration/test_session_recovery.py`

### Procedure

1. Locate the end of the existing test functions (after `test_e05`).
2. Add a new test function `test_e06_recover_corruption_unknown_preserves_session_db` immediately after it.
3. Implement the test that:
   - Creates a temporary valid session database.
   - Patches `build_db_config` to point at the temp database.
   - Mocks `_classify_error` to return `(DbCondition.UNKNOWN, "unknown integrity error")`.
   - Calls `recover_corruption(cfg, "session")`.
   - Asserts `_restore_from_backup` was NOT called.
   - Asserts the session database file is unchanged.

### Method

Create the following test function:

```python
def test_e06_recover_corruption_unknown_preserves_session_db(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify UNKNOWN classification on session DB preserves the database and does not trigger restore.

    REQ-001: recover_corruption() MUST distinguish DbCondition.UNKNOWN from CORRUPTION
             and NOT trigger automatic backup-restore for UNKNOWN conditions on session targets.
    REQ-005: Tests MUST assert that an Unknown classification does not call
             _restore_from_backup() and leaves the target database unmodified.

    Unlike test_e01–test_e04 which exercise physical corruption (which crashes before
    reaching _restore_from_backup()), this test exercises the UNKNOWN classification
    path where _classify_error returns DbCondition.UNKNOWN for an unrecognized exception.
    """
    from unittest.mock import patch, MagicMock

    from db.config import DbConfig
    from db.recovery import (
        DbCondition,
        recover_corruption,
    )

    # Create a valid minimal session database
    session_db_path = str(tmp_path / "e06_session.sqlite")
    conn = sqlite3.connect(session_db_path)
    conn.execute("""CREATE TABLE IF NOT EXISTS sessions (
        session_id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        title TEXT
    )""")
    conn.execute("INSERT INTO sessions VALUES (1, datetime('now'), 'test')")
    conn.commit()
    conn.close()

    # Record original file content for comparison
    original_content = Path(session_db_path).read_bytes()

    # Patch build_db_config to point at our temp DB
    cfg = DbConfig(
        rag_db_path=str(tmp_path / "rag.sqlite"),
        session_db_path=session_db_path,
        workflow_db_path=str(tmp_path / "workflow.sqlite"),
        eventbus_db_path=str(tmp_path / "eventbus.sqlite"),
        sqlite_timeout=1,
        sqlite_busy_timeout_ms=500,
    )
    monkeypatch.setattr("db.helper.build_db_config", lambda: cfg)
    monkeypatch.setattr("db.recovery.build_db_config", lambda: cfg)

    # Patch _classify_error to return UNKNOWN
    with patch("db.recovery._classify_error") as mock_classify, \
         patch("db.recovery._restore_from_backup") as mock_restore:
        mock_classify.return_value = (DbCondition.UNKNOWN, "unknown integrity error")

        result = recover_corruption(cfg, "session")

        # REQ-001: _restore_from_backup MUST NOT be called for UNKNOWN
        mock_restore.assert_not_called()

        # REQ-002: action must indicate preservation, not restoration
        assert result.action != "restored"

        # REQ-005: target database must be unmodified
        current_content = Path(session_db_path).read_bytes()
        assert current_content == original_content

        # REQ-002: success should be False (intervention required)
        assert result.success is False
```

### Details

- Line reference: Insert after the closing brace of `test_e05_concurrent_session_start_under_exclusive_lock` (approximately line ~171 in the current file).
- Follow the existing `test_eNN_*` naming convention.
- Use `pytest.MonkeyPatch` fixture already available in the file's test functions.
- Import `DbConfig` from `db.config` (needs to be added if not already imported at module level).
- Import `DbCondition` from `db.recovery` (needs to be added if not already imported).

## Compatibility considerations

- This is a test-only change. No production code impact.
- The test depends on the UNKNOWN branch being implemented in `recovery.py` — it will fail until that fix is applied.
- The test uses `tmp_path` fixture — standard pytest fixture, no compatibility concerns.

## Security considerations

- No security implications. This is a test addition only.
- Uses temporary files in `tmp_path` — no risk of overwriting real databases.

## Rollback considerations

- To rollback: delete the added test function from the file.
- No operational risk — test changes are always reversible.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tests/integration/test_session_recovery.py::test_e06_recover_corruption_unknown_preserves_session_db | Integration test execution | `uv run pytest tests/integration/test_session_recovery.py::test_e06_recover_corruption_unknown_preserves_session_db -v` | Test passes (after recovery.py fix is applied) |
| tests/integration/test_session_recovery.py | Full integration test suite sanity check | `uv run pytest tests/integration/test_session_recovery.py -v` | All existing tests still pass |

## Completion criteria

- [ ] New test function `test_e06_recover_corruption_unknown_preserves_session_db` added to `tests/integration/test_session_recovery.py`.
- [ ] Test function asserts `_restore_from_backup` is NOT called.
- [ ] Test function asserts session database file is unchanged after UNKNOWN recovery.
- [ ] Test function asserts `result.action` is not "restored".
- [ ] Test function asserts `result.success` is False.
- [ ] Existing tests in `test_session_recovery.py` continue to pass.

## Out of scope

- Adding tests for UNKNOWN on rag DB (covered by separate implementation procedure).
- Adding tests for UNKNOWN on workflow/eventbus DBs.
- Modifying existing `test_e*` functions.
- Changing the `corrupt_wal_db` fixture or `_patch_db_config` helper.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add test_e06_recover_corruption_unknown_preserves_session_db function | Pending | — | — | |
| 2 | Validate all existing tests in test_session_recovery.py still pass | Pending | — | — | |

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
- **Related target files**: tests/integration/test_session_recovery.py
