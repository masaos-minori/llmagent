## Goal
- Make the write request models inherit the shared strict base (REQ-001, strict-base inheritance), remove the `supported_extensions` field completely (REQ-006, owner decision 20261126), and reject empty edit lists and empty `old_text` at the model boundary (REQ-007, empty-edit rejection).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: `FileWriteConfig` field removal, request-model base swap, model-boundary validation for empty edits and empty `old_text`, and the test updates in `tests/mcp_servers/file/test_file_write_mcp_service.py`.
- Out of scope: the posture check removal (seq 11), the health-view removal (seq 12), the inventory removal (seq 13).

## Assumptions
- `config/file_write_mcp_server.toml` is not a target: the key is absent from the file (Plan Step 2 correction); removal touches code, posture, and tests only.
- No insertion operation is designed: empty edit lists and empty `old_text` are rejected instead (Plan Design decisions, owner approved).

## Design decisions
- Empty-list and empty-`old_text` rejection lives at the model boundary (field/model validators on `EditFileRequest` and `EditOperation`), not in the service layer, so the schema contract and the runtime contract agree (REQ-007).
- `FileWriteConfig.from_dict()` drops the `supported_extensions` parsing branch entirely; no legacy tolerance for the key.

## Alternatives considered
- Enforcing the extension control at runtime — rejected by the owner decision (remove, not enforce).

## Implementation
### Target file
`scripts/mcp_servers/file/write_models.py`

### Procedure
1. In `scripts/mcp_servers/file/write_models.py`, make the request models at lines 59, 86, 108, 129 (`WriteFileRequest`, `EditFileRequest`, `CreateDirectoryRequest`, `MoveFileRequest`) inherit the shared strict base.
2. Import the base `StrictRequestModel` from `scripts/mcp_servers/request_contract.py`.
2. Remove the `supported_extensions` field (line 30) and its `from_dict()` parsing (lines 42-44) from `FileWriteConfig`.
3. Add validators rejecting an empty `edits` list and an empty `old_text` in `EditOperation` (line 79).

### Method
- Response models stay plain `BaseModel`; only request models inherit the strict base.

### Details
- `tests/mcp_servers/file/test_file_write_mcp_service.py` line 650 constructs `FileWriteConfig` with `supported_extensions=[]` — drop the keyword in the test update.

## Compatibility considerations
- Callers sending extra request fields to write tools are now rejected (REQ-001 impact, recorded in the Plan).
- Any code reading `cfg.supported_extensions` breaks; the consumers are seq 12 (health view) and the pinned tests (seq 11, 18), all in this Plan's scope.

## Security considerations
- N/A: no secrets; the change removes a configuration contract that claimed an unenforced control.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/file/test_file_write_mcp_service.py -v` (add empty-edit and empty-`old_text` rejection cases); `uv run pytest tests/mcp_servers/file/test_file_schema_consistency.py -v` (seq 20); full `rules/toolchain.md` sequence.

## Completion criteria
- `supported_extensions` is absent from the file; empty edit lists and empty `old_text` raise validation errors; all write request models inherit the strict base; tests pass (AC-1, AC-5).

## Out of Scope
- Posture, health-view, and inventory removal (seq 11, 12, 13).

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
- **Requirement ID**: `REQ-001` (shared strict base), `REQ-006` (`supported_extensions` removal), `REQ-007` (empty-edit rejection)
- **Source issue**: issues/20261119-140516_mcpai009_file-mcp-hardening.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-065258_mcpai009_file-mcp-hardening.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-171048
- **Related target files**: `scripts/mcp_servers/file/write_models.py`
