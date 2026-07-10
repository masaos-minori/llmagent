---
title: "New Tool Registration Procedure"
category: mcp
tags:
  - mcp
  - configuration
related:
  - 04_mcp_00_document-guide.md
  - 04_mcp_06_configuration-file-inventory.md
source:
  - 04_mcp_06_configuration-file-inventory.md
---

# New Tool Registration Procedure

## New Tool Registration Procedure

When adding a new tool to an **existing** MCP server:

| Step | Action | Required? |
|---|---|---|
| 1 | Add the tool name to the appropriate frozenset in `shared/tool_constants.py` (e.g., `READ_TOOLS`, `WRITE_TOOLS`, or create a new `<SERVER>_TOOLS` frozenset and add it to `get_all_mcp_tool_names()`) | **[Required]** |
| 2 | Registry auto-populates from these frozensets at import time — no manual registry edit needed | (automatic) |
| 3 | Implement `dispatch()` handler in the owning MCP server (`mcp/<name>/server.py`) | **[Required]** |
| 4 | Expose tool in `/v1/tools` endpoint (return tool definition with `server_key` field) | **[Recommended]** — enables startup drift validation; no effect on routing |
| 5 | Add LLM schema to `config/tools_definitions.toml` (OpenAI function-calling format) | **[Required]** — if tool should be visible to LLM |
| 6 | Add `tool_safety_tiers` entry in `config/agent.toml` for the new tool | **[Required]** — all tools must have a declared safety tier |
| 7 | Add tool name to `tool_names` in `config/<key>_mcp_server.toml` `[mcp_servers.<key>]` section | **[Optional]** — enables startup drift validation only; routing does not require it |

**Note**: All tools must be explicitly registered in ToolRegistry. No prefix-based routing exists.

### Verification

After completing registration:

```bash
uv run pytest tests/test_tool_constants.py tests/test_route_resolver.py -v
```

Expected: all routing tests pass. If `tool_definitions_strict = true`, restart the agent and confirm startup logs show `"Routing: N/N tools mapped"` with no unmapped warnings.

---


## Related Documents

- [04_mcp_06_configuration-file-inventory.md](04_mcp_06_configuration-file-inventory.md)

## Keywords

configuration
