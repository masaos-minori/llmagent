## Goal
- Align the delete request models with the shared strict base (REQ-001, strict-base inheritance) — base swap only, behavior already `extra="forbid"`.

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: `DeleteFileRequest` (line 74) and `DeleteDirectoryRequest` (line 93) base swap.
- Out of scope: schema generation (seq 06).

## Assumptions
- Verified in Step 3a: `ConfigDict(extra="forbid")` confirmed at lines 74, 93; the swap is behavior-preserving.

## Design decisions
- Replace the per-model `model_config = ConfigDict(extra="forbid")` with inheritance from `StrictRequestModel` (`scripts/mcp_servers/request_contract.py`, line 34), keeping `PathMixin` as the first base so the path validator stays.

## Alternatives considered
- N/A: base swap only; no behavior change.

## Implementation
### Target file
`scripts/mcp_servers/file/delete_models.py`

### Procedure
1. Make `DeleteFileRequest` and `DeleteDirectoryRequest` inherit `StrictRequestModel` (via `PathMixin, StrictRequestModel`) and remove the local `ConfigDict` declarations.

### Method
- N/A: mechanical swap; the shared base carries the same `extra="forbid"` config.

### Details
- `PathMixin`'s absolute-path validator is unchanged.

## Compatibility considerations
- N/A: delete tools already forbade extra fields (Plan Design decisions); no caller impact.

## Security considerations
- N/A: no secrets.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/file/test_call_tool_validation.py -v`; `uv run pytest tests/mcp_servers/file/test_file_schema_consistency.py -v` (seq 20); full `rules/toolchain.md` sequence.

## Completion criteria
- Both delete request models inherit the shared strict base with identical validation behavior; tests pass (AC-1).

## Out of Scope
- Tool schema generation (seq 06).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261126-175917 | 20261126-175917 | PathMixin, StrictRequestModel bases for DeleteFileRequest and DeleteDirectoryRequest; local ConfigDict declarations and import removed; docstring dependency line added. Files: scripts/mcp_servers/file/delete_models.py |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261126-201535 | 20261126-201535 | ruff/mypy/lint-imports/module-size/reference-table pass; targeted tests 11 passed, 3 failed with AttributeError on FileWriteConfig.supported_extensions — known pending failure from seq 03's field removal, owned by seq 12 (health view), expected until it lands per plan-batch rule; full-suite run deferred to end of batch; Step 5/6: N/A: no docs/00_index.md task-scope mapping for scripts/mcp_servers/file/delete_models.py End-of-batch full-suite run passed (15774 passed, 5 skipped), resolving the pending supported_extensions failures noted here; diff-cover 100% on changed lines; gates pass. Intermittent flaky failures in 3 unrelated tests under -n logical, all pass serially. |

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
- **Requirement ID**: `REQ-001` (shared strict base for file request models)
- **Source issue**: issues/20261119-140516_mcpai009_file-mcp-hardening.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-065258_mcpai009_file-mcp-hardening.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-171048
- **Related target files**: `scripts/mcp_servers/file/delete_models.py`