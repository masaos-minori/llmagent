## Goal

Close the two file-delete guard gaps in `scripts/mcp_servers/file/delete_service.py`: the allowed-root
protection is applied only on the recursive path (REQ-007), and no delete verifies that the target is
actually gone before reporting success (REQ-006).

## Scope

- Apply `_check_not_deleting_allowed_root` to both the recursive and the non-recursive
  `delete_directory` paths.
- Add post-delete verification to `delete_file` and `delete_directory`.
- Keep the dedicated delete audit log write after verification, so only verified deletions are
  recorded as deleted.

## Assumptions

- `delete_file` cannot delete an allowed root because `_require_file` already rejects a directory, so
  the widened guard belongs to `delete_directory` only.
- "The target no longer exists" is a sufficient postcondition for both unlink and rmdir/rmtree.
- The dedicated delete audit log format and path are unchanged.

## Design decisions

- Verification failures raise `FileValidationError`, matching the type the surrounding delete failures
  already raise, so "the operation did not produce the expected resulting state" has one failure mode.
- Verification runs before `_write_audit_log`, so a delete that did not take effect is never recorded
  as a successful deletion.
- The widened allowed-root guard keeps raising `FileAuthorizationError`, which is the correct type for
  an authorization refusal and is the type the recursive path already raises.

## Alternatives considered

- Compare the directory tree before and after deletion instead of checking absence: rejected — the
  postcondition the requirement states is absence of the target, and a tree comparison costs a full
  walk for every recursive delete.
- Apply the allowed-root guard only when the target is empty: rejected — the guard exists to prevent
  the root itself being removed, and emptiness is not the risk.

## Implementation

### Target file

`scripts/mcp_servers/file/delete_service.py`

### Procedure

1. Add `_verify_deleted` (new) as a staticmethod next to `_check_not_deleting_allowed_root`.
2. In `delete_directory`, move the `_check_not_deleting_allowed_root` call out of the
   `if req.recursive:` guard so it runs for both paths.
3. In `delete_file`, call the new verification helper after the unlink block and before
   `_write_audit_log`.
4. In `delete_directory`, call the new verification helper after the rmtree/rmdir block and before
   `_write_audit_log`.

### Method

Reuse the existing guard and the existing failure vocabulary; add one small verification helper. No
signature, response model, or configuration change.

### Details

- The recursive-only guard is `if req.recursive:` followed by
  `self._check_not_deleting_allowed_root(target)` at
  `scripts/mcp_servers/file/delete_service.py:183-184`; replace it with an unconditional call placed
  immediately after the `dry_run` early return in `delete_directory`.
- `_check_not_deleting_allowed_root` itself (`scripts/mcp_servers/file/delete_service.py:164-171`)
  is unchanged.
- New helper:

```
    @staticmethod
    def _verify_deleted(target: Path) -> None:
        """Raise FileValidationError if the target still exists after deletion."""
        if target.exists():
            raise FileValidationError(
                f"post-delete verification failed: {target} still exists",
            )
```

- `delete_file`: insert the call between the unlink `except` block
  (`scripts/mcp_servers/file/delete_service.py:114-119`) and
  `self._write_audit_log("delete_file", str(target))` at
  `scripts/mcp_servers/file/delete_service.py:122`.
- `delete_directory`: insert the call between the deletion `except` block
  (`scripts/mcp_servers/file/delete_service.py:192-197`) and
  `self._write_audit_log("delete_directory", str(target))` at
  `scripts/mcp_servers/file/delete_service.py:200`.

## Compatibility considerations

- Behaviour change: deleting an empty allowed root with `recursive=False` previously succeeded and now
  raises `FileAuthorizationError`. `tests/mcp_servers/file/test_file_delete_mcp_service.py` encodes the
  previous behaviour and is inverted by Plan row 20.
- `FileAuthorizationError` derives from `RuntimeError` while `FileValidationError` derives from
  `ValueError`, so callers that caught only the latter on this path now see a different type.
- `dry_run` paths are untouched: verification runs only when a mutation actually happened.

## Security considerations

- The allowed root can no longer be removed through the non-recursive path, which closes the
  command-specific guard gap the Plan records for file-delete.
- Verification messages contain a path only — no file content and no directory listing.

## Rollback considerations

N/A: revert the commit. Reverting reopens the accepted-behaviour gap, so any rollback must re-register
MCP-006 in the known-issue ledger.

## Validation plan

- `uv run pytest -q tests/mcp_servers/file/test_delete_service.py`
- `uv run pytest -q tests/mcp_servers/file/test_file_delete_mcp_service.py`
- `uv run pytest -q tests/mcp_servers/file/`
- `uv run ruff format --check . && uv run ruff check . && uv run mypy --no-namespace-packages scripts/ && uv run lint-imports`
- `uv run python tools/generate_reference_table.py --check`

## Completion criteria

- `delete_directory` on an allowed root raises `FileAuthorizationError` on both the recursive and the
  non-recursive path (AC-007).
- A delete whose target still exists afterwards raises `FileValidationError` instead of returning
  `deleted=True`, and no dedicated audit record is written for it (AC-006).
- Existing happy paths and `dry_run` behaviour in `tests/mcp_servers/file/test_delete_service.py` still
  pass.

## Out of scope

- Changes to the dedicated delete audit log format, path, or rotation.
- Applying the allowed-root guard to `delete_file`.
- Restoring the ability to remove an allowed root through any path.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the new verification helper | Completed | 20261017-182500 | 20261017-182951 | REQ-006 |
| 2 | Make the allowed-root guard unconditional in `delete_directory` | Completed | 20261017-182500 | 20261017-182951 | REQ-007 |
| 3 | Add post-delete verification to both delete paths | Completed | 20261017-182500 | 20261017-182951 | REQ-006 |
| 4 | Add or update tests per Validation plan | Completed | 20261017-190500 | 20261017-192200 | Owned by Plan rows 9 and 20 |
| 5 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261017-190500 | 20261017-192200 |  |

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
- **Related target files**: `scripts/mcp_servers/file/delete_service.py`