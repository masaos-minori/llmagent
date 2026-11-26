## Goal
- Create the schema-and-model consistency test file for all file tools: runtime and discovery schemas match, extra fields are rejected (REQ-001, AC-1).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: one new test file covering read, write, and delete tools.
- Out of scope: the model base swaps and schema-generator switches (seq 01-06).

## Assumptions
- Verified in Step 3a: `tests/mcp_servers/file/` exists; `test_mcp_tools_validation.py` checks tool names only, not schema-model consistency, so the new file adds a distinct coverage layer.
- This row has its own document because it is cited by three other rows (seq 02, 04, 06), so it fails the companion single-citation condition.

## Design decisions
- Two assertion groups per tool family: the `/v1/tools` discovery schema equals `build_input_schema(model)` for the request model, and a runtime call with an extra field is rejected for every file tool.
- The file is created new rather than extending `test_mcp_tools_validation.py`, per the Plan row (Create).

## Alternatives considered
- Extending the existing validation test file — rejected by the Plan's target-file table (new file).

## Implementation
### Target file
`tests/mcp_servers/file/test_file_schema_consistency.py` (new)

### Procedure
1. Create the file with discovery-vs-model schema equality tests for the read, write, and delete tool families.
2. Add extra-field rejection tests for every file tool request model.

### Method
- Import the tool lists and models directly; no HTTP layer needed for schema equality, and the runtime rejection assertions follow the existing `test_call_tool_validation.py` pattern.

### Details
- The file pins the shared generator as the single schema source, so any local helper reintroduced in seq 02, 04, or 06 fails here.

## Compatibility considerations
- N/A: tests only.

## Security considerations
- N/A: the tests verify the strict validation boundary.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/file/test_file_schema_consistency.py -v`; full `rules/toolchain.md` sequence.

## Completion criteria
- Schema equality and extra-field rejection pass for all file tools (AC-1).

## Out of Scope
- Model and schema-generator changes (seq 01-06).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261126-184344 | 20261126-184344 | File created. Group 1: discovery-vs-model schema equality for read (9 tools), write (4), delete (2). Group 2: extra-field rejection for every file tool request model. Step 3a correction: the procedure's wire-boundary assumption is not implementable — no validator is registered for file tools in tool_validators.py and the dispatch handlers build models from cherry-picked arg keys, so an extra field on POST /v1/call_tool is ignored at runtime; the strict-base rejection is asserted at the model boundary instead. Files: tests/mcp_servers/file/test_file_schema_consistency.py |
| 2 | Add or update tests per Validation plan | Completed | 20261126-184344 | 20261126-184344 | The file is the test deliverable; targeted run 6 passed (3 schema-equality + 3 extra-field groups covering all 15 tools). Gap noted for the owner: AC-1 wire-level extra-field rejection is not enforced by the current dispatch path; recorded in the test file docstring. Files: tests/mcp_servers/file/test_file_schema_consistency.py |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261126-201535 | 20261126-201535 | ruff/format/mock-patch-targets/reference-table pass; full-suite run deferred to end of plan batch; Step 5/6: N/A: no docs/00_index.md task-scope mapping for tests/mcp_servers/file/test_file_schema_consistency.py End-of-batch full-suite run passed (15774 passed, 5 skipped); coverage gate N/A for a test-only file (no scripts/ source changed by this row); targeted run 6 passed; gates pass. Intermittent flaky failures in 3 unrelated tests under -n logical, all pass serially. |

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
- **Related target files**: `tests/mcp_servers/file/test_file_schema_consistency.py`