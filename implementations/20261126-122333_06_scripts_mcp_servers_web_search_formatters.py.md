## Goal
- Show download truncation separately from extracted-text truncation, and the content type, in the `browser_fetch` text result (REQ-007).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: `_format_fetch_result` in `scripts/mcp_servers/web_search/formatters.py` and its test companion.
- Out of scope: the response model fields (seq 03) and the fetch logic (seq 04).

## Assumptions
- Implemented after the models procedure (seq 03), which adds the two response fields.
- Verified in Step 3a: the formatter prints `status_code=` and `elapsed=` on the first line and `[RESPONSE TRUNCATED]` when `truncated` is true (`formatters.py:42-52`); the existing test asserts `status_code=200` is present (`test_web_search_formatters.py:60-82`).
- Plan overlap check: this file overlaps no other Frozen Plan.

## Design decisions
- Keep `[RESPONSE TRUNCATED]` for extracted-text truncation and add `[DOWNLOAD TRUNCATED]` for a cut download; the first line gains `content_type=` after the existing fields, so existing substring assertions stay valid.

## Alternatives considered
- N/A: single-function formatting change.

## Implementation
### Target file
`scripts/mcp_servers/web_search/formatters.py`

### Procedure
1. In `_format_fetch_result`, append `content_type={result.content_type}` to the first line (omit the item when empty).
2. Add `[DOWNLOAD TRUNCATED]` as a part when `result.download_truncated` is true, before the existing `[RESPONSE TRUNCATED]` marker.
3. Update the function docstring.

### Method
- Order of lines: status line, then `[DOWNLOAD TRUNCATED]` if set, then `[RESPONSE TRUNCATED]` if set, then the text.

### Details
- No other formatter changes.

### Companion test files
- `tests/mcp_servers/web_search/test_web_search_formatters.py`
  - Procedure: add cases for download truncation only, text truncation only, both, neither, and a present and an empty content type; keep the existing `status_code=200` assertion.
  - Validation: `uv run pytest tests/mcp_servers/web_search/test_web_search_formatters.py`.

## Compatibility considerations
- N/A: the first line gains a suffix and one marker appears only in the new case.

## Security considerations
- N/A: formatting only; no upstream body beyond the extracted text is added.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/web_search/test_web_search_formatters.py`; `uv run ruff format` and `uv run ruff check` on both files; `uv run mypy`; then the sequence in `rules/toolchain.md`.

## Completion criteria
- The four truncation combinations and the content type render as specified; existing formatter tests pass; all validation commands pass.

## Out of Scope
- Model fields, fetch logic, classification, and documentation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add the companion test cases, then confirm they pass | Pending | — | — | |
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
- **Requirement ID**: `REQ-007` (separate truncation metadata)
- **Source issue**: issues/20261119-141107_mcpws001_websearch-fetch-network-boundary.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-114539_mcpws001_websearch-fetch-network-boundary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-122333
- **Related target files**: `scripts/mcp_servers/web_search/formatters.py`, `tests/mcp_servers/web_search/test_web_search_formatters.py`
