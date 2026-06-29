# Implementation Design: MCP Response Truncation Metadata Fix

## Goal

Fix double-truncation bug in `_process_stdio_line` where truncation metadata is computed from suffix-appended text rather than the original response, and add integration tests for all truncation boundary scenarios.

## Scope

- **In-Scope**:
  - Add `truncated`, `total_bytes`, `actual_visible_bytes` fields to `_StdioRequestResult` dataclass
  - Have `_handle_stdio_request` populate these from `TruncationResult`
  - Have `_process_stdio_line` use metadata from `_StdioRequestResult` instead of re-truncating
  - Add integration tests for under-limit, over-limit ASCII, over-limit UTF-8, and valid UTF-8 after truncation
- **Out-of-Scope**:
  - Changing the 512 KB global max response size
  - Adding streaming responses

## Affected Files

1. `scripts/mcp/server.py` — add fields to `_StdioRequestResult`, populate in `_handle_stdio_request`, use in `_process_stdio_line`
2. `tests/test_mcp_server_base.py` — add integration tests for truncation metadata propagation

## Implementation Steps

1. Add `truncated: bool = False`, `total_bytes: int = 0`, `actual_visible_bytes: int = 0` to `_StdioRequestResult` dataclass
2. In `_handle_stdio_request`: pass `tr.truncated`, `tr.total_bytes`, `tr.actual_visible_bytes` when constructing `_StdioRequestResult`
3. In `_process_stdio_line`: read metadata from `req_result` instead of calling `_truncate_with_meta(result)` again
4. Add tests: under-limit, over-limit ASCII, over-limit UTF-8, valid UTF-8 after truncation

## Acceptance Criteria

- [x] `_StdioRequestResult` carries truncation metadata
- [x] `_process_stdio_line` uses metadata from `_StdioRequestResult` (no double-truncation)
- [x] Integration tests confirm correct metadata for all four scenarios
- [x] No regressions in existing tests
