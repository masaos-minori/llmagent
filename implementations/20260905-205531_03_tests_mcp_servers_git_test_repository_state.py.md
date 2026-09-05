## Goal

Remove `tests/mcp_servers/git/test_repository_state.py`'s remaining
dependence on the deprecated `RepoValidationResult` shim ahead of its removal
from `repository_state.py` (REQ-003, REQ-007): migrate the 2 test-only
`RepositoryState.validate_repo()` callers to assert `RepositoryState`'s own
fields directly, and remove the 2 tests that assert on the
`RepoValidationResult` class itself (nothing left to test once REQ-004
deletes the class).

## Scope

- In scope: `TestRepositoryStateGuards.test_validate_repo_delegates_to_state`
  and `test_legacy_validate_repo_delegates` (rewrite to assert
  `RepositoryState` fields directly, dropping the inline
  `RepoValidationResult` import and `isinstance` check); `TestBackwardCompat
  Shims.test_repo_validation_result_shim_exists` and
  `test_repo_validation_result_shim_requires_error_message` (remove
  entirely — Step 3a correction, 2026-09-05: these were missed by the Plan's
  original Background investigation, which counted only the `validate_repo()`
  call sites).
- Out of scope: `TestBackwardCompatShims.test_open_repo_shim`,
  `test_wrap_git_op_shim`, `test_run_tool_shim` — these test the **public**
  `RepositoryState.open_repo()`/`wrap_git_op()`/`run_tool()` shims (lines
  241, 245, 253 of `repository_state.py`), which are distinct methods from
  the **private** `_open_repo()`/`_wrap_git_op()`/`_run_tool()` this Plan
  removes (REQ-004) — confirmed by reading both method bodies this cycle:
  the public `run_tool()` takes an optional `validate_repo_fn` parameter and
  never calls `self._validate_repo()`. Not touched by this row.

## Assumptions

- `repository_state.py`'s edit (the sibling procedure,
  `implementations/20260905-205531_02_scripts_mcp_servers_git_repository_state.py.md`)
  lands together with this file's edit in the same change — this file's
  migration must complete before (or in the same commit as) `RepoValidationResult`
  is deleted, or the two calls this file still makes would break.

## Design decisions

- Replace the two `validate_repo()`-based tests' assertions with direct
  `RepositoryState.snapshot()` field checks rather than deleting them: the
  shim always returns `RepoValidationResult(error_message="")` unconditionally
  (confirmed by reading `validate_repo()`'s body — it never actually inspects
  `repo_path`/`tool_name`), so the tests were already only nominally exercising
  "delegation"; asserting on the snapshot's own fields (e.g. `state.path`,
  `state.ref_valid`) preserves the original intent — confirming a valid
  working repo's guard-relevant properties — without the shim.
- Remove (not migrate) the two `TestBackwardCompatShims` tests that assert on
  `RepoValidationResult` directly: once REQ-004 deletes the class, there is no
  equivalent behavior to assert — a migrated test would be testing nothing.

## Alternatives considered

- Keep the two `RepoValidationResult`-existence tests but change them to
  assert the class does *not* exist (`with pytest.raises(ImportError)`):
  rejected — the codebase convention for removed shims is to delete the test
  along with the code it tested, not add a negative-existence test (no
  precedent for that pattern elsewhere in this test suite).

## Implementation

### Target file
`tests/mcp_servers/git/test_repository_state.py`

### Procedure
1. Rewrite `test_validate_repo_delegates_to_state` (line 159) and
   `test_legacy_validate_repo_delegates` (line 216) to call
   `RepositoryState.snapshot(working_repo)` and assert directly on its own
   fields, dropping the inline `RepoValidationResult` import and
   `isinstance` assertion.
2. Delete `test_repo_validation_result_shim_exists` (line 251) and
   `test_repo_validation_result_shim_requires_error_message` (line 256) from
   `TestBackwardCompatShims`.
3. Confirm no remaining `RepoValidationResult` reference in this file.

### Method
Direct in-place rewrite of 2 test bodies; direct deletion of 2 other test
methods. No fixture or import-block change beyond removing the now-unused
inline `RepoValidationResult` imports (each was imported locally inside its
own test function, not at module level, so no module-level import line needs
touching).

### Details
- Lines 159–164 (current content):
  ```python
      def test_validate_repo_delegates_to_state(self, working_repo: str) -> None:
          state = RepositoryState.snapshot(working_repo)
          result = state.validate_repo(working_repo, "git_test")
          from mcp_servers.git.repository_state import RepoValidationResult

          assert isinstance(result, RepoValidationResult)
  ```
  Rewrite to assert on `state`'s own fields directly, e.g.:
  ```python
      def test_validate_repo_delegates_to_state(self, working_repo: str) -> None:
          state = RepositoryState.snapshot(working_repo)
          assert state.path == working_repo
          assert state.ref_valid is True
  ```
- Lines 216–221 (current content, near-identical body under a "legacy" name):
  ```python
      def test_legacy_validate_repo_delegates(self, working_repo: str) -> None:
          state = RepositoryState.snapshot(working_repo)
          result = state.validate_repo(working_repo, "git_test")
          from mcp_servers.git.repository_state import RepoValidationResult

          assert isinstance(result, RepoValidationResult)
  ```
  Apply the same rewrite pattern as above (or, if the two tests are
  confirmed exact duplicates after rewriting, keep both — this file's other
  `test_legacy_*`/`test_*_delegates` pairs follow the same one-current/
  one-legacy-name convention throughout the class, so removing one would be
  inconsistent with the surrounding test naming pattern; do not remove either
  as part of this row).
- Lines 251–261 (current content, `TestBackwardCompatShims`):
  ```python
      def test_repo_validation_result_shim_exists(self) -> None:
          from mcp_servers.git.repository_state import RepoValidationResult

          assert RepoValidationResult is not None

      def test_repo_validation_result_shim_requires_error_message(self) -> None:
          from mcp_servers.git.repository_state import RepoValidationResult

          with pytest.warns(DeprecationWarning):
              result = RepoValidationResult(error_message="")
          assert result.error_message == ""
  ```
  Delete both methods entirely, keeping `test_open_repo_shim`,
  `test_wrap_git_op_shim`, and `test_run_tool_shim` (out of scope, see Scope
  above) in place.
- After both edits, confirm `rg -n "RepoValidationResult"
  tests/mcp_servers/git/test_repository_state.py` returns zero matches.

## Compatibility considerations

- N/A: test-only file; no external caller depends on its contents.

## Security considerations

- N/A: no security-relevant behavior in this test file's changes.

## Rollback considerations

- Test-only change; `git revert` restores prior test bodies with no data or
  state migration. Must be reverted together with `repository_state.py`'s
  removal if that lands first (their edits are sequenced together, per
  Assumptions above).

## Validation plan

- `uv run pytest tests/mcp_servers/git/test_repository_state.py -v` — all
  tests pass, including the 2 rewritten tests and the reduced
  `TestBackwardCompatShims` (now 3 tests instead of 5).
- `rg -n "RepoValidationResult" tests/mcp_servers/git/test_repository_state.py`
  — zero matches.
- `uv run ruff check tests/mcp_servers/git/test_repository_state.py`
- `uv run mypy tests/mcp_servers/git/test_repository_state.py`

## Completion criteria

- The 2 `validate_repo()`-based tests assert `RepositoryState`'s own fields
  directly, with no `RepoValidationResult` reference remaining.
- `TestBackwardCompatShims` no longer contains
  `test_repo_validation_result_shim_exists` or
  `test_repo_validation_result_shim_requires_error_message`.
- Full file passes `uv run pytest tests/mcp_servers/git/test_repository_state.py -v`.

## Out of scope

- `TestBackwardCompatShims.test_open_repo_shim` / `test_wrap_git_op_shim` /
  `test_run_tool_shim` — test the public shims, unaffected by this Plan.
- `repository_state.py`'s own removal of `RepoValidationResult` /
  `validate_repo()` / `_validate_repo()` / `_run_tool()` — sibling procedure
  document (row 2).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite the 2 `validate_repo()`-based tests to assert `RepositoryState` fields directly | Pending | — | — | |
| 2 | Delete the 2 `RepoValidationResult`-existence tests in `TestBackwardCompatShims` | Pending | — | — | |
| 3 | Run this file's test suite and confirm zero remaining `RepoValidationResult` references | Pending | — | — | |

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
- **Requirement ID**: `REQ-003`, `REQ-007` — migrate test-only `validate_repo()` callers and drop `RepoValidationResult` imports (corrected 2026-09-05 to also cover the 2 `TestBackwardCompatShims` tests)
- **Source issue**: issues/20260902-144913_giterrors_consolidate_domain_errors_and_validation_results.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-192456_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-205531
- **Related target files**: tests/mcp_servers/git/test_repository_state.py
