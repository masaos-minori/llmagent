---
title: "MCP Inconsistencies and Known Issues"
category: mcp
tags:
  - mcp
  - inconsistencies
  - known-issues
  - bugs
related:
  - 04_mcp_00_document-guide.md
---

## Migration Notes

- Migration Date: 2026-07-23
- Source Format: Existing bullet format (Type, Impact scope, Statement A/B, Current safe interpretation, Recommended action, Notes for AI reference)
- Destination Format: Common template (17 fields)
- Note: Existing entry contents are preserved. Missing fields are filled with 'unconfirmed'.

# MCP Inconsistencies and Known Issues

This file catalogs bugs, unimplemented features, contradictions between specifications, and undefined behaviors discovered in the MCP layer during the documentation restructuring process.

---

### MCP-001: `include_disabled` filter and `disabled_code` structured code are evaluated but unimplemented

- **ID**: MCP-001
- **Title**: `include_disabled` filter and `disabled_code` structured code are evaluated but unimplemented
- **Status**: open
- **Severity**: Medium
- **Area**: MCP
- **Type**: implementation-bug
- **Source**: All 10 implementations in `scripts/mcp_servers/*/server.py`
- **Owner**: Unassigned
- **First Found**: Unconfirmed
- **Target**: `/v1/tools` endpoint
- **Related**: `plans/20260717-181151_plan.md`
- **Summary**: The `include_disabled` filter does not work because `/v1/tools` does not accept query parameters.
- **Current Description**: `/v1/tools` currently accepts no query parameters and always returns all tools unconditionally.
- **Observed Implementation**: The `include_disabled` query parameter and `disabled_code` enumeration were evaluated in Requirement 20 but have no implementation.
- **Impact**: Cannot filter out disabled tools.
- **Recommended Action**: Implement by referring to "Future / deferred design options" in `plans/20260717-181151_plan.md`.
- **Resolution Notes**: Intentionally deferred

---

### MCP-002: Tool runtime availability metadata is partially implemented

- **ID**: MCP-002
- **Title**: Tool runtime availability metadata (`config_dependent`/`enabled`/`disabled_reason`/`RuntimeToolRegistry`) is partially implemented
- **Status**: open
- **Severity**: Low
- **Area**: MCP
- **Type**: implementation-bug
- **Source**: `scripts/mcp_servers/web_search/`, `scripts/agent/**`
- **Owner**: Unassigned
- **First Found**: Unconfirmed
- **Target**: `scripts/mcp_servers/web_search/`, `scripts/agent/**`
- **Related**: `docs/04_mcp_03_06_tool-runtime-availability-metadata.md`
- **Summary**: `config_dependent` is partially adopted, but `enabled`/`disabled_reason` are unimplemented.
- **Current Description**: While `browser_fetch` in `web_search-mcp` adopts `config_dependent: True`, `enabled`/`disabled_reason` do not exist in the `/v1/tools` response.
- **Observed Implementation**: `RuntimeToolRegistry` is live-detected by `McpToolDiscoveryService` and connected via `ToolExecutor.set_runtime_registry()`.
- **Impact**: Only `web-search-mcp` lacks `enabled`/`disabled_reason` implementation (the other 4 servers — `git-mcp`/`file-read-mcp`/`file-write-mcp`/`file-delete-mcp` — have them implemented).
- **Recommended Action**: Delete this entry after completing the `enabled`/`disabled_reason` implementation for `web-search-mcp`.
- **Resolution Notes**: Partially implemented

---

## Related Documents

- `04_mcp_00_document-guide.md`

## Keywords

mcp
inconsistencies
known-issues
bugs
