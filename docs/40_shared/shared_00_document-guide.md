---
title: "Shared/DB Documentation Guide"
area: shared
tags:
  - shared
  - db
  - documentation
  - guide
  - routing
  - ai reference
related:
  - governance_03_issue-and-uncertainty-management.md
---

# Shared/DB Documentation Guide

The entry point for the restructured `shared/` and `db/` layered documentation. Read this first to determine which chapter to open.

---

## Purpose of This Document Set

Documents the `shared/` layer (common types, configuration, logging, OTel, tool routing) and the `db/` layer (SQLite connection management, schema, store protocols, maintenance).

---

## Recommended Reading Order (Human)

``` text
shared_01 Overview → shared_02 Types and Protocols → shared_03 Runtime and Execution
  → db_01-03 Architecture and Schema → db_04-07 API and Operations
```

---

## AI Query Routing

| Question | Reference Target |
|---|---|
| Usage/import rules for `shared/` | [shared_01_overview.md](shared_01_overview.md) |
| Type definitions, tool constants | [shared_02_01](shared_02_01_types_and_protocols-core-types.md) / [shared_02_03](shared_02_03_types_and_protocols-reference.md) |
| Tool and execution DTOs | [shared_02_02](shared_02_02_types_and_protocols-tool-and-execution-dto.md) |
| ConfigLoader, Logging | [shared_03_01](shared_03_01_runtime_and_execution-config-and-logging.md) |
| ToolExecutor | [shared_03_02](shared_03_02_runtime_and_execution-tool-executor-and-infrastructure.md) |
| LLMClient, MCP clients, routing | [shared_03_03](shared_03_03_runtime_and_execution-llm-and-mcp-clients.md) |
| Caching, health gate, AI reference guide | [shared_03_04](shared_03_04_runtime_and_execution-caching-and-reference.md) |
| Schema, migrations | [db_01](../41_db/db_01_architecture_and_schema-overview-and-config.md) / [db_02](../41_db/db_02_architecture_and_schema-schema-reference.md) / [db_03](../41_db/db_03_architecture_and_schema-migration-and-scaling.md) |
| Module boundaries, protocols, backends | [db_04](../41_db/db_04_api_and_operations-module-boundaries-and-helper.md) / [db_05](../41_db/db_05_api_and_operations-protocol-and-backend.md) |
| Maintenance, recovery | [db_06](../41_db/db_06_api_and_operations-maintenance-and-rotation.md) / [db_07](../41_db/db_07_api_and_operations-recovery-and-reference.md); ADR-008 Recovery Policy Matrix (recovery policy per persistence domain) |
| Active databases | [db_08](../41_db/db_08_active_databases.md) |
| Known issues | [governance_03_issue-and-uncertainty-management.md](../00_governance/governance_03_issue-and-uncertainty-management.md) |

---

## Navigation to Known Issues

Refer to [governance_03_issue-and-uncertainty-management.md](../00_governance/governance_03_issue-and-uncertainty-management.md) (Part 1, Area: Shared/DB) for a full catalog of known inconsistencies. Note that `ArtifactEvent` does not involve an event bus (it is data definition only).

---

## Canonical Sources

Canonical sources for this area are defined in the [Canonical Source Registry](../00_governance/governance_01_documentation-policy.md#canonical-source-registry). This area guide does not maintain an independent mapping.

---

## File Index

Read the `shared/` documentation group (`shared_01` → `shared_02_*` → `shared_03_*`) and then the `db/` documentation group in [41_db](../41_db/db_01_architecture_and_schema-overview-and-config.md) (`db_01` → `db_08`).

---

## Governance

Cross-cutting documentation rules and policies:

- [Documentation Policy](../00_governance/governance_01_documentation-policy.md)
- [Documentation Metadata](../00_governance/governance_02_documentation-metadata.md)
- [Issue and Uncertainty Management](../00_governance/governance_03_issue-and-uncertainty-management.md)
- [Documentation Checks](../00_governance/governance_04_documentation-checks.md)

## Guidance for Safe AI Use

1. `load_all()` only includes `agent.toml` (`_BASE_CONFIG_FILES = ("agent.toml",)`, see the Process Separation Policy in [shared_03_01](shared_03_01_runtime_and_execution-config-and-logging.md#2a-process-separation-policy-config-isolation-policy)). A `rag_pipeline.toml` configuration file does not exist — each MCP server (including rag-pipeline-mcp) loads its own `config/<key>_mcp_server.toml` due to process isolation policy, so there is no need for explicit loading on the agent side.
2. `orjson.dumps()` returns `bytes` (requires `.decode()`).
3. `ArtifactEvent` is data-only and has no event bus.
4. `LLMMessage` has 7 fields (including `importance`/`pinned`).
5. Do NOT perform manual INSERTs because DB triggers automatically synchronize `chunks_fts`.
6. `SQLiteHelper("workflow")` is enabled (see `db_01`).
7. For details on `LLMClient`, see `agent_05_llm-and-streaming.md` (not covered by this document set).

## Related ADRs

- [ADR-008](../10_adr/ADR-008-sqlite-4db-separation.md) — Separating SQLite into Four Databases

## Keywords

- shared
- db
- documentation
- guide
- routing
- ai reference
