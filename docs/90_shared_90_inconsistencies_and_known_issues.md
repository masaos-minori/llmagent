# Shared/DB Inconsistencies and Known Issues

This file catalogs all known inconsistencies between source documents, implementation
bugs, undocumented areas, unimplemented features, and undefined behavior in the
`shared/` and `db/` layers.

Each entry uses the required format:
- **Type:** `Document inconsistency` / `Implementation bug` / `Undocumented` / `Unimplemented` / `Undefined` / `Needs confirmation`

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

### DESIGN-02: Responsibility boundary between `ToolResultStore` and `messages` history

- **Type:** Needs confirmation
- **Impact scope:** `db/tool_results.py::ToolResultStore`, `agent/session.py` messages table
- **Statement A:** `messages` table stores all LLM conversation messages (user/assistant/tool roles), including tool result messages.
- **Statement B:** `tool_results` table stores full tool result text, which is NOT in the `messages` table (only summary/truncated version appears in message history).
- **Current safe interpretation:** `messages` → conversation flow (what LLM sees). `tool_results` → full output archive (accessible via `/tool show <id>`).
- **Recommended action:** Document that `tool_results` is a supplementary store, not a replacement for `messages`.
- **Notes for AI reference:** When querying conversation history, use `messages`. When retrieving full tool output, use `ToolResultStore.get(id)`.

---
