## Goal
- Replace the local `_input_schema` helper with the shared `build_input_schema()` generator so read tool schemas come from the strict models (REQ-001, shared schema source).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the helper at line 32 and its call sites in `TOOL_LIST`.
- Out of scope: the model base swap itself (seq 01).

## Assumptions
- Verified in Step 3a: the local helper is at line 32 (the Plan cited line 33; corrected).
- After seq 01 the models inherit `StrictRequestModel`, so the generated schema reflects `extra="forbid"` behavior through the shared generator.

## Design decisions
- Use `build_input_schema()` from `scripts/mcp_servers/request_contract.py` (line 44) as the single schema source; delete the local helper.

## Alternatives considered
- N/A: single-function change with no public-contract decision of its own.

## Implementation
### Target file
`scripts/mcp_servers/file/read_tools.py`

### Procedure
1. Import `build_input_schema` from `scripts/mcp_servers/request_contract.py`.
2. Replace the local `_input_schema` helper with calls to `build_input_schema(model)` at the `TOOL_LIST` entries (lines 58, 76, …).

### Method
- N/A: behavior is identical except the shared generator also strips presentation fields consistently.

### Details
- The shared generator removes generated `title` keys; the local helper stripped only top-level and per-property titles, so output is equivalent for these models.

## Compatibility considerations
- `/v1/tools` schema output stays structurally identical for valid requests; extra fields are rejected only after seq 01's base swap.

## Security considerations
- N/A: no secrets.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/file/test_file_schema_consistency.py -v` (seq 20 pins runtime and discovery schemas match); full `rules/toolchain.md` sequence.

## Completion criteria
- No local schema helper remains in the file; all read tool schemas are generated from the strict models; the consistency tests pass (AC-1).

## Out of Scope
- Model inheritance (seq 01).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261126-175315 | 20261126-175315 | local _input_schema helper deleted; call sites use build_input_schema; unused typing/pydantic imports removed; docstring updated. Files: scripts/mcp_servers/file/read_tools.py |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261126-201535 | 20261126-201535 | N/A: no test change needed; targeted tests pass (tests/mcp_servers/file/ 426 passed + schema-consumer tests 172 passed; testmon DB unavailable so same-module path used per Step 4 fallback) row 2 is the validation row (this document's table differs from the template: no separate test row); targeted tests pass, full-suite run deferred to end of plan batch Step 5/6: N/A: no docs/00_index.md task-scope mapping for scripts/mcp_servers/file/read_tools.py End-of-batch full-suite run passed (15774 passed, 5 skipped); diff-cover 100% on changed lines; gates pass. Intermittent flaky failures in 3 unrelated tests under -n logical, all pass serially. |

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
- **Requirement ID**: `REQ-001` (shared strict base and shared schema generator)
- **Source issue**: issues/20261119-140516_mcpai009_file-mcp-hardening.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-065258_mcpai009_file-mcp-hardening.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-171048
- **Related target files**: `scripts/mcp_servers/file/read_tools.py`