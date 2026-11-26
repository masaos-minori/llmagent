## Goal
- Make the read traversal symlink-excluding and limit-aware, and return the structured truncation reason (REQ-002, symlink exclusion; REQ-003, traversal limits with structured reason).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: `search_files` (`rglob("*")` at line 219), the grep traversal (`sorted(base.rglob("*"))` at line 239), and the per-file byte check in `read_single_file`; structured truncation reason wiring from the seq 01 response fields.
- Out of scope: the tree-building helpers (seq 08), config fields and response fields (seq 01).

## Assumptions
- Verified in Step 3a: `rglob` lists symlink entries and follows directory symlinks, so symlink exclusion must be explicit in the traversal loop; `os.walk`-based counting elsewhere does not descend directory symlinks (Plan Step 2 verified behavior).
- Symlinks are excluded by default with no opt-in flag (Plan Design decisions, owner approved 20261126).
- Limits come from `FileReadConfig` fields added in seq 01: `max_tree_nodes=2000`, `max_scanned_files=5000`, `max_total_scan_bytes=10485760`, `traversal_deadline_sec=10.0`, per-file bytes reuses `max_read_bytes`.

## Design decisions
- Traversal loops check `p.is_symlink()` before processing an entry and skip it; directory-symlink entries are not descended, file symlinks are not enumerated or read (REQ-002).
- Each traversal records which limit stopped it and returns the structured reason from the closed vocabulary (`node_limit`, `scanned_file_limit`, `byte_limit`, `deadline`) defined in seq 01.
- The deadline is checked per entry against a monotonic start time captured at traversal entry.

## Alternatives considered
- Following symlinks with loop detection — rejected: exclusion by default is the owner-approved policy; broken links must not raise or hang.

## Implementation
### Target file
`scripts/mcp_servers/file/read_business.py`

### Procedure
1. In `search_files` (line 210), skip symlink entries during `rglob("*")` traversal, enforce `max_scanned_files`, `max_total_scan_bytes`, and `traversal_deadline_sec`, and set the structured truncation reason on `SearchFilesResponse`.
2. In the grep traversal (line 239), apply the same symlink exclusion and limits, and set the reason on `GrepFilesResponse`.
3. In `read_single_file`, keep the per-file byte limit (`max_read_bytes`) and report `byte_limit` as the truncation reason when it stops the read.

### Method
- Existing `truncated` flags stay as boolean compatibility fields; the reason field is the new source of truth.
- `max_search_results` (existing `max_files_per_batch`) keeps its current stop behavior; the new limits are additional guards.

### Details
- Broken symlinks: `is_symlink()` is true, so the entry is skipped before any `stat()` call; no exception path is needed.

## Compatibility considerations
- Callers that relied on symlink entries appearing in search/grep results lose them; this is the intended behavior change (REQ-002).
- Traversal results that previously stopped silently now carry a reason; `truncated` semantics are unchanged.

## Security considerations
- Symlink exclusion closes the escape vector where a symlink inside an allowed directory points outside it (Plan Problem analysis); path-authorization checks in `_resolve_safe` are unchanged.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/file/test_read_service.py -v` (seq 14 adds symlink-exclusion and per-limit truncation-reason cases); full `rules/toolchain.md` sequence.

## Completion criteria
- No symlink entry is enumerated or descended by the read traversals; each limit stop reports its structured reason; tests pass (AC-2).

## Out of Scope
- Tree-building helpers (seq 08), config and response field definitions (seq 01).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-002` (symlink exclusion), `REQ-003` (traversal limits with structured truncation reason)
- **Source issue**: issues/20261119-140516_mcpai009_file-mcp-hardening.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-065258_mcpai009_file-mcp-hardening.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-171048
- **Related target files**: `scripts/mcp_servers/file/read_business.py`
