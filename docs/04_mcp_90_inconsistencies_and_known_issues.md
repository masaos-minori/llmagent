# MCP Inconsistencies and Known Issues

This file catalogs bugs, unimplemented features, spec conflicts, and undefined behavior
in the MCP layer discovered during documentation restructuring.

Each entry format:
- **Type:** `Implementation bug` / `Unimplemented` / `Document inconsistency` / `Undefined` / `Needs confirmation`
- **Impact scope:** Affected modules/behavior
- **Statement A / B:** Conflicting facts (when applicable)
- **Current safe interpretation:** What to assume when uncertain
- **Recommended action:** Fix or investigation needed
- **Notes for AI reference:** Guidance for AI reasoning about this issue

---

### SPEC-01: tool_definitions_strict + /v1/tools mismatch behavior undocumented per-server

- **Type:** Needs confirmation
- **Impact scope:** `AgentREPL._check_tool_definitions()`, all MCP servers
- **Description:** When `tool_definitions_strict=True`, a mismatch between `config/tools_definitions.toml` tool names and a server's `/v1/tools` response causes `RuntimeError`. The exact behavior when a specific server is unreachable (vs tool name mismatch) is not clearly specified. The current code appears to skip the check if ALL servers are unreachable, but the per-server behavior is unclear.
- **Current safe interpretation:** If the agent fails to start with `RuntimeError`, check that tool names in `tool_definitions` exactly match what each server reports via `/v1/tools`.
- **Recommended action:** Document the skip condition ("all servers unreachable → skip") in `05_agent_02_runtime-architecture.md`.

---

### MISSING-01: mdq-mcp documentation claimed stub behavior but FTS5 is functional

- **Type:** Document inconsistency (resolved)
- **Impact scope:** `docs/04_mcp_04_server_catalog.md`, `scripts/mcp/mdq/tools.py`, `scripts/mcp/mdq/server.py`
- **Statement A:** Documentation (catalog) stated "All tools return stub strings. No actual data operations occur."
- **Statement B:** Code (`MdqService`) implements real FTS5 search/indexing using SQLite virtual tables (`sections_fts`).
- **Resolution:** Statement B is correct. The service layer is functional. Tools carry `"status": "stub"` as metadata to signal the server is not production-validated, not that it is non-functional.
- **Current safe interpretation:** mdq-mcp performs real FTS5 search/indexing. It is experimental and not production-validated. Prefer `rag-pipeline-mcp` for production workloads.
- **Recommended action:** Completed — catalog updated to reflect FTS5 is functional; tool status set to `"stub"` as metadata signal; `/health` returns `"stub": true`.

---
