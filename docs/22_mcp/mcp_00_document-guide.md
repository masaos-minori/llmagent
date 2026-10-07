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
  - mcp_01_system_overview.md
  - mcp_02_01_endpoints-and-transport.md
  - mcp_03_01_dispatch-and-routing.md
  - mcp_04_01_web-search-file-read-github.md
  - mcp_05_01_access-control-and-allowlists.md
  - mcp_06_01_configuration-file-inventory.md
  - mcp_07_tool_schema_export_policy.md
  - mcp_08_tool_capability_naming_convention.md
  - governance_03_issue-and-uncertainty-management.md
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
01 → 02 → 03 → 04 → 05 → 06
```

---

## Responsibility Boundaries

### Agent Query Routing Table

| Question | File |
|---|---|
| Which MCP servers exist and what do they do? What are their ports and startup modes? | `mcp_01` |
| `/v1/call_tool`, Bearer authentication, and audit log formats | `mcp_02` |
| Tool routing, ToolExecutor, and adding new servers | `mcp_03` (config defaults are in `mcp_06` Major Default Values) |
| Handling of tool enabled/disabled_reason, config_dependent, and RuntimeToolRegistry | `mcp_03_06` |
| Tools provided by web-search/github/shell/mdq MCPs. mdq-mcp FTS5 search is production-ready; hybrid search is unimplemented | `mcp_04` (mdq-mcp only has FTS5 search implemented) |
| allowed_dirs/allowed_repos, fail-closed/fail-open, dry_run, risk tiers, MDQ/RAG boundary | `mcp_05` |
| Config file list, health verification, default values, startup warnings, failure diagnosis | `mcp_06` |
| Naming convention for tool schema modules, TOOL_LIST exports, and cleanup of _MCP_TOOLS references | `mcp_07` |
| Tool capability naming convention (domain.action format) | `mcp_08` |
| What is broken or unimplemented | [governance_03_issue-and-uncertainty-management.md](../00_governance/governance_03_issue-and-uncertainty-management.md) |

---

## Navigation to Known Issues

Open issues and uncertainties for MCP are managed in [governance_03_issue-and-uncertainty-management.md](../00_governance/governance_03_issue-and-uncertainty-management.md). Per-server implementation notes are in [mcp_04_04_mdq.md](mcp_04_04_mdq.md) and [mcp_05_05_mdq-enforcement-and-lockdown.md](mcp_05_05_mdq-enforcement-and-lockdown.md).

---

## Canonical Sources

Canonical sources for this area are defined in the [Canonical Source Registry](../00_governance/governance_01_documentation-policy.md#canonical-source-registry). This area guide does not maintain an independent mapping.

---

## File Index

| File | Description |
|---|---|
| `mcp_00_document-guide.md` | Entry Point |
| [mcp_01_system_overview.md](mcp_01_system_overview.md) | System Overview |
| [mcp_01_tool_ownership_matrix.md](mcp_01_tool_ownership_matrix.md) | Tool Ownership Matrix |
| [mcp_02_service_boundaries.md](mcp_02_service_boundaries.md) | Service Boundary Definitions |
| [mcp_02_01](mcp_02_01_endpoints-and-transport.md) to [_02](mcp_02_02_startup-modes-and-health.md)/[_03](mcp_02_03_audit-logging-and-errors.md) | Protocol and Transport (3 parts) |
| [mcp_03_01](mcp_03_01_dispatch-and-routing.md) to [_02](mcp_03_02_tool-registry.md)/[_03](mcp_03_03_transport-and-health.md)/[_04](mcp_03_04_tool-call-tracing-and-lifecycle.md)/[_05](mcp_03_05_lifecycle-and-new-server.md)/[_06](mcp_03_06_tool-runtime-availability-metadata.md) | Routing and Lifecycle (6 parts) |
| [mcp_04_01](mcp_04_01_web-search-file-read-github.md) to [_02](mcp_04_02_file-write-file-delete-shell.md)/[_03](mcp_04_03_rag-pipeline-and-cicd.md)/[_04](mcp_04_04_mdq.md)/[_05](mcp_04_05_git.md) | Server Catalog (5 parts, _04=mdq; browser page fetch is part of web-search-mcp under _01) |
| [mcp_05_01](mcp_05_01_access-control-and-allowlists.md) to [_02](mcp_05_02_auth-profiles-and-sandboxing.md)/[_03](mcp_05_03_fail-open-fail-closed-and-risk-tiers.md)/[_04](mcp_05_04_mdq-rag-boundary.md)/[_05](mcp_05_05_mdq-enforcement-and-lockdown.md) | Security Model (5 parts) |
| [mcp_06_01_configuration-file-inventory.md](mcp_06_01_configuration-file-inventory.md) | Config Inventory, purpose and major default values |
| [mcp_06_02_mcpserverconfig-fields-agenttoml-mcp_servers.md](mcp_06_02_mcpserverconfig-fields-agenttoml-mcp_servers.md) | McpServerConfig Fields |
| [mcp_06_03_long-running-http-operation-startup_modesubprocess.md](mcp_06_03_long-running-http-operation-startup_modesubprocess.md) | Long-running Operations |
| [mcp_06_04_verification-methods.md](mcp_06_04_verification-methods.md) | Verification Methods |
| [mcp_06_05_reading-audit-logs.md](mcp_06_05_reading-audit-logs.md) | Audit Log |
| [mcp_06_06_end-to-end-tool-call-tracing.md](mcp_06_06_end-to-end-tool-call-tracing.md) | Tracing |
| [mcp_06_07_mcp-failure-diagnosis.md](mcp_06_07_mcp-failure-diagnosis.md) | Failure Diagnosis |
| [mcp_06_08_settings-with-high-operational-impact.md](mcp_06_08_settings-with-high-operational-impact.md) | Settings with High Operational Impact |
| [mcp_06_09_startup-validation-behavior-tool_definitions_strict.md](mcp_06_09_startup-validation-behavior-tool_definitions_strict.md) | Startup Validation |
| [mcp_06_10_health-reasons-and-error-kinds.md](mcp_06_10_health-reasons-and-error-kinds.md) | health_reason / HealthRegistry |
| [mcp_06_11_new-tool-registration-procedure.md](mcp_06_11_new-tool-registration-procedure.md) | New Tool Registration |
| [mcp_06_12_new-mcp-server-addition-checklist.md](mcp_06_12_new-mcp-server-addition-checklist.md) | New Server Addition Checklist |
| [mcp_06_13_pre-production-fail-open-checklist.md](mcp_06_13_pre-production-fail-open-checklist.md) | Pre-Production Checklist |
| [mcp_06_14_mcp-authentication-setup.md](mcp_06_14_mcp-authentication-setup.md) | Authentication Setup |
| [../91_security/security_01_architecture-and-trust-boundaries.md](../91_security/security_01_architecture-and-trust-boundaries.md) | System architecture / trust boundaries / threat modeling (canonical cross-cutting source) |
| [security_02_high-risk-tool-common-policy.md](../91_security/security_02_high-risk-tool-common-policy.md) | High-risk MCP tool common policy (path/repo allowlists, traversal prevention, approval-risk tier mapping) |
| [mcp_07_tool_schema_export_policy.md](mcp_07_tool_schema_export_policy.md) | Schema Export |
| [mcp_08_tool_capability_naming_convention.md](mcp_08_tool_capability_naming_convention.md) | Capability Naming Convention |
| [governance_03_issue-and-uncertainty-management.md](../00_governance/governance_03_issue-and-uncertainty-management.md) | Known Issues (all areas) |

---

*Note: This section only lists major files defined in the routing table and files explicitly referenced in the text.*

## Governance

Cross-cutting documentation rules and policies:

- [Documentation Policy](../00_governance/governance_01_documentation-policy.md)
- [Documentation Metadata](../00_governance/governance_02_documentation-metadata.md)
- [Issue and Uncertainty Management](../00_governance/governance_03_issue-and-uncertainty-management.md)
- [Documentation Checks](../00_governance/governance_04_documentation-checks.md)

## Known Limitations

None currently known. Open items are tracked in `governance_03_issue-and-uncertainty-management.md` (Part 1, Area: MCP).

## Related ADRs

- [ADR-003](../10_adr/ADR-003-runtime-tool-registry-routing-authority.md) — RuntimeToolRegistry as the Sole Routing Authority
- [ADR-004](../10_adr/ADR-004-environment-failure-handling-policy.md) — Failure Handling Policy Across Environments
- [ADR-007](../10_adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md) — Adoption of HTTP MCP and Non-Support of stdio
- [ADR-012](../10_adr/ADR-012-git-mcp-server-side-write-enforcement.md) — Git MCP Server-Side Write Enforcement

## Keywords

mcp
documentation
guide
routing
file-index
