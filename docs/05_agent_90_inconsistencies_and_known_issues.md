# Agent Inconsistencies and Known Issues

This file catalogs known bugs, spec conflicts, document inconsistencies, unimplemented
areas, and open questions in the agent layer (`agent/`, `shared/`).

Each entry format:
- **Type:** `Document inconsistency` / `Implementation bug` / `Undocumented` / `Needs confirmation` / `Open Question`
- **Impact scope:** Affected modules / behavior
- **Statement A / B:** Conflicting facts (when applicable)
- **Current safe interpretation:** What to assume when uncertain
- **Recommended action:** Fix or investigation needed
- **Notes for AI reference:** Guidance for AI reasoning about this issue

---

## Open Questions

### Session SQLite corruption recovery gap

- **Type:** Resolved — flat `/db` aliases removed (use `/db rag ...` or `/db session ...` instead)
- `/db rag recover [backup-path]` targets `rag.sqlite` only (via `RagMaintenanceService`)
- `/db session recover [backup-path]` exists: calls `DbMaintenanceService.recover_session()` → `recover_corruption(backup_path, target="session")`
- Operator path: `/db session recover /path/to/backup.sqlite`

---

## Migration Notes

### NOTE-04: Flat `/db` aliases removed (2026-06-28)

- **Type:** Breaking change — removed without backward-compatible aliases
- **Removed commands:** `/db urls`, `/db clean <url>`, `/db rebuild-fts`, `/db recover [backup-path]`, `/db stats`, `/db health`, `/db checkpoint [MODE]`, `/db vacuum`, `/db purge [--max-sessions N] [--max-age-days N]`, `/db consistency`
- **Replacement:** Use scoped forms: `/db rag urls|clean|rebuild-fts|recover|stats|consistency` or `/db session stats|health|checkpoint|vacuum|purge|recover`

---

### NOTE-01: `/note` command group removed (2026-06-28)

- **Type:** Breaking change — removed without backward-compatible aliases
- **Removed commands:** `/note add`, `/note list`, `/note delete`, `/note pin`, `/note unpin`, `/note search`
- **Reason:** Persistent notes removed from the Agent command layer. Long-term searchable context should use the memory layer instead.
- **Replacement:** Use `/memory list`, `/memory search`, `/memory show`, `/memory pin`, `/memory unpin`, `/memory delete`, `/memory prune`, `/memory status`
- **Schema impact:** `notes` table removed from new database schema creation; existing databases retain the table for backward compatibility

### NOTE-02: `/ingest` command removed (2026-06-28)

- **Type:** Breaking change — removed without backward-compatible aliases
- **Removed command:** `/ingest <url|path> [lang] [--snippets-only]`
- **Reason:** RAG ingestion is an operational pipeline concern, not an Agent REPL command. The Agent REPL should provide RAG search/debugging, not mutate the RAG DB through `/ingest`.
- **Replacement:** Run the RAG ingestion pipeline outside the Agent REPL using `scripts/rag/ingestion/crawler.py` directly; use `/rag search <query> [--debug]` for retrieval and debugging from the Agent.

### NOTE-03: `/debug audit` removed (2026-06-28)

- **Type:** Breaking change — removed without backward-compatible aliases
- **Removed command:** `/debug audit`
- **Reason:** Audit log browsing is handled by the dedicated `/audit` command. `/debug` should only control debug mode and log verbosity.
- **Replacement:** Use `/audit`, `/audit tail N`, `/audit turn <task_id>`, or `/audit tool <name>`

---

## Undocumented Areas

### UNDOC-02: Plugin tool return value convention not enforced at registration time

- **Type:** Addressed (runtime enforcement exists at call time)
- **Impact scope:** `shared/plugin_registry.py @register_tool`, `shared/tool_executor.py ToolExecutor.execute()`
- **Current state:** `ToolExecutor.execute()` validates the return value at call time: checks `isinstance(result_raw, tuple)`, `len >= 2`, `isinstance(output, str)`, `isinstance(is_error, bool)` — raises `ValueError` or `TypeError` on mismatch. No enforcement at `@register_tool` decoration time.
- **Current safe interpretation:** Return type errors surface on the first call, not at startup. Convention `tuple[str, bool]` is documented in `05_agent_11_extension-points.md`.
- **Notes for AI reference:** Plugin tools bypass MCP routing and TTL cache. A plugin with the same name as an MCP tool shadows the MCP tool.

---

## Document Inconsistencies

### DISC-01: diagnostics.jsonl vs session_diagnostics table dual persistence

- **Type:** Document inconsistency
- **Impact scope:** `05_agent_04_state-and-persistence.md`, `05_agent_10_operations-and-observability.md`
- **Statement A:** `diagnostics.jsonl` is the primary diagnostic persistence mechanism (documented as "may be deprecated in future" with no timeline)
- **Statement B:** `session_diagnostics` table via `DiagnosticStore.save()` is the structured query path for diagnostics
- **Current safe interpretation:** Both stores are active and serve different purposes. `session_diagnostics` for structured SQL queries; `diagnostics.jsonl` for append-only post-mortem analysis. Neither is deprecated.
- **Recommended action:** Clarify in docs that both are active; remove or update "may be deprecated" note with concrete timeline

### DISC-02: memory_jsonl_path vs memory_jsonl_dir

- **Type:** Document inconsistency
- **Impact scope:** `05_agent_12_memory.md` (line 222 — stale reference)
- **Statement A:** Config key is `memory_jsonl_path` (documented in `05_agent_12_memory.md`)
- **Statement B:** Canonical config key is `memory_jsonl_dir` (verified in `config_dataclasses.py:297`, `config_builders.py:203`; `memory_jsonl_path` does not exist in code)
- **Current safe interpretation:** `memory_jsonl_dir` is the canonical key; filename `memories.jsonl` is appended by `factory.py`

### DISC-03: branch field in memory retrieval

- **Type:** Undocumented behavior
- **Impact scope:** `05_agent_12_memory.md` (line 190 — branch described only as "for context filtering")
- **Statement A:** `branch` field is stored metadata for context filtering (implied by doc)
- **Statement B:** `branch` is actively used in `FtsRetriever._context_boost()` as a relevance rescoring signal; records without matching branch are still returned but ranked lower
- **Current safe interpretation:** Branch affects ranking, not filtering — it is an active retrieval parameter

### DISC-04: workflow_mode=required startup blocking scope

- **Type:** Needs confirmation
- **Impact scope:** `05_agent_08_configuration.md` (workflow_mode description)
- **Statement A:** `workflow_mode = "required"` raises `RuntimeError` when `WorkflowLoader` fails during `Orchestrator.__init__()`
- **Statement B:** Unclear whether failure is at agent startup or at first turn — depends on whether `StartupOrchestrator.run()` catches this
- **Current safe interpretation:** Failure occurs during agent boot (Orchestrator construction phase), not at the first turn

### DISC-05: memory SQLite DB location

- **Type:** Document inconsistency
- **Impact scope:** `05_agent_09_data-layer.md` (line 130 — "session.sqlite or separate")
- **Statement A:** Memory tables (`memories`, `memories_fts`, `memories_vec`) are in "session.sqlite or separate" (ambiguous)
- **Statement B:** All memory tables live in `session.sqlite` — verified by `SQLiteHelper("session")` usage throughout `scripts/agent/memory/store.py` and `retriever.py`
- **Current safe interpretation:** Memory tables are in `session.sqlite`, same DB as sessions/messages

---
