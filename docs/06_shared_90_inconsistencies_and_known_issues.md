# Shared/DB Inconsistencies and Known Issues

This file catalogs all known inconsistencies between source documents, implementation
bugs, undocumented areas, unimplemented features, and undefined behavior in the
`shared/` and `db/` layers.

Each entry uses the required format:
- **Type:** `Document inconsistency` / `Implementation bug` / `Undocumented` / `Unimplemented` / `Undefined` / `Needs confirmation`

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

### CONFIG-03: `common.toml` non-integration is a documented DB-layer known issue

- **Type:** Needs confirmation (ownership documented in [06_shared_03](06_shared_03_runtime_and_execution.md) §2a Config Ownership)
- **Impact scope:** `07_spec_db.md §5`, `07_spec_db.md §13`
- **Statement A:** `07_spec_db.md §13` explicitly documents: "`build_db_config()` cannot obtain `rag_db_path` etc. from `load_all()`. `db/helper.py` and `rag/pipeline.py` use the workaround of calling `ConfigLoader().load('common.toml')` separately."
- **Statement B:** Future consideration: include `common.toml` in `load_all()`.
- **Current safe interpretation:** The current system works. Any refactoring must maintain backward compatibility.
- **Recommended action:** Decide whether to merge `common.toml` into `load_all()` list before the next major config refactor. (Ownership is now documented in [06_shared_03](06_shared_03_runtime_and_execution.md) §2a Config Ownership.)
- **Notes for AI reference:** The issue is tracked and acknowledged, not a hidden defect. Canonical ownership table is in [06_shared_03](06_shared_03_runtime_and_execution.md) §2a.

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

### IMPORT-01: `shared/` must not import from `agent/`, `mcp/`, `rag/`, or `db/`

- **Type:** Document inconsistency (architectural constraint)
- **Impact scope:** All modules in `shared/`; enforced by `.importlinter`
- **Statement A:** `06_spec_shared.md §5` states this constraint explicitly.
- **Statement B:** The constraint is enforced via `.importlinter` config. Violations fail `PYTHONPATH=scripts uv run lint-imports`.
- **Current safe interpretation:** Any `import` from `shared/` that reaches `agent/`, `mcp/`, `rag/`, or `db/` is a bug. Fix by inverting the dependency.
- **Recommended action:** Run `lint-imports` to verify. Never add upper-layer imports to `shared/`.
- **Notes for AI reference:** If a `shared/` module needs agent/mcp/rag behavior, use dependency injection via function arguments instead.

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
