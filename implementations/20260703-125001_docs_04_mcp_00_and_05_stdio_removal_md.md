# Step 5 — Remove stale stdio entries from `04_mcp_00` and `04_mcp_05`

## Goal

Remove all stale references to the stdio transport from `docs/04_mcp_00_document-guide.md` and `docs/04_mcp_05_security_and_safety_model.md` so that neither file implies stdio is an active or supported transport.

## Scope

- In-Scope:
  - `docs/04_mcp_00_document-guide.md` line 23: change "HTTP/stdio format" to "HTTP format"
  - `docs/04_mcp_00_document-guide.md` line 46: remove the "What is the stdio transport format?" row from the AI Query Routing Table
  - `docs/04_mcp_00_document-guide.md` line 52: remove the "When to use stdio vs HTTP transport?" row from the AI Query Routing Table
  - `docs/04_mcp_00_document-guide.md` line 102: remove "HTTP vs stdio" from the `04_mcp_02` description in the File Index table
  - `docs/04_mcp_05_security_and_safety_model.md` line 197: remove the `stdio call timeout` row from the Output and Resource Limits table

- Out-of-Scope:
  - `docs/04_mcp_02_protocol_and_transport.md` — may contain a "§When to use stdio" section that `04_mcp_00` currently references; the section in `04_mcp_02` is out of scope for this step (the cross-reference row in `04_mcp_00` is removed, not the section itself)
  - `docs/04_mcp_03_routing_lifecycle_and_execution.md` — the StdioTransport class documentation in this file is out of scope
  - All Python source files
  - No other doc files

## Assumptions

1. The active transport is HTTP-only (`HttpTransport`). `StdioTransport` exists in code for backward compatibility but is not the active transport for any server in the current deployment.
2. The `04_mcp_00` AI Query Routing Table rows at lines 46 and 52 route AI queries to `04_mcp_02` §When to use stdio — removing the rows does not break `04_mcp_02`; it only removes the nav pointer to stale content.
3. The `stdio call timeout` row in `04_mcp_05` (line 197) documents `StdioTransport._STDIO_CALL_TIMEOUT` — this constant may still exist in `scripts/shared/tool_executor.py` but is not exercised by any live server; removing it from the resource limits table is correct because the table documents active transport limits.
4. The `04_mcp_00` File Index description for `04_mcp_02` at line 102 currently reads `HTTP vs stdio` — after this change it should read `HTTP format` only, consistent with the Recommended Reading Order line at line 23.
5. No anchor links elsewhere in the doc set point to the removed `04_mcp_00` table rows; the rows have no anchors.

## Implementation

### Target file

Primary: `/home/masaos/llmagent/docs/04_mcp_00_document-guide.md`
Secondary: `/home/masaos/llmagent/docs/04_mcp_05_security_and_safety_model.md`

### Procedure

**Changes to `04_mcp_00_document-guide.md`:**

1. **Line 23 — Recommended Reading Order block**: Change:
   ```
   02 Protocol and Transport        — HTTP/stdio format, auth, audit log, truncation
   ```
   to:
   ```
   02 Protocol and Transport        — HTTP format, auth, audit log, truncation
   ```

2. **Line 46 — AI Query Routing Table**: Remove the row:
   ```
   | What is the stdio transport format? | `04_mcp_02` |
   ```
   Delete the entire line (including the trailing newline). The surrounding table rows remain intact.

3. **Line 52 — AI Query Routing Table**: Remove the row:
   ```
   | When to use stdio vs HTTP transport? | `04_mcp_02` §When to use stdio |
   ```
   Delete the entire line (including the trailing newline).

4. **Line 102 — File Index table**: Change the `04_mcp_02` description cell:
   ```
   | [04_mcp_02_protocol_and_transport.md](04_mcp_02_protocol_and_transport.md) | `/v1/call_tool` format, Pydantic models, MCPServer base, HTTP vs stdio, auth, audit log |
   ```
   to:
   ```
   | [04_mcp_02_protocol_and_transport.md](04_mcp_02_protocol_and_transport.md) | `/v1/call_tool` format, Pydantic models, MCPServer base, HTTP format, auth, audit log |
   ```

**Changes to `04_mcp_05_security_and_safety_model.md`:**

5. **Line 197 — Output and Resource Limits table**: Remove the row:
   ```
   | stdio call timeout | 60.0 sec (`_STDIO_CALL_TIMEOUT`) | StdioTransport |
   ```
   Delete the entire line (including the trailing newline). The surrounding table rows (`Max response bytes` above and `shell max output` below) remain intact.

### Method

Apply each change with a targeted Edit tool call. Use the full surrounding row text as the `old_string` for uniqueness. For row deletions, use `old_string` = the full row line including the trailing newline (or include one line of surrounding context if needed for uniqueness).

- Change 1: `old_string` = the exact `02 Protocol...` line; `new_string` = same line with `HTTP/stdio` replaced by `HTTP`.
- Changes 2 and 3: `old_string` = the full table row text; `new_string` = empty string (deletes the row).
- Change 4: `old_string` = the full `04_mcp_02` file index row; `new_string` = same row with `HTTP vs stdio` replaced by `HTTP format`.
- Change 5: `old_string` = the full `stdio call timeout` row; `new_string` = empty string.

No structural changes to table headers or separators are needed; these are simple row removals and text substitutions.

### Details

**`04_mcp_00` exact strings:**

- Change 1 target: `02 Protocol and Transport        — HTTP/stdio format, auth, audit log, truncation`
- Change 2 target: `| What is the stdio transport format? | \`04_mcp_02\` |`
- Change 3 target: `| When to use stdio vs HTTP transport? | \`04_mcp_02\` §When to use stdio |`
- Change 4 target cell: `HTTP vs stdio, auth, audit log` → `HTTP format, auth, audit log`

**`04_mcp_05` exact string:**

- Change 5 target: `| stdio call timeout | 60.0 sec (\`_STDIO_CALL_TIMEOUT\`) | StdioTransport |`

**Context verification before editing:**

Run the following to confirm exact line locations before each Edit:
```bash
grep -n "stdio\|HTTP/stdio" /home/masaos/llmagent/docs/04_mcp_00_document-guide.md
grep -n "stdio" /home/masaos/llmagent/docs/04_mcp_05_security_and_safety_model.md
```

## Validation plan

```bash
# Confirm no unintentional stdio references remain in 04_mcp_00
rg "stdio" /home/masaos/llmagent/docs/04_mcp_00_document-guide.md
# Expected: zero matches

# Confirm no unintentional stdio references remain in 04_mcp_05
rg "stdio" /home/masaos/llmagent/docs/04_mcp_05_security_and_safety_model.md
# Expected: zero matches

# Confirm the File Index description for 04_mcp_02 is updated
grep "04_mcp_02_protocol_and_transport.md" /home/masaos/llmagent/docs/04_mcp_00_document-guide.md
# Expected: line contains "HTTP format" not "HTTP vs stdio"

# Confirm the Recommended Reading Order is updated
grep "02 Protocol and Transport" /home/masaos/llmagent/docs/04_mcp_00_document-guide.md
# Expected: "HTTP format, auth, audit log, truncation" (no "stdio")

# Confirm the Output and Resource Limits table in 04_mcp_05 no longer has the stdio row
grep "stdio call timeout" /home/masaos/llmagent/docs/04_mcp_05_security_and_safety_model.md
# Expected: zero matches

# Full sweep per plan requirement
rg -n "stdio" docs/04_mcp_00_document-guide.md docs/04_mcp_05_security_and_safety_model.md
# Expected: zero matches (or only intentional references documenting why stdio is not used)

# Verify table structure is intact after row removals
python3 -c "
import pathlib
for fname in ['docs/04_mcp_00_document-guide.md', 'docs/04_mcp_05_security_and_safety_model.md']:
    text = pathlib.Path(fname).read_text()
    lines = text.splitlines()
    prev_was_header = False
    for i, line in enumerate(lines):
        if '|---|' in line:
            prev_was_header = True
        elif prev_was_header and line.strip() and not line.startswith('|'):
            print(f'{fname}:{i+1}: broken table structure: {line!r}')
            prev_was_header = False
        else:
            prev_was_header = False
print('Table structure check complete.')
"
# Expected: only 'Table structure check complete.' with no warnings
```
