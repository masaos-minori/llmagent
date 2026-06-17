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

- **Type:** RESOLVED (Implementation bug — fixed)
- **Impact scope:** `shared/tool_executor.py` (`ToolExecutor._raw_execute()`), `shared/mcp_config.py` (`McpServerHealthRegistry`)
- **Resolution:** `ToolExecutor._raw_execute()` now calls `record_success()` on transport success and `record_failure()` on `TransportError`. The HEALTHY → DEGRADED → UNAVAILABLE state machine functions as designed. Test coverage added in `tests/test_tool_executor_routing.py` (`TestToolExecutorHealthGate`).
- **Notes for AI reference:** Health state transitions are now active. A server reaching UNAVAILABLE will be blocked from dispatch by the `is_unavailable()` check. The registry resets to HEALTHY on the next successful call via `record_success()`.

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

### UNDOC-01: startup_mode × transport compatibility matrix documented

- **Type:** Resolved
- **Impact scope:** `shared/mcp_config.py`, `04_mcp_01_system_overview.md`
- **Description:** Compatibility matrix exists in `04_mcp_01_system_overview.md` (Startup Modes section). Validation error message in `McpServerConfig.__post_init__()` explains valid alternatives: "startup_mode='subprocess' is only valid for transport='http'; stdio servers use 'persistent' or 'ondemand'".
- **Valid combinations:** persistent+http, subprocess+http, persistent+stdio, ondemand+stdio. Invalid: subprocess+stdio.
- **Recommended action:** None - already documented and enforced.
- **Notes for AI reference:** Always pair `startup_mode="subprocess"` with `transport="http"`.

---

### UNDOC-02: McpServerConfig.transport field uses StrEnum, not Literal type

- **Type:** Resolved
- **Impact scope:** `shared/mcp_config.py` `McpServerConfig.transport`, `startup_mode`, `healthcheck_mode`
- **Description:** Fields use `StrEnum` types (`TransportType`, `StartupMode`, `HealthcheckMode`) which provide stronger typing than `Literal`. Invalid values are caught at runtime via `ValueError` from enum construction. Tests updated to match actual error messages.
- **Current safe interpretation:** Use only valid enum values. Invalid values raise `ValueError: 'X' is not a valid <EnumName>`.
- **Recommended action:** None - already resolved. StrEnum is preferred over Literal for these fields.
- **Notes for AI reference:** `transport`, `startup_mode`, and `healthcheck_mode` are enum-typed. Use `TransportType.HTTP`, `StartupMode.PERSISTENT`, etc.

---

### SPEC-02: shell-mcp startup_mode — `subprocess` vs `persistent`

- **Type:** Document inconsistency
- **Impact scope:** `04_mcp_01_system_overview.md`, `04_mcp_04_server_catalog.md`, `04_mcp_06_configuration_and_operations.md`
- **Statement A:** `04_mcp-shell.md §1` (canonical per-server reference) states `startup_mode = "subprocess"` — the agent manages the server subprocess directly, without OpenRC.
- **Statement B:** Earlier versions of `04_mcp_01` and `04_mcp_04` listed shell-mcp as `persistent (HTTP, OpenRC shell-mcp)`.
- **Current safe interpretation:** `subprocess` is correct per the canonical source. shell-mcp is NOT managed by OpenRC. The agent starts it as a subprocess via `_ServerLifecycleRouter.start_http_subprocess()`.
- **Recommended action:** Fixed in `04_mcp_01` and `04_mcp_04` (2026-06-16). Verify in `config/mcp_servers.toml` that `startup_mode = "subprocess"` is set for the shell server key.
- **Notes for AI reference:** shell-mcp does NOT have an OpenRC `init.d` service. It starts and stops with the agent process.

---

### SPEC-03: shell-mcp `max_output_kb` tool input default — 512 vs 256

- **Type:** Document inconsistency
- **Impact scope:** `04_mcp_04_server_catalog.md` shell-mcp tool input table
- **Statement A:** `04_mcp-shell.md §2.4` (canonical per-server reference) states the tool input `max_output_kb` default is 512 KB. The §3 input schema example also shows `"max_output_kb": 512`.
- **Statement B:** Earlier version of `04_mcp_04` listed 256 as the default.
- **Current safe interpretation:** 512 KB is the correct tool input default. The config server-side cap (`max_output_kb` in `config/shell_mcp_server.toml`) defaults to 4096 KB.
- **Recommended action:** Fixed in `04_mcp_04` (2026-06-16).
- **Notes for AI reference:** Two distinct limits: tool input `max_output_kb` (request-level, default 512 KB) vs config `max_output_kb` (server-side cap, default 4096 KB). The server clamps the request value to the config cap.

---

### SPEC-01: tool_definitions_strict + /v1/tools mismatch behavior undocumented per-server

- **Type:** Needs confirmation
- **Impact scope:** `AgentREPL._check_tool_definitions()`, all MCP servers
- **Description:** When `tool_definitions_strict=True`, a mismatch between `config/tools_definitions.toml` tool names and a server's `/v1/tools` response causes `RuntimeError`. The exact behavior when a specific server is unreachable (vs tool name mismatch) is not clearly specified. The current code appears to skip the check if ALL servers are unreachable, but the per-server behavior is unclear.
- **Current safe interpretation:** If the agent fails to start with `RuntimeError`, check that tool names in `tool_definitions` exactly match what each server reports via `/v1/tools`.
- **Recommended action:** Document the skip condition ("all servers unreachable → skip") in `05_agent_02_runtime-architecture.md`.
