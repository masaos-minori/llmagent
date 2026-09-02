# Implementation Procedure: Add UNKNOWN condition test to test_db_recovery.py

## Goal

Add a unit test verifying that UNKNOWN condition returns `RecoveryResult(success=False, action="error")` without calling `_restore_from_backup()`, per REQ-001 and REQ-004 of plan 20260901-111949.

## Scope

**In-Scope**: Add a single new test function to `tests/db/test_db_recovery.py` that verifies UNKNOWN condition handling.

**Out-of-Scope**: Modify any other test functions; add integration tests; change existing fixtures or helpers; modify `scripts/db/recovery.py`.

## Assumptions

- The fix in `scripts/db/recovery.py` (separate implementation procedure) has been implemented and validated before this test addition.
- The test should use the existing `mock_db_cfg` and `mock_sqlite_helper` fixtures already present in the file.
- The test should follow the same style as existing `test_*` functions in the file.

## Design decisions

- Add a new test function `test_recover_unknown_returns_error_action` following the existing naming convention.
- Mock `_run_integrity_check` to return `(DbCondition.UNKNOWN, "unknown integrity error")`.
- Verify `_restore_from_backup` is NOT called.
- Verify the result has `success=False` and `action="error"`.

## Alternatives considered

- **Alternative 1: Add the test to an existing class.** Rejected: the file uses flat test functions, not classes; adding a class would break consistency.
- **Alternative 2: Test via a real corrupted database.** Rejected: unit test scope; mocking is sufficient and faster.
- **Alternative 3: Test both UNKNOWN and LOCK_CONTENTION together.** Rejected: UNKNOWN requires distinct assertion logic (action="error" vs. the existing behavior for LOCK_CONTENTION).

## Implementation

### Target file

`tests/db/test_db_recovery.py`

### Procedure

1. Locate the end of the existing test functions (after `test_recover_lock_contention` at approximately line ~85).
2. Add a new test function `test_recover_unknown_returns_error_action` immediately after it.
3. Implement the test that:
   - Uses the existing `mock_db_cfg` fixture.
   - Mocks `_run_integrity_check` to return `(DbCondition.UNKNOWN, "unknown integrity error")`.
   - Calls `recover_corruption(target="rag")`.
   - Asserts `_restore_from_backup` was NOT called.
   - Asserts the result has `success=False` and `action="error"`.

### Method

Create the following test function:

```python
def test_recover_unknown_returns_error_action(mock_db_cfg, mock_sqlite_helper):
    """Verify UNKNOWN condition returns success=False, action='error' without restore attempt.

    REQ-001: When condition == DbCondition.UNKNOWN, recover_corruption() MUST return
             early with action='error' and detail indicating manual intervention required,
             WITHOUT attempting _restore_from_backup().
    REQ-004: A new unit test MUST verify UNKNOWN condition returns RecoveryResult(
             success=False, action='error') without calling _restore_from_backup().
    """
    with (
        patch("scripts.db.recovery._run_integrity_check") as mock_integrity,
        patch("scripts.db.recovery._restore_from_backup") as mock_restore,
    ):
        mock_integrity.return_value = (
            DbCondition.UNKNOWN,
            "unknown integrity error",
        )

        result = recover_corruption(target="rag")

        # REQ-001: _restore_from_backup MUST NOT be called for UNKNOWN
        mock_restore.assert_not_called()

        # REQ-001/REQ-004: success must be False
        assert result.success is False

        # REQ-001/REQ-004: action must be 'error'
        assert result.action == "error"

        # REQ-001: detail must indicate manual intervention required
        assert result.detail and "manual" in result.detail.lower()
```

### Details

- Line reference: Insert after the closing brace of `test_recover_lock_contention` (approximately line ~85 in the current file).
- Follow the existing test naming convention (`test_recover_*`).
- Use the existing `mock_db_cfg` and `mock_sqlite_helper` fixtures (already imported and defined at module level).
- Import `DbCondition` from `scripts.db.recovery` (already imported at module level).

## Compatibility considerations

- This is a test-only change. No production code impact.
- The test depends on the UNKNOWN branch being implemented in `recovery.py` — it will fail until that fix is applied.
- The test uses existing fixtures — no compatibility concerns.

## Security considerations

- No security implications. This is a test addition only.
- Uses mocked objects — no risk of overwriting real databases.

## Rollback considerations

- To rollback: delete the added test function from the file.
- No operational risk — test changes are always reversible.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tests/db/test_db_recovery.py::test_recover_unknown_returns_error_action | Unit test execution | `uv run pytest tests/db/test_db_recovery.py::test_recover_unknown_returns_error_action -v` | Test passes (after recovery.py fix is applied) |
| tests/db/test_db_recovery.py | Full test suite sanity check | `uv run pytest tests/db/test_db_recovery.py -v` | All existing tests still pass |

## Completion criteria

- [ ] New test function `test_recover_unknown_returns_error_action` added to `tests/db/test_db_recovery.py`.
- [ ] Test function asserts `_restore_from_backup` is NOT called.
- [ ] Test function asserts `result.success` is False.
- [ ] Test function asserts `result.action` is "error".
- [ ] Test function asserts `result.detail` contains indication of manual intervention.
- [ ] Existing tests in `test_db_recovery.py` continue to pass.

## Out of scope

- Adding tests for UNKNOWN on workflow/eventbus DBs.
- Modifying existing `test_*` functions.
- Changing the `mock_db_cfg` or `mock_sqlite_helper` fixtures.
- Adding integration tests for UNKNOWN handling.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add test_recover_unknown_returns_error_action function | Pending | — | — | |
| 2 | Validate all existing tests in test_db_recovery.py still pass | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-004
- **Source issue**: issues/20260831-181721_adr008_01_recover_corruption_unknown_classification_gap.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260901-111949_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260901-111949
- **Related target files**: tests/db/test_db_recovery.py
