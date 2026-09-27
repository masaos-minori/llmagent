## Goal

Fix `ReadSecurityGuards._validate_file`'s directory branch so it does not apply the file-content byte-size limit to a directory's filesystem `stat().st_size`, fixing `tests/mcp_servers/file/test_read_security.py::TestValidateFileDirBranch::test_validates_existing_directory` (REQ-001).

## Scope

In scope: `_validate_file`'s `expected_type == "dir"` branch in `scripts/mcp_servers/file/read_security.py` only. Out of scope: the `expected_type == "file"` branch (must continue applying `_check_size_limit`) and `scripts/mcp_servers/file/common.py`'s `check_size_limit` function (confirmed already correct for the file case).

## Assumptions

- No current caller of `_validate_file(..., expected_type="dir")` depends on a meaningful directory size being returned — to be confirmed via Implementation step 1 before finalizing the exact sentinel/return-value approach.

## Design decisions

- Skip `_check_size_limit` entirely for the directory branch, returning a sentinel size (`0`) rather than restructuring `_validate_file`'s return type — minimal change, preserves the existing `tuple[Path, int]` signature.

## Alternatives considered

- Changing `_validate_file`'s return type to make the size `Path` case-conditional (e.g. `int | None`): rejected as a larger, type-signature-changing diff than necessary if no caller actually consumes a directory's returned size meaningfully (per Implementation step 1's check).

## Implementation

### Target file

`scripts/mcp_servers/file/read_security.py`

### Procedure

1. Search all callers of `_validate_file(..., expected_type="dir")` via `rg -n 'expected_type="dir"' scripts/mcp_servers/file/` to confirm none of them use the returned size for anything meaningful (adversarial verification before deciding the exact fix shape).
2. Modify `_validate_file` (lines 53-66) so the `else` branch (directory case) does not call `self._check_size_limit(target)` — return `(target, 0)` for the directory case instead, while the `if expected_type == "file":` branch continues to call `_check_size_limit` and return its real size unchanged.

### Method

Direct conditional restructuring of `_validate_file`'s final `size = ...` line — split into an `if/else` based on `expected_type`, rather than the current unconditional call after the `if/else` that only handles the `_require_file`/`_require_dir` validation.

### Details

- Before:
  ```
  if expected_type == "file":
      self._require_file(target, raw_path)
  else:
      self._require_dir(target, raw_path)
  size = self._check_size_limit(target)
  return target, size
  ```
- After:
  ```
  if expected_type == "file":
      self._require_file(target, raw_path)
      size = self._check_size_limit(target)
  else:
      self._require_dir(target, raw_path)
      size = 0
  return target, size
  ```
- Confirm via Implementation step 1's search whether any caller reads the returned size for a directory call — if one does and depends on a real value, escalate this as a Plan Gap rather than silently returning `0` (per `rules/workflow-lifecycle.md`).

## Compatibility considerations

- Any caller of `_validate_file(..., expected_type="dir")` that previously received (or crashed on) a directory's filesystem-block size will now receive `0` — confirmed via Implementation step 1 this does not break any current caller's logic.

## Security considerations

- This removes a size check for directories, but that check was never a meaningful security boundary for directories (filesystem block-count size is unrelated to actual content exposure risk) — no security regression; the file-content size limit remains fully enforced for the `expected_type == "file"` case.

## Rollback considerations

- `git revert` the commit, or manually restore the unconditional `_check_size_limit` call.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `scripts/mcp_servers/file/read_security.py` | Unit | `uv run pytest tests/mcp_servers/file/test_read_security.py -q` | All tests pass, including `TestValidateFileDirBranch::test_validates_existing_directory`; file-branch size-limit enforcement remains intact |

## Completion criteria

- `uv run pytest tests/mcp_servers/file/test_read_security.py -q` passes with no failures.
- A directory larger than `max_read_bytes` (by filesystem `stat()` accounting) is successfully validated (not rejected).
- A file larger than `max_read_bytes` still correctly raises `FileValidationError` (no regression in the file-size-limit case).

## Out of scope

- `tests/mcp_servers/file/test_read_service.py` (covered by its own implementation procedure document from this same Plan).
- `scripts/mcp_servers/file/common.py`'s `check_size_limit` function (confirmed already correct).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: existing `TestValidateFileDirBranch` test already covers this fix |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: no docs/00_index.md task-scope mapping for this file |

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
- **Requirement ID**: REQ-001: skip size-limit check for directories in `_validate_file`
- **Source issue**: issues/20260927-075249_mcp001_mcp-file-server-read-tests-size-limit-and-missing-exception.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260927-084210_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-092759
- **Related target files**: scripts/mcp_servers/file/read_security.py
