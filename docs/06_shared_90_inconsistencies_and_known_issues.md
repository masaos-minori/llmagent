# Shared/DB Inconsistencies and Known Issues

This file catalogs all known inconsistencies between source documents, implementation
bugs, undocumented areas, unimplemented features, and undefined behavior in the
`shared/` and `db/` layers.

Each entry uses the required format:
- **Type:** `Document inconsistency` / `Implementation bug` / `Undocumented` / `Unimplemented` / `Undefined` / `Needs confirmation`

---

### CONFIG-01: `ConfigLoader.load_all()` does not include `common.toml` (RESOLVED)

- **Type:** Document inconsistency (resolved)
- **Impact scope:** `shared/config_loader.py`
- **Description:** `common.toml` was previously excluded from `load_all()`. As of the current implementation, `common.toml` is included at index 0 of `_BASE_CONFIG_FILES` (12 files total). See [06_shared_03](06_shared_03_runtime_and_execution.md) §2a Config Ownership for the canonical ownership table.
- **Current safe interpretation:** `load_all()` now includes all 12 config files including `common.toml`. `build_db_config()` calls `ConfigLoader().load_all()` (no separate `load("common.toml")` needed).
- **Recommended action:** Complete.
- **Notes for AI reference:** `common.toml` is included at index 0 of `_BASE_CONFIG_FILES`. The ownership table in [06_shared_03](06_shared_03_runtime_and_execution.md) §2a is the canonical reference.

---

### CONFIG-03: `common.toml` non-integration is a documented DB-layer known issue (RESOLVED)

- **Type:** Needs confirmation (resolved)
- **Impact scope:** `shared/config_loader.py`, `db/config.py`
- **Description:** `common.toml` was previously absent from `load_all()`, requiring separate loading. As of the current implementation, `common.toml` is included in `load_all()` at index 0. `build_db_config()` now calls `ConfigLoader().load_all()` directly.
- **Current safe interpretation:** The issue is resolved. All DB and embedding paths are available from `load_all()`.
- **Recommended action:** Complete.
- **Notes for AI reference:** `build_db_config()` in `db/config.py` calls `ConfigLoader().load_all()` (line 56). No separate `load("common.toml")` call is needed.

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

### DESIGN-01: Responsibility boundary between `MemoryDeleteStore` and `SQLiteMemoryDeleteStore` (RESOLVED)

- **Type:** Document inconsistency (resolved)
- **Impact scope:** `db/store_protocols.py::MemoryDeleteStore` (Protocol), `db/store_impl.py::SQLiteMemoryDeleteStore` (implementation)
- **Statement A:** `MemoryDeleteStore` is a `Protocol` defining `delete_memories_before(older_than_days)`.
- **Statement B:** `SQLiteMemoryDeleteStore` implements this protocol for SQLite (deletes from `memories`, `memories_fts`, `memories_vec` atomically).
- **Current safe interpretation:** The Protocol/implementation split allows future non-SQLite backends. For current SQLite-only deployments, use `SQLiteMemoryDeleteStore` directly.
- **Resolution:** Extensibility rationale documented in [06_shared_05 §4 MemoryDeleteStore](06_shared_05_db_api_and_operations.md). Directory listing updated in [06_shared_04](06_shared_04_db_architecture_and_schema.md).
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

### UNIMPL-01: `ArtifactEvent` has no event bus (RESOLVED)

- **Type:** Unimplemented (resolved)
- **Impact scope:** `shared/events.py::ArtifactEvent`
- **Description:** `ArtifactEvent` is a TypedDict with no delivery system, no consumers. Future event-envelope fields (`event_id`, `source`, `correlation_id`) are documented as aspirational in the module docstring and in [06_shared_02](06_shared_02_types_and_protocols.md).
- **Current safe interpretation:** Creating an `ArtifactEvent` instance triggers no action. It is a type annotation only.
- **Recommended action:** Complete. Future envelope design is documented; implementation is deferred.

---
