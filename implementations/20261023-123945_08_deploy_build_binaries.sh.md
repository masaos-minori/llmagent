## Goal
Carry each server's own config file name in `ENTRIES` and make the generated launcher call `ConfigLoader.restrict_to()` before importing the server module (`REQ-003`).

## Scope
- Extend the `ENTRIES` rows (lines 121-137) with a fourth `:`-separated field, update the parsing in the main loop (lines 336-348), `build_one` and `gen_launcher` (lines 236-257), and the table comment.
- The `mcpstart002` plan edits only the `gen_launcher` comment; apply the two changes sequentially.

## Assumptions
- Verified by probe: with restrict-first, the shell, git, web_search, github, cicd, rag_pipeline and mdq modules import successfully; the three file servers need the file-package row first.
- Nuitka compiles the launcher and follows static imports; the added `from shared.config_loader import ConfigLoader` is static, so no `--include-module` flag is needed (confirmed only by the Phase 5 rebuild, plan UNK-01).

## Design decisions
- Put the literal config file name in the launcher so the restriction is active before the server module is imported; `run_http()` calls `restrict_to` again with the same set, which is allowed.
- A test (new test module) pins each `ENTRIES` config name against the server class `own_config_file`, so the duplicated name cannot drift.

## Alternatives considered
- Dynamic import in the launcher: rejected, Nuitka may not bundle dynamically imported modules.

## Implementation
### Target file
`deploy/build_binaries.sh`

### Procedure
1. Change each MCP `ENTRIES` row to `module:final_name:Class:config_file` (for example `mcp_servers.shell.shell_server:mcp_shell:ShellMCPServer:shell_mcp_server.toml`) and the agent row to `agent.repl:agent::`; update the table comment (fields and count).
2. In the main loop split the rest of the row into `final_name`, `cls` and `cfg` (`cfg="${r2#*:}"` where `r2` is what follows `final_name`).
3. Pass `cfg` through `build_one` to `gen_launcher` as a fourth argument.
4. In the MCP branch of `gen_launcher` emit `from shared.config_loader import ConfigLoader`, then `ConfigLoader.restrict_to("${cfg}")`, then `from ${module} import ${cls}`, then the existing `__main__` block.

### Method
- Keep the agent branch (empty `cls`) unchanged.
- Keep comments in the script's existing Japanese.

### Details
- Config names: shell "shell_mcp_server.toml", git "git_mcp_server.toml", web_search "web_search_mcp_server.toml", file_delete "file_delete_mcp_server.toml", file_write "file_write_mcp_server.toml", file_read "file_read_mcp_server.toml", github "github_mcp_server.toml", cicd "cicd_mcp_server.toml", rag_pipeline "rag_pipeline_mcp_server.toml", mdq "mdq_mcp_server.toml" (each equals the class `own_config_file`).
- Evidence: `deploy/build_binaries.sh:121-137`, `:236-257`, `:336-348`.

## Compatibility considerations
- Generated launchers change; binary behavior is otherwise the same. Existing `BUILD_ONLY` filtering uses `final_name` and is unaffected.

## Security considerations
- Strengthens ADR-002 config isolation: a server process can no longer read another server's configuration, including its token and policy settings, through package imports or ahead of the restriction.

## Rollback considerations
- N/A: revert the commit and rebuild the binaries.

## Validation plan
- `bash -n deploy/build_binaries.sh`, `uv run pytest tests/mcp_servers/test_config_isolation_import.py tests/tools/test_manage_binaries.py`, then the Plan's Phase 5 rebuild of all ten binaries with a smoke start of each.

## Completion criteria
- `ENTRIES` carries a config name per server, the generated launcher orders `restrict_to` before the server import, the script parses, and the rebuilt binaries start.

## Out of Scope
- The `gen_launcher` comment (posture-gate plan)
- `LAZY_IMPORTS`

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the `ENTRIES`, parsing and launcher-template changes per Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan (`tests/mcp_servers/test_config_isolation_import.py`, tracked in its own document) | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) and the Phase 5 rebuild | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-003` (restrict config before the server import in the launcher)
- **Source issue**: issues/20261023-114103_mcpstart004_server-modules-load-config-before-isolation-and-package-init-imports-sibling-servers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261023-115449_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-123945
- **Related target files**: deploy/build_binaries.sh
