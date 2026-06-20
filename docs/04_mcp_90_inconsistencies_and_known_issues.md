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

### SPEC-01: tool_definitions_strict + /v1/tools mismatch behavior undocumented per-server

- **Type:** Needs confirmation
- **Impact scope:** `AgentREPL._check_tool_definitions()`, all MCP servers
- **Description:** When `tool_definitions_strict=True`, a mismatch between `config/tools_definitions.toml` tool names and a server's `/v1/tools` response causes `RuntimeError`. The exact behavior when a specific server is unreachable (vs tool name mismatch) is not clearly specified. The current code appears to skip the check if ALL servers are unreachable, but the per-server behavior is unclear.
- **Current safe interpretation:** If the agent fails to start with `RuntimeError`, check that tool names in `tool_definitions` exactly match what each server reports via `/v1/tools`.
- **Recommended action:** Document the skip condition ("all servers unreachable → skip") in `05_agent_02_runtime-architecture.md`.

---

