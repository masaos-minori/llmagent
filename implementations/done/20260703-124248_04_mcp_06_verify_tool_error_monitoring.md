# Implementation: Verify and update `04_mcp_06` ToolExecutor transport error description

## Goal

Perform a full read of `docs/04_mcp_06_configuration_and_operations.md`, confirm there is no "returns `is_error=True`" wording for `HttpTransport`, and add a clarifying sentence to the "Tool error monitoring" subsection if the `TransportError` → `_record_transport_error()` flow is not explicitly described.

## Scope

- In-Scope: Read the full file; optionally add one clarifying sentence to the "Tool error monitoring" subsection (lines ~519-564) only if the flow description is absent.
- Out-of-Scope: No changes to any other section; no changes to any other file; no changes to production Python code.

## Assumptions

1. `docs/04_mcp_06_configuration_and_operations.md` does not contain any "returns `is_error=True`" wording for `HttpTransport` (pre-verified by grep in the plan's design phase).
2. The "Tool error monitoring" section (lines ~519-564) describes two error categories (transport / tool) but does not currently call out the `TransportError` → `_record_transport_error()` chain explicitly.
3. If the clarifying sentence is already present, this step is a no-op and no edit is made.

## Implementation

### Target file

`/home/masaos/llmagent/docs/04_mcp_06_configuration_and_operations.md`

### Procedure

1. Read the full file end-to-end.
2. Search for any occurrence of `returns.*is_error=True` in the file. If found, correct it (treat as a blocking issue — escalate if found).
3. Locate the "Tool error monitoring" subsection (`### Tool error monitoring`, around line 519).
4. Check whether the subsection already contains a sentence about `HttpTransport` raising `TransportError` that is caught by `ToolExecutor._record_transport_error()`.
5. If absent, add the following sentence immediately after the two-row table (before `#### Per-server tool error counters`):
   ```
   Transport errors are raised by `HttpTransport` as `TransportError` and caught by
   `ToolExecutor._record_transport_error()`, which increments `stat_transport_errors`
   and calls `HealthRegistry.record_failure()`.
   ```
6. If already present, make no edit.
7. Verify with `grep -n "returns.*is_error=True" docs/04_mcp_06*` returns 0 matches.

### Method

- Use the Edit tool: `old_string` = the blank line immediately before `#### Per-server tool error counters`; `new_string` = the clarifying sentence (preceded by a blank line) followed by another blank line and the heading.
- This is a targeted one-sentence addition. Do not restructure the section.

### Details

- Target subsection heading: `### Tool error monitoring` (around line 519).
- The two-row table describes `Transport error` (error_type=transport) and `Tool error` (error_type=tool).
- The clarifying sentence must reference:
  - `HttpTransport` (the class that raises `TransportError`)
  - `ToolExecutor._record_transport_error()` (the method that catches and converts it)
  - `stat_transport_errors` (the counter that is incremented)
  - `HealthRegistry.record_failure()` (the registry call made on transport failure)
- All four references are verifiable in `scripts/shared/tool_executor.py` at lines 398-419.

## Validation plan

```bash
# No forbidden phrase in 04_mcp_06
grep -n "returns.*is_error=True" /home/masaos/llmagent/docs/04_mcp_06*
# Expected: 0 matches

# TransportError boundary described (either from pre-existing text or new sentence)
grep -n "_record_transport_error\|stat_transport_errors" /home/masaos/llmagent/docs/04_mcp_06*
# Expected: at least 1 match (new or existing)

# No regressions in tests
uv run pytest tests/test_tool_executor.py -v
# Expected: all existing tests pass
```
