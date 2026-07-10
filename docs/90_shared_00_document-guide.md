---
title: "Shared/DB Documentation Guide"
category: shared
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

Entry point for the restructured `shared/` and `db/` layer documentation.
Read this file first to choose which chapter to open.

---

## Purpose of This Document Set

These files document the `shared/` layer (common types, config, logging, plugins,
OTel, tool routing) and the `db/` layer (SQLite connection management, schemas, store
protocols, and maintenance).

---

## Recommended Reading Order (Human)

```
01 Overview → 02 Types and Protocols → 03 Runtime and Execution
  → 04 DB Architecture/Schema → 05 DB API and Operations → 90 Inconsistencies
```

---

## AI Query Routing Table

File suffixes below match the File Index; full filenames start with the `90_shared_0N_<topic>-` prefix shown there.

| Question | File suffix §Section |
|---|---|
| What layers does `shared/` serve? / import rules? | `...purpose-and-scope.md` / `...constraints-and-reference.md` §7 |
| What types are in `shared/types.py`? (`LLMMessage`, `RagConfig`) | `...core-types.md` §3-4 |
| What tool frozensets exist? | `...reference.md` (02) §10 |
| Does `ConfigLoader.load_all()` include `agent.toml`? | `...config-and-logging.md` §2 — **Yes**, index 0 of `_BASE_CONFIG_FILES`; see §2a |
| How do plugins load? | `...plugin-and-tool-runtime.md` §4 |
| How does `ToolExecutor.execute()` work? Does `LLMClient` have docs? | `...llm-and-mcp-clients.md` §9/§10 (+ `05_agent_05_llm-and-streaming.md`) |
| What SQLite DBs exist? Does `SQLiteHelper` support `workflow.sqlite`? | `...overview-and-config.md` (04) §2/§4 (yes; undocumented in spec) |
| What is the `rag.sqlite` / `session.sqlite` schema? | `...schema-reference.md` §5/§6 |
| Scaling limits for RAG architecture? | `...migration-and-scaling.md` §11 |
| How to open a DB connection? Module boundaries? | `...module-boundaries-and-helper.md` §2/§1a |
| What are the store protocols? | `...protocol-and-backend.md` §3 |
| How to delete old memories? RAG consistency check? | `...maintenance-and-rotation.md` §7/§7b |
| How to recover from DB corruption? Recreate DB? | `...recovery-and-reference.md` §9/§11 |
| What is broken or undocumented? | `90_shared_90_inconsistencies_and_known_issues.md` |

---

## Navigation to Major Known Issues

See [90_shared_90_inconsistencies_and_known_issues.md](90_shared_90_inconsistencies_and_known_issues.md) for the full catalog, including DOCREF-01 (`90_shared.md` references non-existent `06_ref-sqlite.md`) and DOCFIELD-01 (`LLMMessage` field count discrepancy, 5 vs 7). `ArtifactEvent` having no event bus is out of scope — data definition only, no runtime integration planned.

---

## Canonical Source Rules

- `06_spec_shared.md` / `07_ref-sqlite.md` / `07_spec_db.md` / `90_shared.md` are deleted legacy sources; their content lives in the `90_shared_02_*` through `90_shared_05_*` files above
- When source files disagree, trust the new restructured files (see `90_shared_90` for all discrepancies)

---

## File Index

### Overview

| File | Description |
|---|---|
| [90_shared_01_overview-purpose-and-scope.md](90_shared_01_overview-purpose-and-scope.md) | Purpose, scope |
| [90_shared_01_overview-layer-responsibilities.md](90_shared_01_overview-layer-responsibilities.md) | Layer structure, `shared/`/`db/` responsibilities |
| [90_shared_01_overview-constraints-and-reference.md](90_shared_01_overview-constraints-and-reference.md) | Import constraints, executive summary, AI reference |

### Types and Protocols

| File | Description |
|---|---|
| [90_shared_02_types_and_protocols-core-types.md](90_shared_02_types_and_protocols-core-types.md) | LLMMessage, RagConfig, RawHit/MergedHit/RankedHit/RagHit |
| [90_shared_02_types_and_protocols-tool-and-execution-dto.md](90_shared_02_types_and_protocols-tool-and-execution-dto.md) | ToolCallResult, ActionResult, ToolSpec, CacheEntry, ArtifactEvent, ShellPolicy |
| [90_shared_02_types_and_protocols-reference.md](90_shared_02_types_and_protocols-reference.md) | DbConfig, tool constants, CallToolRequest/Response, Protocol vs DTO |

### Runtime and Execution

| File | Description |
|---|---|
| [90_shared_03_runtime_and_execution-config-and-logging.md](90_shared_03_runtime_and_execution-config-and-logging.md) | ConfigLoader, Config Isolation Policy, Logger |
| [90_shared_03_runtime_and_execution-plugin-and-tool-runtime.md](90_shared_03_runtime_and_execution-plugin-and-tool-runtime.md) | plugin_registry, token_counter, otel_tracer, git_helper, formatters |
| [90_shared_03_runtime_and_execution-llm-and-mcp-clients.md](90_shared_03_runtime_and_execution-llm-and-mcp-clients.md) | ToolExecutor, LLMClient, McpServerConfig, execution flow |
| [90_shared_03_runtime_and_execution-caching-and-reference.md](90_shared_03_runtime_and_execution-caching-and-reference.md) | LlmRetryHandler, ToolResultCache, ToolSpec, PluginToolInvoker |

### DB Architecture and Schema

| File | Description |
|---|---|
| [90_shared_04_db_architecture_and_schema-overview-and-config.md](90_shared_04_db_architecture_and_schema-overview-and-config.md) | DB layer structure, DbConfig, SQLiteHelper |
| [90_shared_04_db_architecture_and_schema-schema-reference.md](90_shared_04_db_architecture_and_schema-schema-reference.md) | rag/session/workflow.sqlite schemas, timestamp policy |
| [90_shared_04_db_architecture_and_schema-migration-and-scaling.md](90_shared_04_db_architecture_and_schema-migration-and-scaling.md) | Migration approach, constraints, scaling limits |

### DB API and Operations

| File | Description |
|---|---|
| [90_shared_05_db_api_and_operations-module-boundaries-and-helper.md](90_shared_05_db_api_and_operations-module-boundaries-and-helper.md) | Module boundaries, `SQLiteHelper` (`db/helper.py`) |
| [90_shared_05_db_api_and_operations-protocol-and-backend.md](90_shared_05_db_api_and_operations-protocol-and-backend.md) | Protocol groups, SQLite backend, memory tables |
| [90_shared_05_db_api_and_operations-maintenance-and-rotation.md](90_shared_05_db_api_and_operations-maintenance-and-rotation.md) | Maintenance functions, DB rotation, RAG consistency |
| [90_shared_05_db_api_and_operations-recovery-and-reference.md](90_shared_05_db_api_and_operations-recovery-and-reference.md) | Corruption recovery, error handling, verification |

### Inconsistencies

| File | Description |
|---|---|
| [90_shared_90_inconsistencies_and_known_issues.md](90_shared_90_inconsistencies_and_known_issues.md) | DOCREF-01, CONFIG-01/02/03, GLOBAL-01, PLUGIN-01, IMPORT-01, DOCFIELD-01, others |

---

## Guidance for Safe AI Use

1. **`load_all()` includes `agent.toml`** at index 0 of `_BASE_CONFIG_FILES`. See `90_shared_03_runtime_and_execution-config-and-logging.md` §2a. Only `rag_pipeline.toml` needs explicit loading.
2. **`orjson.dumps()` returns `bytes`.** Call `.decode()` before using as string.
3. **`ArtifactEvent` is data only.** No event bus exists.
4. **`LLMMessage` has 7 fields** including `importance` and `pinned` (not 5 as in the old `90_shared.md`).
5. **DB triggers auto-sync `chunks_fts`.** Do not manually INSERT into `chunks_fts`.
6. **`SQLiteHelper("workflow")` is valid** — documented in `90_shared_04_db_architecture_and_schema-overview-and-config.md`.
7. **For `LLMClient` details**, see `05_agent_05_llm-and-streaming.md` — not covered here.

## Related Documents

- `90_shared_01_overview-purpose-and-scope.md`
- `90_shared_02_types_and_protocols-core-types.md`
- `90_shared_03_runtime_and_execution-config-and-logging.md`
- `90_shared_04_db_architecture_and_schema-overview-and-config.md`
- `90_shared_05_db_api_and_operations-module-boundaries-and-helper.md`
- `90_shared_90_inconsistencies_and_known_issues.md`

## Keywords

shared
db
documentation
guide
routing
ai reference
sqlite
