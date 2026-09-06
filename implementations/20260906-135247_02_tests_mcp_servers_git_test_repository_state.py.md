## Goal
Remove `TestBackwardCompatShims` — the only test coverage exercising the dead
`RepositoryState.open_repo`/`.wrap_git_op`/`.run_tool` trio the sibling document (seq
01) deletes from `scripts/mcp_servers/git/repository_state.py` (REQ-002, REQ-003).

## Scope
- In scope: delete the `TestBackwardCompatShims` class and its section-header comment
  (lines 228-254) from `tests/mcp_servers/git/test_repository_state.py`.
- Out of scope: every other class in this file (`TestSnapshotCapture`,
  `TestGuardDelegation`, `TestPipelineOrdering`,
  `TestVerifyPreconditionsDryRunAndDetachedHead`, `TestGuardIntegration`,
  `TestAuditLogVerification`, `TestPostconditionChecks`, `TestResolveRemoteUrl`,
  `TestRedactRemoteUrl`, `TestGetRepoLock`, `TestHeadIdentityRecheck`,
  `TestProtectedBranchCheck`, `TestRefValidValidation`, `TestStage3Authorization`) —
  none reference the deleted trio (confirmed in the sibling document's Method).

## Assumptions
- This document's removal lands in the same implementation cycle as the sibling
  document (seq 01)'s production-code removal — removing this class first (before the
  production methods) would leave the test suite unaffected either way (the class
  would simply keep testing methods that still exist), but removing the production
  methods first without this change would break test collection with `AttributeError`.
  Recommended order: this document's removal, then seq 01's, then run the full
  `tests/mcp_servers/git/` suite once both land.

## Design decisions
- Delete the whole class rather than individual test methods — all three tests
  (`test_open_repo_shim`, `test_wrap_git_op_shim`, `test_run_tool_shim`) exist solely
  to exercise the dead trio; none tests any other behavior worth preserving under a
  different name.
- Remove the `# ── Backward-compat shim tests ──` section-header comment (line 228)
  along with the class — an orphaned section header with no class beneath it would be
  confusing to a future reader.

## Alternatives considered
- Keep the tests but mark them `@pytest.mark.skip`: rejected — the methods they test
  are being deleted entirely, not deprecated; a skipped test for a nonexistent method
  is dead weight, not a safety net.

## Implementation
### Target file
`tests/mcp_servers/git/test_repository_state.py`

### Procedure
1. Delete lines 228-254: the `# ── Backward-compat shim tests ──` comment header, the
   blank lines immediately around it, and the full `class TestBackwardCompatShims:`
   body (`test_open_repo_shim`, `test_wrap_git_op_shim`, `test_run_tool_shim`).
2. Confirm the file transitions cleanly from `TestGuardDelegation`'s last test
   (`test_legacy_validate_repo_delegates`, ending at line 225) directly to the
   `# ── Pipeline ordering tests ──` section header and `class TestPipelineOrdering:`
   (currently starting at line 256/259) with normal two-blank-line spacing, matching
   the file's existing class-separation convention elsewhere.

### Method
Confirmed via `rg` this cycle (2026-09-06) that `state.open_repo(`, `state.wrap_git_op(`,
and `state.run_tool(` appear only within this class (lines 234, 243, 252) — no other
class in this file, and no file elsewhere in `tests/` or `scripts/`, references them
(see sibling document seq 01's Method for the full cross-repository sweep).

### Details
No other test in this file imports or depends on `TestBackwardCompatShims`'s contents
— each test class in this file is self-contained per its own fixtures
(`working_repo`/`bare_repo`, module-level).

## Compatibility considerations
Purely a test-file change; no production behavior is affected. Test count for this
file drops by exactly 3 (100 → 97 collected items in this file, matching the 3 deleted
`test_*` functions).

## Security considerations
N/A: no security-relevant behavior in this test-only change.

## Rollback considerations
Revert via `git checkout` on this file alone if removing it surfaces an unexpected
dependency; low risk per Method's confirmed zero cross-class/cross-file coupling.

## Validation plan
- `uv run pytest tests/mcp_servers/git/test_repository_state.py -v` — 97 tests
  collected (100 minus the 3 deleted), all passing.
- `uv run pytest tests/mcp_servers/git/ -v` (full suite, run together with sibling
  document seq 01's production removal in the same cycle) — no failures.
- `uv run ruff check tests/mcp_servers/git/test_repository_state.py`.

## Completion criteria
- `TestBackwardCompatShims` no longer exists in the file.
- `rg -n "TestBackwardCompatShims|open_repo_shim|wrap_git_op_shim|run_tool_shim" tests/mcp_servers/git/test_repository_state.py`
  returns no matches.
- Full git-mcp test suite passes with no new failure once this document and the
  sibling document (seq 01) have both landed.

## Out of scope
- The production-code removal itself — tracked in the sibling document, seq 01.
- Any other test file — none reference the deleted trio (confirmed in seq 01's
  Method).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-002, REQ-003 (test coverage accompanying the production removal)
- **Source issue**: issues/20260902-144914_gitcleanup_remove_placeholders_and_align_docs_with_verified_implementation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-192746_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260906-135247
- **Related target files**: tests/mcp_servers/git/test_repository_state.py
