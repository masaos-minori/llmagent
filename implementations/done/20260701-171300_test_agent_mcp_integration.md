# Implementation: Remove stdio integration tests from test_agent_mcp_integration.py

## Goal

Remove TC-A06 through TC-A09 (stdio-specific integration tests) from
tests/integration/test_agent_mcp_integration.py so that no integration test
exercises real stdio subprocesses.

## Scope

- Target file: tests/integration/test_agent_mcp_integration.py
- Deletion only; no new HTTP integration tests are added in this step.

## Assumptions

- TC-A06 through TC-A09 use real subprocess pipes and are not replaceable with simple mocks.
- HTTP transport integration tests already cover transport correctness separately.
- `_make_stdio_executor` helper (line 44) and `_STDIO_KEY` / `_STDIO_TOOL` constants (lines 25-27) are used only by TC-A06 through TC-A09; they can be removed with those tests.
- Other test cases (TC-A01 through TC-A05, TC-A10+) are HTTP-based and must be preserved.

## Implementation

### Target file: tests/integration/test_agent_mcp_integration.py

#### Procedure

1. Remove `from shared.tool_executor import StdioTransport, ToolExecutor` — update import to remove `StdioTransport`.
2. Remove constants `_STDIO_KEY` (line 25) and `_STDIO_TOOL` (line 27).
3. Delete helper function `_make_stdio_executor` (lines 44-59).
4. Delete test `test_a06_stdio_pipe_close_raises_transport_error` (approx. lines 156-170).
5. Delete test `test_a07_stdio_response_timeout` (approx. lines 172-190).
6. Delete test `test_a08_stdio_malformed_json` (approx. lines 191-211).
7. Delete test `test_a09_stdio_response_id_mismatch` (approx. lines 212-end of function).
8. Remove any comment blocks labeling the TC-A06 through TC-A09 sections.

#### Method

- Read each deletion target in full before removing to confirm no shared logic is embedded.
- After each deletion, verify the file still parses (no dangling references).

#### Details

- Import cleanup: after removing `StdioTransport`, the import line becomes:
  `from shared.tool_executor import ToolExecutor`
  (and possibly `HttpTransport` if needed by remaining tests).
- Module-level docstring (lines 3-5) references stdio; update to reflect HTTP-only scope.
- Confirm `_STDIO_KEY` and `_STDIO_TOOL` are not referenced by any surviving test before deleting.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| Integration tests | `uv run pytest tests/integration/ -v` | All remaining integration tests pass |
| Stdio reference check | `grep -n "stdio\|StdioTransport\|_STDIO" tests/integration/test_agent_mcp_integration.py` | Zero matches |
| Lint | `pre-commit run --files tests/integration/test_agent_mcp_integration.py` | Pass |
