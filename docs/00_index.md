# Documentation Overview

Project documentation top-level navigation hub. It lists all top-level categories and links to their entry files. `01_overview.md` continues to exist as the system-wide architecture overview and is not replaced by this file.

## Categories

- [Overview](01_overview.md) — System-wide architecture and file structure
- [Deployment](02_deployment.md) — Environment setup and deployment procedures
- [RAG](03_rag_00_document-guide.md) — Retrieval-Augmented Generation pipeline
- [MCP](04_mcp_00_document-guide.md) — Model Context Protocol servers
- [Agent](05_agent_00_document-guide.md) — Agent REPL system and operation
- [Event Bus](06_eventbus_00_document-guide.md) — Event Bus infrastructure
- [Shared/DB](90_shared_00_document-guide.md) — Shared infrastructure and database layer
- [Documentation Policy](00_governance_01_documentation-policy.md) — Canonical source precedence (including decision target → canonical source mapping), conflict resolution, ADR conventions
- [Documentation Metadata](00_governance_02_documentation-metadata.md) — Metadata conventions, terminology glossary, link rules
- [Issue and Uncertainty Management](00_governance_03_issue-and-uncertainty-management.md) — Known Issues templates, Needs Confirmation inventory
- [Documentation Checks](00_governance_04_documentation-checks.md) — Automated and manual validation checks, governance verification matrix
- [ADR Index](adr-index.md) — ADR list, dependency graph, invariant verification matrix
- [Known Issues](#known-issues) — Known inconsistencies per category

## Recommended Reading Order

1. [System Overview](01_overview.md) — Start here to understand the overall system picture
2. [Deployment Guide](02_deployment.md) — Set up your environment
3. Select an area of interest:
   - [RAG Pipeline](03_rag_00_document-guide.md)
   - [MCP Servers](04_mcp_00_document-guide.md)
   - [Agent System](05_agent_00_document-guide.md)
   - [Event Bus](06_eventbus_00_document-guide.md)
   - [Shared Infrastructure](90_shared_00_document-guide.md)
4. Check for known issues in your area of interest

## Known Issues

All areas' known inconsistencies and unresolved items are tracked in one place:

- [Issue and Uncertainty Management](00_governance_03_issue-and-uncertainty-management.md) — Part 1: Known Issues (all areas)

## Document References by Task

Migrated from `routing.md`. Load only the necessary documents according to the task type. DO NOT load all `docs/*.md`.

### Domain specs

| Task scope | Reference docs |
|---|---|
| Agent spec (overview, design, known issues) | `05_agent_00_document-guide.md` + `05_agent_01_system-overview.md` |
| Agent known issues / inconsistencies | `00_governance_03_issue-and-uncertainty-management.md` (Part 1, Area: Agent) |
| MCP server spec (overview, design, known issues) | `04_mcp_00_document-guide.md` + `04_mcp_01_system_overview.md` |
| RAG pipeline spec (overview, design, known issues) | `03_rag_00_document-guide.md` + `03_rag_01_system_overview.md` |
| MDQ vs RAG boundary | `04_mcp_05_01_access-control-and-allowlists.md` MDQ vs RAG Boundary |
| DB layer spec (schema, ops, known issues) | `90_shared_04_01_db_architecture_and_schema-overview-and-config.md` + `90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md` |
| Shared infra spec (config, logging, types, constants) | `90_shared_00_document-guide.md` + `90_shared_01_overview.md` |

### Implementation reference

#### System overview

| Task scope | Reference docs |
|---|---|
| System-wide architecture overview | `01_overview.md` (indexes `01_overview-arch-*.md`) |
| File / module layout | `01_overview.md` (indexes `01_overview-files-*.md`) |
| `tools/` scripts overview (CI checks, doc formatting, historical doc migration) | `tools/01_overview.md` |
| Documentation set index / navigation | `00_index.md` |
| Deployment / env setup | `02_deployment.md` + `rules/env.md` |

#### Agent

| Task scope | Reference docs |
|---|---|
| Memory layer (types / store / retriever / extract / jsonl_store / services.py) | `05_agent_04_01_state-and-persistence-state-model.md` + `05_agent_08_01_configuration-loading-agent-config.md` + `05_agent_12_03_memory-module-ref-core-and-store.md` + `05_agent_12_04_memory-module-ref-retrieval-and-injection.md` |
| OTel observability (otel_tracer.py) | `05_agent_10_01_operations-and-observability-startup-and-health.md` + `05_agent_08_01_configuration-loading-agent-config.md` |
| Agent REPL slash commands (`CommandRegistry`) | `05_agent_07_01_cli-and-commands-cli-reference.md` |
| Agent startup / verification / troubleshooting | `05_agent_10_01_operations-and-observability-startup-and-health.md` |
| Agent features / slash commands / tool calling | `05_agent_01_system-overview.md` + `05_agent_07_01_cli-and-commands-cli-reference.md` |
| AgentREPL class structure | `05_agent_02_runtime-architecture.md` + `05_agent_13_reference-api.md` |
| Agent REPL flow / tool execution | `05_agent_03_01_turn-processing-flow-overview.md` + `05_agent_06_01_tool-execution-and-approval-execution.md` |
| AgentContext / DI hub | `05_agent_02_runtime-architecture.md` + `05_agent_04_01_state-and-persistence-state-model.md` |
| AgentConfig / config constants | `05_agent_08_01_configuration-loading-agent-config.md` |
| Session / DB persistence | `05_agent_09_01_data-layer-session-db.md` + `90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md` |
| LLM client (streaming/retry) | `05_agent_05_llm-and-streaming.md` |
| CLI view / readline | `05_agent_07_01_cli-and-commands-cli-reference.md` |

#### MCP

| Task scope | Reference docs |
|---|---|
| MCP server implementation | `04_mcp_02_01_endpoints-and-transport.md` + `04_mcp_03_01_dispatch-and-routing.md` |
| MCP transport / startup_mode / lifecycle | `04_mcp_03_01_dispatch-and-routing.md` + `05_agent_08_01_configuration-loading-agent-config.md` |
| ToolRouteResolver / route_resolver.py | `04_mcp_03_01_dispatch-and-routing.md` + `05_agent_08_01_configuration-loading-agent-config.md` |
| ServerLifecycleManager / lifecycle.py | `04_mcp_03_01_dispatch-and-routing.md` + `05_agent_02_runtime-architecture.md` |
| ToolSpec / tool_spec.py (execution metadata DAG) | `05_agent_08_01_configuration-loading-agent-config.md` |
| tool_cache.py (_CacheEntry LRU cache) | `05_agent_08_01_configuration-loading-agent-config.md` |
| TransportType / StartupMode / HealthcheckMode enums (mcp_config.py) | `04_mcp_03_01_dispatch-and-routing.md` + `04_mcp_06_02_configuration-file-inventory.md` |
| MCP security model (allowlist / denylist / fail-closed) | `04_mcp_05_01_access-control-and-allowlists.md` |
|---|---|
| System security architecture / trust boundaries / threat model | `00_security_01_architecture-and-trust-boundaries.md` |
| High-risk MCP tool policy (path/repo allowlists, traversal prevention, approval-to-risk-tier mapping) | `00_security_02_high-risk-tool-common-policy.md` |
| Any MCP server (catalog only) | `04_mcp_04_01_web-search-file-read-github.md` |
| mdq-mcp specifics | `04_mcp_04_04_mdq.md` + `00_governance_03_issue-and-uncertainty-management.md` (Part 1, Area: MCP) |
| MCP known bugs / inconsistencies | `00_governance_03_issue-and-uncertainty-management.md` (Part 1, Area: MCP) |

#### RAG

| Task scope | Reference docs |
|---|---|
| RAG pipeline modification | `03_rag_03_01_query_pipeline-overview.md` + `03_rag_04_05_dto-types.md` + `90_shared_02_01_types_and_protocols-core-types.md` |
| RAG types / repository / LLM utils | `03_rag_04_05_dto-types.md` + `90_shared_02_01_types_and_protocols-core-types.md` |
| Ingestion pipeline run (execute commands, file lifecycle) | `03_rag_02_01_ingestion_pipeline-overview.md` + `03_rag_05_1-configuration-reference.md` |
| crawler.py changes / API reference | `03_rag_02_02_ingestion_pipeline-crawler.md` |
| chunk_splitter.py changes / API reference | `03_rag_02_03_ingestion_pipeline-chunksplitter.md` |
| ingester.py changes / API reference | `03_rag_02_04_ingestion_pipeline-ingester.md` |
| RAG known bugs / inconsistencies | `00_governance_03_issue-and-uncertainty-management.md` (Part 1, Area: RAG) |
| RAG configuration parameters | `03_rag_05_1-configuration-reference.md` |

#### DB / Shared

| Task scope | Reference docs |
|---|---|
| SQLite / DB connection / WAL / transactions | `90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md` |
| Config / logger / formatters / rag_utils | `90_shared_03_01_runtime_and_execution-config-and-logging.md` |
| Shared layer / DB layer known issues / inconsistencies | `00_governance_03_issue-and-uncertainty-management.md` (Part 1, Area: Shared/DB) |

#### Event Bus

| Task scope | Reference docs |
|---|---|
| Event Bus (overview) | `06_eventbus_01_system-overview.md` |
| Event Bus (HTTP API) | `06_eventbus_02_operations.md` |
| Event Bus (persistence) | `06_eventbus_03_persistence_schema_and_replay.md` |
| Event Bus (DLQ/offsets) | `06_eventbus_04_dlq_offsets_and_delivery_semantics.md` |
| Event Bus (config/ops) | `06_eventbus_05_configuration-and-operations.md` |
| Event Bus (API ref) | `06_eventbus_06_reference-api.md` |
| Event Bus (issues) | `00_governance_03_issue-and-uncertainty-management.md` (Part 1, Area: EventBus) |

## Related Documents

- `01_overview.md`
- `02_deployment.md`
- `03_rag_00_document-guide.md`
- `04_mcp_00_document-guide.md`
- `05_agent_00_document-guide.md`
- `06_eventbus_00_document-guide.md`
- `90_shared_00_document-guide.md`

## Keywords

documentation
navigation
overview
index
knowledge-base
