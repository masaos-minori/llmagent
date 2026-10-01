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
source:
  - shared_00_document-guide.md
---

# Shared/DB Documentation Guide

The entry point for the restructured `shared/` and `db/` layered documentation. Read this first to determine which chapter to open.

---

## Purpose of This Document Set

Documents the `shared/` layer (common types, configuration, logging, OTel, tool routing) and the `db/` layer (SQLite connection management, schema, store protocols, maintenance).

---

## Recommended Reading Order (Human)

``` text
01 Overview → 02 Types and Protocols → 03 Runtime and Execution
  → 04 DB Architecture/Schema → 05 DB API and Operations → 90 Inconsistencies
```

---

## AI Query Routing

| Question | Reference Target |
|---|---|
| Usage/import rules for `shared/` | `overview` |
| Type definitions, tool constants | `02_core-types` / `02_reference` |
| ConfigLoader, Logging | `03_config-and-logging` |
| ToolExecutor, LLMClient | `03_tool-executor` / `03_llm-and-mcp-clients` |
| Schema, Migrations | `04_overview` / `04_schema` / `04_migration` |
| Module boundaries, Protocols | `05_module-boundaries` / `05_protocol` |
| Maintenance, Recovery | `05_maintenance` / `05_recovery` (API/operational); ADR-008 Recovery Policy Matrix (recovery policy per persistence domain) |
| Known issues | `90_inconsistencies` |

---

## Navigation to Major Known Issues

Refer to [governance_03_issue-and-uncertainty-management.md](../00_governance/governance_03_issue-and-uncertainty-management.md) (Part 1, Area: Shared/DB) for a full catalog of known inconsistencies. Note that `ArtifactEvent` does not involve an event bus (it is data definition only).

---

## Canonical Sources

Canonical sources for this area are defined in the [Canonical Source Registry](../00_governance/governance_01_documentation-policy.md#canonical-source-registry). This area guide does not maintain an independent mapping.

---

## File Index

Read the `shared/` documentation group in order: `overview` → `02_types` → `03_runtime`. Read the `db/` documentation group in order: `04_schema` → `05_operations`. (Explicit in code)

---

## Governance

Cross-cutting documentation rules and policies:

- [Documentation Policy](../00_governance/governance_01_documentation-policy.md)
- [Documentation Metadata](../00_governance/governance_02_documentation-metadata.md)
- [Issue and Uncertainty Management](../00_governance/governance_03_issue-and-uncertainty-management.md)
- [Documentation Checks](../00_governance/governance_04_documentation-checks.md)

## Guidance for Safe AI Use

1. `load_all()` only includes `agent.toml` (`_BASE_CONFIG_FILES = ("agent.toml",)`, see `shared_03_01` section 2a). A `rag_pipeline.toml` configuration file does not exist — each MCP server (including rag-pipeline-mcp) loads its own `config/<key>_mcp_server.toml` due to process isolation policy, so there is no need for explicit loading on the agent side.
2. `orjson.dumps()` returns `bytes` (requires `.decode()`).
3. `ArtifactEvent` is data-only and has no event bus.
4. `LLMMessage` has 7 fields (including `importance`/`pinned`; not 5 as in old ~~~~~~~~~~~~~~~~~~~~~~~~`90_shared.md`~~ (deleted)~~ (deleted)~~ (deleted)~~ (deleted)~~ (deleted)~~ (deleted)~~ (deleted)~~ (deleted)~~ (deleted)~~ (deleted)~~ (deleted)~~ (deleted)).
5. Do NOT perform manual INSERTs because DB triggers automatically synchronize `chunks_fts`.
6. `SQLiteHelper("workflow")` is enabled (see `db_01`).
7. For details on `LLMClient`, see `agent_05_llm-and-streaming.md` (not covered by this document set).

## Related ADRs

- [ADR-008](../10_adr/ADR-008-sqlite-4db-separation.md) — Separating SQLite into Four Databases
