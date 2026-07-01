# Implementation: Remove StdioTransport test classes from test_tool_executor.py and test_tool_executor_routing.py

## Goal

Remove all stdio-specific test classes and imports from test_tool_executor.py and
test_tool_executor_routing.py so that no test code exercises StdioTransport after
the HTTP-only transport migration.

## Scope

- Target files:
  - tests/test_tool_executor.py
  - tests/test_tool_executor_routing.py
- Only deletion of stdio test code; no new code is added in this step.

## Assumptions

- StdioTransport remains importable from shared.tool_executor during this step (removal happens in a future PR).
- Removing test classes does not affect any other test class in these files.
- test_set_session_id_skips_stdio_transports in test_tool_executor_routing.py may still be relevant; check before deleting.

## Implementation

### Target file: tests/test_tool_executor.py

#### Procedure

1. Remove `StdioTransport` from the import statement at line 18.
2. Delete class `TestStdioTransportResponseId` (lines 25-41, inclusive).
3. Delete class `TestStdioTransportStop` (lines 312-357, inclusive).
4. Verify no remaining references to `StdioTransport` in the file.

#### Method

- Direct deletion of class blocks.
- After each deletion, check that surrounding class boundaries are intact.

#### Details

- `TestStdioTransportResponseId` contains three tests: test_response_id_mismatch_raises, test_response_id_match_succeeds, test_no_expected_id_skips_validation. All test `StdioTransport._parse_stdio_response()` — a stdio-only static method.
- `TestStdioTransportStop` tests subprocess lifecycle termination. HTTP transports have no equivalent.
- Import line pattern: `from shared.tool_executor import StdioTransport, ...` — remove `StdioTransport,` from the list; keep remaining imports.

### Target file: tests/test_tool_executor_routing.py

#### Procedure

1. Remove `StdioTransport` from the import statement at line 23.
2. Delete class `TestStdioTransportCall` (approx. lines 302-357).
3. Delete class `TestStdioTransportStart` (approx. lines 461-end of class).
4. Keep `_stdio_cfg()` helper function (line 34) if any remaining test still references it; otherwise remove.
5. Check `test_set_session_id_skips_stdio_transports` (line 559): if it tests HTTP-agnostic behavior, keep it with a non-Stdio config; otherwise remove.
6. Verify no remaining `StdioTransport` references.

#### Method

- Direct deletion of class blocks.
- After deletion, run `grep StdioTransport tests/test_tool_executor_routing.py` to confirm zero references.

#### Details

- `TestStdioTransportCall` has five test methods exercising direct call routing through StdioTransport.
- `TestStdioTransportStart` has four test methods exercising subprocess startup and error handling.
- `_stdio_cfg()` returns a stdio McpServerConfig; keep only if referenced by surviving tests.

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| Unit tests | `uv run pytest tests/test_tool_executor.py -v` | All remaining tests pass; no StdioTransport errors |
| Unit tests | `uv run pytest tests/test_tool_executor_routing.py -v` | All remaining tests pass |
| Import check | `grep StdioTransport tests/test_tool_executor.py tests/test_tool_executor_routing.py` | Zero matches |
| Lint | `pre-commit run --files tests/test_tool_executor.py tests/test_tool_executor_routing.py` | Pass |
