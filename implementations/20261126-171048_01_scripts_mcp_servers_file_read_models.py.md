## Goal
- Make the read request models inherit the shared strict base (REQ-001, strict-base inheritance), add the traversal-limit config fields with the plan defaults (REQ-003, traversal limits), and add the structured truncation-reason field to traversal responses.

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: `FileReadConfig` new fields, request-model base swap, structured truncation-reason field on traversal responses.
- Out of scope: enforcement in the traversal code (seq 07, 08), tool schema generation (seq 02).

## Assumptions
- Plan-proposed defaults approved by the owner (20261126): `max_tree_nodes` (new) = 2000, `max_scanned_files` (new) = 5000, `max_total_scan_bytes` (new) = 10485760, `traversal_deadline_sec` (new) = 10.0; per-file bytes reuses the existing `max_read_bytes`.
- The new limits add no posture checks (Plan Assumptions), so no inventory change beyond seq 13's `supported_extensions` removal.

## Design decisions
- The truncation reason is a structured response field with a closed vocabulary — `node_limit` (new), `scanned_file_limit` (new), `byte_limit` (new), `deadline` (new) — so callers can distinguish "stopped by limit" from "complete" (REQ-003).
- Config fields are parsed through the existing `get_typed` pattern in `from_dict()`; defaults are the plan values above.

## Alternatives considered
- Silent stop without a reason field — rejected by the Plan (REQ-003 requires a structured reason).

## Implementation
### Target file
`scripts/mcp_servers/file/read_models.py`

### Procedure
1. In `scripts/mcp_servers/file/read_models.py`, make the request models at lines 70, 83, 112 (`ListDirectoryRequest`, `DirectoryTreeRequest`, `ReadTextFileRequest`) and `SearchFilesRequest`, `GrepFilesRequest`, `GetFileInfoRequest` inherit the shared strict base.
2. Import the base `StrictRequestModel` from `scripts/mcp_servers/request_contract.py`.
3. Add `max_tree_nodes` (new), `max_scanned_files` (new), `max_total_scan_bytes` (new), `traversal_deadline_sec` (new) to `FileReadConfig` (line 25) with the plan defaults and `from_dict()` parsing.
4. Add the structured truncation-reason field to `DirectoryTreeResponse`, `SearchFilesResponse`, `GrepFilesResponse`.

### Method
- Keep existing per-request validators (e.g. head/tail exclusivity) unchanged.
- Existing `truncated` flags stay; the reason field is additive so current callers keep working.

### Details
- Only request models inherit the strict base; response models are not request models and stay plain `BaseModel`.

## Compatibility considerations
- Extra request fields are rejected for read tools after the base swap (REQ-001 compatibility impact recorded in the Plan); this is the point of the change.

## Security considerations
- N/A: no secrets; the change is validation-boundary hardening.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/file/test_file_read_mcp_models.py -v`; the schema-consistency tests in seq 20 pin the strict base; then the `rules/toolchain.md` sequence.

## Completion criteria
- All read request models inherit the strict base, the four config fields exist with the plan defaults, traversal responses carry the truncation-reason field, and the tests pass (AC-1, AC-2).

## Out of Scope
- Traversal enforcement logic (seq 07, 08) and tool schema generation (seq 02).

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
- **Requirement ID**: `REQ-001` (shared strict base for file request models), `REQ-003` (traversal limits with structured truncation reason)
- **Source issue**: issues/20261119-140516_mcpai009_file-mcp-hardening.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-065258_mcpai009_file-mcp-hardening.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-171048
- **Related target files**: `scripts/mcp_servers/file/read_models.py`
