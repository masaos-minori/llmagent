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

### BUG-01: McpServerHealthRegistry record_success/record_failure never called

- **Type:** Implementation bug
- **Impact scope:** `shared/tool_executor.py` (`ToolExecutor._raw_execute()`), `shared/mcp_config.py` (`McpServerHealthRegistry`)
- **Statement A:** `McpServerHealthRegistry` is designed to transition servers through HEALTHY → DEGRADED → UNAVAILABLE states based on consecutive failures. `ToolExecutor._raw_execute()` checks `is_unavailable()` and blocks dispatch when UNAVAILABLE.
- **Statement B:** `ToolExecutor._raw_execute()` does NOT call `record_failure()` on transport errors or `record_success()` on success. The failure counter is never incremented.
- **Current safe interpretation:** DEGRADED and UNAVAILABLE states are never reached in practice. The health registry always returns HEALTHY. The `is_unavailable()` check at the start of `_raw_execute()` is effectively dead code.
- **Recommended action:** Add `record_failure()` call after transport errors in `_raw_execute()` and `record_success()` call after successful responses. (`tool_executor.py:509-516`)
- **Notes for AI reference:** Do not rely on health state transitions to detect degraded MCP servers. Use `/mcp` health probes or log monitoring instead.

---

### MISSING-01: mdq-mcp service layer is placeholder implementation

- **Type:** Unimplemented
- **Impact scope:** `mcp/mdq/service.py`, `mcp/mdq/indexer.py`, `mcp/mdq/search.py`; all 7 mdq tools
- **Description:** The mdq-mcp server schema, HTTP endpoints, and `MCPServer` base class are complete. All 7 MCP tools (`search_docs`, `get_chunk`, `outline`, `index_paths`, `refresh_index`, `stats`, `grep_docs`) call `MdqService` which returns stub strings: `"Search results for: {query}"`, `"Indexing complete"`, etc. No actual data operations occur.
- **Planned features not yet implemented:** FTS5 index (Phase 2), embedding index `md_chunks_vec`, summary cache, AST parser (Phase 3)
- **Current safe interpretation:** mdq-mcp tools always return stub strings. They do not search, index, or retrieve any data. `outline` is the only tool with partial real behavior (reads file content via `parse_markdown()` but returns it as-is).
- **Recommended action:** Implement `MdqService` with real FTS5 indexing and search before using in production.
- **Notes for AI reference:** Do NOT use `search_docs`, `get_chunk`, `stats`, `index_paths`, `refresh_index`, or `grep_docs` to retrieve actual document content. Use `rag-pipeline-mcp` instead. Only `outline` may return file content (partial implementation).

---

### MISSING-02: shell_run_bg tool is not implemented

- **Type:** Unimplemented
- **Impact scope:** `mcp/shell/server.py`, `shared/tool_constants.py`
- **Statement A:** `shell_run_bg` appears in documentation references (`04_spec_mcp.md §6.2` mentions it in the shell server tool list).
- **Statement B:** The tool is NOT implemented in `mcp/shell/server.py`. Only `shell_run` is implemented.
- **Current safe interpretation:** `shell_run_bg` cannot be called. Calling it will return `("Unknown tool: shell_run_bg", True)`.
- **Recommended action:** Either implement `shell_run_bg` (background command execution with job ID tracking) or remove references from documentation.
- **Notes for AI reference:** Use `shell_run` only. Do not attempt `shell_run_bg`.

---

### MISSING-03: query_sqlite not in static routing table

- **Type:** Undefined / Document inconsistency
- **Impact scope:** `shared/tool_constants.py`, `shared/route_resolver.py`, `ToolRouteResolver._fallback_route()`
- **Statement A:** `04_spec_mcp.md §6.2` includes `sqlite-mcp` in the server list with `query_sqlite` as its tool.
- **Statement B:** `query_sqlite` is NOT defined in any frozenset in `shared/tool_constants.py`. The static routing table in `ToolRouteResolver._fallback_route()` does not include it. A comment in `06_ref-mcp.md §3` notes it is defined separately as a prefix rule in `route_resolver.py`.
- **Current safe interpretation:** `query_sqlite` MUST be declared in `McpServerConfig.tool_names` for the `sqlite` server key. Without `tool_names`, routing will fail with `ValueError: Unknown tool: 'query_sqlite'`.
- **Recommended action:** Add `query_sqlite` to `shared/tool_constants.py` as part of a `SQLITE_TOOLS` frozenset, OR confirm `tool_names = ["query_sqlite"]` is always set in config.
- **Notes for AI reference:** Always verify sqlite-mcp config includes `tool_names = ["query_sqlite"]`.

---

### UNDOC-01: startup_mode="subprocess" + transport="stdio" validation not documented

- **Type:** Document inconsistency / Needs confirmation
- **Impact scope:** `shared/mcp_config.py` `McpServerConfig.__post_init__()` (line 57-67)
- **Statement A:** `04_spec_mcp.md §9.2` shows a startup_mode table covering `http` and `stdio` transports but does not mention validation errors.
- **Statement B:** `04_spec_mcp.md §13` notes that `startup_mode="subprocess"` + `transport="stdio"` raises `ValueError` in `mcp_config.py:57-67`. This validation is not described in the startup mode compatibility table.
- **Current safe interpretation:** `startup_mode="subprocess"` is ONLY valid with `transport="http"`. Using it with `transport="stdio"` raises `ValueError` at agent startup.
- **Recommended action:** Add explicit compatibility table to `McpServerConfig` documentation noting the invalid combination.
- **Notes for AI reference:** Always pair `startup_mode="subprocess"` with `transport="http"`. Never use it with `transport="stdio"`.

---

### UNDOC-02: McpServerConfig.transport field is str, not Literal type

- **Type:** Needs confirmation
- **Impact scope:** `shared/mcp_config.py` `McpServerConfig.transport`
- **Description:** `transport` is typed as `str`. The valid values are `"http"` and `"stdio"` only (validated in `__post_init__`), but the type annotation does not use `Literal["http", "stdio"]`. This makes type checkers unable to catch invalid values at the call site.
- **Current safe interpretation:** Use only `"http"` or `"stdio"`. Any other value raises `ValueError` at runtime.
- **Recommended action:** Change annotation to `transport: Literal["http", "stdio"]` in `McpServerConfig`. Referenced in `implementations/20260606-194710_shared_types.md`.
- **Notes for AI reference:** No functional impact. Type-safety enhancement only.

---

### SPEC-01: tool_definitions_strict + /v1/tools mismatch behavior undocumented per-server

- **Type:** Needs confirmation
- **Impact scope:** `AgentREPL._check_tool_definitions()`, all MCP servers
- **Description:** When `tool_definitions_strict=True`, a mismatch between `config/tools_definitions.toml` tool names and a server's `/v1/tools` response causes `RuntimeError`. The exact behavior when a specific server is unreachable (vs tool name mismatch) is not clearly specified. The current code appears to skip the check if ALL servers are unreachable, but the per-server behavior is unclear.
- **Current safe interpretation:** If the agent fails to start with `RuntimeError`, check that tool names in `tool_definitions` exactly match what each server reports via `/v1/tools`.
- **Recommended action:** Document the skip condition ("all servers unreachable → skip") in `05_agent_02_runtime-architecture.md`.
