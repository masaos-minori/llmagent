## Goal
- Make the tree-building helpers symlink-excluding and limit-aware (REQ-002, symlink exclusion; REQ-003, traversal limits).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: `build_tree` (line 21), `count_tree_nodes` (line 54), `has_depth_limit` (line 96).
- Out of scope: the `rglob` traversals in `read_business.py` (seq 07); the dry-run scan walk is not in this file (Step 3a correction: `_scan_directory_for_dry_run` lives in `delete_service.py`, seq 09).

## Assumptions
- Verified in Step 3a: `build_tree` enumerates entries via `iterdir()` without symlink exclusion; the file is 100 lines and contains no dry-run scan function.
- `os.walk` does not descend directory symlinks, so the delete-side dry-run scan needs no symlink change (Plan Problem analysis); only the read traversal path carries the escape vector.

## Design decisions
- `build_tree` skips entries where `path.is_symlink()` is true before any `stat()` call, so broken links never raise.
- Node-count limit enforcement is passed into `build_tree` as the `max_tree_nodes` value from `FileReadConfig` (seq 01); the structured truncation reason is set on the response by the caller in `read_business.py` (seq 07).

## Alternatives considered
- N/A: helper-level change with no contract decision of its own.

## Implementation
### Target file
`scripts/mcp_servers/file/read_static_helpers.py`

### Procedure
1. In `build_tree`, skip symlink entries during `iterdir()` enumeration.
2. Make `count_tree_nodes` count only non-symlink entries so the node limit is measured against the same set the tree exposes.
3. Keep `has_depth_limit` semantics; depth behavior is unchanged by this Plan.

### Method
- Helper signatures gain the limit parameters needed for enforcement; no instance state is introduced (the file's contract is stateless helpers).

### Details
- `TreeNode` entries for symlinks are not created; `size` is read from `stat()` only for non-symlink entries.

## Compatibility considerations
- Tree responses lose symlink entries (REQ-002 impact, recorded in the Plan).

## Security considerations
- N/A: no secrets; symlink exclusion is the security change.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/file/test_read_service.py -v` (seq 14 covers tree-building symlink exclusion); full `rules/toolchain.md` sequence.

## Completion criteria
- `build_tree` and `count_tree_nodes` exclude symlinks; the node limit is enforced against the enumerated set; tests pass (AC-2).

## Out of Scope
- `rglob` traversals (seq 07), delete dry-run scan (seq 09).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-002` (symlink exclusion), `REQ-003` (traversal limits)
- **Source issue**: issues/20261119-140516_mcpai009_file-mcp-hardening.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-065258_mcpai009_file-mcp-hardening.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-171048
- **Related target files**: `scripts/mcp_servers/file/read_static_helpers.py`
