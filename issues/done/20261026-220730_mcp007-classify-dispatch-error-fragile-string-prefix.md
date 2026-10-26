# _classify_dispatch_error uses fragile string prefix matching

## Priority
Low

## Summary
The `_classify_dispatch_error` function in `web_search_server.py` classifies dispatch errors by matching against hardcoded string prefixes, which is fragile and breaks if the error message format changes.

## Background
The `_classify_dispatch_error` function at lines 168-176 of `web_search_server.py`:

```python
def _classify_dispatch_error(output: str) -> str:
    """Classify a non-raised DispatchResult error by its output text prefix."""
    if output.startswith("Validation error: "):
        return "validation_error"
    if output.startswith("Unknown tool: "):
        return "unknown_tool"
    if output == "Tool name must be a non-empty string":
        return "invalid_tool_name"
    return "dispatch_error"
```

This function is called from the `call_tool` endpoint at line 274:

```python
if outcome == "error":
    error_type = _classify_dispatch_error(r.output)
```

The error messages come from `dispatch_tool` in `dispatch.py`:
- `"Validation error: {e}"` (line 215)
- `"Unknown tool: {name}"` (line 169)
- `"Tool name must be a non-empty string"` (line 163)

## Problem
The classification relies on exact string prefix matching:
1. `"Validation error: "` prefix match — if the error message format changes (e.g., adds a prefix like `"Error: Validation error: "`), classification fails.
2. `"Unknown tool: "` prefix match — same fragility.
3. Exact equality `"Tool name must be a non-empty string"` — breaks if the message is localized or reformatted.

This is a maintenance hazard: any change to the error message format in `dispatch.py` will silently break the classification without raising an error.

## Reason for Change
String prefix matching is fragile and breaks silently when error message formats change. A more robust approach would use structured error types or exception-based classification.

## Implementation Intent
1. Have `dispatch_tool` return a structured error type alongside the output string, or
2. Use exception-based classification instead of string matching, or
3. Define constants for the error prefixes and validate them in tests.

## Target Files or Areas
- `scripts/mcp_servers/web_search/web_search_server.py` — `_classify_dispatch_error` (lines 168-176)
- `scripts/mcp_servers/dispatch.py` — `dispatch_tool` (lines 143-216)

## Required Changes
- Replace string prefix matching with structured error classification
- Either add an `error_type` field to `DispatchResult` or use exception-based classification
- Update callers to use the new classification mechanism

## Constraints
- Must not change the existing error message format (backward compatibility)
- Must preserve the current classification taxonomy

## Acceptance Criteria
- Classification works correctly even if error message format changes
- Error types are classified consistently across all MCP servers
- No silent misclassification

## Testing Expectations
- Unit test: verify classification works with various error message formats
- Integration test: verify classification consistency across MCP servers
- Regression test: ensure existing classification results are preserved

## Documentation Impact
Document the error classification taxonomy in `dispatch.py`.

## Out of Scope
- Changes to the error message format itself
- Changes to how `WebSearchUpstreamError` subclasses are classified

## Dependencies
N/A: none

## Unresolved Questions
- Should `DispatchResult` include an `error_type` field?
- Are there other MCP servers with the same pattern?

## AI Implementation Instruction
In `scripts/mcp_servers/web_search/web_search_server.py`, replace string prefix matching in `_classify_dispatch_error` with a more robust classification mechanism. Consider adding an `error_type` field to `DispatchResult` in `dispatch.py`. Do not modify any other MCP server's classification logic.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261026-220730
- **Related target files**: scripts/mcp_servers/web_search/web_search_server.py, scripts/mcp_servers/dispatch.py
