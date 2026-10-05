---
title: "Documentation Overview"
area: overview
tags:
  - overview
  - navigation
  - index
related:
  - overview_00_document-guide.md
  - deployment_00_document-guide.md
  - security_00_document-guide.md
  - rag_00_document-guide.md
  - mcp_00_document-guide.md
  - agent_00_document-guide.md
  - eventbus_00_document-guide.md
  - shared_00_document-guide.md
---
# Documentation Overview

Project documentation top-level navigation hub. It lists all top-level categories and links to their entry files. `01_overview/overview_00_document-guide.md` continues to exist as the system-wide architecture overview and is not replaced by this file.

## Categories

- [Overview](01_overview/overview_00_document-guide.md) — System-wide architecture and file structure
- [Deployment](90_deployment/deployment_00_document-guide.md) — Environment setup and deployment procedures
- [Security](91_security/security_00_document-guide.md) — Trust boundaries and high-risk tool policy
- [RAG](21_rag/rag_00_document-guide.md) — Retrieval-Augmented Generation pipeline
- [MCP](22_mcp/mcp_00_document-guide.md) — Model Context Protocol servers
- [Agent](23_agent/agent_00_document-guide.md) — Agent REPL system and operation
- [Event Bus](24_eventbus/eventbus_00_document-guide.md) — Event Bus infrastructure
- [Shared/DB](40_shared/shared_00_document-guide.md) — Shared infrastructure and database layer
- [Documentation Policy](00_governance/governance_01_documentation-policy.md) — Canonical source precedence (including decision target → canonical source mapping), conflict resolution, ADR conventions
- [Documentation Metadata](00_governance/governance_02_documentation-metadata.md) — Metadata conventions, terminology glossary, link rules
- [Issue and Uncertainty Management](00_governance/governance_03_issue-and-uncertainty-management.md) — Known Issues templates, inventory of unconfirmed claims
- [Documentation Checks](00_governance/governance_04_documentation-checks.md) — Automated and manual validation checks, governance verification matrix
- [Change Impact and Dependency Graphs](00_governance/governance_05_change-impact-and-dependency-graphs.md) — Change impact rules, RACI model, dependency-graph taxonomy
- [ADR Index](10_adr/adr-index.md) — ADR list, dependency graph, invariant verification matrix
- [Known Issues](#known-issues) — Known inconsistencies per category

## Recommended Reading Order

1. [System Overview](01_overview/overview_00_document-guide.md) — Start here to understand the overall system picture
2. [Deployment Guide](90_deployment/deployment_00_document-guide.md) — Set up your environment
3. Select an area of interest:
   - [RAG Pipeline](21_rag/rag_00_document-guide.md)
   - [MCP Servers](22_mcp/mcp_00_document-guide.md)
   - [Agent System](23_agent/agent_00_document-guide.md)
   - [Event Bus](24_eventbus/eventbus_00_document-guide.md)
   - [Shared Infrastructure](40_shared/shared_00_document-guide.md)
4. Check for known issues in your area of interest

## Known Issues

All areas' known inconsistencies and unresolved items are tracked in one place:

- [Issue and Uncertainty Management](00_governance/governance_03_issue-and-uncertainty-management.md) — Part 1: Known Issues (all areas)

## Document References by Task

Load only the necessary documents according to the task type. DO NOT load all `docs/*.md`.

### Domain specs

| Task scope | Reference docs |
|---|---|
| Agent spec (overview, design, known issues) | `23_agent/agent_00_document-guide.md` + `23_agent/agent_01_system-overview.md` |
| Agent known issues / inconsistencies | `00_governance/governance_03_issue-and-uncertainty-management.md` (Part 1, Area: Agent) |
| MCP server spec (overview, design, known issues) | `22_mcp/mcp_00_document-guide.md` + `22_mcp/mcp_01_system_overview.md` |
| RAG pipeline spec (overview, design, known issues) | `21_rag/rag_00_document-guide.md` + `21_rag/rag_01_system_overview.md` |
| MDQ vs RAG boundary | `22_mcp/mcp_05_04_mdq-rag-boundary.md` |
| DB layer spec (schema, ops, known issues) | `41_db/db_01_architecture_and_schema-overview-and-config.md` + `41_db/db_04_api_and_operations-module-boundaries-and-helper.md` |
| Shared infra spec (config, logging, types, constants) | `40_shared/shared_00_document-guide.md` + `40_shared/shared_01_overview.md` |

### Implementation reference

#### System overview

| Task scope | Reference docs |
|---|---|
| System-wide architecture overview | `01_overview/overview_00_document-guide.md` (indexes `overview-arch-*.md`) |
| File / module layout | `01_overview/overview_00_document-guide.md` (indexes `overview-files-*.md`) |
| `tools/` scripts overview (CI checks, doc formatting, historical doc migration) | `tools/TOOL_DESCRIPTIONS.md` |
| Documentation set index / navigation | `00_index.md` |
| Deployment / env setup | `90_deployment/deployment_01_deployment.md` + `rules/env.md` |

#### Agent

| Task scope | Reference docs |
|---|---|
| Memory layer (types / store / retriever / extract / jsonl_store / services.py) | `23_agent/agent_04_01_state-and-persistence-state-model.md` + `23_agent/agent_08_01_configuration-loading-agent-config.md` + `23_agent/agent_12_03_memory-module-ref-core-and-store.md` + `23_agent/agent_12_04_memory-module-ref-retrieval-and-injection.md` |
| OTel observability (otel_tracer.py) | `23_agent/agent_10_01_operations-and-observability-startup-and-health.md` + `23_agent/agent_08_01_configuration-loading-agent-config.md` |
| Agent REPL slash commands (`CommandRegistry`) | `23_agent/agent_07_03_cli-and-commands-command-registry.md` |
| Agent startup / verification / troubleshooting | `23_agent/agent_10_01_operations-and-observability-startup-and-health.md` |
| Agent features / slash commands / tool calling | `23_agent/agent_01_system-overview.md` + `23_agent/agent_07_03_cli-and-commands-command-registry.md` |
| AgentREPL class structure | `23_agent/agent_02_runtime-architecture.md` + `23_agent/agent_13_reference-api.md` |
| Agent REPL flow / tool execution | `23_agent/agent_03_01_turn-processing-flow-overview.md` + `23_agent/agent_06_01_tool-execution-and-approval-execution.md` |
| AgentContext / DI hub | `23_agent/agent_02_runtime-architecture.md` + `23_agent/agent_04_01_state-and-persistence-state-model.md` |
| AgentConfig / config constants | `23_agent/agent_08_01_configuration-loading-agent-config.md` |
| Session / DB persistence | `23_agent/agent_09_01_data-layer-session-db.md` + `41_db/db_04_api_and_operations-module-boundaries-and-helper.md` |
| LLM client (streaming/retry) | `23_agent/agent_05_llm-and-streaming.md` |
| CLI view / readline | `23_agent/agent_07_02_cli-and-commands-cliview.md` + `23_agent/agent_07_05_cli-and-commands-repl-io.md` |

#### MCP

| Task scope | Reference docs |
|---|---|
| MCP server implementation | `22_mcp/mcp_02_01_endpoints-and-transport.md` + `22_mcp/mcp_03_01_dispatch-and-routing.md` |
| MCP transport / startup_mode / lifecycle | `22_mcp/mcp_03_01_dispatch-and-routing.md` + `23_agent/agent_08_01_configuration-loading-agent-config.md` |
| ToolRouteResolver / route_resolver.py | `22_mcp/mcp_03_01_dispatch-and-routing.md` + `23_agent/agent_08_01_configuration-loading-agent-config.md` |
| HttpServerLifecycleManager / http_lifecycle.py | `22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md` + `23_agent/agent_02_runtime-architecture.md` |
| ToolSpec / tool_spec.py (execution metadata DAG) | `23_agent/agent_08_01_configuration-loading-agent-config.md` |
| tool_cache.py (CacheEntry LRU cache) | `23_agent/agent_08_01_configuration-loading-agent-config.md` |
| TransportType / StartupMode enums (mcp_config.py) | `22_mcp/mcp_03_01_dispatch-and-routing.md` + `22_mcp/mcp_06_02_configuration-file-inventory.md` |
| MCP security model (allowlist / denylist / fail-closed) | `22_mcp/mcp_05_01_access-control-and-allowlists.md` |
| System security architecture / trust boundaries / threat model | `91_security/security_01_architecture-and-trust-boundaries.md` |
| High-risk MCP tool policy (path/repo allowlists, traversal prevention, approval-to-risk-tier mapping) | `91_security/security_02_high-risk-tool-common-policy.md` |
| Any MCP server (catalog only) | `22_mcp/mcp_04_01_web-search-file-read-github.md` |
| mdq-mcp specifics | `22_mcp/mcp_04_04_mdq.md` + `00_governance/governance_03_issue-and-uncertainty-management.md` (Part 1, Area: MCP) |
| MCP known bugs / inconsistencies | `00_governance/governance_03_issue-and-uncertainty-management.md` (Part 1, Area: MCP) |

#### RAG

| Task scope | Reference docs |
|---|---|
| RAG pipeline modification | `21_rag/rag_03_01_query_pipeline-overview.md` + `21_rag/rag_04_05_dto-types.md` + `40_shared/shared_02_01_types_and_protocols-core-types.md` |
| RAG types / repository / LLM utils | `21_rag/rag_04_05_dto-types.md` + `40_shared/shared_02_01_types_and_protocols-core-types.md` |
| Ingestion pipeline run (execute commands, file lifecycle) | `21_rag/rag_02_01_ingestion_pipeline-overview.md` + `21_rag/rag_05_1-configuration-reference.md` |
| crawler.py changes / API reference | `21_rag/rag_02_02_ingestion_pipeline-crawler.md` |
| chunk_splitter.py changes / API reference | `21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md` |
| ingester.py changes / API reference | `21_rag/rag_02_04_ingestion_pipeline-ingester.md` |
| RAG known bugs / inconsistencies | `00_governance/governance_03_issue-and-uncertainty-management.md` (Part 1, Area: RAG) |
| RAG configuration parameters | `21_rag/rag_05_1-configuration-reference.md` |

#### DB / Shared

| Task scope | Reference docs |
|---|---|
| SQLite / DB connection / WAL / transactions | `41_db/db_04_api_and_operations-module-boundaries-and-helper.md` |
| Config / logger / formatters / rag_utils | `40_shared/shared_03_01_runtime_and_execution-config-and-logging.md` |
| Shared layer / DB layer known issues / inconsistencies | `00_governance/governance_03_issue-and-uncertainty-management.md` (Part 1, Area: Shared/DB) |

#### Event Bus

| Task scope | Reference docs |
|---|---|
| Event Bus (overview) | `24_eventbus/eventbus_01_system-overview.md` |
| Event Bus (HTTP API) | `24_eventbus/eventbus_02_api-reference-index.md` |
| Event Bus (persistence) | `24_eventbus/eventbus_07_persistence_schema_and_replay.md` |
| Event Bus (DLQ/offsets) | `24_eventbus/eventbus_06_dlq_offsets_and_delivery_semantics.md` |
| Event Bus (config/ops) | `24_eventbus/eventbus_09_configuration-and-operations.md` |
| Event Bus (API ref) | `24_eventbus/eventbus_10_reference_api.md` |
| Event Bus (issues) | `00_governance/governance_03_issue-and-uncertainty-management.md` (Part 1, Area: EventBus) |

## Keywords

documentation
navigation
overview
index
knowledge-base
