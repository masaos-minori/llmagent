## Goal

Close the two file-write guard gaps in `scripts/mcp_servers/file/write_service.py`: `edit_file`
bypasses the byte limit and the atomic write path (REQ-005), and no write or move verifies the
resulting filesystem state before reporting success (REQ-004).

## Scope

- Enforce `max_write_bytes` in `edit_file`.
- Route the `edit_file` write through `_atomic_write` instead of the non-atomic `_write_content`.
- Add post-write size verification to `write_file` and `edit_file`.
- Add post-move verification to `move_file`.
- Delete `_write_content` once nothing uses it.

## Assumptions

- `self._max_write_bytes` is already available on the service instance, so no configuration change is
  needed for `edit_file`.
- Nothing outside this file calls `_write_content`; the only call site is inside `_write_if_changed`.
- A size comparison against the encoded payload is a sufficient postcondition for a write, and
  destination-present plus source-absent is a sufficient postcondition for a move.

## Design decisions

- Verification failures raise `FileValidationError`, the same type the surrounding write and move
  failures already raise, so callers see one failure mode for "the operation did not produce the
  expected resulting state".
- Verification runs after the mutation and before the response is built, so a success response always
  means the resulting state was observed.
- The expected byte count is taken from the encoded payload the service intended to write, not from
  the value the write path reports back, so the comparison is independent of the write implementation.

## Alternatives considered

- Keep `_write_content` and make it atomic: rejected — `_atomic_write` already implements tmp-file
  plus `os.replace` with cleanup and the same exception mapping, so a second atomic path would be
  duplicate logic.
- Report a verification mismatch as a warning in the response instead of raising: rejected — AC-004
  requires the failure to be reported, and a success response with an unverified result is the exact
  behaviour this requirement removes.

## Implementation

### Target file

`scripts/mcp_servers/file/write_service.py`

### Procedure

1. Add `_verify_written_size` (new) and `_verify_moved` (new) as staticmethods next to `_atomic_write`.
2. In `edit_file`, add the byte-limit check after `_apply_text_edits` and before `_write_if_changed`.
3. In `_write_if_changed`, call `_atomic_write` instead of `_write_content`.
4. In `write_file`, verify the written size after `_atomic_write`.
5. In `edit_file`, verify the written size when `applied` is true.
6. In `move_file`, verify the resulting state after `shutil.move`.
7. Delete `_write_content`.

### Method

Reuse the existing failure vocabulary and the existing atomic write path; add only two small
verification helpers. No signature, response model, or configuration change.

### Details

- Byte limit in `edit_file`: mirror the check already in `write_file`
  (`scripts/mcp_servers/file/write_service.py:125-130`) using
  `len(modified.encode("utf-8"))` and the same message shape, placed after
  `WriteFileService._apply_text_edits` (`scripts/mcp_servers/file/write_service.py:200`).
- `_write_if_changed` currently calls `WriteFileService._write_content(target, modified)` at
  `scripts/mcp_servers/file/write_service.py:116`; replace it with
  `WriteFileService._atomic_write(target, modified)`. The return value is discarded as the write size
  is verified separately by the caller.
- New helpers, placed after `_atomic_write` (`scripts/mcp_servers/file/write_service.py:137-156`):

```
    @staticmethod
    def _verify_written_size(target: Path, expected_bytes: int) -> None:
        """Raise FileValidationError if the written file is missing or the wrong size."""
        try:
            actual = target.stat().st_size
        except FileNotFoundError as e:
            raise FileValidationError(
                f"post-write verification failed: {target} does not exist",
            ) from e
        if actual != expected_bytes:
            raise FileValidationError(
                f"post-write verification failed: expected {expected_bytes} bytes, got {actual}",
            )

    @staticmethod
    def _verify_moved(src: Path, dest: Path) -> None:
        """Raise FileValidationError if the move did not produce the expected state."""
        if not dest.exists():
            raise FileValidationError(
                f"post-move verification failed: {dest} does not exist",
            )
        if src.exists():
            raise FileValidationError(
                f"post-move verification failed: {src} still exists",
            )
```

- `write_file`: call `_verify_written_size(target, size)` between
  `size = self._atomic_write(target, req.content)` (`scripts/mcp_servers/file/write_service.py:133`)
  and the response, using the pre-write `size` computed from `raw_bytes` as the expected value.
- `edit_file`: after `_write_if_changed` returns, call `_verify_written_size(target, len(modified.encode("utf-8")))`
  when `applied` is true.
- `move_file`: call `_verify_moved(src, dest)` between the `shutil.move` block
  (`scripts/mcp_servers/file/write_service.py:255-262`) and the `MoveFileResponse` return
  (`scripts/mcp_servers/file/write_service.py:264`).
- `_write_content` is `scripts/mcp_servers/file/write_service.py:86-92`; its only call site is the
  one replaced in step 3, so it is deleted with `_cleanup_tmp` retained for `_atomic_write`.

## Compatibility considerations

- `edit_file` now rejects payloads over the limit that it previously accepted, and now writes through
  a tmp file, which leaves a `.tmp_<name>` file only on failure paths that already cleaned it up.
- `dry_run` paths are untouched: verification runs only when a mutation actually happened.
- Response models and tool output formats are unchanged.

## Security considerations

- The byte limit closes the unbounded-write path on `edit_file`, which is the file-write common-guard
  gap the Plan records.
- Verification messages contain paths and byte counts only — never file content.

## Rollback considerations

N/A: revert the commit. Reverting reopens the accepted-behaviour gap, so any rollback must re-register
MCP-006 in the known-issue ledger.

## Validation plan

- `uv run pytest -q tests/mcp_servers/file/test_file_write_mcp_service.py`
- `uv run pytest -q tests/mcp_servers/file/`
- `uv run ruff format --check . && uv run ruff check . && uv run mypy --no-namespace-packages scripts/ && uv run lint-imports`
- `uv run python tools/generate_reference_table.py --check`

## Completion criteria

- `edit_file` rejects a payload over `max_write_bytes` with `FileValidationError` before any write
  (AC-005).
- `edit_file` writes through `_atomic_write`, and `_write_content` no longer exists (AC-005).
- A write whose resulting size differs from the intended payload, and a move whose destination is
  missing or whose source survives, raise `FileValidationError` instead of returning success (AC-004).
- Existing happy paths and `dry_run` behaviour in `tests/mcp_servers/file/test_file_write_mcp_service.py`
  still pass.

## Out of scope

- Changing `max_write_bytes` configuration or its default value.
- Adding hash or content-equality verification beyond size.
- Changes to `create_directory`, which already reports `created` from an existence check.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the verification helpers | Pending | — | — | REQ-004 |
| 2 | Enforce the byte limit and the atomic path in `edit_file` | Pending | — | — | REQ-005 |
| 3 | Add post-write and post-move verification calls | Pending | — | — | REQ-004 |
| 4 | Delete `_write_content` | Pending | — | — | Deletion-first |
| 5 | Add or update tests per Validation plan | Pending | — | — | Owned by Plan row 8 |
| 6 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

## Work Items Created

- None.

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-004, REQ-005
- **Source issue**: `issues/20261017-115004_mcp006_implement-missing-guard-layers-for-high-risk-tool-categories.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261017-160222_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261017-162434
- **Related target files**: `scripts/mcp_servers/file/write_service.py`
