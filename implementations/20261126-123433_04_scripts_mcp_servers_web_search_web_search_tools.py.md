## Goal
- Publish both tool `inputSchema` values from the runtime request models so discovery and runtime validation share one contract (REQ-003).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the two `inputSchema` entries of `TOOL_LIST` in `scripts/mcp_servers/web_search/web_search_tools.py` and the test companion.
- Out of scope: the model changes (seq 03) and the tool metadata fields (unchanged).

## Assumptions
- Implemented after the models procedure (seq 03), which sets the field descriptions and bounds the schemas derive from.
- Verified in Step 3a: both schemas are hand-written dicts, `search_web` already reads its maximum from the config (`get_max_results_limit()`), and the existing drift test covers `search_web` only (`web_search_tools.py:14-90`; `test_web_search_tool_schema.py:1-40`).
- `build_input_schema` exists in `scripts/mcp_servers/request_contract.py` and is already used by the GitHub tools.
- Plan overlap check: no other Frozen Plan edits this file.

## Design decisions
- Generated schemas gain `additionalProperties: false` and the model defaults; descriptions come from the model fields, so the `description` strings move out of this module.

## Alternatives considered
- Keep hand-written schemas with a drift test only: rejected, the issue asks for one generator.

## Implementation
### Target file
`scripts/mcp_servers/web_search/web_search_tools.py`

### Procedure
1. Import `build_input_schema` and the two request models.
2. Replace the `inputSchema` literal of `search_web` with `build_input_schema(SearchRequest)` and that of `browser_fetch` with `build_input_schema(BrowserFetchRequest)`.
3. Leave every other tool field unchanged; keep the `get_max_results_limit` import only if still used, otherwise remove it.

### Method
- The `search_web` `max_results` maximum now comes from the model's configured `le` bound, which is the value `get_max_results_limit()` returned.

### Details
- Keep the tool descriptions and metadata as they are.

### Companion test files
- `tests/mcp_servers/web_search/test_web_search_tool_schema.py`
  - Procedure: extend the parity tests to `browser_fetch` (required `url`, non-empty `url`, `max_response_kb` bounds equal to the model), assert both published schemas equal `build_input_schema` of the model, assert `additionalProperties` is false for both, and assert an unknown field is rejected by each model; keep the existing `search_web` drift tests.
  - Validation: `uv run pytest tests/mcp_servers/web_search/test_web_search_tool_schema.py`.

## Compatibility considerations
- The published `/v1/tools` schema gains `additionalProperties: false` and defaults; the Agent validates arguments against the published schema, so a caller passing an undeclared argument is now rejected.

## Security considerations
- N/A: schema publication only; rejecting undeclared arguments narrows the input surface.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/web_search/test_web_search_tool_schema.py tests/mcp_servers/test_tool_schema_contract.py`; `uv run ruff format` and `uv run ruff check` on both files; `uv run mypy`; then the sequence in `rules/toolchain.md`.

## Completion criteria
- Both schemas equal the model-generated schemas; the parity tests cover both tools; `test_tool_schema_contract.py` still passes; all validation commands pass.

## Out of Scope
- Model changes, tool metadata, and documentation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add the companion parity tests, then confirm they pass | Pending | — | — | |
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
- **Requirement ID**: `REQ-003` (schemas generated from the models, drift covered for both tools)
- **Source issue**: issues/20261119-141108_mcpws002_websearch-config-audit-redaction.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-114838_mcpws002_websearch-config-audit-redaction.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-123433
- **Related target files**: `scripts/mcp_servers/web_search/web_search_tools.py`, `tests/mcp_servers/web_search/test_web_search_tool_schema.py`
