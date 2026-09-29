## Goal

Add an integration-level test for `recover_corruption()`'s `INVALID_FORMAT` dispatch branch in `tests/db/test_db_recovery.py`, mirroring the existing `LOCK_CONTENTION`/`PERMISSION_FAILURE` sibling tests, closing REQ-001 (and the remaining open question behind NC-021).

## Scope

In-scope: add one new test function `test_recover_invalid_format` to `tests/db/test_db_recovery.py`, placed immediately after `test_recover_permission_failure`, exercising `recover_corruption()`'s dispatch for `DbCondition.INVALID_FORMAT`. Out-of-scope: any change to `scripts/db/recovery.py` (`_classify_error()`, `DbCondition`, `recover_corruption()`), and re-litigating whether `INVALID_FORMAT` is dead code (ADR-008 Decision Details #14 already settles keeping it).

## Assumptions

The existing unit test `test_classify_error_invalid_format` (`tests/db/test_db_recovery.py:561`) already covers the classification mapping and is out of scope here. The `mock_db_cfg`/`mock_sqlite_helper` fixtures (already used by the sibling tests) require no changes, since the new test exercises the same `recover_corruption(target="rag")` call path.

## Design decisions

Place the new test immediately after `test_recover_permission_failure` so the three sibling conditions appear in `DbCondition`'s (and the dispatch tuple's) declaration order: `LOCK_CONTENTION` → `PERMISSION_FAILURE` → `INVALID_FORMAT`. Mirror the two existing sibling tests exactly (same fixtures, same mock target, same assertion shape) rather than introducing new test infrastructure or design choices.

## Alternatives considered

Writing a fixture-based test that triggers `INVALID_FORMAT` through a real "file is not a database" signal was rejected in favor of the simpler `patch(..._run_integrity_check, return_value=(DbCondition.INVALID_FORMAT, ...))` approach, which matches the established pattern of the two sibling tests and keeps the test focused on the dispatch branch rather than on constructing a corrupt DB file.

## Implementation
### Target file

`tests/db/test_db_recovery.py`

### Procedure

Add `test_recover_invalid_format(mock_db_cfg, mock_sqlite_helper)` immediately after `test_recover_permission_failure` (currently ending at line 106). Follow that function's exact structure:

1. `patch("scripts.db.recovery._run_integrity_check")` with `return_value=(DbCondition.INVALID_FORMAT, "<message>")`.
2. Call `recover_corruption(target="rag")`.
3. Assert `result.success is False`.
4. Assert `result.action == "error"`.
5. Assert `result.detail and "invalid_format" in result.detail`.

No production code changes. No new imports (the needed symbols `DbCondition`, `recover_corruption` are already imported at the top of the file).

### Method

Mirror `test_recover_lock_contention` (line 85) and `test_recover_permission_failure` (line 97):

```python
def test_recover_invalid_format(mock_db_cfg, mock_sqlite_helper):
    with patch(
        "scripts.db.recovery._run_integrity_check",
        return_value=(DbCondition.INVALID_FORMAT, "file is not a database"),
    ):
        result = recover_corruption(target="rag")

        assert result.success is False
        assert result.action == "error"
        assert result.detail and "invalid_format" in result.detail
```

The mocked `_run_integrity_check` returns `(DbCondition.INVALID_FORMAT, "...")`; `recover_corruption()` reads it at `scripts/db/recovery.py:423`, matches the tuple at lines 429-433, and returns `RecoveryResult(success=False, action="error", detail=f"{condition.value}: {detail}")` at lines 434-439, whose `detail` contains the substring `"invalid_format"`.

### Details

- Insertion point: directly after `test_recover_permission_failure` ends (line 106) and before `test_recover_no_backup` begins (line 109). Preserve the blank-line separation between functions used throughout the file.
- The message string passed to the mock is arbitrary (only `DbCondition.INVALID_FORMAT` drives the branch); `"file is not a database"` mirrors the real signal `_classify_error()` recognizes at `scripts/db/recovery.py:62-63` and is descriptive without being asserted.
- Line length stays within the 88-char limit enforced by `ruff format` (`rules/coding.md`).

## Compatibility considerations

N/A: test-only change. No public/runtime interface change; `recover_corruption()` has 5 importers (`scripts/agent/services/db_maintenance_service.py`, `scripts/agent/services/rag_maintenance_service.py`, `scripts/db/__init__.py`, plus 2 test modules) but none are affected since no production code changes.

## Security considerations

N/A: adding a unit/integration test with mocked dependencies; no secrets, credentials, or I/O touched.

## Rollback considerations

Delete the added `test_recover_invalid_format` function to fully revert. No production code is changed, so there is no runtime rollback beyond removing the test.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/db/test_db_recovery.py` | Integration (new test) | `uv run pytest tests/db/test_db_recovery.py -v` | New `test_recover_invalid_format` passes; all existing tests in the file still pass |
| Full suite | Regression | `uv run pytest -q` (once) | No new failures vs. pre-change baseline |

## Completion criteria

`tests/db/test_db_recovery.py` contains a `test_recover_invalid_format` function that follows the same structure as `test_recover_lock_contention`/`test_recover_permission_failure`, passes when run individually (`uv run pytest tests/db/test_db_recovery.py -v`), and the full suite shows no new failures (`uv run pytest -q`).

## Out of scope

Any change to `scripts/db/recovery.py` (`_classify_error()`, `DbCondition` enum, `recover_corruption()`'s dispatch), and re-litigating whether `INVALID_FORMAT` should be removed as dead code.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `test_recover_invalid_format` to `tests/db/test_db_recovery.py` | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: documentation removal is handled by the sibling implementation procedure for `docs/00_governance/governance_03_issue-and-uncertainty-management.md` |

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
- **Requirement ID**: REQ-001 (add the integration test for the `INVALID_FORMAT` dispatch branch)
- **Source issue**: issues/20260927-211353_nc021_add-missing-integration-test-for-unreachable-invalid_format-branch.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260928-152012_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260928-175052
- **Related target files**: tests/db/test_db_recovery.py
