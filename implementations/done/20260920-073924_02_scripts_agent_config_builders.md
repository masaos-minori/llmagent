## Goal

Refactor `scripts/agent/config_builders.py` to: (1) remove the six `_DEFAULT_*` constant tables and replace them with imports from `constants.py`, (2) consolidate five of the six `_get_*_or_default` helpers into a single generic helper while preserving `_get_str_or_default`'s special semantics, (3) decompose the four long builder functions (>30 lines) into sub-functions under 30 lines each, and (4) split `build_agent_config` into three named sub-functions.

## Scope

- Modify only `scripts/agent/config_builders.py` — no other file changes in this document
- Remove `_DEFAULT_*` constants and add import from `constants.py`
- Consolidate `_get_list_or_default`, `_get_dict_or_default`, `_get_int_or_default`, `_get_float_or_default`, `_get_bool_or_default` into one generic helper
- Decompose `_build_llm_config` (55 lines), `_build_tool_config` (52 lines), `_build_memory_config` (48 lines), `_build_approval_config` (48 lines)
- Split `build_agent_config` into three sub-functions
- Keep `_get_str_or_default`, `_build_rag_config` (27 lines), `_build_diagnostics_config` (18 lines), and `_validate_dry_run_tools` unchanged

## Assumptions

- `_get_str_or_default`'s special semantics (empty-string default preservation) applies only to keys whose default is `""` — specifically `llm_url`, `tokenize_url` in LLMConfig and `allowed_root` in ApprovalConfig. Three call sites use `_get_str + or` pattern intentionally (`memory_jsonl_dir`, `otel_service_name`, `audit_log_file`) — these must NOT be converted to `_get_str_or_default`.
- Moving defaults to `constants.py` will not change runtime behavior because dataclass defaults are evaluated at class definition time, not at import time. The dependency flows one direction (`config_dataclasses.py` → `constants.py`).
- The three-part split of `build_agent_config` is feasible given the current separation of concerns within the function.
- `_validate_dry_run_tools` stays in `config_builders.py` since it references `_DEFAULT_DRY_RUN_TOOLS` which will be in `constants.py`, creating a cross-module dependency.

## Design decisions

- Generic helper signature: `_get_or_default(cfg, key, getter, default)` where `getter` is the typed validator (e.g., `_get_int`). This preserves the existing call-site pattern: `_get_or_default(cfg, "key", _get_int, default_value)`.
- Builder decomposition uses private sub-helpers (e.g., `_extract_llm_transport_fields`, `_extract_llm_context_fields`) that return partial field dicts, assembled by the parent builder.
- `build_agent_config` splitting follows actual responsibility boundaries: config loading + registry resolution (~14 lines), production validation (~9 lines), builder orchestration + assembly (~22 lines).

## Alternatives considered

- Replacing all six `_get_*_or_default` helpers with a single generic including `_get_str_or_default` — rejected because it would conflate two different semantics (None vs "" distinction).
- Using a decorator-based approach for builder decomposition — rejected as unnecessary complexity for a simple field-grouping pattern.
- Keeping `build_agent_config` as a single function but extracting only the config-loading part — rejected because the validation and assembly responsibilities are distinct enough to warrant separate functions.

## Implementation
### Target file

`scripts/agent/config_builders.py` (modify)

### Procedure

#### Phase A: Replace constants with imports

1. Remove the six `_DEFAULT_*` constant table definitions (lines 71-127).
2. Add an import line after the existing imports:
   ```python
   from agent.constants import (
       _DEFAULT_APPROVAL_RISK_RULES,
       _DEFAULT_DRY_RUN_TOOLS,
       _DEFAULT_PLAN_BLOCKED_TOOLS,
       _DEFAULT_PROTECTED_PATHS,
       _DEFAULT_RESOURCE_KEYS,
       _DEFAULT_SHELL_SAFE_PREFIXES,
   )
   ```
3. Update all call sites that reference `_DEFAULT_*` to use the imported names directly:
   - Line 294: `list(_DEFAULT_PLAN_BLOCKED_TOOLS)` → unchanged (already uses the name)
   - Line 379: `_DEFAULT_APPROVAL_RISK_RULES` → unchanged
   - Line 382: `list(_DEFAULT_PROTECTED_PATHS)` → unchanged
   - Line 388: `list(_DEFAULT_SHELL_SAFE_PREFIXES)` → unchanged
   - Line 391: `_DEFAULT_RESOURCE_KEYS` → unchanged
   - Line 394: `_DEFAULT_DRY_RUN_TOOLS` → unchanged

#### Phase B: Consolidate `_get_*_or_default` helpers

1. Remove the following five helper functions (lines 135-177):
   - `_get_list_or_default`
   - `_get_dict_or_default`
   - `_get_int_or_default`
   - `_get_float_or_default`
   - `_get_bool_or_default`

2. Add a single generic helper:
   ```python
   def _get_or_default(
       cfg: dict[str, Any], key: str, getter: Callable[[dict[str, Any], str], Any], default: Any
   ) -> Any:
       """Extract a value from cfg using *getter*, falling back to *default* when absent.
       
       Only use this for keys whose default is non-empty (non-zero for numbers,
       non-empty string for strings). For empty-string defaults, use
       `_get_str_or_default` instead to preserve None vs "" semantics.
       """
       v = getter(cfg, key)
       return v if v is not None else default
   ```

3. Update all call sites to use the consolidated pattern:
   - `_get_list_or_default(cfg, key, default)` → `_get_or_default(cfg, key, _get_list, default)`
   - `_get_dict_or_default(cfg, key, default)` → `_get_or_default(cfg, key, _get_dict, default)`
   - `_get_int_or_default(cfg, key, default)` → `_get_or_default(cfg, key, _get_int, default)`
   - `_get_float_or_default(cfg, key, default)` → `_get_or_default(cfg, key, _get_float, default)`
   - `_get_bool_or_default(cfg, key, default)` → `_get_or_default(cfg, key, _get_bool, default)`

4. Preserve `_get_str_or_default` as-is (lines 151-159) — do NOT modify it.

#### Phase C: Decompose long builder functions

1. **Decompose `_build_llm_config`** (currently ~55 lines):
   - Extract `_extract_llm_transport_fields(cfg)` — handles `llm_url`, `http_timeout`, `llm_max_retries`, `llm_retry_base_delay`, `sse_heartbeat_timeout`, `sse_malformed_retry`, `sse_reconnect_max`, `llm_stream_retry_on_heartbeat_timeout`, `llm_stream_retry_on_malformed_chunk`
   - Extract `_extract_llm_context_fields(cfg)` — handles `tokenize_url`, `context_token_limit`, `context_char_limit`, `context_compress_turns`, `history_protect_turns`, `budget_warn_ratio`
   - Extract `_extract_llm_temperature_fields(cfg)` — handles `llm_temperature`, `title_llm_temperature`, `title_llm_max_tokens`, `llm_compress_temperature`, `llm_compress_max_tokens`
   - Each sub-function returns a partial dict of fields for its group
   - Parent function assembles the full `LLMConfig` from the three partial dicts

2. **Decompose `_build_tool_config`** (currently ~52 lines):
   - Extract `_extract_tool_execution_fields(cfg)` — handles `serial_tool_calls`, `tool_definitions_strict`, `routing_drift_strict`, `tool_dedup_max_repeats`, `tool_cycle_detect_window`, `tool_error_max_consecutive`, `tool_error_retry_max`
   - Extract `_extract_tool_limits_fields(cfg)` — handles `tool_concurrency_limits`, `masked_fields`, `plan_blocked_tools`, `max_tool_turns`, `tool_result_max_llm_chars`, `tool_results_turn_max_chars`
   - Extract `_extract_tool_schema_fields(cfg, system_prompt_tool)` — handles `tool_definitions`, `system_prompts`, `system_prompt_tool`, `allowed_tools`
   - Each sub-function returns a partial dict of fields for its group
   - Parent function assembles the full `ToolConfig` from the three partial dicts

3. **Decompose `_build_memory_config`** (currently ~48 lines):
   - Extract `_extract_memory_core_fields(cfg)` — handles `use_memory_layer`, `memory_jsonl_dir`, `memory_max_inject_semantic`, `memory_max_inject_episodic`, `memory_min_importance`
   - Extract `_extract_memory_embedding_fields(cfg)` — handles `memory_embed_enabled`, `memory_dedup_threshold`, `memory_embed_timeout_sec`
   - Extract `_extract_memory_search_fields(cfg)` — handles `memory_retention_days`, `memory_fts_limit`, `memory_rrf_k`, `memory_recency_days`, `memory_local_only`
   - Each sub-function returns a partial dict of fields for its group
   - Parent function assembles the full `MemoryConfig` from the three partial dicts, wrapping in try/except for ValueError conversion

4. **Decompose `_build_approval_config`** (currently ~48 lines):
   - Extract `_extract_approval_risk_fields(cfg)` — handles `approval_risk_rules`, `approval_protected_paths`, `approval_high_risk_branches`, `approval_shell_safe_prefixes`, `approval_resource_keys`
   - Extract `_extract_approval_tool_fields(cfg)` — handles `approval_dry_run_tools`, `tool_safety_tiers`, `tool_safety_tier validation loop`
   - Extract `_extract_approval_github_fields(cfg)` — handles `allowed_root`, `approval_github_allowed_repos`, `gitops_push_blocked`
   - Each sub-function returns a partial dict of fields for its group
   - Parent function assembles the full `ApprovalConfig` from the three partial dicts

#### Phase D: Split `build_agent_config`

1. Create `_resolve_config_source_and_registry(cfg_override)` (~14 lines):
   ```python
   def _resolve_config_source_and_registry(
       cfg_override: dict[str, Any] | None
   ) -> tuple[dict[str, Any], set[str]]:
       """Resolve config source and tool registry. Returns (cfg, known_tools)."""
       cfg = cfg_override if cfg_override is not None else load_config()
       try:
           from shared.tool_registry import get_registry
           known_tools = set(get_registry().get_all_tool_names())
       except ValueError as exc:
           raise ConfigReloadValidationError(
               f"Tool registry resolution failed during config build: {exc}"
           ) from exc
       except ImportError as exc:
           raise ConfigReloadValidationError(
               f"Tool registry module unavailable during config build: {exc}"
           ) from exc
       return cfg, known_tools
   ```

2. Create `_run_production_validation(cfg, security_profile_val, known_tools)` (~9 lines):
   ```python
   def _run_production_validation(
       cfg: dict[str, Any],
       security_profile_val: SecurityProfile,
       known_tools: set[str],
   ) -> None:
       """Run production config validation; exit on errors."""
       results = ProductionConfigValidator().validate(
           cfg, security_profile=security_profile_val, known_tools=known_tools
       )
       if results.errors:
           logger.error("Production config validation failed:")
           for err in results.errors:
               logger.error(f"  - {err}")
           sys.exit(1)
       for warning in results.warnings:
           logger.warning(warning)
   ```

3. Create `_assemble_agent_config(cfg, system_prompt_tool, security_profile_val)` (~22 lines):
   ```python
   def _assemble_agent_config(
       cfg: dict[str, Any],
       system_prompt_tool: str,
       security_profile_val: SecurityProfile,
   ) -> AgentConfig:
       """Assemble AgentConfig by delegating to builder functions."""
       security_lockdown_enabled = _get_bool_or_default(cfg, "security_lockdown_enabled", False)
       otel_enabled = _get_bool_or_default(cfg, "otel_enabled", False)
       structured_log = _get_bool_or_default(cfg, "structured_log", False)
       return AgentConfig(
           llm=_build_llm_config(cfg),
           rag=_build_rag_config(cfg),
           tool=_build_tool_config(cfg, system_prompt_tool),
           memory=_build_memory_config(cfg),
           mcp=MCPConfig(
               mcp_servers=_build_mcp_servers(cfg),
               security_profile=security_profile_val,
               security_lockdown_enabled=security_lockdown_enabled,
           ),
           approval=_build_approval_config(cfg),
           obs=ObservabilityConfig(
               otel_enabled=otel_enabled,
               otel_endpoint=_get_str_or_default(cfg, "otel_endpoint", ""),
               otel_service_name=_get_str(cfg, "otel_service_name") or "llm-agent",
               audit_log_file=_get_str(cfg, "audit_log_file") or "/opt/llm/logs/audit.log",
               structured_log=structured_log,
           ),
           diagnostics=_build_diagnostics_config(cfg),
           agent_memory_max_startup_snippets=_get_int_or_default(
               cfg, "agent_memory_max_startup_snippets", 10
           ),
       )
   ```

4. Rewrite `build_agent_config` to delegate:
   ```python
   def build_agent_config(cfg_override: dict[str, Any] | None = None) -> AgentConfig:
       """Construct AgentConfig from a config dict.
       
       If cfg_override is provided it is used directly (for /reload and tests).
       Otherwise configuration is loaded from files via load_config().
       """
       cfg, known_tools = _resolve_config_source_and_registry(cfg_override)
       system_prompt_tool = cfg.get("system_prompt_tool", "")
       security_profile_val = SecurityProfile(cfg.get("security_profile", "production"))
       _run_production_validation(cfg, security_profile_val, known_tools)
       return _assemble_agent_config(cfg, system_prompt_tool, security_profile_val)
   ```

### Method

Use Edit tool to apply changes incrementally:
1. First edit: replace constants section with imports
2. Second edit: replace five `_get_*_or_default` helpers with generic helper
3. Third edit: decompose each builder function
4. Fourth edit: split `build_agent_config`

## Details

- Line count target after refactor: under 200 lines (excluding `constants.py`)
- AC-1: `scripts/agent/config_builders.py` is under 200 lines (excluding `constants.py`)
- AC-3: No `_get_*_or_default` wrapper functions remain (except `_get_str_or_default`)
- AC-4: Each decomposed `_build_*` function is under 30 lines
- AC-5: `build_agent_config` is split into three named sub-functions

## Compatibility considerations

- Public API surface unchanged: `build_agent_config`, `load_config`, `ConfigLoadError` remain exported.
- `_get_str_or_default` semantics preserved for keys with empty-string defaults (`llm_url`, `tokenize_url`, `allowed_root`).
- Three call sites using `_get_str + or` pattern (`memory_jsonl_dir`, `otel_service_name`, `audit_log_file`) must NOT be converted to `_get_str_or_default`.
- `_validate_dry_run_tools` stays in `config_builders.py` since it references `_DEFAULT_DRY_RUN_TOOLS` which will be imported from `constants.py`.
- Import compatibility verified against Reference Files:
  - `scripts/agent/context.py` — imports `build_agent_config`
  - `scripts/agent/services/config_outcome_classification.py` — imports `_build_mcp_servers`
  - `shared/config_errors.py` — defines `ConfigLoadError`
  - `agent/services/exceptions.py` — defines `ConfigReloadValidationError`

## Security considerations

- No security impact — this is a structural refactor only.
- The `_validate_dry_run_tools` function remains in `config_builders.py` and continues to validate dry-run tools against `_DEFAULT_DRY_RUN_TOOLS` from `constants.py`.

## Rollback considerations

- If the refactor introduces regressions, revert all four edits to restore the original file.
- The rollback path is straightforward: undo each Edit operation in reverse order.

## Validation plan

1. Unit test: `uv run pytest tests/agent/test_config_builders.py -q` — verify zero failures.
2. Dataclass test: `uv run pytest tests/agent/test_config_dataclasses.py -q` — verify zero failures.
3. Full suite regression: `uv run pytest tests/ -q` — verify zero failures.
4. Import verification: `python -c "from agent.config_builders import build_agent_config, load_config, ConfigLoadError"` — verify public API surface unchanged.
5. Verify `_get_str_or_default` semantics preserved: empty string default must not collapse to `""` when key is absent.

## Completion criteria

- [ ] Six `_DEFAULT_*` constants removed from `config_builders.py`; import added instead
- [ ] Five `_get_*_or_default` helpers consolidated into one `_get_or_default` generic helper
- [ ] `_get_str_or_default` preserved unchanged
- [ ] Three `_get_str + or` call sites (`memory_jsonl_dir`, `otel_service_name`, `audit_log_file`) left untouched
- [ ] Four long builder functions decomposed into sub-functions under 30 lines each
- [ ] `_build_rag_config` (27 lines) and `_build_diagnostics_config` (18 lines) kept as-is
- [ ] `build_agent_config` split into three named sub-functions
- [ ] File line count under 200 lines
- [ ] All existing tests pass without modification
- [ ] Public API surface unchanged (import check succeeds)

## Out of scope

- Modifying `constants.py` (covered by seq=01 document)
- Modifying `config_dataclasses.py` to import from `constants.py` (covered by seq=03 document)
- Adding new config sections or fields
- Changing the TOML configuration schema
- Modifying `shared/` modules
- Performance optimization of config loading

## execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace constants with imports from constants.py | Pending | — | — | |
| 2 | Consolidate _get_*_or_default helpers | Pending | — | — | |
| 3 | Decompose _build_llm_config | Pending | — | — | |
| 4 | Decompose _build_tool_config | Pending | — | — | |
| 5 | Decompose _build_memory_config | Pending | — | — | |
| 6 | Decompose _build_approval_config | Pending | — | — | |
| 7 | Split build_agent_config into three sub-functions | Pending | — | — | |

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
- **Requirement ID**: REQ-002, REQ-003, REQ-004
- **Source issue**: issues/20260919-223836_refactor_config_builders_split_and_consolidate.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-071804_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260920-073924
- **Related target files**: scripts/agent/config_builders.py
