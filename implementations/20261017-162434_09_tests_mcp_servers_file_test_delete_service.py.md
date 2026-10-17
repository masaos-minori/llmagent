## Goal

Extend `tests/mcp_servers/file/test_delete_service.py` with the cases that pin the new file-delete
guards: unconditional allowed-root protection on the non-recursive path, and post-delete verification
(REQ-006, REQ-007).

## Scope

- Add a non-recursive allowed-root rejection test.
- Add post-delete verification tests for `delete_file` and `delete_directory`.
- Add a test that a failed delete writes no dedicated audit record.
- Leave every existing test unchanged.

## Assumptions

- The existing `service` fixture returns `(svc, tmp_path)` with `tmp_path` as the only allowed root, so
  an allowed-root case can use `tmp_path` directly.
- The existing tests build request stand-ins with `type("Request", (), {...})`; new cases follow that
  style rather than importing the request models.
- The existing `pathlib.Path.rmdir` failure test raises through the `except OSError` branch before any
  verification runs, so it is unaffected.

## Design decisions

- Simulate a silent no-op delete by patching `pathlib.Path.unlink` and `shutil.rmtree` to return
  without removing anything, which is the exact condition post-delete verification exists to catch.
- Assert `FileAuthorizationError` for the allowed-root case so the widened guard is distinguished from
  the emptiness failure that previously produced `FileValidationError`.
- Use an empty allowed root for the non-recursive case, because with an empty root the only possible
  failure source is the guard.

## Alternatives considered

- Reuse the recursive allowed-root test with `recursive=False`: rejected — it would not show that the
  guard, rather than a non-empty-directory error, caused the denial.
- Assert only that some exception is raised: rejected — the two guard types have different meanings for
  callers.

## Implementation

### Target file

`tests/mcp_servers/file/test_delete_service.py`

### Procedure

1. Add a non-recursive allowed-root case next to the existing recursive one in the delete-directory
   group.
2. Add a post-delete verification group with one case per delete operation.
3. Add the no-audit-record case.

### Method

Use `patch("pathlib.Path.unlink")` and `patch("mcp_servers.file.delete_service.shutil.rmtree")` with no
side effect, so the call succeeds and the target survives, then assert the verification rejection.

### Details

- Non-recursive allowed root: `tmp_path` empty, request stand-in with `recursive=False` and
  `dry_run=False`; assert `pytest.raises(FileAuthorizationError, match="allowed root")` and that
  `tmp_path` still exists.
- `delete_file` verification: create a file, patch `pathlib.Path.unlink` to a no-op, assert
  `FileValidationError` matching `post-delete verification failed` and that the file still exists.
- `delete_directory` verification: create a directory, patch `mcp_servers.file.delete_service.shutil.rmtree`
  to a no-op with `recursive=True`, assert the same rejection and that the directory still exists.
- No-audit-record case: run the same no-op `delete_file` scenario and assert the service's
  `audit_log_path` file contains no `delete_file` line, which pins that verification runs before the
  audit write.

## Compatibility considerations

- No existing assertion is changed. `test_delete_directory_recursive_on_allowed_root_raises` and
  `test_delete_directory_os_error_raises_400` must keep passing unchanged.
- The behaviour change for non-recursive allowed-root deletes is also encoded in
  `tests/mcp_servers/file/test_file_delete_mcp_service.py`, handled by Plan row 20.

## Security considerations

N/A: test-only change; the cases assert guards are enforced rather than relaxed.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest -q tests/mcp_servers/file/test_delete_service.py`
- `uv run pytest -q tests/mcp_servers/file/`
- `uv run ruff format --check . && uv run ruff check . && uv run mypy --no-namespace-packages scripts/ && uv run lint-imports`

## Completion criteria

- The non-recursive allowed-root case passes with `FileAuthorizationError` (AC-007).
- Both post-delete verification cases pass and each asserts the target still exists (AC-006).
- The no-audit-record case passes, proving verification precedes the audit write (AC-006).
- All pre-existing tests in the file still pass.

## Out of scope

- Server-layer audit-record tests, which live in Plan row 7.
- Changes to the dedicated delete audit log format.
- Dry-run scan behaviour.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the non-recursive allowed-root case | Pending | — | — | REQ-007 |
| 2 | Add the post-delete verification and no-audit cases | Pending | — | — | REQ-006 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

## Work Items Created

- None.

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-006, REQ-007
- **Source issue**: `issues/20261017-115004_mcp006_implement-missing-guard-layers-for-high-risk-tool-categories.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261017-160222_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261017-162434
- **Related target files**: `tests/mcp_servers/file/test_delete_service.py`
