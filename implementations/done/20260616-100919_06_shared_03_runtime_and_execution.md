# Implementation: docs/06_shared_03_runtime_and_execution.md

## Goal

Create the runtime infrastructure reference covering ConfigLoader, Logger, plugin_registry,
OTel tracer, token_counter, formatters, ToolExecutor flow, and McpServerConfig.

## Scope

- Content from: `06_spec_shared.md` §6.1-6.2 + §6.5-6.8 + §7-8 + §10-11 + §13
- Content from: `06_ref-infra.md` and `06_ref-mcp.md` (supplementary API details)
- Output: `docs/06_shared_03_runtime_and_execution.md`
- Not covered: type/DTO definitions (→ 02), DB layer (→ 04/05)

## Assumptions

- ToolExecutor is the central execution path; plugin > UNAVAILABLE check > cache > MCP
- ServerLifecycleManager was deleted; routing handled by factory.py _ServerLifecycleRouter
- load_all() loads 11 hardcoded files (excludes common.toml)

## Implementation

### Target file

`docs/06_shared_03_runtime_and_execution.md`

### Procedure

1. ConfigLoader (shared/config_loader.py): constructor, load(), load_all() signatures;
   list of 11 hardcoded files; silent skip vs ValueError distinction; _ prefix exclusion
2. Logger (shared/logger.py): constructor, log methods, set_context/clear_context;
   FileHandler + StreamHandler; structured_log option; propagate=False
3. plugin_registry (shared/plugin_registry.py): load_plugins(), register_tool(),
   get_tool(), register_command(), register_pipeline_stage(), iter_commands()
4. OTel tracer (shared/otel_tracer.py): build_tracer() signature; private provider design;
   NoOp stub when disabled
5. token_counter (shared/token_counter.py): get_token_count() signature;
   POST /tokenize → chars//4 fallback; _WarnOnce once-only warning
6. formatters (shared/formatters.py): truncate(), fmt_kvlog(), fmt_size(), fmt_md_link(),
   MAX_SNIPPET_CHARS
7. git_helper (shared/git_helper.py): get_repo_info() return dict; no "origin" key;
   commit is hexsha[:8]; returns None on any exception
8. ToolExecutor flow (shared/tool_executor.py): execution order diagram;
   ToolCallResult dataclass; TTL+LRU cache (is_error=false only); concurrency Semaphore
9. McpServerConfig (shared/mcp_config.py): reference to spec_mcp.md §9.1

### Method

- Use subsection per module; include key signatures and notes
- ToolExecutor flow section: reproduce the 5-step execution order from spec §8.3
- Error handling table from spec §11

### Details

- load_all() file list: llm, http, rag, context, tools, memory, otel, security,
  system_prompts, mcp_servers, tools_definitions (11 files; common.toml excluded)
- ToolCallResult: dataclass(output: str, is_error: bool, request_id: str, server_key: str)
- Cache stores only is_error=false results (TTL + LRU)

## Validation plan

- File exists at `docs/06_shared_03_runtime_and_execution.md`
- Sections for all 9 modules
- ToolExecutor 5-step execution flow present
- load_all() 11-file list present
- Error handling table present
