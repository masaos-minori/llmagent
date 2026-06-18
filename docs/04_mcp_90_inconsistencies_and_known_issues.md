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

### BUG-02: `app_module` value in github-mcp inconsistent with other servers

- **Type:** Implementation bug
- **Impact scope:** `mcp/github/server.py`, `MCPServer.run_http()`
- **Description:** `GithubMCPServer.app_module = "github_mcp_server:app"` (bare module name) while all other 10 servers use the dotted path `"mcp.<submodule>.server:app"`. If `run_http()` were called on github-mcp, uvicorn would fail to import the module.
- **Mitigation:** github-mcp uses OpenRC-managed persistent HTTP mode, so `run_http()` is never called. The entry point script (`scripts/mcp/github/server.py`) uses `uvicorn.run("mcp.github.server:app", ...)` directly.
- **Recommended action:** Fix the class attribute for consistency, or add a doc comment explaining why it differs.

---

### BUG-03: Dry-run inputSchema omission for file/github/cicd tools

- **Type:** Implementation issue
- **Impact scope:** `mcp/file/write_tools.py`, `mcp/file/delete_tools.py`, `mcp/cicd/tools.py` — `inputSchema` definitions
- **Description:** Several tools support `dry_run` in their Pydantic request models and service layer, but do NOT expose it in the MCP tool `inputSchema`. The LLM therefore never sees `dry_run` as an available parameter unless it already knows about it.
- **Affected tools:**
  | Server | Tool | dry_run in model | dry_run in inputSchema | dry_run in service |
  |---|---|---|---|---|
  | file-write-mcp | `write_file` | Yes | **No** | Yes |
  | file-write-mcp | `move_file` | Yes | **No** | Yes |
  | file-delete-mcp | `delete_file` | Yes | **No** | Yes |
  | file-delete-mcp | `delete_directory` | Yes | **No** | Yes |
  | cicd-mcp | `trigger_workflow` | Yes | **No** | Yes |
- **Impact:** Tools still accept `dry_run` if manually specified (Pydantic ignores undeclared inputSchema fields), but LLMs cannot discover the parameter from the schema.
- **Recommended action:** Add `dry_run` to the `inputSchema` definitions for all affected tools.

---

### BUG-04: CreateDirectoryRequest lacks dry_run entirely

- **Type:** Implementation gap
- **Impact scope:** `mcp/file/write_models.py`, `mcp/file/write_service.py`
- **Description:** `CreateDirectoryRequest` has no `dry_run` field in its Pydantic model, inputSchema, or service handler. The 04_mcp_04 documentation previously claimed it supported dry_run (now corrected).
- **Recommended action:** Add `dry_run` field to `CreateDirectoryRequest` model, inputSchema, and `create_directory()` service method if dry-run support is desired.

---

### DOC-01: Cache key documented as MD5, code uses plain string

- **Type:** Document inconsistency (resolved)
- **Impact scope:** `shared/tool_executor.py`, `04_mcp_03_routing_lifecycle_and_execution.md`
- **Description:** Docs state cache key is `MD5(tool_name + orjson_sorted(args))`. The code uses `f"{tool_name}:{_json_dumps(args)}"` — a plain string without hashing. A separate `tool_call_key()` MD5 helper function exists in the codebase but is never called in the cache path.
- **Resolution:** Doc updated 2026-06-18 — cache key documented as plain string, NOT MD5. The `tool_call_key()` function remains unused (available for future use).
- **Current safe interpretation:** The cache key is a plain concatenation of tool name and JSON args with colon separator. No hash is computed.
- **Recommended action:** Complete.

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
