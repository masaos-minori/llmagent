# MCP Documentation Guide

Entry point for the restructured MCP documentation set.
Read this file first to choose which chapter to open.

---

## Purpose of This Document Set

These 9 files document the MCP (Model Context Protocol) layer: 11 tool servers that give
the agent safe, controlled access to external resources.

They replace the original 13 source files (`04_spec_mcp.md`, `04_mcp-*.md`, `06_ref-mcp.md`)
as the primary reference. Source files are retained unchanged.

---

## Recommended Reading Order (Human)

```
01 System Overview               — start here; server list, ports, transport types
    ↓
02 Protocol and Transport        — HTTP/stdio format, auth, audit log, truncation
    ↓
03 Routing, Lifecycle, Execution — ToolExecutor, routing, startup modes, watchdog
    ↓
04 Server Catalog                — per-server specs (all 11 servers)
    ↓
05 Security and Safety Model     — allowlists, denylist, fail-open/closed, risk tiers
    ↓
06 Configuration and Operations  — config files, OpenRC, health probes, new server checklist
    ↓
90 Inconsistencies and Issues    — bugs, placeholders, spec conflicts
    ↓
99 Source Mapping                — audit table (verification only)
```

---

## AI Query Routing Table

| Question | File |
|---|---|
| What MCP servers exist and what do they do? | `04_mcp_01` |
| What ports do the servers run on? | `04_mcp_01` |
| What startup modes are available? | `04_mcp_01` |
| How does `/v1/call_tool` work? | `04_mcp_02` |
| What is the stdio transport format? | `04_mcp_02` |
| How does Bearer authentication work? | `04_mcp_02` |
| What is the audit log format? | `04_mcp_02` |
| How are tools routed to servers? | `04_mcp_03` |
| How does ToolExecutor work? | `04_mcp_03` |
| How does the watchdog work? | `04_mcp_03` |
| How do I add a new MCP server? | `04_mcp_03` |
| What tools does web-search-mcp provide? | `04_mcp_04` |
| What tools does github-mcp provide? | `04_mcp_04` |
| What does shell-mcp's shell_run accept? | `04_mcp_04` |
| Is mdq-mcp fully implemented? | `04_mcp_04` (no; stub only), `04_mcp_90` (MISSING-01) |
| How does allowed_dirs work? | `04_mcp_05` |
| How does github allowed_repos work? | `04_mcp_05` |
| What is fail-closed vs fail-open? | `04_mcp_05` |
| Which tools support dry_run? | `04_mcp_05` |
| What are the risk tiers? | `04_mcp_05` |
| What config files exist per server? | `04_mcp_06` |
| How do I verify a server is healthy? | `04_mcp_06` |
| What are the default config values? | `04_mcp_06` |
| What is broken or not yet implemented? | `04_mcp_90` |
| Does McpServerHealthRegistry actually work? | `04_mcp_90` (BUG-01: no) |

---

## Navigation to Major Known Issues

| Issue | Location |
|---|---|
| HealthRegistry record_success/failure never called (BUG) | [04_mcp_90 §BUG-01](04_mcp_90_inconsistencies_and_known_issues.md) |
| mdq-mcp service layer is placeholder (all 7 tools) | [04_mcp_90 §MISSING-01](04_mcp_90_inconsistencies_and_known_issues.md) |
| startup_mode="subprocess" + transport="stdio" validation | [04_mcp_90 §UNDOC-01](04_mcp_90_inconsistencies_and_known_issues.md) |

---

## Canonical Source Rules

- `06_ref-mcp.md` was canonical for `ToolExecutor`, `HttpTransport`, `StdioTransport`, routing. Content now in `04_mcp_03`.
- `04_spec_mcp.md` was canonical for system overview, server table, McpServerConfig. Content now in `04_mcp_01`, `04_mcp_03`, `04_mcp_06`.
- `04_mcp-protocol.md` was canonical for watchdog, startup modes, new server procedure. Content now in `04_mcp_03`.
- Per-server `04_mcp-*.md` files are canonical for server-specific specs. Content now in `04_mcp_04`.
- When old files and new files disagree, trust the new restructured files.

---

## File Index

| File | Description |
|---|---|
| [04_mcp_01_system_overview.md](04_mcp_01_system_overview.md) | Purpose, 11-server catalog with ports, transport types, startup modes, major constraints |
| [04_mcp_02_protocol_and_transport.md](04_mcp_02_protocol_and_transport.md) | `/v1/call_tool` format, Pydantic models, MCPServer base, HTTP vs stdio, auth, audit log |
| [04_mcp_03_routing_lifecycle_and_execution.md](04_mcp_03_routing_lifecycle_and_execution.md) | ToolRouteResolver, ToolExecutor, HttpTransport, StdioTransport, startup modes, watchdog, new server |
| [04_mcp_04_server_catalog.md](04_mcp_04_server_catalog.md) | Per-server specs for all 11 servers: tools, config, security, logs, limitations |
| [04_mcp_05_security_and_safety_model.md](04_mcp_05_security_and_safety_model.md) | Allowlists, denylist, fail-open/closed, dry_run, risk tiers, AI safety notes |
| [04_mcp_06_configuration_and_operations.md](04_mcp_06_configuration_and_operations.md) | Config file inventory, McpServerConfig fields, defaults, OpenRC, health probes, new-server checklist |
| [04_mcp_90_inconsistencies_and_known_issues.md](04_mcp_90_inconsistencies_and_known_issues.md) | BUG-01/MISSING-01/02/03/UNDOC-01/02/SPEC-01 with AI safety guidance |
| [04_mcp_99_source_mapping.md](04_mcp_99_source_mapping.md) | Audit: maps every source section to new location; 13 source files fully mapped |

---

## Known Limitations

- Original source files are retained unchanged. This document set supersedes them.
- `04_spec_mcp.md` §13 known issues are fully transcribed into `04_mcp_90`.
