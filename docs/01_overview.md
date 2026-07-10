---
title: "System Overview Index"
category: overview
tags:
  - system-overview
  - architecture
  - introduction
  - index
related:
  - 01_overview-arch-process.md
  - 01_overview-arch-pipelines.md
  - 01_overview-arch-features.md
  - 01_overview-files-build.md
  - 01_overview-files-rag.md
  - 01_overview-files-scripts.md
  - 01_overview-files-shared.md
  - 01_overview-files-config.md
  - 01_overview-files-misc.md
source:
  - 01_overview.md
---

# Overview & Architecture & File Structure (Index)

| File | Content |
|---|---|
| [01_overview-arch-process.md](01_overview-arch-process.md) | Process architecture (LLM services, MCP servers, configuration isolation) |
| [01_overview-arch-pipelines.md](01_overview-arch-pipelines.md) | Pipeline architecture (ingestion/query pipelines, turn processing order, workflow modes) |
| [01_overview-arch-features.md](01_overview-arch-features.md) | Feature architecture (implemented features, implementation notes) |
| [01_overview-files-build.md](01_overview-files-build.md) | Build and models file structure |
| [01_overview-files-rag.md](01_overview-files-rag.md) | RAG files file structure |
| [01_overview-files-scripts.md](01_overview-files-scripts.md) | Scripts file structure |
| [01_overview-files-shared.md](01_overview-files-shared.md) | Shared infrastructure file structure |
| [01_overview-files-config.md](01_overview-files-config.md) | Configuration file structure |
| [01_overview-files-misc.md](01_overview-files-misc.md) | Miscellaneous file structure |

## Implementation Intent

- Split `01_overview-arch.md` into 3 files at H2 boundaries: process, pipelines, features
- Split `01_overview-files.md` into 6 files at directory-based logical boundaries: build, rag, scripts, shared, config, misc
- Each file has YAML Front Matter with title, category, tags, related documents, and keywords
- This file is the system-wide overview index. For detailed document sets, see the catalog below.

## Implementation References

| File | Content |
|---|---|
| [01_overview-arch-process.md](01_overview-arch-process.md) | System-wide architecture |
| [01_overview-arch-pipelines.md](01_overview-arch-pipelines.md) | System-wide architecture |
| [01_overview-arch-features.md](01_overview-arch-features.md) | System-wide architecture |
| [01_overview-files-build.md](01_overview-files-build.md) | File/module structure |
| [01_overview-files-rag.md](01_overview-files-rag.md) | File/module structure |
| [01_overview-files-scripts.md](01_overview-files-scripts.md) | File/module structure |
| [01_overview-files-shared.md](01_overview-files-shared.md) | File/module structure |
| [01_overview-files-config.md](01_overview-files-config.md) | File/module structure |
| [01_overview-files-misc.md](01_overview-files-misc.md) | File/module structure |
| [02_deployment.md](02_deployment.md) | Installation steps, deployment |
| [03_rag_00_document-guide.md](03_rag_00_document-guide.md) | RAG document set guide |
| [03_rag_01_system_overview.md](03_rag_01_system_overview.md) | RAG system overview |
| [03_rag_02_ingestion_pipeline.md](03_rag_02_ingestion_pipeline.md) | Ingestion pipeline (CLI, API, config) |
| [03_rag_03_query_pipeline.md](03_rag_03_query_pipeline.md) | Query pipeline |
| [03_rag_04_data_model_and_interfaces.md](03_rag_04_data_model_and_interfaces.md) | Data model & interfaces |
| [03_rag_05_configuration_and_operations.md](03_rag_05_configuration_and_operations.md) | RAG configuration & operations |
| [03_rag_90_inconsistencies_and_known_issues.md](03_rag_90_inconsistencies_and_known_issues.md) | RAG known issues & inconsistencies |
| [04_mcp_00_document-guide.md](04_mcp_00_document-guide.md) | MCP document set guide |
| [04_mcp_01_system_overview.md](04_mcp_01_system_overview.md) | MCP system overview |
| [04_mcp_02_protocol_and_transport.md](04_mcp_02_protocol_and_transport.md) | MCP protocol & transport |
| [04_mcp_03_routing_lifecycle_and_execution.md](04_mcp_03_routing_lifecycle_and_execution.md) | Routing, lifecycle & execution |
| [04_mcp_04_server_catalog.md](04_mcp_04_server_catalog.md) | MCP server catalog (all 10 servers) |
| [04_mcp_05_security_and_safety_model.md](04_mcp_05_security_and_safety_model.md) | MCP security & safety model |
| [04_mcp_06_configuration_and_operations.md](04_mcp_06_configuration_and_operations.md) | MCP configuration & operations |
| [04_mcp_90_inconsistencies_and_known_issues.md](04_mcp_90_inconsistencies_and_known_issues.md) | MCP known issues & inconsistencies |
| [05_agent_00_document-guide.md](05_agent_00_document-guide.md) | Agent document set guide |
| [05_agent_01_system-overview.md](05_agent_01_system-overview.md) | Agent system overview |
| [05_agent_02_runtime-architecture.md](05_agent_02_runtime-architecture.md) | Runtime architecture |
| [05_agent_03_turn-processing-flow.md](05_agent_03_turn-processing-flow.md) | Turn processing flow |
| [05_agent_04_state-and-persistence.md](05_agent_04_state-and-persistence.md) | State & persistence |
| [05_agent_05_llm-and-streaming.md](05_agent_05_llm-and-streaming.md) | LLM & SSE streaming |
| [05_agent_06_tool-execution-and-approval.md](05_agent_06_tool-execution-and-approval.md) | Tool execution & approval flow |
| [05_agent_07_cli-and-commands.md](05_agent_07_cli-and-commands.md) | CLI & slash commands |
| [05_agent_08_configuration.md](05_agent_08_configuration.md) | Agent configuration |
| [05_agent_09_data-layer.md](05_agent_09_data-layer.md) | Data layer |
| [05_agent_10_operations-and-observability.md](05_agent_10_operations-and-observability.md) | Startup, verification, troubleshooting, OTel |
| [05_agent_11_extension-points.md](05_agent_11_extension-points.md) | Extension points (plugins) |
| [05_agent_12_reference-api.md](05_agent_12_reference-api.md) | API reference |
| [90_shared_00_document-guide.md](90_shared_00_document-guide.md) | shared/DB document set guide |
| [90_shared_01_overview.md](90_shared_01_overview.md) | shared/DB layer overview |
| [90_shared_02_types_and_protocols.md](90_shared_02_types_and_protocols.md) | Common types & protocol definitions |
| [90_shared_03_runtime_and_execution.md](90_shared_03_runtime_and_execution.md) | Execution infrastructure (ConfigLoader, Logger, plugins) |
| [90_shared_04_db_architecture_and_schema.md](90_shared_04_db_architecture_and_schema.md) | DB structure & schema |
| [90_shared_05_db_api_and_operations.md](90_shared_05_db_api_and_operations.md) | DB API & maintenance operations |
| [90_shared_90_inconsistencies_and_known_issues.md](90_shared_90_inconsistencies_and_known_issues.md) | shared/DB known issues & inconsistencies |

## Related Documents

- `01_overview-arch-process.md`
- `01_overview-arch-pipelines.md`
- `01_overview-arch-features.md`
- `01_overview-files-build.md`
- `01_overview-files-rag.md`
- `01_overview-files-scripts.md`
- `01_overview-files-shared.md`
- `01_overview-files-config.md`
- `01_overview-files-misc.md`
- `02_deployment.md`

## Keywords

system-overview
architecture
introduction
index
overview
deployment
rag
mcp
agent
shared
