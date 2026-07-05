# Shared/DB Documentation Guide

Entry point for the restructured `shared/` and `db/` layer documentation.
Read this file first to choose which chapter to open.

---

## Purpose of This Document Set

These 7 files document the `shared/` layer (common types, config, logging, plugins,
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
| What layers does `shared/` serve? | `90_shared_01` |
| What import rules apply to `shared/`? | `90_shared_01` §7 |
| What types are in `shared/types.py`? | `90_shared_02` §3-4 |
| What is `LLMMessage`? (all fields incl. `importance`/`pinned`) | `90_shared_02` §3 |
| What is `RagConfig`? | `90_shared_02` §4 |
| What tool frozensets exist? | `90_shared_02` §10 |
| How does `ConfigLoader.load_all()` work? | `90_shared_03` §2 |
| Does `load_all()` include `common.toml`? | **Yes** — included at index 0 of `_BASE_CONFIG_FILES`; see `90_shared_03` §2a Config Ownership |
| How do plugins load? | `90_shared_03` §4 |
| How does `ToolExecutor.execute()` work? | `90_shared_03` §9 |
| What SQLite DBs exist? | `90_shared_04` §2 |
| What is the `rag.sqlite` schema? | `90_shared_04` §5 |
| What is the `session.sqlite` schema? | `90_shared_04` §6 |
| Does `SQLiteHelper` support `workflow.sqlite`? | `90_shared_04` §4 (yes; undocumented in spec) |
| How to open a DB connection? | `90_shared_05` §2 |
| What are the store protocols? | `90_shared_05` §3 |
| Where are DB store module boundaries and import rules? | `90_shared_05` §1a |
| How to delete old memories? | `90_shared_05` §7 (`prune_old_memories`) |
| How to recover from DB corruption? | `90_shared_05` §8 |
| What is broken or undocumented? | `90_shared_90` |
| Does `LLMClient` have docs? | **Yes** — see `90_shared_03` §10 + `05_agent_05` |

---

## Navigation to Major Known Issues

| Issue | Location |
|---|---|
| `90_shared.md` references non-existent `06_ref-sqlite.md` | [90_shared_90 DOCREF-01](90_shared_90_inconsistencies_and_known_issues.md) |
| `ArtifactEvent` has no event bus | Out of scope — data definition only, no runtime integration planned |
| `LLMMessage` field count discrepancy (5 vs 7) | [90_shared_90 DOCFIELD-01](90_shared_90_inconsistencies_and_known_issues.md) |

---

## Canonical Source Rules

- `06_spec_shared.md` is canonical for `shared/` layer behavior; content now in `90_shared_02` / `90_shared_03`
- `07_ref-sqlite.md` and `07_spec_db.md` are deleted — their content is in `90_shared_04` and `90_shared_05`
- `90_shared.md` was an index; its type definitions are superseded by `06_spec_shared.md`
- When source files disagree, trust the new restructured files (see `90_shared_90` for all discrepancies)

---

## File Index

| File | Description |
|---|---|
| [90_shared_01_overview.md](90_shared_01_overview.md) | Layer structure, scope, import constraints, persistence picture, executive summary |
| [90_shared_02_types_and_protocols.md](90_shared_02_types_and_protocols.md) | All type definitions: LLMMessage, RagConfig, RagHit, LLMUsage/LLMResponse, ActionResult, ArtifactEvent, ShellPolicy, tool constants |
| [90_shared_03_runtime_and_execution.md](90_shared_03_runtime_and_execution.md) | ConfigLoader, Logger, plugin_registry, token_counter, OTel, git_helper, formatters, ToolExecutor flow, McpServerConfig |
| [90_shared_04_db_architecture_and_schema.md](90_shared_04_db_architecture_and_schema.md) | DB file structure, DbConfig, all table schemas (rag/session/workflow), FTS5/vec, schema init |
| [90_shared_05_db_api_and_operations.md](90_shared_05_db_api_and_operations.md) | SQLiteHelper full API, store protocols, SQLite implementations, ToolResultStore, memory ops, maintenance, corruption recovery |
| [90_shared_90_inconsistencies_and_known_issues.md](90_shared_90_inconsistencies_and_known_issues.md) | 13 cataloged issues: DOCREF-01, CONFIG-01/02/03, GLOBAL-01, PLUGIN-01, EXCEPT-01, UNDOC-04, IMPORT-01, API-01, DESIGN-01/02, DOCFIELD-01 |

---

## Guidance for Safe AI Use

1. **`load_all()` now includes `common.toml`** (DB paths, embedding URL, sqlite-vec path) at index 0. See [90_shared_03](90_shared_03_runtime_and_execution.md) §2a Config Ownership for the full ownership table. Only `rag_pipeline.toml` still requires explicit loading.
2. **`orjson.dumps()` returns `bytes`.** Call `.decode()` before using as string.
3. **`ArtifactEvent` is data only.** No event bus exists.
4. **`LLMMessage` has 7 fields** including `importance` and `pinned` (not 5 as in the old `90_shared.md`).
5. **DB triggers auto-sync `chunks_fts`.** Do not manually INSERT into `chunks_fts`.
6. **`SQLiteHelper("workflow")` is valid** — workflow.sqlite is documented in [90_shared_04](90_shared_04_db_architecture_and_schema.md).
7. **For `LLMClient` details**, see `05_agent_05_llm-and-streaming.md` — not covered here.
