---
title: "MCP Documentation Guide"
category: mcp
tags:
  - mcp
  - documentation
  - guide
  - routing
  - file-index
related:
  - 04_mcp_01_system_overview.md
  - 04_mcp_02_protocol_and_transport.md
  - 04_mcp_03_routing_lifecycle_and_execution.md
  - 04_mcp_04_server_catalog.md
  - 04_mcp_05_security_and_safety_model.md
  - 04_mcp_06_configuration-file-inventory.md
  - 04_mcp_07_tool_schema_export_policy.md
  - 04_mcp_90_inconsistencies_and_known_issues.md
---

# MCP Documentation Guide

Entry point for the restructured MCP documentation set.
Read this file first to choose which chapter to open.

---

## Reading Order

```
01 → 02 → 03 → 04 → 05 → 06 → 90
```

---

## AI Query Routing Table

| Question | File |
|---|---|
| What MCP servers exist and what do they do? | `04_mcp_01` |
| What ports do the servers run on? | `04_mcp_01` |
| What startup modes are available? | `04_mcp_01` |
| How does `/v1/call_tool` work? | `04_mcp_02` |
| How does Bearer authentication work? | `04_mcp_02` |
| What is the audit log format? | `04_mcp_02` |
| How are tools routed to servers? | `04_mcp_03` |
| How does ToolExecutor work? | `04_mcp_03` |
| How does the watchdog work? | `04_mcp_03` §Watchdog; config defaults in `04_mcp_06` §Major Default Values |
| How do I add a new MCP server? | `04_mcp_03` |
| How are startup tool-definition warnings triggered? | `04_mcp_06` §Startup Validation Behavior |
| How do I diagnose an MCP failure? | `04_mcp_06` §MCP Failure Diagnosis |
| What tools does web-search-mcp provide? | `04_mcp_04` |
| What tools does github-mcp provide? | `04_mcp_04` |
| What does shell-mcp's shell_run accept? | `04_mcp_04` |
| Is mdq-mcp production-ready? | `04_mcp_04` (production-ready; FTS5 search and indexing implemented) |
| How does allowed_dirs work? | `04_mcp_05` |
| How does github allowed_repos work? | `04_mcp_05` |
| What is fail-closed vs fail-open? | `04_mcp_05` |
| Which tools support dry_run? | `04_mcp_05` |
| What are the risk tiers? | `04_mcp_05` |
| How are tool schema modules named? | `04_mcp_07` |
| What is the canonical TOOL_LIST export? | `04_mcp_07` |
| How do I clean up _MCP_TOOLS references? | `04_mcp_07` |
| What config files exist per server? | `04_mcp_06` |
| How do I verify a server is healthy? | `04_mcp_06` |
| What are the default config values? | `04_mcp_06` |
| When to use MDQ vs RAG? | `04_mcp_05 §MDQ vs RAG Boundary` |
| What is the MDQ/RAG boundary rule? | `04_mcp_05 §MDQ vs RAG Boundary` |
| What is broken or not yet implemented? | `04_mcp_90` |

---

## Navigation to Major Known Issues

| Issue | Location |
|---|---|
| mdq-mcp is production-ready (FTS5 search and indexing implemented) | [04_mcp_04 §mdq-mcp](04_mcp_04_server_catalog.md) |
| cicd workflow_allowlist RuntimeError claim mismatch | [MCP-09](04_mcp_90_inconsistencies_and_known_issues.md#mcp-09-cicd-workflow_allowlist-policy-mismatch--runtimeerror-vs-warning) |

---

## Canonical Source Rules

- `06_ref-mcp.md` was canonical for `ToolExecutor`, `HttpTransport`, routing. Content now in `04_mcp_03`.
- `04_spec_mcp.md` was canonical for system overview, server table, McpServerConfig. Content now in `04_mcp_01`, `04_mcp_03`, `04_mcp_06`.
- `04_mcp-protocol.md` was canonical for watchdog, startup modes, new server procedure. Content now in `04_mcp_03`.
- Per-server `04_mcp-*.md` files are canonical for server-specific specs. Content now in `04_mcp_04`.
- When old files and new files disagree, trust the new restructured files.

---

## File Index

| File | Description |
|---|---|
| [04_mcp_00_document-guide.md](04_mcp_00_document-guide.md) | Entry point |
| [04_mcp_01_system_overview.md](04_mcp_01_system_overview.md) | System overview |
| [04_mcp_02_protocol_and_transport.md](04_mcp_02_protocol_and_transport.md) | Protocol and transport |
| [04_mcp_03_routing_lifecycle_and_execution.md](04_mcp_03_routing_lifecycle_and_execution.md) | Routing and lifecycle |
| [04_mcp_04_server_catalog.md](04_mcp_04_server_catalog.md) | Server catalog |
| [04_mcp_05_security_and_safety_model.md](04_mcp_05_security_and_safety_model.md) | Security model |
| [04_mcp_06_purpose.md](04_mcp_06_purpose.md) | Config purpose |
| [04_mcp_06_configuration-file-inventory.md](04_mcp_06_configuration-file-inventory.md) | Config inventory |
| [04_mcp_06_mcpserverconfig-fields-agenttoml-mcp_servers.md](04_mcp_06_mcpserverconfig-fields-agenttoml-mcp_servers.md) | McpServerConfig fields |
| [04_mcp_06_major-default-values.md](04_mcp_06_major-default-values.md) | Default values |
| [04_mcp_06_long-running-http-operation-startup_modesubprocess.md](04_mcp_06_long-running-http-operation-startup_modesubprocess.md) | Long-running ops |
| [04_mcp_06_verification-methods.md](04_mcp_06_verification-methods.md) | Verification |
| [04_mcp_06_reading-audit-logs.md](04_mcp_06_reading-audit-logs.md) | Audit logs |
| [04_mcp_06_end-to-end-tool-call-tracing.md](04_mcp_06_end-to-end-tool-call-tracing.md) | Tracing |
| [04_mcp_06_mcp-failure-diagnosis.md](04_mcp_06_mcp-failure-diagnosis.md) | Failure diagnosis |
| [04_mcp_06_settings-with-high-operational-impact.md](04_mcp_06_settings-with-high-operational-impact.md) | High-impact settings |
| [04_mcp_06_startup-validation-behavior-tool_definitions_strict.md](04_mcp_06_startup-validation-behavior-tool_definitions_strict.md) | Startup validation |
| [04_mcp_06_watchdog-configuration-monitoring.md](04_mcp_06_watchdog-configuration-monitoring.md) | Watchdog config |
| [04_mcp_06_watchdog-health-reasons-scheduling.md](04_mcp_06_watchdog-health-reasons-scheduling.md) | Watchdog health |
| [04_mcp_06_new-tool-registration-procedure.md](04_mcp_06_new-tool-registration-procedure.md) | New tool reg |
| [04_mcp_06_new-mcp-server-addition-checklist.md](04_mcp_06_new-mcp-server-addition-checklist.md) | New server checklist |
| [04_mcp_06_pre-production-fail-open-checklist.md](04_mcp_06_pre-production-fail-open-checklist.md) | Pre-prod checklist |
| [04_mcp_06_local-to-production-auth-migration.md](04_mcp_06_local-to-production-auth-migration.md) | Auth migration |
| [04_mcp_07_tool_schema_export_policy.md](04_mcp_07_tool_schema_export_policy.md) | Schema export |
| ~~04_mcp_07_mdq_rag_boundary.md~~ | Removed |
| [04_mcp_90_inconsistencies_and_known_issues.md](04_mcp_90_inconsistencies_and_known_issues.md) | Known issues |

---

## Migration Notes

### POST /v1/search (removed — 2026-06-26)

The `POST /v1/search` endpoint on `rag-pipeline-mcp` has been removed.

**Before:**
```http
POST /v1/search
{"query": "...", "history_context": "..."}
```

**After (canonical MCP tool call):**
```http
POST /v1/call_tool
{"name": "rag_run_pipeline", "args": {"query": "...", "history_context": []}}
```

Update any `rag_service_url` callers to use the MCP tool call format.
This change is not backward-compatible — no compatibility shim is provided.

---

## Legacy Source Document Policy

**Policy: Delete.** Git history preserves all content. Archive is not required.

Legacy MCP source files (`04_spec_mcp.md`, `04_mcp-*.md`, `06_ref-mcp.md`) were retained
through the documentation restructuring phase (plans 71-76) and deleted as of 2026-06-26.
If recovery is needed, use `git log --all -- docs/<filename>`.

---

## Known Limitations

- `04_spec_mcp.md` §13 known issues are fully transcribed into `04_mcp_90`.

## Related Documents

- `04_mcp_01_system_overview.md`
- `04_mcp_02_protocol_and_transport.md`
- `04_mcp_03_routing_lifecycle_and_execution.md`
- `04_mcp_04_server_catalog.md`
- `04_mcp_05_security_and_safety_model.md`
- `04_mcp_06_configuration-file-inventory.md`
- `04_mcp_07_tool_schema_export_policy.md`
- `04_mcp_90_inconsistencies_and_known_issues.md`

## Keywords

mcp
documentation
guide
routing
file-index
