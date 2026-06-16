# Shared/DB Inconsistencies and Known Issues

This file catalogs all known inconsistencies between source documents, implementation
bugs, undocumented areas, unimplemented features, and undefined behavior in the
`shared/` and `db/` layers.

Each entry uses the required format:
- **Type:** `Document inconsistency` / `Implementation bug` / `Undocumented` / `Unimplemented` / `Undefined` / `Needs confirmation`

---

### DOCREF-01: `06_shared.md` references `06_ref-sqlite.md` — actual file is `07_ref-sqlite.md`

- **Type:** Document inconsistency
- **Impact scope:** `docs/06_shared.md` line 3; any reader following the link
- **Statement A:** `06_shared.md` header links to `06_ref-infra.md` and `06_ref-mcp.md` for module details.
- **Statement B:** The DB reference document is `docs/07_ref-sqlite.md`. There is no `docs/06_ref-sqlite.md`.
- **Current safe interpretation:** Follow `07_ref-sqlite.md` for all SQLiteHelper and db/ API details.
- **Recommended action:** Update `06_shared.md` to reference `07_ref-sqlite.md` or the new restructured files.
- **Notes for AI reference:** Do not look for `06_ref-sqlite.md` — it does not exist.

---

### CONFIG-01: `ConfigLoader.load_all()` does not include `common.toml`

- **Type:** Document inconsistency / Needs confirmation
- **Impact scope:** `shared/config_loader.py`, `agent/config.py`, `db/helper.py`, `rag/pipeline.py`
- **Statement A:** `ConfigLoader.load_all()` merges 11 hardcoded files and is described as loading "all configuration."
- **Statement B:** `common.toml` (which contains `rag_db_path`, `session_db_path`, `sqlite_vec_so`, `embed_url`, etc.) is NOT in the 11-file list.
- **Current safe interpretation:** `common.toml` is always loaded separately. Do not assume `load_all()` provides DB or embedding paths.
- **Recommended action:** Either add `common.toml` to `load_all()` or document explicitly that it must be loaded separately.
- **Notes for AI reference:** Code calling `build_db_config()` must separately call `ConfigLoader().load("common.toml")`.

---

### CONFIG-02: `build_db_config()` uses a separate load as a workaround

- **Type:** Implementation bug (architectural workaround)
- **Impact scope:** `db/helper.py`, `db/config.py`
- **Statement A:** `build_db_config()` loads `common.toml` independently via `ConfigLoader().load("common.toml")` rather than using `load_all()`.
- **Statement B:** This is a known workaround because `load_all()` omits `common.toml`.
- **Current safe interpretation:** The workaround works correctly. DB paths are properly resolved.
- **Recommended action:** Track with CONFIG-01 resolution.
- **Notes for AI reference:** This is intentional, not accidental. The workaround is documented in `07_spec_db.md §5`.

---

### CONFIG-03: `common.toml` non-integration is a documented DB-layer known issue

- **Type:** Needs confirmation
- **Impact scope:** `07_spec_db.md §5`, `07_spec_db.md §13`
- **Statement A:** `07_spec_db.md §13` explicitly documents: "`build_db_config()` cannot obtain `rag_db_path` etc. from `load_all()`. `db/helper.py` and `rag/pipeline.py` use the workaround of calling `ConfigLoader().load('common.toml')` separately."
- **Statement B:** Future consideration: include `common.toml` in `load_all()`.
- **Current safe interpretation:** The current system works. Any refactoring must maintain backward compatibility.
- **Recommended action:** Decide whether to merge `common.toml` into `load_all()` list before the next major config refactor.
- **Notes for AI reference:** The issue is tracked and acknowledged, not a hidden defect.

---

### TYPE-01: `McpServerConfig.transport` is typed as `str`, not `Literal["http", "stdio"]`

- **Type:** Needs confirmation
- **Impact scope:** `shared/mcp_config.py::McpServerConfig.transport`
- **Statement A:** `transport` field is validated in `__post_init__` to only accept `"http"` or `"stdio"`.
- **Statement B:** The type annotation is `str`, so type checkers cannot catch invalid values at call sites.
- **Current safe interpretation:** Only `"http"` or `"stdio"` are valid at runtime. Use these values only.
- **Recommended action:** Change annotation to `transport: Literal["http", "stdio"]`.
- **Notes for AI reference:** Referenced in `implementations/20260606-194710_shared_types.md`. No functional impact; type-safety enhancement only.

---

### GLOBAL-01: `token_counter._warned_unavailable` is a module-level global variable

- **Type:** Implementation bug (design concern)
- **Impact scope:** `shared/token_counter.py::_warned_unavailable`
- **Statement A:** `_warned_unavailable` is a module-level boolean that suppresses repeated "tokenize endpoint unavailable" warnings.
- **Statement B:** Module-level state persists across test runs and multiple `ToolExecutor` instances, making tests non-isolated.
- **Current safe interpretation:** The warning suppression works correctly in production (single process). Test isolation may be affected.
- **Recommended action:** Move to instance variable. Tracked in `implementations/20260606-194738_shared_global_state.md`.
- **Notes for AI reference:** Do not rely on warning count in tests. In production, warning fires once per process lifetime.

---

### PLUGIN-01: `plugin_registry.load_plugins()` has no machine-readable failure report

- **Type:** Unimplemented
- **Impact scope:** `shared/plugin_registry.py::load_plugins()`
- **Statement A:** `load_plugins()` returns `int` (count of loaded plugins).
- **Statement B:** Failed plugins are logged as WARNING and skipped. There is no structured return value indicating which plugins failed and why.
- **Current safe interpretation:** Check agent startup logs for plugin load failures. Do not rely on return value for error detection.
- **Recommended action:** Return a structured result `{loaded: int, failed: list[{path, error}]}` instead of bare `int`.
- **Notes for AI reference:** `load_plugins()` is fail-open; a return value of `5` does not mean all 5 succeeded without errors.

---

### EXCEPT-01: `git_helper.get_repo_info()` catches broad exceptions and returns `None`

- **Type:** Implementation bug (design concern)
- **Impact scope:** `shared/git_helper.py::get_repo_info()`
- **Statement A:** Returns `{"branch", "commit", "message", "author"}` on success.
- **Statement B:** Catches `except Exception` broadly — covers `GitPython not installed`, `not a git repo`, permission errors, and any other exception — returning `None` in all cases.
- **Current safe interpretation:** `None` return means "could not get repo info." Reason is unknown from return value alone.
- **Recommended action:** Return a typed result `{"ok": bool, "data": dict | None, "reason": str}` or raise specific exceptions.
- **Notes for AI reference:** Do not attempt to distinguish between "not a git repo" and "GitPython not installed" from the return value.

---

### UNDOC-01: `shared/llm_client.py` (`LLMClient`, `RobustSSEParser`) is documented in shared-layer specs

- **Type:** Resolved
- **Impact scope:** `shared/llm_client.py`; `06_shared_03_runtime_and_execution.md` §10
- **Description:** Added shared-layer documentation for `LLMClient` including responsibility, main API (`call()`, `stream()`, `build_payload()`), error behavior, retry logic, and statistics. Cross-reference to `05_agent_05_llm-and-streaming.md` for streaming protocol details.
- **Current safe interpretation:** See `06_shared_03` §10 for shared-layer view; `05_agent_05` for full streaming details.
- **Recommended action:** None - already documented.
- **Notes for AI reference:** `LLMClient` uses exponential backoff retry, SSE streaming with heartbeat timeout handling.

---

### UNDOC-02: `shared/tool_executor.py` detailed behavior is documented in shared-layer specs

- **Type:** Resolved
- **Impact scope:** `shared/tool_executor.py`; `06_shared_03_runtime_and_execution.md` §9
- **Description:** Added shared-layer documentation for `ToolExecutor` including execution flow, cache behavior (TTL+LRU, is_error=False only), health gate (UNAVAILABLE blocks dispatch), concurrency behavior (Semaphore-based), side-effect detection, and result contract (`ToolCallResult`).
- **Current safe interpretation:** See `06_shared_03` §9 for shared-layer view; `04_mcp_03` for routing details; `05_agent_06` for approval flow.
- **Recommended action:** None - already documented.
- **Notes for AI reference:** `ToolExecutor.execute()` → plugin priority → health gate → cache → raw MCP call.

---

### UNDOC-03: DB triggers in `schema_sql.py` are documented in specification tables

- **Type:** Resolved
- **Impact scope:** `scripts/db/schema_sql.py` lines 43–63; `chunks_fts` and `chunks_vec` synchronization
- **Description:** Trigger DDL added to [06_shared_04_db_architecture_and_schema.md](06_shared_04_db_architecture_and_schema.md) with full trigger table showing behavior for each trigger (`chunks_ai`, `chunks_au`, `chunks_ad`, `chunks_vec_ad`).
- **Current safe interpretation:** Triggers exist and automatically synchronize `chunks_fts` on `chunks` INSERT/UPDATE/DELETE, and remove `chunks_vec` entries on chunk delete.
- **Recommended action:** None - already documented.
- **Notes for AI reference:** Do NOT manually synchronize `chunks_fts` after INSERT/UPDATE/DELETE — triggers handle this automatically.

---

### UNDOC-04: `ToolExecutor` referenced in `shared/` specs but details depend on other documents

- **Type:** Undocumented (cross-reference gap)
- **Impact scope:** `06_spec_shared.md §7.3`, `§8.3`; `shared/tool_executor.py`
- **Statement A:** `06_spec_shared.md` documents `ToolExecutor.execute()` input/output and the execution flow.
- **Statement B:** Full details (concurrency limits, health registry integration, cache eviction policy) are in `04_mcp_03` and `05_agent_06`.
- **Current safe interpretation:** For routing and lifecycle: see `04_mcp_03`. For approval flow: see `05_agent_06`. For shared-layer type contracts: see this document set.
- **Recommended action:** Add explicit cross-references in `06_shared_03_runtime_and_execution.md`.
- **Notes for AI reference:** Do not look for `ToolExecutor` field-level documentation in `06_shared_*` — it is in `04_mcp_03`.

---

### UNIMPL-01: `ArtifactEvent` event bus is not implemented

- **Type:** Unimplemented
- **Impact scope:** `shared/events.py::ArtifactEvent`
- **Statement A:** `ArtifactEvent` is a `TypedDict` with fields for `event_type`, `repo`, `branch`, `commit`, `path`, `pr_number`, `session_id`, `timestamp`.
- **Statement B:** `06_spec_shared.md §6.11` explicitly states: "Event bus is not implemented (pure data definition only)."
- **Current safe interpretation:** `ArtifactEvent` is a data structure only. No publish/subscribe mechanism exists. Do not assume events are delivered to any subscriber.
- **Recommended action:** Implement event bus before using `ArtifactEvent` in production workflows.
- **Notes for AI reference:** Creating an `ArtifactEvent` dict does nothing. No listeners will receive it.

---

### IMPORT-01: `shared/` must not import from `agent/`, `mcp/`, `rag/`, or `db/`

- **Type:** Document inconsistency (architectural constraint)
- **Impact scope:** All modules in `shared/`; enforced by `.importlinter`
- **Statement A:** `06_spec_shared.md §5` states this constraint explicitly.
- **Statement B:** The constraint is enforced via `.importlinter` config. Violations fail `PYTHONPATH=scripts uv run lint-imports`.
- **Current safe interpretation:** Any `import` from `shared/` that reaches `agent/`, `mcp/`, `rag/`, or `db/` is a bug. Fix by inverting the dependency.
- **Recommended action:** Run `lint-imports` to verify. Never add upper-layer imports to `shared/`.
- **Notes for AI reference:** If a `shared/` module needs agent/mcp/rag behavior, use dependency injection via function arguments instead.

---

### API-01: `orjson.dumps()` returns `bytes`, not `str` — `.decode()` required

- **Type:** Resolved
- **Impact scope:** `shared/json_utils.py::dumps()`; all call sites in `shared/`, `db/`, `agent/`, `mcp/`, `rag/`
- **Description:** Added `shared/json_utils.dumps()` helper that wraps `orjson.dumps().decode()` returning `str` directly. All 29 call sites across the codebase replaced with `_json_dumps()` import. Default behavior uses `OPT_SORT_KEYS` for deterministic output.
- **Current safe interpretation:** Use `from shared.json_utils import dumps as _json_dumps` for string JSON serialization. For indented output, pass `option=orjson.OPT_INDENT_2`.
- **Recommended action:** None — already implemented and all call sites migrated.
- **Notes for AI reference:** Direct `.decode()` repetition reduced to zero outside `json_utils.py` itself.

---

### DESIGN-01: Responsibility boundary between `MemoryDeleteStore` and `SQLiteMemoryDeleteStore`

- **Type:** Needs confirmation
- **Impact scope:** `db/store.py::MemoryDeleteStore` (Protocol), `db/store.py::SQLiteMemoryDeleteStore` (implementation)
- **Statement A:** `MemoryDeleteStore` is a `Protocol` defining `delete_memories_before(older_than_days)`.
- **Statement B:** `SQLiteMemoryDeleteStore` implements this protocol for SQLite (deletes from `memories`, `memories_fts`, `memories_vec` atomically).
- **Current safe interpretation:** The Protocol/implementation split allows future non-SQLite backends. For current SQLite-only deployments, use `SQLiteMemoryDeleteStore` directly.
- **Recommended action:** Document that `MemoryDeleteStore` protocol exists for extensibility, not because non-SQLite backends are planned.
- **Notes for AI reference:** Do not confuse `SQLiteMemoryDeleteStore` (cross-table delete) with `MemoryStore.delete()` (single-entry delete).

---

### DESIGN-02: Responsibility boundary between `ToolResultStore` and `messages` history

- **Type:** Needs confirmation
- **Impact scope:** `db/tool_results.py::ToolResultStore`, `agent/session.py` messages table
- **Statement A:** `messages` table stores all LLM conversation messages (user/assistant/tool roles), including tool result messages.
- **Statement B:** `tool_results` table stores full tool result text, which is NOT in the `messages` table (only summary/truncated version appears in message history).
- **Current safe interpretation:** `messages` → conversation flow (what LLM sees). `tool_results` → full output archive (accessible via `/tool show <id>`).
- **Recommended action:** Document that `tool_results` is a supplementary store, not a replacement for `messages`.
- **Notes for AI reference:** When querying conversation history, use `messages`. When retrieving full tool output, use `ToolResultStore.get(id)`.

---

### DOCFIELD-01: `LLMMessage` field discrepancy between `06_shared.md` and `06_spec_shared.md`

- **Type:** Document inconsistency
- **Impact scope:** `shared/types.py::LLMMessage`
- **Statement A:** `06_shared.md` lists 5 fields: `role`, `content`, `tool_calls`, `tool_call_id`, `name`.
- **Statement B:** `06_spec_shared.md §9.1` lists 7 fields, adding: `importance: float` (compression prioritization) and `pinned: bool` (preserve during compression).
- **Current safe interpretation:** `06_spec_shared.md` is canonical. `LLMMessage` has 7 fields including `importance` and `pinned`. Both are optional (`total=False`).
- **Recommended action:** Update `06_shared.md` to reflect the current 7-field definition.
- **Notes for AI reference:** When building `LLMMessage` objects, `importance` and `pinned` fields may be present. Do not filter them out.

---

### DOCMISS-01: `SQLiteHelper target="workflow"` and `db/workflow_schema.py` absent from `07_spec_db.md`

- **Type:** Document inconsistency
- **Impact scope:** `07_spec_db.md` (specification); `07_ref-sqlite.md` (reference)
- **Statement A:** `07_ref-sqlite.md` documents `SQLiteHelper` constructor with three valid targets: `"rag"`, `"session"`, `"workflow"`, and includes a section on `db/workflow_schema.py`.
- **Statement B:** `07_spec_db.md §2` only mentions `rag.sqlite` and `session.sqlite`. `workflow.sqlite` and `db/workflow_schema.py` are absent.
- **Current safe interpretation:** `workflow.sqlite` and `"workflow"` target exist and are production code. Trust `07_ref-sqlite.md` for the complete picture.
- **Recommended action:** Add `workflow.sqlite` to `07_spec_db.md` specification.
- **Notes for AI reference:** `SQLiteHelper("workflow")` is valid. It connects to `workflow.sqlite` with schema managed by `db/workflow_schema.py`.
