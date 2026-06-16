# Shared/DB Documentation Guide

Entry point for the restructured `shared/` and `db/` layer documentation.
Read this file first to choose which chapter to open.

---

## Purpose of This Document Set

These 8 files document the `shared/` layer (common types, config, logging, plugins,
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
    ↓
99 Source Mapping           — audit table (verification only)
```

---

## AI Query Routing Table

| Question | File |
|---|---|
| What layers does `shared/` serve? | `06_shared_01` |
| What import rules apply to `shared/`? | `06_shared_01` §7 |
| What types are in `shared/types.py`? | `06_shared_02` §3-4 |
| What is `LLMMessage`? (all fields incl. `importance`/`pinned`) | `06_shared_02` §3 |
| What is `RagConfig`? | `06_shared_02` §4 |
| What tool frozensets exist? | `06_shared_02` §10 |
| How does `ConfigLoader.load_all()` work? | `06_shared_03` §2 |
| Does `load_all()` include `common.toml`? | **No** — `06_shared_03` §2 + `06_shared_90` CONFIG-01 |
| How do plugins load? | `06_shared_03` §4 |
| How does `ToolExecutor.execute()` work? | `06_shared_03` §9 |
| What SQLite DBs exist? | `06_shared_04` §2 |
| What is the `rag.sqlite` schema? | `06_shared_04` §5 |
| What is the `session.sqlite` schema? | `06_shared_04` §6 |
| Does `SQLiteHelper` support `workflow.sqlite`? | `06_shared_04` §4 (yes; undocumented in spec) |
| How to open a DB connection? | `06_shared_05` §2 |
| What are the store protocols? | `06_shared_05` §3 |
| How to delete old memories? | `06_shared_05` §7 (`prune_old_memories`) |
| How to recover from DB corruption? | `06_shared_05` §8 |
| What is broken or undocumented? | `06_shared_90` |
| Does `LLMClient` have docs? | **Partial** — see `06_shared_90` UNDOC-01 + `05_agent_05` |

---

## Navigation to Major Known Issues

| Issue | Location |
|---|---|
| `06_shared.md` references non-existent `06_ref-sqlite.md` | [06_shared_90 DOCREF-01](06_shared_90_inconsistencies_and_known_issues.md) |
| `load_all()` omits `common.toml` | [06_shared_90 CONFIG-01/02/03](06_shared_90_inconsistencies_and_known_issues.md) |
| `McpServerConfig.transport` not typed as `Literal` | [06_shared_90 TYPE-01](06_shared_90_inconsistencies_and_known_issues.md) |
| `LLMClient` undocumented in shared-layer specs | [06_shared_90 UNDOC-01](06_shared_90_inconsistencies_and_known_issues.md) |
| DB triggers not documented in spec tables | [06_shared_90 UNDOC-03](06_shared_90_inconsistencies_and_known_issues.md) |
| `ArtifactEvent` has no event bus | [06_shared_90 UNIMPL-01](06_shared_90_inconsistencies_and_known_issues.md) |
| `workflow.sqlite` absent from `07_spec_db.md` | [06_shared_90 DOCMISS-01](06_shared_90_inconsistencies_and_known_issues.md) |
| `LLMMessage` field count discrepancy (5 vs 7) | [06_shared_90 DOCFIELD-01](06_shared_90_inconsistencies_and_known_issues.md) |

---

## Canonical Source Rules

- `06_spec_shared.md` is canonical for `shared/` layer behavior; content now in `06_shared_02` / `06_shared_03`
- `07_ref-sqlite.md` is canonical for `SQLiteHelper` and `db/store.py` API details; content now in `06_shared_05`
- `07_spec_db.md` is canonical for DB schemas and `DbConfig`; content now in `06_shared_04`
- `06_shared.md` was an index; its type definitions are superseded by `06_spec_shared.md`
- When source files disagree, trust the new restructured files (see `06_shared_90` for all discrepancies)

---

## File Index

| File | Description |
|---|---|
| [06_shared_01_overview.md](06_shared_01_overview.md) | Layer structure, scope, import constraints, persistence picture, executive summary |
| [06_shared_02_types_and_protocols.md](06_shared_02_types_and_protocols.md) | All type definitions: LLMMessage, RagConfig, RagHit, LLMUsage/LLMResponse, ActionResult, ArtifactEvent, ShellPolicy, tool constants |
| [06_shared_03_runtime_and_execution.md](06_shared_03_runtime_and_execution.md) | ConfigLoader, Logger, plugin_registry, token_counter, OTel, git_helper, formatters, ToolExecutor flow, McpServerConfig |
| [06_shared_04_db_architecture_and_schema.md](06_shared_04_db_architecture_and_schema.md) | DB file structure, DbConfig, all table schemas (rag/session/workflow), FTS5/vec, schema init |
| [06_shared_05_db_api_and_operations.md](06_shared_05_db_api_and_operations.md) | SQLiteHelper full API, store protocols, SQLite implementations, ToolResultStore, memory ops, maintenance, corruption recovery |
| [06_shared_90_inconsistencies_and_known_issues.md](06_shared_90_inconsistencies_and_known_issues.md) | 19 cataloged issues: DOCREF-01, CONFIG-01/02/03, TYPE-01, GLOBAL-01, PLUGIN-01, EXCEPT-01, UNDOC-01/02/03/04, UNIMPL-01, IMPORT-01, API-01, DESIGN-01/02, DOCFIELD-01, DOCMISS-01 |
| [06_shared_99_source_mapping.md](06_shared_99_source_mapping.md) | Audit: maps every source section to its new location; coverage summary |

---

## Guidance for Safe AI Use

1. **Do not assume `load_all()` covers all config.** `common.toml` (DB paths, embedding URL) is loaded separately.
2. **`orjson.dumps()` returns `bytes`.** Call `.decode()` before using as string.
3. **`ArtifactEvent` is data only.** No event bus exists.
4. **`LLMMessage` has 7 fields** including `importance` and `pinned` (not 5 as in the old `06_shared.md`).
5. **DB triggers auto-sync `chunks_fts`.** Do not manually INSERT into `chunks_fts`.
6. **`SQLiteHelper("workflow")` is valid** despite being absent from `07_spec_db.md`.
7. **For `LLMClient` details**, see `05_agent_05_llm-and-streaming.md` — not covered here.
