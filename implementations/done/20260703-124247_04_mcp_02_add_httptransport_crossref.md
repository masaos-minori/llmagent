# Implementation: Strengthen HttpTransport error-shape section in `04_mcp_02`

## Goal

Add an explicit callout block to the "Common Error Shape" section of `docs/04_mcp_02_protocol_and_transport.md` stating that `HttpTransport.call()` never returns `is_error=True` for transport failures, with a cross-reference to the corrected `04_mcp_03` section.

## Scope

- In-Scope: Insert a blockquote note immediately after the existing paragraph at lines 259-261 of `docs/04_mcp_02_protocol_and_transport.md`.
- Out-of-Scope: No changes to any other file; no changes to production Python code; no edits to lines outside the target paragraph block.

## Assumptions

1. Lines 259-261 of `docs/04_mcp_02_protocol_and_transport.md` currently read:
   ```
   HTTP transport errors (4xx/5xx) are caught by `HttpTransport.call()`, which raises a
   `TransportError` exception. `ToolExecutor._record_transport_error()` converts this to
   `ToolCallResult(output=str(e), is_error=True, error_type="transport")`.
   ```
2. The text at lines 259-261 is already partially correct (it says "raises a `TransportError` exception") — the new note supplements it with an explicit negative assertion and cross-reference.
3. The markdown anchor `04_mcp_03_routing_lifecycle_and_execution.md#httptransport` is valid after Step 1 corrects that section.

## Implementation

### Target file

`/home/masaos/llmagent/docs/04_mcp_02_protocol_and_transport.md`

### Procedure

1. Read the file to confirm the existing paragraph text at lines 259-261.
2. Identify the exact string ending with `error_type="transport")`.
3. Append the blockquote note immediately after that paragraph (before the `### HealthRegistry updates` heading at line 263).
4. Verify with `grep -n "_record_transport_error" docs/04_mcp_02*` returns at least 1 match.
5. Verify the blockquote note text contains the phrase "never returns `is_error=True`".

### Method

Locate the paragraph block ending at line 261 and insert the following blockquote immediately after it (with a blank line separating the paragraph from the blockquote):

```markdown

> **Note:** `HttpTransport.call()` never returns `is_error=True` for transport failures.
> It raises `TransportError`. `ToolExecutor._record_transport_error()` catches this and
> returns `ToolCallResult(error_type="transport")`. See [04_mcp_03 §HttpTransport](04_mcp_03_routing_lifecycle_and_execution.md#httptransport).
```

Use the Edit tool with `old_string` set to the exact three-line paragraph text (lines 259-261) and `new_string` set to the same paragraph text plus the blockquote above.

### Details

- The `old_string` for the Edit tool must be:
  ```
  HTTP transport errors (4xx/5xx) are caught by `HttpTransport.call()`, which raises a
  `TransportError` exception. `ToolExecutor._record_transport_error()` converts this to
  `ToolCallResult(output=str(e), is_error=True, error_type="transport")`.
  ```
- The `new_string` appends a blank line and the blockquote immediately after the paragraph closing period.
- Do not modify the `### HealthRegistry updates` heading or its content.
- The cross-reference URL uses a relative path; no `http://` prefix is needed.

## Validation plan

```bash
# Cross-reference to _record_transport_error is present
grep -n "_record_transport_error" /home/masaos/llmagent/docs/04_mcp_02*
# Expected: at least 1 match in the newly inserted note

# "never returns is_error=True" statement is present
grep -n 'never returns.*is_error' /home/masaos/llmagent/docs/04_mcp_02*
# Expected: at least 1 match

# No regressions in tests
uv run pytest tests/test_tool_executor.py -v
# Expected: all existing tests pass
```
