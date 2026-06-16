# Shared/DB Documentation Source Mapping

Audit table mapping content from the 4 source files to the 8 restructured output files.

Status: **Preserved** / **Summarized+Link** / **Merged** / **Flag(90)**

---

## Source File Inventory

| File | Lines | Primary content |
|---|---|---|
| `06_shared.md` | 96 | Index + `RagHit`, `LLMMessage`, `RagConfig` type definitions |
| `06_spec_shared.md` | 383 | Full shared layer spec (all modules, DTOs, execution flows) |
| `07_spec_db.md` | 367 | DB layer spec (schemas, DbConfig, SQLiteHelper, maintenance, ToolResultStore) |
| `07_ref-sqlite.md` | 601 | Full SQLiteHelper API, store.py protocols, maintenance.py, memory tables, workflow_schema |
| **Total** | **1447** | — |

---

## 1. `06_shared.md`

| Source section | New file | New section | Status |
|---|---|---|---|
| Module index table | `06_shared_01` | §5 Responsibilities of `shared/` | Summarized+Link |
| MCP `/v1/call_tool` protocol reference | `06_shared_02` | §11 CallToolRequest/CallToolResponse Reference | Preserved |
| Plugin tool return convention | `06_shared_03` | §4 plugin_registry | Preserved |
| `RagHit` TypedDict definition | `06_shared_02` | §5 RagHit | Preserved |
| `LLMMessage` TypedDict (5 fields) | `06_shared_02` | §3 LLMMessage | Merged (7-field version from `06_spec_shared.md` is canonical) |
| `RagConfig` Protocol definition | `06_shared_02` | §4 RagConfig | Preserved |
| Link to `06_ref-sqlite.md` | — | (stale link; actual file is `07_ref-sqlite.md`) | Flag(90) DOCREF-01 |

---

## 2. `06_spec_shared.md`

| Source section | New file | New section | Status |
|---|---|---|---|
| §1 Purpose | `06_shared_01` | §1 Purpose | Preserved |
| §2 Scope | `06_shared_01` | §2 Scope | Preserved |
| §3 Background | `06_shared_01` | §7 Import Direction Constraints | Merged |
| §4 Prerequisites | `06_shared_01` | §9 Major Constraints | Merged |
| §5 Constraints | `06_shared_01` | §9 Major Constraints | Preserved |
| §6.1 ConfigLoader | `06_shared_03` | §2 ConfigLoader | Preserved |
| §6.2 Logger | `06_shared_03` | §3 Logger | Preserved |
| §6.3 LLMMessage/RagConfig types | `06_shared_02` | §3-4 | Summarized+Link |
| §6.4 Tool constants | `06_shared_02` | §10 Tool Constants | Preserved |
| §6.5 plugin_registry | `06_shared_03` | §4 plugin_registry | Preserved |
| §6.6 OTel tracing | `06_shared_03` | §6 otel_tracer | Preserved |
| §6.7 token_counter | `06_shared_03` | §5 token_counter | Preserved |
| §6.8 formatters | `06_shared_03` | §8 formatters | Preserved |
| §6.9 LLMUsage/LLMResponse DTOs | `06_shared_02` | §6 LLMUsage/LLMResponse | Preserved |
| §6.10 ActionResult | `06_shared_02` | §7 ActionResult | Preserved |
| §6.11 ArtifactEvent | `06_shared_02` | §8 ArtifactEvent | Preserved |
| §6.12 ShellPolicy | `06_shared_02` | §9 ShellPolicy | Preserved |
| §7.1 ConfigLoader I/O | `06_shared_03` | §2 ConfigLoader | Preserved |
| §7.2 Logger I/O | `06_shared_03` | §3 Logger | Merged |
| §7.3 ToolExecutor I/O | `06_shared_03` | §9 ToolExecutor | Preserved |
| §8.1 Config loading flow | `06_shared_03` | §11 Execution Flow Summary | Preserved |
| §8.2 Plugin load flow | `06_shared_03` | §4 plugin_registry | Preserved |
| §8.3 ToolExecutor execution flow | `06_shared_03` | §9 ToolExecutor | Preserved |
| §9.1 LLMMessage (7-field version) | `06_shared_02` | §3 LLMMessage | Preserved (canonical) |
| §9.2 Tool constants table | `06_shared_02` | §10 Tool Constants | Preserved |
| §9.3 McpServerConfig reference | `06_shared_03` | §10 McpServerConfig | Summarized+Link |
| §9.4 LLMUsage/LLMResponse | `06_shared_02` | §6 | Preserved |
| §9.5 ActionResult | `06_shared_02` | §7 | Preserved |
| §9.6 ArtifactEvent | `06_shared_02` | §8 | Preserved |
| §9.7 ShellPolicy note | `06_shared_02` | §9 | Preserved |
| §10.1–10.7 Public interfaces | `06_shared_03` | §2–8 (per module) | Preserved |
| §11 Error handling | `06_shared_03` | §2–8 (inline per module) | Merged |
| §12 Validation plan | — | (internal reference) | — |
| §13 Known issues | `06_shared_90` | All entries | Preserved |

---

## 3. `07_spec_db.md`

| Source section | New file | New section | Status |
|---|---|---|---|
| §1 Purpose | `06_shared_04` | §1 Purpose | Preserved |
| §2 Scope | `06_shared_04` | §2 Overall DB Layer Structure | Merged |
| §3 Background | `06_shared_04` | §4 DB File Structure | Merged |
| §4 Prerequisites | `06_shared_04` | §9 Constraint List | Merged |
| §5 Constraints | `06_shared_04` | §9 Constraint List | Preserved |
| §6.1 Connection management | `06_shared_04` | §4 DB File Structure | Preserved |
| §6.2 Schema management | `06_shared_04` | §8 Schema Generation | Preserved |
| §6.3 Maintenance functions | `06_shared_05` | §7 Maintenance Functions | Preserved |
| §7.1 SQLiteHelper I/O | `06_shared_05` | §2 SQLiteHelper | Preserved |
| §7.2 DbConfig | `06_shared_04` | §3 DbConfig | Preserved |
| §8.1 DB init flow | `06_shared_04` | §8 Schema Generation | Preserved |
| §8.2 Vector search flow | `06_shared_05` | §3 VectorStore Protocol | Merged |
| §9.1 rag.sqlite schema | `06_shared_04` | §5 rag.sqlite Schema | Preserved |
| §9.2 session.sqlite schema | `06_shared_04` | §6 session.sqlite Schema | Preserved |
| §10.1 SQLiteHelper API | `06_shared_05` | §2 SQLiteHelper | Summarized+Link |
| §10.2 Schema management API | `06_shared_05` | §8 (verification) | Preserved |
| §10.3 Maintenance functions API | `06_shared_05` | §7 | Preserved |
| §10.4 ToolResultStore API | `06_shared_05` | §5 ToolResultStore | Preserved |
| §11 Error handling | `06_shared_05` | §9 Error Handling | Preserved |
| §12 Validation plan | `06_shared_05` | §10 Verification Plan | Preserved |
| §13 Known issues | `06_shared_90` | CONFIG-02/03, UNDOC-03 | Preserved |
| Missing: `workflow.sqlite` | `06_shared_04` | §7 workflow.sqlite Schema | From `07_ref-sqlite.md`; Flag(90) DOCMISS-01 |

---

## 4. `07_ref-sqlite.md`

| Source section | New file | New section | Status |
|---|---|---|---|
| SQLiteHelper overview | `06_shared_04` | §4 DB File Structure | Merged |
| Constructor (3 targets incl. `"workflow"`) | `06_shared_04` | §4 + §7 | Preserved |
| Instance attributes | `06_shared_04` | §4 | Preserved |
| `open()` method detail | `06_shared_05` | §2 `open()` method | Preserved |
| `execute()` / `executemany()` / `fetchall()` | `06_shared_05` | §2 Core methods | Preserved |
| `commit()` / `close()` | `06_shared_05` | §2 Core methods | Preserved |
| `begin_immediate()` / `begin_exclusive()` | `06_shared_05` | §2 Core methods | Preserved |
| `health_check()` / `checkpoint()` / `vacuum()` | `06_shared_05` | §2 Core methods | Preserved |
| Usage patterns table | `06_shared_05` | §2 Typical usage patterns | Preserved |
| `db/store.py` overview | `06_shared_05` | §3 Protocol Groups | Preserved |
| `VectorStore` Protocol | `06_shared_05` | §3 VectorStore | Preserved |
| `DocumentStore` Protocol | `06_shared_05` | §3 DocumentStore | Preserved |
| `SessionStore` Protocol | `06_shared_05` | §3 SessionStore | Preserved |
| SQLite backend implementations | `06_shared_05` | §4 SQLite Backend Implementations | Preserved |
| `MemoryDeleteStore` / `SQLiteMemoryDeleteStore` | `06_shared_05` | §4 + Flag(90) DESIGN-01 | Preserved |
| `db/maintenance.py` overview + API | `06_shared_05` | §7 Maintenance Functions | Preserved |
| `RetentionConfig` | `06_shared_05` | §7 | Preserved |
| `purge_old_sessions` behavior | `06_shared_05` | §7 | Preserved |
| `prune_old_memories` behavior | `06_shared_05` | §7 | Preserved |
| `RecoveryResult` + `recover_corruption` | `06_shared_05` | §8 Corruption Recovery | Preserved |
| `rotate_*` behavior | `06_shared_05` | §7 | Preserved |
| `db/tool_results.py` — `ToolResultStore` | `06_shared_05` | §5 ToolResultStore | Preserved |
| `memories` / `memories_fts` / `memories_vec` tables | `06_shared_04` | §6 session.sqlite Schema | Preserved |
| `memory_links` table | `06_shared_04` | §6 | Preserved |
| `MemoryStore` API | `06_shared_05` | §6 Memory-Related Tables | Preserved |
| `db/workflow_schema.py` | `06_shared_04` | §7 workflow.sqlite Schema | Preserved; Flag(90) DOCMISS-01 |

---

## Coverage Summary

| Source file | Mapped | Unmapped |
|---|---|---|
| `06_shared.md` | All | Stale `06_ref-sqlite.md` link (flagged) |
| `06_spec_shared.md` | All except §12 (internal) | §12 validation |
| `07_spec_db.md` | All except §12 (internal) | `workflow.sqlite` absence (flagged as DOCMISS-01) |
| `07_ref-sqlite.md` | All | — |

All significant content from the 4 source files has been mapped. No source information
has been silently dropped. Stale references and gaps are documented in
[06_shared_90_inconsistencies_and_known_issues.md](06_shared_90_inconsistencies_and_known_issues.md).
