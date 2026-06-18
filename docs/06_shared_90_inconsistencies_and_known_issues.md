# Shared/DB Inconsistencies and Known Issues

This file catalogs all known inconsistencies between source documents, implementation
bugs, undocumented areas, unimplemented features, and undefined behavior in the
`shared/` and `db/` layers.

Each entry uses the required format:
- **Type:** `Document inconsistency` / `Implementation bug` / `Undocumented` / `Unimplemented` / `Undefined` / `Needs confirmation`

---

### DOCREF-01: `06_shared.md` references `06_ref-sqlite.md` — actual file is `07_ref-sqlite.md`

- **Type:** RESOLVED (Document inconsistency)
- **Resolution:** `06_shared.md` (the old monolithic doc) no longer exists — it was restructured into `06_shared_0*` files. No stale reference to `06_ref-sqlite.md` remains in the current docs. `06_shared_05_db_api_and_operations.md` and `06_shared_04_db_architecture_and_schema.md` serve as the authoritative DB API references.
- **Notes for AI reference:** Use `06_shared_05_db_api_and_operations.md` for `SQLiteHelper` API. `07_ref-sqlite.md` is a legacy reference file.

---

### CONFIG-01: `ConfigLoader.load_all()` does not include `common.toml`

- **Type:** Document inconsistency / Documentation gap resolved (see §2a Config Ownership in [06_shared_03](06_shared_03_runtime_and_execution.md))
- **Impact scope:** `shared/config_loader.py`, `agent/config.py`, `db/helper.py`, `rag/pipeline.py`
- **Statement A:** `ConfigLoader.load_all()` merges 11 hardcoded files and is described as loading "all configuration."
- **Statement B:** `common.toml` (which contains `rag_db_path`, `session_db_path`, `sqlite_vec_so`, `embed_url`, etc.) is NOT in the 11-file list.
- **Current safe interpretation:** `common.toml` is always loaded separately. Do not assume `load_all()` provides DB or embedding paths.
- **Recommended action:** Either add `common.toml` to `load_all()` or document explicitly that it must be loaded separately. (Documentation gap resolved — see [06_shared_03](06_shared_03_runtime_and_execution.md) §2a Config Ownership for canonical ownership table.)
- **Notes for AI reference:** Code calling `build_db_config()` must separately call `ConfigLoader().load("common.toml")`. Canonical ownership table is in [06_shared_03](06_shared_03_runtime_and_execution.md) §2a.

---

### CONFIG-02: `build_db_config()` uses a separate load as a workaround

- **Type:** RESOLVED (Implementation bug — fixed)
- **Resolution:** `build_db_config()` now explicitly uses `ConfigLoader().load("common.toml")` instead of `load_all()`, which does not include `common.toml`. The docstring is updated to explain why. This eliminates the silent empty-string fallback for `rag_db_path` / `session_db_path` and makes the loading intent explicit.
- **Notes for AI reference:** `build_db_config()` uses `load("common.toml")`. Do not use `load_all()` for DB path configuration. See [06_shared_03](06_shared_03_runtime_and_execution.md) §2a Config Ownership for the full ownership table.

---

### CONFIG-03: `common.toml` non-integration is a documented DB-layer known issue

- **Type:** Needs confirmation (ownership documented in [06_shared_03](06_shared_03_runtime_and_execution.md) §2a Config Ownership)
- **Impact scope:** `07_spec_db.md §5`, `07_spec_db.md §13`
- **Statement A:** `07_spec_db.md §13` explicitly documents: "`build_db_config()` cannot obtain `rag_db_path` etc. from `load_all()`. `db/helper.py` and `rag/pipeline.py` use the workaround of calling `ConfigLoader().load('common.toml')` separately."
- **Statement B:** Future consideration: include `common.toml` in `load_all()`.
- **Current safe interpretation:** The current system works. Any refactoring must maintain backward compatibility.
- **Recommended action:** Decide whether to merge `common.toml` into `load_all()` list before the next major config refactor. (Ownership is now documented in [06_shared_03](06_shared_03_runtime_and_execution.md) §2a Config Ownership.)
- **Notes for AI reference:** The issue is tracked and acknowledged, not a hidden defect. Canonical ownership table is in [06_shared_03](06_shared_03_runtime_and_execution.md) §2a.

---

### TYPE-01: `McpServerConfig.transport` is typed as `str`, not `Literal["http", "stdio"]`

- **Type:** RESOLVED (code already uses `TransportType` StrEnum)
- **Impact scope:** `shared/mcp_config.py::McpServerConfig.transport`
- **Resolution:** `McpServerConfig.transport` is typed as `TransportType` (a `StrEnum` with `HTTP = "http"`, `STDIO = "stdio"`). `__post_init__` converts string inputs from config files via `TransportType(self.transport)`. The type annotation in `04_mcp_06_configuration_and_operations.md` was stale and has been updated to `TransportType`.
- **Notes for AI reference:** Use `TransportType.HTTP` or `TransportType.STDIO` for type-safe construction. String values `"http"` / `"stdio"` are accepted at runtime via `__post_init__` conversion. `TransportType` is consistent with `StartupMode` and `HealthcheckMode` enums on the same dataclass.

---

### GLOBAL-01: `token_counter._warned_unavailable` is a module-level global variable

- **Type:** RESOLVED (global removed, state moved to caller)
- **Impact scope:** `shared/token_counter.py`, `agent/history.py`
- **Resolution:** The `_warned_unavailable` module-level global has been removed. `get_token_count()` now accepts `warn_once: _WarnOnce | None = None`. `HistoryManager.__init__` creates `self._warn_once = _WarnOnce()` and passes it to `get_token_count()`. Tests use local `_WarnOnce()` instances — no global state access needed.
- **Notes for AI reference:** Do NOT access `token_counter._warned_unavailable` — it no longer exists. Tests that verify warn-once behavior should create a local `_WarnOnce()` and pass it as `warn_once=`. The `_estimate_tokens()` function returns `(total, breakdown)` with per-category token counts.

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

- **Type:** RESOLVED (Structured result with failure reasons implemented)
- **Impact scope:** `shared/git_helper.py::get_repo_info()`
- **Resolution:** `get_repo_info()` now returns `RepoInfoResult` (frozen dataclass) instead of `dict | None`. On success: `RepoInfoResult(success=True, data={branch, commit, message, author})`. On failure: `RepoInfoResult(success=False, failure_reason=FailureReason.*)`. `FailureReason` is a `StrEnum` with 5 values: `GITPYTHON_NOT_INSTALLED`, `NOT_A_GIT_REPO`, `PERMISSION_DENIED`, `GIT_ERROR`, `OTHER_ERROR`. `git.exc.InvalidGitRepositoryError` is now distinguished from generic `git.exc.GitError`.
- **Notes for AI reference:** Check `result.success` (not truthiness — `RepoInfoResult` is always truthy). Access data via `result.data["branch"]` etc. Inspect `result.failure_reason` for precise failure cause.

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

- **Type:** RESOLVED (cross-reference gap — documented)
- **Resolution:** `06_shared_03_runtime_and_execution.md §13` now contains: "`ToolExecutor` details are in this document (§9), `04_mcp_03_routing_lifecycle_and_execution.md`, and `05_agent_06_tool-execution-and-approval.md`." The cross-references are explicit.
- **Notes for AI reference:** For routing: `04_mcp_03`. For approval flow: `05_agent_06`. For execution flow and type contracts: `06_shared_03 §9`.

---

### UNIMPL-01: `ArtifactEvent` event bus is not implemented

- **Type:** RESOLVED (Option A — documented as data-only)
- **Impact scope:** `shared/events.py::ArtifactEvent`
- **Resolution (Option A selected):** Module docstring now explicitly states `ArtifactEvent` is a pure data structure with no delivery system, no event bus, and no consumers. The ambiguous phrase "no event bus yet" was replaced with clear documentation that creating an `ArtifactEvent` instance triggers no action.
- **Recommended action:** None — use `ArtifactEvent` only as a type annotation. If an event bus is needed in the future, implement it as a separate feature.
- **Notes for AI reference:** Creating an `ArtifactEvent` dict does nothing. No listeners will receive it. No consumers exist in the current codebase.

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

- **Type:** RESOLVED (Document inconsistency)
- **Resolution:** `06_shared.md` (the old monolithic doc) no longer exists. `06_shared_02_types_and_protocols.md §3` documents the complete 7-field definition including `importance: float` and `pinned: bool`. The stale "(see DOCFIELD-01)" note has been removed from that doc.
- **Notes for AI reference:** `LLMMessage` has 7 fields: `role` (required), `content`, `tool_calls`, `tool_call_id`, `name`, `importance`, `pinned`. All except `role` are optional (`total=False`). Source: `shared/types.py`.

---

### DOCMISS-01: `SQLiteHelper target="workflow"` and `db/workflow_schema.py` absent from `07_spec_db.md`

- **Type:** RESOLVED (Document inconsistency)
- **Resolution:** `06_shared_04_db_architecture_and_schema.md §7` now documents `workflow.sqlite` schema (`tasks`, `attempts`, `processed_events`, `artifacts` tables) and the `"workflow"` target in `SQLiteHelper`. `06_shared_05_db_api_and_operations.md` includes `target="workflow"` in the constructor reference and AI FAQ.
- **Notes for AI reference:** `SQLiteHelper("workflow")` is valid and connects to `workflow.sqlite`. Schema initialized by `db/workflow_schema.py::init_schema()`.
- **Recommended action:** Add `workflow.sqlite` to `07_spec_db.md` specification.
- **Notes for AI reference:** `SQLiteHelper("workflow")` is valid. It connects to `workflow.sqlite` with schema managed by `db/workflow_schema.py`.
