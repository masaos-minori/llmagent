## Goal

Verify that `docs/04_mcp_01_system_overview.md`, `docs/04_mcp_02_protocol_and_transport.md`, and `docs/04_mcp_03_routing_lifecycle_and_execution.md` contain no stale stdio or ondemand references, and fix any that are found.

## Scope

- **In-Scope:**
  - Run `rg` against the three files for `stdio|STDIO|ondemand|ONDEMAND`
  - If results are found: remove or replace each stale reference
- **Out-of-Scope:**
  - Other doc files (`docs/05_agent_*.md`, `docs/01_overview-arch.md`) — these are a known follow-up
  - Any non-doc source files

## Assumptions

1. The plan states all three files were grep-confirmed to have no stdio/ondemand references; this step is a final safety check.
2. If references are found, the expected fix is to delete the offending sentence/row or replace "stdio" with "http" / "HTTP" depending on context.
3. No behavioral change to any code is implied by edits to these doc files.

## Implementation

### Target file

- `/home/masaos/llmagent/docs/04_mcp_01_system_overview.md`
- `/home/masaos/llmagent/docs/04_mcp_02_protocol_and_transport.md`
- `/home/masaos/llmagent/docs/04_mcp_03_routing_lifecycle_and_execution.md`

### Procedure

1. Run the verification grep:
   ```bash
   rg -n "stdio|STDIO|ondemand|ONDEMAND" \
     docs/04_mcp_01_system_overview.md \
     docs/04_mcp_02_protocol_and_transport.md \
     docs/04_mcp_03_routing_lifecycle_and_execution.md
   ```

2. If the command returns **no output**: no edits needed. Record "verified clean" and proceed to Step 7 (final validation sweep).

3. If the command returns **one or more lines**:
   a. Read the surrounding context (+-5 lines) to understand the reference.
   b. For each hit:
      - If it is a table row describing StdioTransport or ondemand mode: delete the row.
      - If it is a prose sentence describing stdio as a supported transport: remove or replace with a note that only HTTP transport is supported.
      - If it is a code example or diagram: update to use `http` transport.
   c. Apply each edit using the Edit tool.

### Method

- `rg -n` for line numbers; Read tool with `offset` and `limit` for context.
- Edit tool for targeted single-line or multi-line deletion.

### Details

- All three files were confirmed clean by the plan author (grep returned no results during planning). The high-confidence outcome of this step is "no edits required."
- If edits are required, follow the same approach used for `docs/04_mcp_05_security_and_safety_model.md` (Step 4 doc): delete the exact row using Edit tool with precise `old_string` match.

## Validation plan

```bash
# Final check -- all three files clean
rg "stdio|STDIO|ondemand|ONDEMAND" \
  docs/04_mcp_01_system_overview.md \
  docs/04_mcp_02_protocol_and_transport.md \
  docs/04_mcp_03_routing_lifecycle_and_execution.md
# Expected: zero results
```
