## Goal

Update the characterization test in `tests/mcp_servers/file/test_file_delete_mcp_service.py` that
records the previously accepted behaviour: deleting the allowed root through the non-recursive path was
not blocked by the guard. After the guard is widened, that behaviour is a denial (REQ-007).

## Scope

- Rename `test_non_recursive_root_directory_not_blocked_by_guard` to
  `test_non_recursive_root_directory_blocked_by_guard` (new).
- Invert its expectation from `FileValidationError` to `FileAuthorizationError`.
- Make the case discriminating by deleting the subdirectory that made the root non-empty.
- Leave the neighbouring recursive-guard and subdir-success tests unchanged.

## Assumptions

- The test builds its own `DeleteFileService` with `allowed_dirs=[tmp_path]`, so it does not depend on
  the module's `service` fixture.
- With an empty allowed root, the only possible failure on the non-recursive path is the guard: without
  the guard `rmdir` would succeed.
- `FileAuthorizationError` derives from `RuntimeError` and `FileValidationError` from `ValueError`, so
  the two expectations are not interchangeable.

## Design decisions

- Remove the `(tmp_path / "subdir").mkdir()` setup: with the subdirectory present, the old test could
  have been passing because of the non-empty-directory error rather than because the guard was absent.
  An empty root pins the guard itself.
- Match on `allowed root` in the exception message, mirroring the recursive-guard test directly above it.

## Alternatives considered

- Keep the subdirectory and only change the expected exception type: rejected — the test would still not
  distinguish the guard from the emptiness failure.
- Delete the test: rejected — it is the only test in this file that names the non-recursive path, and the
  inversion is what records the closed gap.

## Implementation

### Target file

`tests/mcp_servers/file/test_file_delete_mcp_service.py`

### Procedure

1. Rename the test method.
2. Replace the `FileValidationError` import inside the method with `FileAuthorizationError`.
3. Delete the subdirectory creation line.
4. Change the `pytest.raises` call to expect `FileAuthorizationError` with `match="allowed root"`.
5. Add an assertion that `tmp_path` still exists after the denial.

### Method

Keep the method's existing structure: build a service with `allowed_dirs=[tmp_path]`, build a
`DeleteDirectoryRequest` for `tmp_path` with `recursive=False`, and assert the raise.

### Details

- The test to change is `test_non_recursive_root_directory_not_blocked_by_guard` at
  `tests/mcp_servers/file/test_file_delete_mcp_service.py:259-271`.
- The neighbouring `test_recursive_delete_of_allowed_root_raises_auth_error` at
  `tests/mcp_servers/file/test_file_delete_mcp_service.py:233-246` and
  `test_recursive_delete_of_subdir_succeeds` stay exactly as written.
- After the change the two tests assert the same guard on both paths, which is the pair the Plan records
  as AC-007.

## Compatibility considerations

- This test is the only known test that encodes the old accepted behaviour for the non-recursive path;
  the change is intentional and is the observable half of the behaviour change.
- The file's dry-run and subdir-success tests are unaffected because they never target the allowed root.

## Security considerations

N/A: test-only change; the case asserts the guard denies.

## Rollback considerations

N/A: revert the commit. Reverting restores the accepted behaviour, so any rollback must re-register
MCP-006 in the known-issue ledger.

## Validation plan

- `uv run pytest -q tests/mcp_servers/file/test_file_delete_mcp_service.py`
- `uv run pytest -q tests/mcp_servers/file/`
- `uv run ruff format --check . && uv run ruff check . && uv run mypy --no-namespace-packages scripts/ && uv run lint-imports`

## Completion criteria

- The renamed test passes with `FileAuthorizationError` matching `allowed root` (AC-007).
- The allowed root still exists after the denial.
- The recursive-guard and subdir-success tests still pass unchanged.

## Out of scope

- Post-delete verification tests, which live in Plan row 9.
- Server-layer audit-record tests, which live in Plan row 7.
- Any change to `DeleteFileService` itself, which is Plan row 5.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rename and invert the characterization test | Pending | — | — | REQ-007 |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

## Work Items Created

- None.

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-007
- **Source issue**: `issues/20261017-115004_mcp006_implement-missing-guard-layers-for-high-risk-tool-categories.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261017-160222_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261017-162434
- **Related target files**: `tests/mcp_servers/file/test_file_delete_mcp_service.py`
