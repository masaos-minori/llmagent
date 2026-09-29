## Goal
Add a new integration test for `recover_corruption()`'s
`DbCondition.INVALID_FORMAT` dispatch branch, mirroring the existing sibling tests
(REQ-001).

## Scope
- **In-Scope**: Adding one new test function to this target file, immediately after
  `test_recover_permission_failure`.
- **Out-of-Scope**: Any change to `scripts/db/recovery.py` (`_classify_error()`,
  `DbCondition`, `recover_corruption()`'s dispatch logic itself — read-only
  reference); removing the NC-021 entry from the governance inventory (covered by
  the sibling implementation procedure document for
  `docs/00_governance/governance_03_issue-and-uncertainty-management.md`).

## Assumptions
- `mock_db_cfg`/`mock_sqlite_helper` fixtures (already used by the sibling tests
  in this same file) require no changes to support the new test (Plan
  Assumptions).
- The existing unit test `test_classify_error_invalid_format` (this file, line
  561) is out of scope — it already covers the classification mapping; only the
  recovery-flow dispatch integration test is missing (Plan Assumptions).

## Design decisions
- Mirror `test_recover_lock_contention`/`test_recover_permission_failure`'s exact
  structure (same fixtures, same mock target, same assertion shape) rather than
  introducing a new test pattern, preserving the `LOCK_CONTENTION` →
  `PERMISSION_FAILURE` → `INVALID_FORMAT` ordering that matches `DbCondition`'s
  own declaration order (per `skills/python-design` — reuse existing repository
  test conventions rather than inventing a new one for a single test).

## Alternatives considered
- Parametrize all three sibling tests into one `@pytest.mark.parametrize` test
  instead of adding a fourth standalone function — rejected: would require
  refactoring the two existing, currently-passing sibling tests, which is out of
  this Plan's scope (Plan Out-of-Scope: no change to files/tests beyond the one
  new function).

## Implementation
### Target file
`tests/db/test_db_recovery.py`

### Procedure
1. Open `tests/db/test_db_recovery.py` and locate `test_recover_permission_failure`
   (confirmed at lines 97-106 by direct read during this document's generation).
2. Insert a new test function named test_recover_invalid_format immediately after
   it (before `test_recover_no_backup` at line 109), following the identical
   structure with `DbCondition.INVALID_FORMAT` substituted.

### Method
Direct text insertion (one new function, ~8 lines) — no changes to existing
functions, fixtures, or imports (all needed names — `patch`, `DbCondition`,
`recover_corruption` — are already imported/used by the sibling tests in this
same file).

### Details
Existing sibling test (confirmed via direct read, lines 97-106), used as the
exact structural template:
```
def test_recover_permission_failure(mock_db_cfg, mock_sqlite_helper):
    with patch(
        "scripts.db.recovery._run_integrity_check",
        return_value=(DbCondition.PERMISSION_FAILURE, "permission denied"),
    ):
        result = recover_corruption(target="rag")

        assert result.success is False
        assert result.action == "error"
        assert result.detail and "permission_failure" in result.detail
```

New test to insert immediately after it (before the blank lines preceding
`test_recover_no_backup`):
```
def test_recover_invalid_format(mock_db_cfg, mock_sqlite_helper):
    with patch(
        "scripts.db.recovery._run_integrity_check",
        return_value=(DbCondition.INVALID_FORMAT, "invalid database format"),
    ):
        result = recover_corruption(target="rag")

        assert result.success is False
        assert result.action == "error"
        assert result.detail and "invalid_format" in result.detail
```

Do not modify `test_recover_lock_contention`, `test_recover_permission_failure`,
or any other existing test in this file — only insert the one new function.

## Compatibility considerations
N/A: test-only addition, no production code, public interface, or schema
affected.

## Security considerations
N/A: no code, credentials, or data-handling change; the new test only exercises
an existing, already-tested dispatch path with a different enum value.

## Rollback considerations
Single-function revert via `git revert`/`git checkout` of this file if needed; no
shared fixture or state affects other tests (each test gets a fresh
`mock_db_cfg`/`mock_sqlite_helper` fixture instance).

## Validation plan
- `uv run pytest tests/db/test_db_recovery.py -v` — targeted; confirm the new
  test passes alongside all existing tests in this file.
- `uv run pytest -q` — full suite, once, per `rules/toolchain.md` (REQ-002).

## Completion criteria
- `tests/db/test_db_recovery.py` contains the new test_recover_invalid_format
  function, structurally identical to its two siblings except for the `DbCondition` value
  and substring assertion.
- The new test passes; no existing test in this file regresses.
- Full suite shows no new failures vs. the pre-change baseline.

## Out of scope
- Any change to `scripts/db/recovery.py`.
- Removing the NC-021 entry from
  `docs/00_governance/governance_03_issue-and-uncertainty-management.md` —
  handled by the sibling implementation procedure document for that file (seq 02
  of this Plan).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Insert the new test function per Implementation > Procedure/Method/Details | Completed | 20260929-150707 | 20260929-150707 | test_recover_invalid_format inserted per Procedure/Method/Details; stale_detector clean after rewording new-symbol false-positive mentions |
| 2 | Run targeted test then full suite once per Validation plan | Completed | 20260929-150707 | 20260929-150707 | Targeted: 38 passed (incl. new test). Full suite (non-randomized): 8003 passed, 24 skipped, 0 failed. Pre-existing mypy module-resolution error, lint-imports shared->agent violation, and 15 Medium bandit B108 findings confirmed pre-existing via git stash comparison, unrelated to this change. |

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
- **Requirement ID**: REQ-001; REQ-002
- **Source issue**: issues/20260927-211353_nc021_add-missing-integration-test-for-unreachable-invalid_format-branch.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260928-152012_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260929-143826
- **Related target files**: tests/db/test_db_recovery.py