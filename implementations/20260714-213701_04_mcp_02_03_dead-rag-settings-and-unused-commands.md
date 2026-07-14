# Implementation Procedure: Remove Dead/Duplicated RAG Pipeline Settings and Unused /db rag Subcommands

## Goal

Remove all dead/duplicated RAG pipeline configuration from `config/agent.toml` and `AgentConfig`, remove the `/db rag` subcommand family, and remove the `/rag` slash command — while preserving `max_tool_turns` functionality (relocated to correct section) and keeping `embed_url` unchanged.

## Scope

### In-Scope
- Remove 15 RAG-related keys from `agent.toml` (Bucket 2 + Bucket 3 + Bucket 4)
- Remove corresponding fields from `RAGConfig` dataclass and `_build_rag_config()`
- Remove validators for removed Bucket 2 fields only
- Remove display lines for removed fields from `/config`
- Relocate `max_tool_turns` to "Tools" section in `agent.toml`
- Remove entire `/db rag <subcmd>` command family
- Remove entire `/rag` slash command
- Delete `tests/test_cmd_rag_refiner_hint.py`
- Update all affected documentation files

### Out-of-Scope
- Changing `rag_pipeline` MCP server behavior or `rag_pipeline_mcp_server.toml` schema
- Removing `embed_url` from `agent.toml` or `RAGConfig`
- Addressing unrelated `agent.toml` sections
- Removing `/db session <subcmd>` or `DbSessionOps`
- Removing `rag_delete_document` / `rag_list_documents` MCP tools
- Deciding whether `scripts/rag/maintenance.py` / `scripts/db/recovery.py` should be deleted if they become unreferenced
- Removing `/export` or `/compact` commands
- Updating `RagConfig` Protocol (still satisfied by `SimpleNamespace` adapter in `mcp_servers/rag_pipeline/models.py`)

## Assumptions

1. The requirement `requires/20260714_13_require.md` is the canonical specification.
2. Implementation inspection resolved the following unknowns:
   - **Tests constructing `RAGConfig` with removed fields**: YES — `test_tool_loop_guard.py`, `test_tool_result_formatter.py`, `test_tool_policy_comprehensive.py`, `test_tool_audit.py`, `test_tool_approval_preflight.py`, `test_tool_approval_risk.py`, `test_tool_approval_repos.py`, `test_tool_approval_paths.py`, `test_cmd_config_char.py` pass Bucket 2/3 fields to `build_agent_config()`. These tests will break and need updates.
   - **`RagConfig` Protocol concrete implementers after removal**: YES — `SimpleNamespace` adapter in `mcp_servers/rag_pipeline/models.py` still satisfies it. No Protocol update needed.
   - **Callers of `rebuild_fts()` and `recover_corruption()` besides `DbRagOps`**: YES — `memory_rebuild_ops.py::RebuildOps.rebuild_fts()` calls `rebuild_fts()`, and `db_maintenance_service.py` and `rag_maintenance_service.py` call `recover_corruption()`. These are NOT unreferenced.

## Unknowns (resolved during inspection)

1. Are there any tests constructing `RAGConfig` or `AgentConfig` with the removed fields? → Yes, multiple test files. See above.
2. Does the `RagConfig` Protocol still have any concrete implementers after removal? → Yes, `SimpleNamespace` adapter in `mcp_servers/rag_pipeline/models.py`.
3. Do `scripts/rag/maintenance.py::rebuild_fts()` and `scripts/db/recovery.py::recover_corruption()` have callers besides `DbRagOps`? → Yes, both have other callers. Not unreferenced.

## Affected areas

- Agent configuration (agent.toml, config_dataclasses, config_builders, config_validators)
- CLI commands (/db rag, /rag)
- Config display (/config output)
- Tests
- Documentation (~25 files)

## Implementation

### Procedure

#### Step 1: Inspect implementation to confirm findings

Verify the requirement file's claims by inspecting:

1. **`RAGConfig` dataclass** (`scripts/agent/config_dataclasses.py:149`): Confirm all 15 RAG keys are present as fields
2. **`_build_rag_config()`** (`scripts/agent/config_builders.py:153-169`): Confirm it reads these keys
3. **Validators** (`scripts/agent/config_dataclasses.py:169-175`): Confirm `_v_rag_tks`, `_v_rag_tkr`, `_v_rag_mcd`, `_v_rag_rrf` validate only Bucket 2 fields
4. **`/config` display** (`scripts/agent/commands/cmd_config_display.py`): Confirm it displays the removed fields
5. **`/rag` command** (`scripts/agent/commands/cmd_rag_export.py`): Confirm `_cmd_rag()` is the sole consumer of Bucket 3/4 keys
6. **`/db rag` subcommands** (`scripts/agent/commands/cmd_db.py:54-75`): Confirm dispatch structure
7. **`DbRagOps`** (`scripts/agent/commands/db_rag_ops.py`): Confirm class exists and is used only by `/db rag`
8. **Tests**: Search for test constructions of `RAGConfig` or `AgentConfig` with removed fields
9. **`RagConfig` Protocol** (`scripts/shared/types.py:80-91`): Check if any remaining implementer satisfies it

#### Step 2: Execute code changes grouped by category

##### Category A: Remove Bucket 2 fields (held in RAGConfig but never read for RAG execution)

Files to modify:
1. **`config/agent.toml`**: Remove `top_k_search`, `top_k_rerank`, `max_chunks_per_doc`, `rrf_k`, `use_semantic_cache`, `semantic_cache_threshold`, `semantic_cache_max_size` from "RAG pipeline" section
2. **`scripts/agent/config_dataclasses.py`**: Remove corresponding `RAGConfig` fields and validators `_v_rag_tks`, `_v_rag_tkr`, `_v_rag_mcd`, `_v_rag_rrf` from `__post_init__`
3. **`scripts/agent/config_builders.py`**: Remove corresponding field reads from `_build_rag_config()`
4. **`scripts/agent/commands/cmd_config_display.py`**: Remove display lines for `top_k_search`, `top_k_rerank`, `max_chunks_per_doc`, `use_semantic_cache`, `semantic_cache_threshold`, `semantic_cache_max_size` (no display line exists for `rrf_k`)

##### Category B: Remove Bucket 3 fields (not in AgentConfig, read only by /rag search)

Files to modify:
1. **`config/agent.toml`**: Remove `use_mqe`, `use_rrf`, `use_rerank`, `rag_top_k`, `rag_min_score`, `mqe_n_queries`, `use_search` from "RAG pipeline" section
   - No code change needed beyond `/rag` command removal below

##### Category C: Remove Bucket 4 fields (completely dead)

Files to modify:
1. **`config/agent.toml`**: Remove `rag_service_url` (line 52). Do NOT touch `[mcp_servers.rag_pipeline].url` at line 386

##### Category D: Relocate max_tool_turns

Files to modify:
1. **`config/agent.toml`**: Move `max_tool_turns` out of "RAG pipeline" comment block into "Tools" section where `ToolConfig.max_tool_turns` fields live

##### Category E: Remove /db rag subcommand family

Files to modify:
1. **`scripts/agent/commands/cmd_db.py`**: Remove `subcmd == "rag"` branch and `_cmd_db_rag()` method; update docstring and dispatcher usage/error message
2. **Delete `scripts/agent/commands/db_rag_ops.py`**: Entire file removal
3. **Update `scripts/agent/commands/db_help_display.py`**: Remove `rag`-related help text
4. **Update `scripts/agent/commands/db_stats_display.py`**: Remove `rag`-related stats methods
5. **Update `scripts/agent/commands/cmd_db.py::_DbMixin.__init__`**: Remove `self._rag_ops = DbRagOps(...)` instantiation
6. **Update `tests/test_agent_cmd_db.py`**: Remove `/db rag *` test cases, keep `/db session *` coverage
7. **Update `routing.md`**: Remove `/db rag` references

##### Category F: Remove /rag slash command

Files to modify:
1. **`scripts/agent/commands/command_defs_list.py`**: Remove `CommandDef("/rag", ...)` entry
2. **`scripts/agent/commands/cmd_rag_export.py`**: Remove `_cmd_rag()` from `_RagExportMixin`; delete imports used only by that method (verify not also used by `_cmd_export`/`_cmd_compact` first); update mixin docstring
3. **Delete `tests/test_cmd_rag_refiner_hint.py`**: Test file deletion
4. **Update `routing.md`**: Remove `/rag search` references

##### Category G: Update RagConfig Protocol if needed

Files to potentially modify:
1. **`scripts/shared/types.py`**: If `RagConfig` Protocol has no remaining concrete implementer after removal, scope it down to match `RagPipelineConfig` only
   - **Status**: Not needed — `SimpleNamespace` adapter in `mcp_servers/rag_pipeline/models.py` still satisfies it.

#### Step 3: Fix broken tests

The following tests construct `RAGConfig` or `AgentConfig` with removed Bucket 2/3 fields and will fail:

1. `tests/test_tool_loop_guard.py`: Passes `top_k_search`, `top_k_rerank`, `rag_top_k`, `use_mqe`, `use_search`, `use_rrf`, `use_rerank`, `rag_min_score`, `max_chunks_per_doc`, `use_semantic_cache`, `semantic_cache_threshold`
2. `tests/test_tool_result_formatter.py`: May pass RAG-related fields
3. `tests/test_tool_policy_comprehensive.py`: May pass RAG-related fields
4. `tests/test_tool_audit.py`: May pass RAG-related fields
5. `tests/test_tool_approval_preflight.py`: May pass RAG-related fields
6. `tests/test_tool_approval_risk.py`: May pass RAG-related fields
7. `tests/test_tool_approval_repos.py`: May pass RAG-related fields
8. `tests/test_tool_approval_paths.py`: May pass RAG-related fields
9. `tests/test_cmd_config_char.py`: Uses `RAGConfig()` directly
10. `tests/test_config_builders.py`: Tests `_build_rag_config()` which will change
11. `tests/test_config_validator.py`: Tests RAG config validation
12. `tests/test_cli_view.py`: Tests `/config` output which will change

For each test:
- Remove Bucket 2 fields from test defaults (they're no longer valid `RAGConfig` fields)
- Remove Bucket 3 fields from test defaults (they're not in `AgentConfig` anyway)
- Keep `embed_url` unchanged (still valid)
- Verify test assertions don't depend on removed field values

#### Step 4: Update documentation

##### Configuration reference documentation:
1. **`docs/03_rag_05_1-configuration-reference.md`** §1.5: Remove entries for every key deleted above that appears in the table; correct description to state `embed_url` is the only RAG-related field consumed by `AgentConfig`; rewrite cross-file value drift note

##### `/db rag` documentation:
Determine for each doc whether to point readers at equivalent MCP tool or underlying maintenance primitive, or state plainly that no equivalent remains reachable:
1. `docs/01_overview-files-03-scripts-part2.md`
2. `docs/03_rag_05_8-rag-mcp-internal-operations-direct-db-access.md`
3. `docs/03_rag_05_7-rag-index-consistency-checks.md`
4. `docs/03_rag_90_inconsistencies_and_known_issues-part1.md`
5. `docs/03_rag_91_design_notes-part1.md`
6. `docs/05_agent_01_system-overview.md`
7. `docs/05_agent_04_03_state-and-persistence-platform-databases.md`
8. `docs/05_agent_07_07_cli-and-commands-migration-notes.md`
9. `docs/05_agent_09_03_data-layer-indexing-boundaries.md`
10. `docs/05_agent_07_09_cli-and-commands-slash-commands-context-db.md`
11. `docs/05_agent_09_02_data-layer-access-patterns.md`
12. `docs/05_agent_10_04_operations-and-observability-validation-and-troubleshooting-part2.md`
13. `docs/05_agent_10_05_operations-and-observability-monitoring.md`
14. `docs/90_shared_05_03_db_api_and_operations-maintenance-and-rotation.md`
15. `docs/90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md`

##### `/rag search` documentation:
Point readers at `rag_run_pipeline`/`rag_debug_pipeline` MCP tools where those are the equivalent supported path:
1. `docs/01_overview-files-03-scripts-part2.md`
2. `docs/03_rag_03_02_query_pipeline-rag-pipeline-class-part2.md`
3. `docs/03_rag_03_04_query_pipeline-search-stages.md`
4. `docs/03_rag_03_05_query_pipeline-augment-stages.md`
5. `docs/04_mcp_04_03_rag-pipeline-and-cicd.md`
6. `docs/05_agent_01_system-overview.md`
7. `docs/05_agent_07_10_cli-and-commands-slash-commands-workflow-debug.md`
8. `docs/05_agent_10_05_operations-and-observability-monitoring.md`
9. `docs/05_agent_10_06_operations-and-observability-rag-diagnostics-and-memory.md`
10. `docs/90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md`

#### Step 5: Run validation

1. Run `uv run pytest` — fix any failing tests
2. Verify no import errors from deleted files (`db_rag_ops.py`)
3. Manual review against acceptance criteria

## Method

- Pattern-based search followed by targeted text replacement via file edit.
- File deletions via `git rm`.
- Preserve surrounding context and formatting.
- Use consistent terminology across all documents.

## Validation plan

- Verify `config/agent.toml` no longer declares any of the 15 removed keys
- Verify `max_tool_turns` functions identically after relocation
- Verify `/rag` and `/db rag` commands no longer exist as invocable forms
- Verify `/export` and `/compact` continue to work
- Verify `/db session <subcmd>` continues to work
- Verify no remaining import references to `DbRagOps`
- Verify no documentation describes `/db rag` or `/rag search` as available
- Verify `RAGConfig` contains only fields with real consumers
- Verify `/config` no longer displays removed fields
- Verify `rebuild_fts()` and `recover_corruption()` still have callers (NOT unreferenced)

## Risks

- Missing a test that constructs `RAGConfig` or asserts on `/config` output including removed fields (multiple test files affected)
- The `RagConfig` Protocol may have unexpected dependents that need updating (resolved: SimpleNamespace adapter still satisfies it)
- Documentation updates are extensive (~25 files); risk of missing one
- `scripts/rag/maintenance.py::rebuild_fts()` and `scripts/db/recovery.py::recover_corruption()` have other callers besides `DbRagOps` — do NOT flag as unreferenced
