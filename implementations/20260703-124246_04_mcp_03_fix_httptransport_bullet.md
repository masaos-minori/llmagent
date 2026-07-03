# Implementation: Fix the incorrect HttpTransport description in `04_mcp_03`

## Goal

Replace the false "returns `is_error=True`" bullet in the HttpTransport section of `docs/04_mcp_03_routing_lifecycle_and_execution.md` with an accurate statement that `HttpTransport.call()` raises `TransportError` and that `ToolExecutor._record_transport_error()` performs the conversion.

## Scope

- In-Scope: Edit the single bullet at line 214 of `docs/04_mcp_03_routing_lifecycle_and_execution.md`.
- Out-of-Scope: No changes to any other file; no changes to production Python code; no changes to test files.

## Assumptions

1. Line 214 currently reads exactly: `- Catches all HTTP and request errors; returns \`is_error=True\` with message`
2. The surrounding context (lines 206-218) remains stable and is not edited concurrently.
3. The markdown renderer does not require any special escaping for backtick strings in bullet points.
4. Adding a second bullet below the replaced line does not break any anchor links elsewhere in the doc set.

## Implementation

### Target file

`/home/masaos/llmagent/docs/04_mcp_03_routing_lifecycle_and_execution.md`

### Procedure

1. Read the file to confirm line 214 contains the exact string `Catches all HTTP and request errors; returns \`is_error=True\` with message`.
2. Replace that single bullet with the two-bullet block specified below (see Method).
3. Verify with `grep -n "returns.*is_error=True" docs/04_mcp_03*` returns 0 matches.
4. Verify with `grep -n "TransportError" docs/04_mcp_03*` shows at least 1 match inside the HttpTransport section (lines ~206-218).

### Method

Replace the old bullet:

```
- Catches all HTTP and request errors; returns `is_error=True` with message
```

with these two bullets:

```
- Raises `TransportError` on all transport-level failures (timeout, HTTP non-2xx, malformed response, retry exhausted); does NOT return `is_error=True` directly
- `ToolExecutor._record_transport_error()` catches `TransportError` and converts it to `ToolCallResult(error_type="transport")`
```

Use the Edit tool with `old_string` set to the exact text of the old bullet (including the leading `- `) and `new_string` set to the two-bullet block above.

### Details

- Target section heading: `## HttpTransport (\`shared/tool_executor.py\`)`
- The bullet to replace is at line 214 (confirmed by file read).
- The surrounding lines (lines 213, 215) must not be altered.
- The new bullets align with the implementation in `scripts/shared/tool_executor.py`:
  - `HttpTransport.call()` raises `TransportError` at lines 185, 195, 203, 208-209.
  - `ToolExecutor._record_transport_error()` at lines 398-419 catches `TransportError` and returns `ToolCallResult(..., error_type="transport")`.

## Validation plan

```bash
# No forbidden phrase remains in the HttpTransport section
grep -n "returns.*is_error=True" /home/masaos/llmagent/docs/04_mcp_03*
# Expected: 0 matches

# TransportError is now mentioned in the HttpTransport section
grep -n "TransportError" /home/masaos/llmagent/docs/04_mcp_03*
# Expected: at least 1 match in lines 206-220

# No regressions in tests
uv run pytest tests/test_tool_executor.py -v
# Expected: all existing tests pass (no new tests added in this step)
```
