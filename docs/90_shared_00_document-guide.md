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

These 17 files document the `shared/` layer (common types, config, logging, plugins,
OTel, tool routing) and the `db/` layer (SQLite connection management, schemas, store
protocols, and maintenance). They replace the 4 source files as the primary reference.

---

## Recommended Reading Order (Human)

```
01 Overview                 — start here: layer structure, import rules, persistence
    ↓
02 Types and Protocols      — LLMMessage, RagConfig, ActionResult, tool constants
    ↓
03 Runtime and Execution    — ConfigLoader, Logger, ToolExecutor, plugins
    ↓
04 DB Architecture / Schema — rag.sqlite, session.sqlite, workflow.sqlite schemas
    ↓
05 DB API and Operations    — SQLiteHelper API, store protocols, maintenance
    ↓
90 Inconsistencies          — known bugs, undocumented areas, design concerns
```

---

## AI Query Routing Table

| Question | File |
|---|---|
| What layers does `shared/` serve? | `90_shared_01_overview` |
| What import rules apply to `shared/`? | `90_shared_01_import_rules` §7 |
| What types are in `shared/types.py`? | `90_shared_02_core` §3-4 |
| What is `LLMMessage`? (all fields incl. `importance`/`pinned`) | `90_shared_02_core` §3 |
| What is `RagConfig`? | `90_shared_02_core` §4 |
| What tool frozensets exist? | `90_shared_02_agent` §10 |
| How does `ConfigLoader.load_all()` work? | `90_shared_03_infra` §2 |
| Does `load_all()` include `agent.toml`? | **Yes** — included at index 0 of `_BASE_CONFIG_FILES`; see `90_shared_03_infra` §2a Config Ownership |
| How do plugins load? | `90_shared_03_infra` §4 |
| How does `ToolExecutor.execute()` work? | `90_shared_03_executor` §9 |
| What SQLite DBs exist? | `90_shared_04_config` §2 |
| What is the `rag.sqlite` schema? | `90_shared_04_rag_schema` §5 |
| What is the `session.sqlite` schema? | `90_shared_04_session_workflow` §6 |
| Does `SQLiteHelper` support `workflow.sqlite`? | `90_shared_04_config` §4 (yes; undocumented in spec) |
| How to open a DB connection? | `90_shared_05_sqlitehelper` §2 |
| What are the store protocols? | `90_shared_05_protocols` §3 |
| Where are DB store module boundaries and import rules? | `90_shared_05_sqlitehelper` §1a |
| How to delete old memories? | `90_shared_05_maintenance` §7 (`prune_old_memories`) |
| How to recover from DB corruption? | `90_shared_05_recovery` §9 |
| What is broken or undocumented? | `90_shared_90` |
| Does `LLMClient` have docs? | **Yes** — see `90_shared_03_llm` §10 + `05_agent_05` |
| Scaling limits for RAG architecture? | `90_shared_04_scaling_limits` §11 |
| What is the RAG consistency check? | `90_shared_05_recovery` §7b |
| How to recreate DB after schema change? | `90_shared_05_recovery` §11 |

---

## Navigation to Major Known Issues

| Issue | Location |
|---|---|
| `90_shared.md` references non-existent `06_ref-sqlite.md` | [90_shared_90 DOCREF-01](90_shared_90_inconsistencies_and_known_issues.md) |
| `ArtifactEvent` has no event bus | Out of scope — data definition only, no runtime integration planned |
| `LLMMessage` field count discrepancy (5 vs 7) | [90_shared_90 DOCFIELD-01](90_shared_90_inconsistencies_and_known_issues.md) |

---

## Canonical Source Rules

- `06_spec_shared.md` is canonical for `shared/` layer behavior; content now in `90_shared_02_core` / `90_shared_03_*`
- `07_ref-sqlite.md` and `07_spec_db.md` are deleted — their content is in `90_shared_04_*` and `90_shared_05_*`
- `90_shared.md` was an index; its type definitions are superseded by `06_spec_shared.md`
- When source files disagree, trust the new restructured files (see `90_shared_90` for all discrepancies)

---

## File Index

### Overview

| File | Description |
|---|---|
| [90_shared_01_overview.md](90_shared_01_overview.md) | Layer structure, scope, import constraints, persistence picture, executive summary |
| [90_shared_01_import_rules_and_constraints.md](90_shared_01_import_rules_and_constraints.md) | Import direction rules, major constraints, AI Reference Guide |

### Types and Protocols

| File | Description |
|---|---|
| [90_shared_02_types_and_protocols_core.md](90_shared_02_types_and_protocols_core.md) | Core types: LLMMessage, RagConfig, RagHit variants, LLMUsage/LLMResponse, ToolCallResult, ActionResult, ArtifactEvent |
| [90_shared_02_types_and_protocols_agent.md](90_shared_02_types_and_protocols_agent.md) | Agent/tool types: ShellPolicy, DbConfig, tool constants, CallToolRequest/Response, ToolSpec, CacheEntry, PluginFailure, ToolDefinition |

### Runtime and Execution

| File | Description |
|---|---|
| [90_shared_03_runtime_and_execution_infra.md](90_shared_03_runtime_and_execution_infra.md) | ConfigLoader, Logger, plugin_registry, token_counter, OTel, git_helper |
| [90_shared_03_runtime_and_execution_executor.md](90_shared_03_runtime_and_execution_executor.md) | Formatters, ToolExecutor execution flow, cache, health gate, concurrency |
| [90_shared_03_runtime_and_execution_llm.md](90_shared_03_runtime_and_execution_llm.md) | LLMClient, SSE streaming, retry, McpServerConfig, McpServerHealthRegistry |
| [90_shared_03_runtime_and_execution_other.md](90_shared_03_runtime_and_execution_other.md) | Execution flow summary, LlmRetryHandler, ToolResultCache, ToolSpec, PluginToolInvoker, McpServerHealthState, LlmPayloadHandler, LlmHotConfigHandler, AI Reference Guide |

### DB Architecture and Schema

| File | Description |
|---|---|
| [90_shared_04_db_overview_and_config.md](90_shared_04_db_overview_and_config.md) | Overall DB layer structure, DbConfig, SQLiteHelper connection behavior |
| [90_shared_04_db_rag_schema.md](90_shared_04_db_rag_schema.md) | rag.sqlite schema: documents, chunks, chunks_fts, chunks_vec, auto-sync triggers |
| [90_shared_04_session_workflow_schemas.md](90_shared_04_session_workflow_schemas.md) | session.sqlite and workflow.sqlite schemas: sessions, messages, memories, tasks, approvals |
| [90_shared_04_db_operational.md](90_shared_04_db_operational.md) | Timestamp policy, schema generation, constraints, AI Reference Guide, source of truth |
| [90_shared_04_db_scaling_limits.md](90_shared_04_db_scaling_limits.md) | Scaling limits and migration signals: corpus size, write concurrency, FTS5 latency |

### DB API and Operations

| File | Description |
|---|---|
| [90_shared_05_db_module_boundaries_and_sqlitehelper.md](90_shared_05_db_module_boundaries_and_sqlitehelper.md) | Module boundaries, SQLiteHelper full API, usage patterns |
| [90_shared_05_db_store_protocols.md](90_shared_05_db_store_protocols.md) | Protocol groups (VectorStore, DocumentStore, SessionStore), SQLite backend implementations |
| [90_shared_05_db_maintenance_and_ops.md](90_shared_05_db_maintenance_and_ops.md) | Memory operations, maintenance functions, MaintenanceMode/MaintenanceResult, RetentionConfig, DB rotation |
| [90_shared_05_db_recovery_and_verification.md](90_shared_05_db_recovery_and_verification.md) | RAG consistency checks, corruption recovery, error handling, DB recreation procedure, verification plan, AI Reference Guide |

### Inconsistencies

| File | Description |
|---|---|
| [90_shared_90_inconsistencies_and_known_issues.md](90_shared_90_inconsistencies_and_known_issues.md) | 13 cataloged issues: DOCREF-01, CONFIG-01/02/03, GLOBAL-01, PLUGIN-01, EXCEPT-01, UNDOC-04, IMPORT-01, API-01, DESIGN-01/02, DOCFIELD-01 |

---

## Guidance for Safe AI Use

1. **`load_all()` now includes `agent.toml`** (DB paths, embedding URL, sqlite-vec path) at index 0. See [90_shared_03_infra](90_shared_03_runtime_and_execution_infra.md) §2a Config Ownership for the full ownership table. Only `rag_pipeline.toml` still requires explicit loading.
2. **`orjson.dumps()` returns `bytes`.** Call `.decode()` before using as string.
3. **`ArtifactEvent` is data only.** No event bus exists.
4. **`LLMMessage` has 7 fields** including `importance` and `pinned` (not 5 as in the old `90_shared.md`).
5. **DB triggers auto-sync `chunks_fts`.** Do not manually INSERT into `chunks_fts`.
6. **`SQLiteHelper("workflow")` is valid** — workflow.sqlite is documented in [90_shared_04_config](90_shared_04_db_overview_and_config.md).
7. **For `LLMClient` details**, see `05_agent_05_llm-and-streaming.md` — not covered here.
