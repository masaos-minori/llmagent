---
name: 20260618-151134_04_mcp_06_configuration_and_operations.md
description: Add "New Tool Registration Procedure" section documenting the 3-step process
metadata:
  type: implementation
---

# Goal

Add a standalone "New Tool Registration Procedure" section to `docs/04_mcp_06_configuration_and_operations.md` that documents the simplified 3-step process for adding a new tool to an existing MCP server. The existing "New MCP Server Addition Checklist" covers adding a whole server; this section covers adding a tool to an existing server.

# Scope

- **File:** `docs/04_mcp_06_configuration_and_operations.md`
- **Change:** Add new section before the existing "New MCP Server Addition Checklist"
- **Out of scope:** Existing checklist items, other documentation files

# Assumptions

1. The existing checklist at the end of the doc covers full server addition; a new section for tool-only addition is missing.
2. The 3-step procedure matches the plan: (1) add to `tool_constants.py` frozenset, (2) add to `tool_names` in server config, (3) verify via routing coverage log at startup.
3. Startup validation is available after the `route_resolver.py` change (passes `known_tools` to `ToolRouteResolver`).

# Implementation

## Target file

`docs/04_mcp_06_configuration_and_operations.md`

## Procedure

Insert new section before the "New MCP Server Addition Checklist" section (before the checklist heading).

## Method

New section content:
```markdown
## New Tool Registration Procedure

When adding a new tool to an **existing** MCP server:

1. **Add the tool name to `shared/tool_constants.py`**
   - Add to the appropriate frozenset (`READ_TOOLS`, `WRITE_TOOLS`, etc.)
   - If no set fits, create a new `<SERVER>_TOOLS` frozenset and add it to `get_all_mcp_tool_names()`

2. **Add the tool name to `tool_names` in the server config (`config/agent.toml`)**
   - Find the `[mcp_servers.<server_key>]` block
   - Append the tool name to `tool_names = [...]`

3. **Verify routing coverage at startup**
   - Start the agent or run `uv run pytest tests/test_route_resolver.py -v`
   - Startup logs confirm: "Routing: N/N tools mapped"
   - If a warning appears ("N-1/N tools mapped; 1 unmapped: [tool_name]"), the tool is missing from step 1 or 2

> **Note:** If the tool name follows the `github_` prefix convention and the server key is `github`,
> no entry in `tool_constants.py` is needed — prefix matching handles it automatically.
```

## Details

- Position: insert just above the "## New MCP Server Addition Checklist" heading.
- Do not modify the existing checklist.

# Validation plan

| Check | Command | Expected |
|---|---|---|
| Section exists | `grep "New Tool Registration Procedure" docs/04_mcp_06_configuration_and_operations.md` | 1 match |
| No broken markdown | manual review | headings, code blocks correct |
