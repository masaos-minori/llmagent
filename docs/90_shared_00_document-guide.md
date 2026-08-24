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
  - 90_shared_90_inconsistencies_and_known_issues.md
source:
  - 90_shared_00_document-guide.md
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
| Usage/import rules for `shared/` | `01_overview` / `01_constraints` |
| Type definitions, tool constants | `02_core-types` / `02_reference` |
| ConfigLoader, Logging | `03_config-and-logging` |
| ToolExecutor, LLMClient | `03_tool-executor` / `03_llm-and-mcp-clients` |
| Schema, Migrations | `04_overview` / `04_schema` / `04_migration` |
| Module boundaries, Protocols | `05_module-boundaries` / `05_protocol` |
| Maintenance, Recovery | `05_maintenance` / `05_recovery` |
| Known issues | `90_inconsistencies` |

---

## Navigation to Major Known Issues

Refer to [90_shared_90_inconsistencies_and_known_issues.md](90_shared_90_inconsistencies_and_known_issues.md) for a full catalog of known inconsistencies (currently no open items). Note that `ArtifactEvent` does not involve an event bus (it is data definition only).

---

## Canonical Source Rules

- `06_spec_shared.md` / `07_ref-sqlite.md` / `07_spec_db.md` / `90_shared.md` are legacy source files that have been deleted; their content now resides within the restructured `90_shared_02_*` through `90_shared_05_*` files.
- If contents conflict between source files, trust the new restructured files (see `90_shared_90` for all discrepancies).

---

## File Index

Read the `shared/` documentation group in order: `01_overview` → `02_types` → `03_runtime`. Read the `db/` documentation group in order: `04_schema` → `05_operations`. (Explicit in code)

---

## Governance

Cross-cutting documentation rules and policies:

- [Documentation Policy](00_governance_01_documentation-policy.md)
- [Documentation Metadata](00_governance_02_documentation-metadata.md)
- [Issue and Uncertainty Management](00_governance_03_issue-and-uncertainty-management.md)
- [Documentation Checks](00_governance_04_documentation-checks.md)

## Guidance for Safe AI Use

1. `load_all()` only includes `agent.toml` (`_BASE_CONFIG_FILES = ("agent.toml",)`, see `90_shared_03_01` section 2a). A `rag_pipeline.toml` configuration file does not exist — each MCP server (including rag-pipeline-mcp) loads its own `config/<key>_mcp_server.toml` due to process isolation policy, so there is no need for explicit loading on the agent side.
2. `orjson.dumps()` returns `bytes` (requires `.decode()`).
3. `ArtifactEvent` is data-only and has no event bus.
4. `LLMMessage` has 7 fields (including `importance`/`pinned`; not 5 as in old `90_shared.md`).
5. Do NOT perform manual INSERTs because DB triggers automatically synchronize `chunks_fts`.
6. `SQLiteHelper("workflow")` is enabled (see `90_shared_04_01`).
7. For details on `LLMClient`, see `05_agent_05_llm-and-streaming.md` (not covered by this document set).

## Related ADRs

- [ADR-008](adr/ADR-008-sqlite-4db-separation.md) — SQLiteを4DBへ分離する
- [ADR-011](adr/ADR-011-database-corruption-recovery-safety-boundary.md) — Database Corruption Recovery Safety Boundary
