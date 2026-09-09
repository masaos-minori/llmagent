## Goal

Add regression tests for the HEALTHY-path case where `workflow`/`eventbus` targets are rejected before any database access, ensuring `_run_integrity_check` and `_vacuum_db` are not called.

## Scope

In scope: adding four new test functions to `tests/db/test_db_recovery.py` — two for the HEALTHY-underlying-database case (one for workflow, one for eventbus), and two for the dry_run mode case (one for workflow, one for eventbus). Out of scope: modifying existing test functions beyond adding `assert_not_called()` assertions for `_run_integrity_check`/`_vacuum_db`.

## Assumptions

- The existing `mock_db_cfg` fixture provides `workflow_db_path` and `eventbus_db_path` attributes (confirmed at lines 20-21 of the test file).
- The existing `mock_sqlite_helper` fixture is sufficient for mocking SQLiteHelper in these tests.
- The `DbCondition.HEALTHY` constant is importable from `scripts.db.recovery` (confirmed at line 7 of the test file).

## Design decisions

Each new test follows the pattern established by `test_recover_corrupt_workflow_prohibited`: mock `_run_integrity_check` to return `(DbCondition.HEALTHY, None)`, assert `result.action == "no_recovery_allowed"`, and assert `_run_integrity_check`/`_vacuum_db` are not called.

## Alternatives considered

- Combining workflow and eventbus into a single parametrized test — rejected: separate tests provide clearer isolation and match the existing pattern used by `test_recover_corrupt_workflow_prohibited` and `test_recover_eventbus_uses_correct_db_path`.
- Testing the CORRUPTION path again — rejected: `test_recover_corrupt_workflow_prohibited` already covers this; the gap is specifically the HEALTHY path.

## Implementation
### Target file
`tests/db/test_db_recovery.py`

### Procedure
1. Add `test_recover_healthy_workflow_prohibited`: mock `_run_integrity_check` returning `(DbCondition.HEALTHY, None)`, assert `action="no_recovery_allowed"`, assert `_run_integrity_check` not called, assert `_vacuum_db` not called.
2. Add `test_recover_healthy_eventbus_prohibited`: same pattern as above for eventbus.
3. Add `test_recover_dry_run_workflow_prohibited`: `dry_run=True`, mock `_run_integrity_check` returning `(DbCondition.HEALTHY, None)`, assert rejection before integrity check.
4. Add `test_recover_dry_run_eventbus_prohibited`: same pattern as above for eventbus.
5. Update existing `test_recover_corrupt_workflow_prohibited`, `test_recover_workflow_uses_correct_db_path`, `test_recover_eventbus_uses_correct_db_path` to add `assert_not_called()` assertions for `_run_integrity_check`.

### Method
```python
def test_recover_healthy_workflow_prohibited(mock_db_cfg, mock_sqlite_helper):
    """Regression: workflow target with HEALTHY DB must reject before any DB access."""
    with patch(
        "scripts.db.recovery._run_integrity_check",
        return_value=(DbCondition.HEALTHY, None),
    ) as mock_integrity:
        with patch("scripts.db.recovery._vacuum_db") as mock_vacuum:
            result = recover_corruption(target="workflow")
            
            assert result.success is False
            assert result.action == "no_recovery_allowed"
            assert result.detail and "Automatic recovery is prohibited" in result.detail
            mock_integrity.assert_not_called()
            mock_vacuum.assert_not_called()


def test_recover_healthy_eventbus_prohibited(mock_db_cfg, mock_sqlite_helper):
    """Regression: eventbus target with HEALTHY DB must reject before any DB access."""
    with patch(
        "scripts.db.recovery._run_integrity_check",
        return_value=(DbCondition.HEALTHY, None),
    ) as mock_integrity:
        with patch("scripts.db.recovery._vacuum_db") as mock_vacuum:
            result = recover_corruption(target="eventbus")
            
            assert result.success is False
            assert result.action == "no_recovery_allowed"
            assert result.detail and "Automatic recovery is prohibited" in result.detail
            mock_integrity.assert_not_called()
            mock_vacuum.assert_not_called()


def test_recover_dry_run_workflow_prohibited(mock_db_cfg, mock_sqlite_helper):
    """Regression: dry_run mode must reject workflow before any DB access."""
    with patch(
        "scripts.db.recovery._run_integrity_check",
        return_value=(DbCondition.HEALTHY, None),
    ) as mock_integrity:
        result = recover_corruption(target="workflow", dry_run=True)
        
        assert result.success is False
        assert result.action == "no_recovery_allowed"
        assert result.dry_run is True
        mock_integrity.assert_not_called()


def test_recover_dry_run_eventbus_prohibited(mock_db_cfg, mock_sqlite_helper):
    """Regression: dry_run mode must reject eventbus before any DB access."""
    with patch(
        "scripts.db.recovery._run_integrity_check",
        return_value=(DbCondition.HEALTHY, None),
    ) as mock_integrity:
        result = recover_corruption(target="eventbus", dry_run=True)
        
        assert result.success is False
        assert result.action == "no_recovery_allowed"
        assert result.dry_run is True
        mock_integrity.assert_not_called()
```

### Details
- All four tests use the existing `mock_db_cfg` and `mock_sqlite_helper` fixtures.
- Each test mocks `_run_integrity_check` to return `(DbCondition.HEALTHY, None)` — this ensures the test exercises the HEALTHY branch that was previously untested for workflow/eventbus.
- The `assert_not_called()` assertions on `_run_integrity_check` confirm the domain-policy check now runs before any database access.
- For the dry_run tests, only `_run_integrity_check` needs to be asserted-not-called (not `_vacuum_db`) because dry_run mode doesn't call `_vacuum_db` even for healthy rag/session targets.
- Existing tests (`test_recover_corrupt_workflow_prohibited`, `test_recover_workflow_uses_correct_db_path`, `test_recover_eventbus_uses_correct_db_path`) need `assert_not_called()` added for `_run_integrity_check` since they will now receive rejection before the integrity check is ever reached.

## Compatibility considerations

N/A: these are new tests only; existing tests continue to pass unchanged (or are updated minimally to reflect the new control flow ordering).

## Security considerations

N/A: no credential access, network operations, or filesystem writes introduced.

## Rollback considerations

Revert is removing the four new test functions and restoring the three existing tests to their original form (without `assert_not_called()` additions). No data loss risk.

## Validation plan

- Unit: run new tests individually — `uv run pytest tests/db/test_db_recovery.py::test_recover_healthy_workflow_prohibited -v`, `uv run pytest tests/db/test_db_recovery.py::test_recover_healthy_eventbus_prohibited -v`, `uv run pytest tests/db/test_db_recovery.py::test_recover_dry_run_workflow_prohibited -v`, `uv run pytest tests/db/test_db_recovery.py::test_recover_dry_run_eventbus_prohibited -v`.
- Regression: run full test suite — `uv run pytest tests/db/test_db_recovery.py -v`.

## Completion criteria

- Four new test functions exist and pass: `test_recover_healthy_workflow_prohibited`, `test_recover_healthy_eventbus_prohibited`, `test_recover_dry_run_workflow_prohibited`, `test_recover_dry_run_eventbus_prohibited` (AC-1).
- Each new test asserts `result.action == "no_recovery_allowed"` and `_run_integrity_check`/`_vacuum_db` are not called (AC-2).
- Existing `test_recover_corrupt_workflow_prohibited`, `test_recover_workflow_uses_correct_db_path`, `test_recover_eventbus_uses_correct_db_path` continue to pass with minimal updates (only `assert_not_called()` additions) (AC-3).

## Out of scope

Modifying existing test functions beyond adding `assert_not_called()` assertions for `_run_integrity_check`/`_vacuum_db`; changing the `mock_db_cfg` fixture structure; adding integration tests outside the unit-test scope.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add regression tests for HEALTHY-path workflow/eventbus | Pending | — | — | |
| 2 | Add regression tests for dry_run workflow/eventbus | Pending | — | — | |
| 3 | Update existing tests with assert_not_called() | Pending | — | — | |
| 4 | Run validation sequence (rules/toolchain.md) | Pending | — | — | |

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
- **Requirement ID**: REQ-004, REQ-005
- **Source issue**: issues/20260907-124049_h0706_recovery_target_check_before_vacuum.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260908-075615_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260909-065442
- **Related target files**: tests/db/test_db_recovery.py
