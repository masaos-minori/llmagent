## Goal

`REQ-004`: add success/failure regression coverage for the three new postcondition
checks in `format_checkout()`/`format_pull()`/`format_push()`, and fix five existing
tests that would otherwise be broken by the new checks due to unconfigured `MagicMock`
attributes.

## Scope

- **In-Scope**: fix `test_create_branch_checks_out_new_head`,
  `test_existing_branch_uses_git_checkout` (`TestFormatCheckout`),
  `test_real_pull_without_branch`, `test_real_pull_with_branch`,
  `test_empty_pull_result_reports_up_to_date` (`TestFormatPull`) to explicitly
  configure the `MagicMock` attributes the new checks read; add new success/failure
  tests for each of the three checks.
- **Out-of-Scope**: `TestFormatPush`'s existing tests — confirmed unaffected (string-
  content comparisons only, no new-check-relevant `MagicMock` attribute involved).

## Assumptions

- **Critical finding (adversarial review of the source Plan)**: confirmed via Read
  (`tests/mcp_servers/git/test_format_output.py:298-369`) that:
  - `test_create_branch_checks_out_new_head` and `test_existing_branch_uses_git_checkout`
    use `repo = MagicMock()` without setting `repo.active_branch.name` or
    `repo.head.is_detached` — once `format_checkout()` adds `if
    repo.active_branch.name != req.branch or repo.head.is_detached: raise
    GitServiceError(...)`, both tests would raise, since an unconfigured
    `MagicMock().active_branch.name` never equals the literal string `req.branch`, and
    an unconfigured `MagicMock().head.is_detached` is itself a truthy `MagicMock`
    instance.
  - `test_real_pull_without_branch`, `test_real_pull_with_branch`, and
    `test_empty_pull_result_reports_up_to_date` do not set
    `repo.index.unmerged_blobs.return_value` — once `format_pull()` adds `if
    repo.index.unmerged_blobs(): raise GitServiceError(...)`, all three would raise,
    since an unconfigured `MagicMock()` call return value is itself truthy.
  - `TestFormatPush`'s four existing tests only assert on the returned string content
    (`"push output"`, `"[DRY RUN] ..."`, the default message) — none of these strings
    contain a rejection marker (`"[rejected]"`, `"non-fast-forward"`, `"failed to
    push"`), so `format_push()`'s new check does not alter their behavior; confirmed no
    fix needed for this class.
  - This document depends on the companion `format_output.py` implementation procedure
    document (REQ-001/002/003) landing first.

## Design decisions

- For the two `TestFormatCheckout` fixes: set `repo.head.is_detached = False`
  explicitly in both tests; for `test_create_branch_checks_out_new_head`, set
  `new_branch.name = "new-feat"` (matching `req.branch`) so
  `repo.active_branch.name`... — confirm during implementation whether
  `repo.create_head.return_value` (`new_branch`) is what `format_checkout()` reads as
  `repo.active_branch` after calling `.checkout()`, or whether `repo.active_branch`
  must be separately set to a `MagicMock` with `.name = "new-feat"` (GitPython's real
  behavior is that `new_branch.checkout()` changes `repo.active_branch`, but a
  `MagicMock`'s `repo.active_branch` is not automatically linked to
  `repo.create_head.return_value`'s `.checkout()` call — so `repo.active_branch.name`
  must be explicitly set to `"new-feat"` in the test, independent of `new_branch`).
  For `test_existing_branch_uses_git_checkout`, set `repo.active_branch.name = "main"`
  (matching `req.branch="main"`).
- For the three `TestFormatPull` fixes: add `repo.index.unmerged_blobs.return_value =
  []` to each test's setup.
- New tests: `test_checkout_postcondition_failure_wrong_branch`,
  `test_checkout_postcondition_failure_detached_head`,
  `test_pull_postcondition_failure_unresolved_conflicts`,
  `test_push_postcondition_failure_rejection_marker_in_output` — each configures the
  mock to trigger the new check's failure branch and asserts `pytest.raises
  (GitServiceError, match=...)`.
- New success-path tests are largely already covered by the five fixed existing tests
  (once corrected, they exercise the success path of the new checks) — add one
  additional explicit success test only for `format_push()` (since no existing test
  currently exercises the new rejection-marker check's pass-through path with a
  non-empty, non-rejecting result string beyond `"push output"`, which already covers
  it — confirm no additional test is actually needed here beyond the fix, per Design's
  minimal-test-addition principle).

## Alternatives considered

- Leaving the five existing tests broken and simply noting the expected failures:
  rejected — per the source Plan's own AC-04 ("正常系...で従来通りの成功メッセージが
  返ることを確認できる（回帰防止）"), these tests exist specifically to lock the happy
  path; letting them break would violate the Plan's own stated regression-safety goal.

## Implementation

### Target file
`tests/mcp_servers/git/test_format_output.py`

### Procedure
1. Fix `test_create_branch_checks_out_new_head` (lines 298-308): add
   `repo.active_branch.name = "new-feat"` and `repo.head.is_detached = False`.
2. Fix `test_existing_branch_uses_git_checkout` (lines 310-317): add
   `repo.active_branch.name = "main"` and `repo.head.is_detached = False`.
3. Fix `test_real_pull_without_branch`, `test_real_pull_with_branch`,
   `test_empty_pull_result_reports_up_to_date` (lines 343-369): add
   `repo.index.unmerged_blobs.return_value = []` to each.
4. Add `test_checkout_postcondition_failure_wrong_branch`: `repo = MagicMock();
   repo.active_branch.name = "other-branch"; repo.head.is_detached = False`; assert
   `pytest.raises(GitServiceError)` on `format_checkout(repo, req)` with
   `req.branch="main"`.
5. Add `test_checkout_postcondition_failure_detached_head`: `repo.active_branch.name =
   "main"; repo.head.is_detached = True`; assert `pytest.raises(GitServiceError)`.
6. Add `test_pull_postcondition_failure_unresolved_conflicts`: `repo.index.
   unmerged_blobs.return_value = ["conflicted_file.py"]`; assert
   `pytest.raises(GitServiceError)`.
7. Add `test_push_postcondition_failure_rejection_marker_in_output`: `repo.git.push.
   return_value = "! [rejected] main -> main (non-fast-forward)"`; assert
   `pytest.raises(GitServiceError)`.
8. Import `GitServiceError` and `pytest` at the top of the file if not already present
   (confirm via `rg "^import pytest|GitServiceError" tests/mcp_servers/git/
   test_format_output.py` before adding).

### Method
Four existing-test fixes (adding missing `MagicMock` attribute configuration) plus
four new failure-path tests, one per postcondition check plus the detached-HEAD
variant of the checkout check.

### Details
- Do not modify `TestFormatPush`'s four existing tests (confirmed unaffected).
- Do not modify any test in `TestFormatStatus`, `TestFormatLog`, `TestFormatDiff`,
  `TestFormatBranch`, `TestFormatShow`, `TestFormatAdd`, `TestFormatCommit`.

## Compatibility considerations

N/A: test-only changes.

## Security considerations

N/A: no security-relevant logic in this file; these tests verify the security-relevant
behavior implemented in the companion `format_output.py` document.

## Rollback considerations

- Revert the five fixed tests to their prior (broken-under-the-new-checks) form and
  remove the four new tests; only meaningful in conjunction with reverting the
  companion `format_output.py` document's changes.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/mcp_servers/git/test_format_output.py` | Unit | `PYTHONPATH=scripts uv run pytest tests/mcp_servers/git/test_format_output.py -v` | All existing tests pass (including the 5 fixed ones); all 4 new failure-path tests pass |
| Repository-wide | Full suite | `PYTHONPATH=scripts uv run pytest` | No new failures |

## Completion criteria

- The 5 identified existing tests are fixed and pass under the new postcondition
  checks.
- 4 new tests cover each postcondition check's failure path.
- `TestFormatPush`'s existing tests remain unmodified and passing.

## Out of scope

- `scripts/mcp_servers/git/format_output.py`'s implementation — see the companion
  implementation procedure document for REQ-001/002/003.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Fix `TestFormatCheckout`'s 2 existing tests (missing `active_branch.name`/`head.is_detached`) | Pending | — | — | Per adversarial-review finding, user-approved |
| 2 | Fix `TestFormatPull`'s 3 existing tests (missing `unmerged_blobs.return_value`) | Pending | — | — | Per adversarial-review finding, user-approved |
| 3 | Add 4 new postcondition-failure tests | Pending | — | — | |
| 4 | Run the validation sequence (`rules/toolchain.md`) scoped to this file | Pending | — | — | Apply only after the companion `format_output.py` document lands |
| 5 | Documentation update | N/A | — | — | Not in scope for this file |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| Assumption | コンパニオン `format_output.py` の実装（REQ-001/002/003）が完了していないため、既存テストの修正と新規テスト追加が実行不可。手順書の前提と実際のコードに依存関係あり。 | No | 2026-08-25 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-004` — add postcondition regression tests, fix existing tests broken by the new checks
- **Source issue**: `issues/20260823_git_postcondition_verification_issue.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260825-134130_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260825-182037
- **Related target files**: `tests/mcp_servers/git/test_format_output.py`
