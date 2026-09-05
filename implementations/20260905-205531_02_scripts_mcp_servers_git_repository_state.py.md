## Goal

Remove `repository_state.py`'s dead/test-only `RepoValidationResult`
shim surface — the class itself, `RepositoryState.validate_repo()` (test-only,
migrated by REQ-003/the sibling row for `test_repository_state.py`),
`RepositoryState._validate_repo()`/`WriteProtectionPipeline._validate_repo()`
(dead code), their sole callers `RepositoryState._run_tool()`/
`WriteProtectionPipeline._run_tool()` (also dead — a Step 3a correction to
this Plan, see Design decisions), and the `__all__` export — so no dead
duplicate-error-type surface remains in this file (REQ-004).

## Scope

- In scope: delete `RepoValidationResult` (class), `RepositoryState.
  validate_repo()`, `RepositoryState._validate_repo()`,
  `RepositoryState._run_tool()`, `WriteProtectionPipeline._validate_repo()`,
  `WriteProtectionPipeline._run_tool()`, the `__all__` export entry, and the
  now-unused `import warnings`.
- Out of scope: `_check_repo_path()`/`_check_write()` (each class's own
  helper) — left in place, now uncalled, per this Plan's Out-of-Scope
  deferring the broader dead-method sweep to `gitcleanup`'s Plan.
  `git_service.py`'s separate `RepoValidationResult` (REQ-005, deferred to
  `gitdispatch`'s Plan).

## Assumptions

- `tests/mcp_servers/git/test_repository_state.py`'s migration (REQ-003, the
  sibling implementation procedure for that file) lands in the same change —
  its two `validate_repo()` calls must no longer reference the removed method
  by the time this file's `validate_repo()` is deleted.

## Design decisions

- **Step 3a correction (2026-09-05)**: the Plan as originally frozen listed
  only `RepoValidationResult`, `validate_repo()`, and the two `_validate_repo()`
  methods for removal. Re-verification this cycle found `RepositoryState.
  _run_tool()` (line 409) and `WriteProtectionPipeline._run_tool()` (line 754)
  each exist solely to call the `_validate_repo()` method being removed
  (`result = self._validate_repo(repo_path, tool_name)`), and each already has
  zero external callers itself (`rg -n "_run_tool\(" scripts/ tests/` — only
  the two definitions and their own internal calls). Leaving `_run_tool()` in
  place would leave it referencing an undefined attribute (a mypy failure);
  removing it alongside `_validate_repo()` is the minimal, self-consistent
  fix. The Plan document has been corrected accordingly (REQ-004, the
  `Implementation Target Files` row).
- `_check_repo_path()`/`_check_write()` are left in place rather than also
  removed: each still compiles and lints cleanly as an unused-but-defined
  private method (ruff/mypy do not flag unreferenced private methods by
  default), and their removal is explicitly `gitcleanup`'s broader
  placeholder-sweep scope per this Plan's own Out-of-Scope section — not
  re-litigated here.
- Remove `import warnings` (line 14): its only use in this file is
  `RepoValidationResult.__init__`'s `warnings.warn(...)` deprecation notice
  (line 40), which is deleted with the class; leaving the import would fail
  `ruff` (F401 unused import).

## Alternatives considered

- Leave `_run_tool()` calling `_validate_repo()` but stub `_validate_repo()`
  to return a fixed no-op value: rejected — reintroduces the exact dead-code
  duplication this row exists to remove, just under a different name.
- Also remove `_check_repo_path()`/`_check_write()` now that they lose their
  only caller: rejected — out of this row's frozen scope (`gitcleanup`'s
  Plan); removing them is a separate, broader dead-method sweep this Plan
  explicitly defers.

## Implementation

### Target file
`scripts/mcp_servers/git/repository_state.py`

### Procedure
1. Remove `import warnings` (line 14).
2. Remove the `RepoValidationResult` class and its preceding shim comment
   (lines 32–45).
3. Remove `RepositoryState._run_tool()` and `RepositoryState._validate_repo()`
   (lines 409–432).
4. Remove `WriteProtectionPipeline._run_tool()` and
   `WriteProtectionPipeline._validate_repo()` (lines 754–779).
5. Remove `"RepoValidationResult"` from the `__all__` list (line 811).

### Method
Direct deletion of each block; no replacement code. Each removed method is
either test-only (`validate_repo()`, migrated off by the sibling
`test_repository_state.py` procedure) or dead code with zero external
callers (`_validate_repo()` ×2, `_run_tool()` ×2, confirmed by `rg`).

### Details
- `import warnings` at line 14 — remove; re-run `rg -n "warnings"
  scripts/mcp_servers/git/repository_state.py` after edit and confirm zero
  matches remain.
- Lines 32–45 (re-verified 2026-09-05, current content):
  ```python
  # Local shim for legacy callers until they migrate away from RepoValidationResult.
  # New code should use RepositoryState directly.
  class RepoValidationResult:
      """Result of repo path and write guard validation."""

      error_message: str

      def __init__(self, error_message: str) -> None:
          warnings.warn(
              "RepoValidationResult is deprecated; use RepositoryState instead",
              DeprecationWarning,
              stacklevel=2,
          )
          self.error_message = error_message
  ```
  Delete this whole block; keep the surrounding blank-line spacing consistent
  with the rest of the file (two blank lines before `logger = logging.
  getLogger(__name__)`, which currently follows at line 48).
- Lines 409–432 (`RepositoryState._run_tool()` + `RepositoryState.
  _validate_repo()`):
  ```python
      def _run_tool(self, tool_name: str, repo_path: str, op):
          """Validate repo/write guards, open the repo, and run op with error wrapping."""
          result = self._validate_repo(repo_path, tool_name)
          if result.error_message:
              return result.error_message
          repo = self._open_repo(repo_path)
          return self._wrap_git_op(tool_name, lambda: op(repo))

      def _validate_repo(self, repo_path: str, tool_name: str):
          """Check repo_path and write guard; return result with error_message (empty on success)."""
          ok, err, _resolved = self._check_repo_path(repo_path)
          if not ok:
              return RepoValidationResult(error_message=err)
          if tool_name in {
              "git_add",
              "git_commit",
              "git_checkout",
              "git_pull",
              "git_push",
          }:
              ok, err = self._check_write()
              if not ok:
                  return RepoValidationResult(error_message=err)
          return RepoValidationResult(error_message="")
  ```
  Delete both methods entirely; `_open_repo()` and `_wrap_git_op()`
  (immediately above/below this block) are unaffected and keep their other
  callers.
- Lines 754–779 (`WriteProtectionPipeline._run_tool()` + `WriteProtectionPipeline.
  _validate_repo()`): same shape as above, on `WriteProtectionPipeline` —
  delete both methods entirely.
- `__all__` (currently lines 806–812): remove the `"RepoValidationResult",`
  entry (line 811), keeping `"RepositoryState"`, `"WriteProtectionPipeline"`,
  `"PipelineStage"`, `"PipelineResult"`.
- `RepositoryState.validate_repo()` (lines 235–239, test-only per REQ-003)
  is removed only after `tests/mcp_servers/git/test_repository_state.py`'s
  migration lands (sibling procedure document,
  `implementations/20260905-205531_03_tests_mcp_servers_git_test_repository_state.py.md`)
  — sequence this file's edit after that test file's edit in the same change
  set, not before.

## Compatibility considerations

- No active production caller of any removed symbol exists (confirmed via
  `rg` across `scripts/` and `tests/` this cycle). The only test caller
  (`test_repository_state.py`'s two `validate_repo()` calls) is migrated by
  the sibling procedure in the same change.
- `_check_repo_path()`/`_check_write()` remain defined but now uncalled —
  harmless, deferred to `gitcleanup`'s Plan.

## Security considerations

- N/A: removes dead validation-shim code only; the live write-protection path
  (`verify_authorization()`/`verify_preconditions()`/`verify_postcondition()`)
  is untouched by this row.

## Rollback considerations

- Single-file deletion of a self-contained dead-code cluster; `git revert`
  restores it with no data/state migration. Must be reverted together with
  the sibling `test_repository_state.py` procedure's revert if that lands
  first (their edits are sequenced, per Details above).

## Validation plan

- `uv run pytest tests/mcp_servers/git/test_repository_state.py -v` — migrated
  tests pass; no `RepoValidationResult` import remains.
- `uv run pytest tests/mcp_servers/git/ -v` (full suite) — no new failures.
- `uv run ruff check scripts/mcp_servers/git/repository_state.py` — confirms
  the removed `import warnings` does not leave an F401 finding.
- `uv run mypy scripts/mcp_servers/git/repository_state.py` — confirms no
  dangling reference to the removed `_validate_repo()`/`_run_tool()` methods
  or `RepoValidationResult` type.
- `uv run bandit -r scripts/mcp_servers/git/ -c pyproject.toml`
- `PYTHONPATH=scripts uv run lint-imports`

## Completion criteria

- `rg -n "RepoValidationResult" scripts/mcp_servers/git/repository_state.py`
  returns zero matches.
- `rg -n "_run_tool\(|_validate_repo\(" scripts/mcp_servers/git/repository_state.py`
  returns zero matches.
- `__all__` no longer lists `"RepoValidationResult"`.
- `import warnings` no longer appears in the file.
- `tests/mcp_servers/git/test_repository_state.py` passes with the migrated
  assertions.

## Out of scope

- `_check_repo_path()`/`_check_write()` removal — `gitcleanup`'s Plan.
- `git_service.py`'s `RepoValidationResult`/`GitService._validate_repo()` —
  `gitdispatch`'s Plan (REQ-005).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove `import warnings`, `RepoValidationResult` class, `validate_repo()`, both `_validate_repo()`/`_run_tool()` pairs, and the `__all__` export entry | Pending | — | — | Sequence after the `test_repository_state.py` migration lands |
| 2 | Run `tests/mcp_servers/git/test_repository_state.py` and the full git-mcp suite | Pending | — | — | |
| 3 | Run the validation sequence (ruff, mypy, bandit, lint-imports) | Pending | — | — | |

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
- **Requirement ID**: `REQ-004` — remove `repository_state.py`'s dead `RepoValidationResult` shim surface (corrected 2026-09-05 to include `_run_tool()`)
- **Source issue**: issues/20260902-144913_giterrors_consolidate_domain_errors_and_validation_results.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260904-192456_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-205531
- **Related target files**: scripts/mcp_servers/git/repository_state.py
