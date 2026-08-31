---
title: "MCP Documentation Guide"
area: mcp
tags:
  - mcp
  - documentation
  - guide
  - routing
  - file-index
related:
  - 04_mcp_01_system_overview.md
  - 04_mcp_02_01_endpoints-and-transport.md
  - 04_mcp_03_01_dispatch-and-routing.md
  - 04_mcp_04_01_web-search-file-read-github.md
  - 04_mcp_05_01_access-control-and-allowlists.md
  - 04_mcp_06_02_configuration-file-inventory.md
  - 04_mcp_07_tool_schema_export_policy.md
  - 04_mcp_08_tool_capability_naming_convention.md
  - 04_mcp_90_inconsistencies_and_known_issues.md
---

# MCP Documentation Guide

Entry point for the restructured MCP documentation set. Read this file first to determine which chapter you should open.

---

## Design Intent

### Purpose of the Documentation Set

Provides guidance on determining which chapters to open as the entry point for the MCP documentation set.

---

## Current Implementation Behavior

### Recommended Reading Order

``` text
01 → 02 → 03 → 04 → 05 → 06 → 90
```

---

## Responsibility Boundaries

### Agent Query Routing Table

| Question | File |
|---|---|
| Which MCP servers exist and what do they do? What are their ports and startup modes? | `04_mcp_01` |
| `/v1/call_tool`, Bearer authentication, and audit log formats | `04_mcp_02` |
| Tool routing, ToolExecutor, and adding new servers | `04_mcp_03` (config defaults are in `04_mcp_06` Major Default Values) |
| Handling of tool enabled/disabled_reason, config_dependent, and RuntimeToolRegistry | `04_mcp_03_06` |
| Tools provided by web-search/github/shell/mdq MCPs. MDQ-mcp FTS5 search is production-ready; hybrid search is unimplemented | `04_mcp_04` (mdq-mcp only has FTS5 search implemented) |
| allowed_dirs/allowed_repos, fail-closed/fail-open, dry_run, risk tiers, MDQ/RAG boundary | `04_mcp_05` |
| Config file list, health verification, default values, startup warnings, failure diagnosis | `04_mcp_06` |
| Naming convention for tool schema modules, TOOL_LIST exports, and cleanup of _MCP_TOOLS references | `04_mcp_07` |
| Tool capability naming convention (domain.action format) | `04_mcp_08` |
| What is broken or unimplemented | `04_mcp_90` |
---

## Navigation to Major Known Issues

| Issue | Location |
|---|---|
| mdq-mcp is production-ready (FTS5 search and indexing are implemented) | [04_mcp_04_04_mdq.md](04_mcp_04_04_mdq.md) |

---

## Canonical Source Rules

- `06_ref-mcp.md` was the canonical source for `ToolExecutor`, `HttpTransport`, and routing. Its content is now in `04_mcp_03`.
- `04_spec_mcp.md` was the canonical source for system overview, server list, and McpServerConfig. Its content is now in `04_mcp_01`, `04_mcp_03`, and `04_mcp_06`.
- `04_mcp-protocol.md` was the canonical source for watchdog, startup modes, and new server addition procedures. Its content is now in `04_mcp_03`.
- The per-server `04_mcp-*.md` files are the canonical sources for server-specific specifications. Their content is now in `04_mcp_04`.
- If there is a discrepancy between old and new files, trust the newly restructured files.

---

## File Index

| File | Description |
|---|---|
| [04_mcp_00_document-guide.md](04_mcp_00_document-guide.md) | Entry Point |
| [04_mcp_01_system_overview.md](04_mcp_01_system_overview.md) | System Overview |
| [04_mcp_01_tool_ownership_matrix.md](04_mcp_01_tool_ownership_matrix.md) | Tool Ownership Matrix |
| [04_mcp_02_service_boundaries.md](04_mcp_02_service_boundaries.md) | Service Boundary Definitions |
| [04_mcp_02_01](04_mcp_02_01_endpoints-and-transport.md) 〜 [_02](04_mcp_02_02_startup-modes-and-health.md)/[_03](04_mcp_02_03_audit-logging-and-errors.md) | Protocol and Transport (3 parts) |
| [04_mcp_03_01](04_mcp_03_01_dispatch-and-routing.md) 〜 [_02](04_mcp_03_02_tool-registry.md)/[_03a](04_mcp_03_03_transport-and-health.md)/[_03b](04_mcp_03_03_transport-and-health.md)/[_04](04_mcp_03_04_tool-call-tracing-and-watchdog.md)/[_05](04_mcp_03_05_lifecycle-and-new-server.md)/[_06](04_mcp_03_06_tool-runtime-availability-metadata.md) | Routing and Lifecycle (7 parts) |
| [04_mcp_04_01](04_mcp_04_01_web-search-file-read-github.md) 〜 [_02](04_mcp_04_02_file-write-file-delete-shell.md)/[_03](04_mcp_04_03_rag-pipeline-and-cicd.md)/[_04](04_mcp_04_04_mdq.md)/[_05](04_mcp_04_05_git.md) | Server Catalog (5 parts, _04=mdq. browser-mcp was merged into web-search-mcp under _01 on 2026-07-20; old _06 was deleted) |
| [04_mcp_05_01](04_mcp_05_01_access-control-and-allowlists.md) 〜 [_02](04_mcp_05_02_auth-profiles-and-sandboxing.md)/[_03](04_mcp_05_03_fail-open-fail-closed-and-risk-tiers.md)/[_04](04_mcp_05_04_mdq-rag-boundary.md)/[_05](04_mcp_05_05_mdq-enforcement-and-lockdown.md) | Security Model (5 parts) |
| [04_mcp_06_01_purpose.md](04_mcp_06_01_purpose.md) | Config Purpose |
| [04_mcp_06_02_configuration-file-inventory.md](04_mcp_06_02_configuration-file-inventory.md) | Config Inventory |
| [04_mcp_06_03_mcpserverconfig-fields-agenttoml-mcp_servers.md](04_mcp_06_03_mcpserverconfig-fields-agenttoml-mcp_servers.md) | McpServerConfig Fields |
| [04_mcp_06_04_major-default-values.md](04_mcp_06_04_major-default-values.md) | Default Values |
| [04_mcp_06_05_long-running-http-operation-startup_modesubprocess.md](04_mcp_06_05_long-running-http-operation-startup_modesubprocess.md) | Long-running Operations |
| [04_mcp_06_06_verification-methods.md](04_mcp_06_06_verification-methods.md) | Verification Methods |
| [04_mcp_06_07_reading-audit-logs.md](04_mcp_06_07_reading-audit-logs.md) | Audit Log |
| [04_mcp_06_08_end-to-end-tool-call-tracing.md](04_mcp_06_08_end-to-end-tool-call-tracing.md) | Tracing |
| [04_mcp_06_09_mcp-failure-diagnosis.md](04_mcp_06_09_mcp-failure-diagnosis.md) | Failure Diagnosis |
| [04_mcp_06_10_settings-with-high-operational-impact.md](04_mcp_06_10_settings-with-high-operational-impact.md) | Settings with High Operational Impact |
| [04_mcp_06_11_startup-validation-behavior-tool_definitions_strict.md](04_mcp_06_11_startup-validation-behavior-tool_definitions_strict.md) | Startup Validation |
| [04_mcp_06_12_watchdog-configuration-monitoring.md](04_mcp_06_12_watchdog-configuration-monitoring.md) | watchdog deletion note (2026-07-16) |
| [04_mcp_06_13_watchdog-health-reasons-scheduling.md](04_mcp_06_13_watchdog-health-reasons-scheduling.md) | health_reason / HealthRegistry |
| [04_mcp_06_14_new-tool-registration-procedure.md](04_mcp_06_14_new-tool-registration-procedure.md) | New Tool Registration |
| [04_mcp_06_15_new-mcp-server-addition-checklist.md](04_mcp_06_15_new-mcp-server-addition-checklist.md) | New Server Addition Checklist |
| [04_mcp_06_16_pre-production-fail-open-checklist.md](04_mcp_06_16_pre-production-fail-open-checklist.md) | Pre-Production Checklist |
| [04_mcp_06_17_local-to-production-auth-migration.md](04_mcp_06_17_local-to-production-auth-migration.md) | Auth Migration |
| [00_security_01_architecture-and-trust-boundaries.md](00_security_01_architecture-and-trust-boundaries.md) | System architecture / trust boundaries / threat modeling (canonical cross-cutting source) |
| [00_security_02_high-risk-tool-common-policy.md](00_security_02_high-risk-tool-common-policy.md) | High-risk MCP tool common policy (path/repo allowlists, traversal prevention, approval-risk tier mapping) |
| [04_mcp_07_tool_schema_export_policy.md](04_mcp_07_tool_schema_export_policy.md) | Schema Export |
| [04_mcp_08_tool_capability_naming_convention.md](04_mcp_08_tool_capability_naming_convention.md) | Capability Naming Convention |
| ~~[04_mcp_07_mdq_rag_boundary.md]~~ | Deleted |
| [04_mcp_90_inconsistencies_and_known_issues.md](04_mcp_90_inconsistencies_and_known_issues.md) | Known Issues |

---

## Governance

Cross-cutting documentation rules and policies:

- [Documentation Policy](00_governance_01_documentation-policy.md)
- [Documentation Metadata](00_governance_02_documentation-metadata.md)
- [Issue and Uncertainty Management](00_governance_03_issue-and-uncertainty-management.md)
- [Documentation Checks](00_governance_04_documentation-checks.md)

## Migration Notes

### POST /v1/search (Deleted — 2026-06-26)

The `POST /v1/search` endpoint in `rag-pipeline-mcp` has been removed. Any code calling `rag_service_url` must be updated to the canonical MCP tool call format: `POST /v1/call_tool {"name": "rag_run_pipeline", "args": {"query": "...", "history_context": []}}`. This change is not backward compatible — no compatibility shim will be provided.

### Gateway-style Tool Names vs. Actual Tool Names (Clarifying Naming)

Mapping of initial "MCP Integrated Plugin System" proposals (Gateway-style function names) to current actual tool names:
`list_files` $\to$ `list_directory`, `read_file` $\to$ `read_text_file`, `search_file` $\to$ `search_files`, `invoke_script` $\to$ `shell_run`. When referring to tools in future proposals, use actual tool names instead of Gateway-style.

---

## Legacy Source Document Policy

**Policy: Deletion.** Since full content is preserved in Git history, archiving is unnecessary.

Old MCP source files (`04_spec_mcp.md`, `04_mcp-*.md`, `06_ref-mcp.md`) were kept during the documentation restructuring phase (plan 71-76), but were deleted as of 2026-06-26. If restoration is needed, use `git log --all -- docs/<filename>`.

---

## Known Limitations

- The known issues from `04_spec_mcp.md` section 13 have all been transferred to `04_mcp_90`.

## Unconfirmed Items

- [NC-002](00_governance_03_issue-and-uncertainty-management.md): Reason for unused ResultSource field
- [NC-005](00_governance_03_issue-and-uncertainty-management.md): Dead code detection for AuditLogRecord/ApprovalDecision (resolved)
- [NC-006](00_governance_03_issue-and-uncertainty-management.md): Future usability of result_source field

*Note: This section only lists major files defined in the routing table and files explicitly referenced in the text.*

## Related ADRs

- [ADR-003](adr/ADR-003-runtime-tool-registry-routing-authority.md) — RuntimeToolRegistryを唯一のルーティング権威とする
- [ADR-004](adr/ADR-004-environment-failure-handling-policy.md) — 環境における障害処理方針
- [ADR-007](adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md) — HTTP MCP採用とstdio非サポート
- [ADR-012](adr/ADR-012-git-mcp-server-side-write-enforcement.md) — Git MCP Server-Side Write Enforcement

## Related Documents

- `04_mcp_01_system_overview.md`
- `04_mcp_02_01_endpoints-and-transport.md`
- `04_mcp_03_01_dispatch-and-routing.md`
- `04_mcp_04_01_web-search-file-read-github.md`
- `04_mcp_05_01_access-control-and-allowlists.md`
- `04_mcp_06_01_purpose.md`
- `04_mcp_07_tool_schema_export_policy.md`
- `04_mcp_08_tool_capability_naming_convention.md`
- `04_mcp_90_inconsistencies_and_known_issues.md`

## Keywords

mcp
documentation
guide
routing
file-index
