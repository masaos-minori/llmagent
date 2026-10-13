## Goal
- Update the exact field-set assertion for `FileReadConfig` so it includes `auth_token` once row 5 adds the field (REQ-005).

## Scope
- In: the expected set in `test_dataclass_fields`.
- Out: other tests in the file.

## Assumptions
- Row 5 adds `auth_token` to `FileReadConfig`. Until then this test would fail after the model change, so this row lands together with row 5 (Plan Step 5).
- Measured: 1 failure once the field exists (the only failure outside the 401 group).

## Design decisions
- Add `"auth_token"` to the expected set; keep the assertion exact (it documents the contract).

## Alternatives considered
N/A: the exact-set assertion is the file's existing style.

## Implementation
### Target file
`tests/mcp_servers/file/test_file_read_mcp_models.py`

### Procedure
1. Add `"auth_token"` to the expected field set (see Details).
2. Run the file's tests.

### Method
- Anchor: `test_dataclass_fields` at line 51 builds `fields` from `dataclasses.fields(FileReadConfig)` and asserts an exact set.

### Details
Row 27 edits one assertion (`test_dataclass_fields`, Before/After):

```python
# Before:
        assert fields == {
            "max_read_bytes",
            "allowed_dirs",
            "max_depth",
            "max_files_per_batch",
        }
# After:
        assert fields == {
            "max_read_bytes",
            "allowed_dirs",
            "max_depth",
            "max_files_per_batch",
            "auth_token",
        }
```

## Compatibility considerations
- Test-only; couples to row 5 (apply in the same Plan step).

## Security considerations
N/A: test code.

## Rollback considerations
- Revert together with row 5.

## Validation plan
- `uv run ruff format tests/mcp_servers/file/test_file_read_mcp_models.py` and `uv run ruff check` on it.
- `uv run pytest tests/mcp_servers/file/test_file_read_mcp_models.py -q`.

## Completion criteria
- `test_dataclass_fields` passes with the model from row 5 and fails if the field is removed.

## Out of scope
- Other model tests; the model change itself (row 5).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `auth_token` to the expected field set | Completed | — | — | Plan Step 5; with row 5 |
| 2 | Run this file's tests | Completed | — | — |  |

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
- **Requirement ID**: `REQ-005` (existing tests keep passing under authentication: the exact field-set test expects the new field)
- **Source issue**: issues/20261013-113008_mcp007_register-bearer-auth-in-shell-github-file-mcp-servers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261013-120538_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261013-123717
- **Related target files**: tests/mcp_servers/file/test_file_read_mcp_models.py