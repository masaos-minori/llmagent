# Implementation Procedure: Consolidate field collection, remove pre-validation, extract parameterized reload helper, replace magic strings, reduce AgentContext coupling

## Goal

Consolidate duplicated field collection and dual-validation pattern in `ConfigReloadService` into a single unified flow; parameterize repetitive reload methods; replace magic strings with named constants; reduce AgentContext coupling — enabling independent unit testing of each concern without full context mocking.

## Scope

- Consolidate `_collect_request_values()` and `_apply_llm_prompt_params()` into single `_collect_field_changes()` method
- Remove `_validate_request()` pre-validation
- Extract parameterized `_reload_section()` helper
- Replace magic strings with named constants
- Reduce AgentContext coupling in `_sync_services()`

## Assumptions

- Constructor-injection/delegation pattern used in `orchestrator.py` and `ingester.py` splits is the preferred approach
- Post-application validation can replicate all pre-validation failure modes
- All four `_reload_*` methods should use the parameterized helper

## Design decisions

- Unified field collector replaces both `_collect_request_values()` and `_apply_llm_prompt_params()` — populates one set of change dicts (`llm_changes`, `rag_changes`, `tool_changes`)
- Post-application validator moves all validation to after application — removes `_validate_request()` entirely
- Parameterized reload helper extracts common pattern from `_reload_approval_config`, `_reload_tool_allowlist`, `_reload_memory_runtime`, `_reload_security_profile` into `_reload_section(ctx, new_cfg, section_name, field_mappings)`
- Magic string constants defined at module level: `FIELD_HTTP_TIMEOUT`, `FIELD_CONTEXT_CHAR_LIMIT`, `FIELD_SYSTEM_PROMPT_TOOL`, etc.
- Decoupled service sync passes only required service instances instead of accessing `ctx.services_required.*` directly

## Alternatives considered

- Keep dual-validation pattern but unify field collection only — rejected because REQ-002 requires removing pre-validation entirely
- Add a separate validation layer class — rejected because REQ-002 specifies moving validation inside `_apply_rag_tool_params()`
- Use dependency injection for AgentContext — rejected because REQ-005 specifies passing explicit service parameters, not changing the constructor interface

## Implementation

### Target file

`scripts/agent/services/config_reload.py`

### Procedure

1. Define module-level magic string constants
2. Create `_collect_field_changes()` replacing `_collect_request_values()` + `_apply_llm_prompt_params()`
3. Remove `_validate_request()` and its call from `apply_config_dict()`
4. Extract `_reload_section()` helper for the four `_reload_*` methods
5. Refactor `_sync_services()` to accept explicit service parameters

### Method

#### Step 1: Module-level constants

Add at module level (after imports, before class definition):

```python
# Magic string constants — replaces scattered literal field names
FIELD_HTTP_TIMEOUT = "http_timeout"
FIELD_CONTEXT_TOKEN_LIMIT = "context_token_limit"
FIELD_EMBED_URL = "embed_url"
FIELD_USE_SEMANTIC_CACHE = "use_semantic_cache"
FIELD_MAX_TOOL_TURNS = "max_tool_turns"
FIELD_TOOL_RESULT_MAX_LLM_CHARS = "tool_result_max_llm_chars"
FIELD_CONTEXT_CHAR_LIMIT = "context_char_limit"
FIELD_CONTEXT_COMPRESS_TURNS = "context_compress_turns"
FIELD_SERIAL_TOOL_CALLS = "serial_tool_calls"
FIELD_TOOL_DEFINITIONS_STRICT = "tool_definitions_strict"
FIELD_PLAN_BLOCKED_TOOLS = "plan_blocked_tools"
FIELD_LLML_TEMPERATURE = "llm_temperature"
FIELD_LLML_MAX_TOKENS = "llm_max_tokens"
FIELD_LLML_URL = "llm_url"
FIELD_WEB_SEARCH_URL = "web_search_url"
FIELD_LLML_MAX_RETRIES = "llm_max_retries"
FIELD_LLML_RETRY_BASE_DELAY = "llm_retry_base_delay"
FIELD_SSE_HEARTBEAT_TIMEOUT = "sse_heartbeat_timeout"
FIELD_SSE_MALFORMED_RETRY = "sse_malformed_retry"
FIELD_SSE_RECONNECT_MAX = "sse_reconnect_max"
FIELD_LLML_STREAM_RETRY_ON_HEARTBEAT_TIMEOUT = "llm_stream_retry_on_heartbeat_timeout"
FIELD_LLML_STREAM_RETRY_ON_MALFORMED_CHUNK = "llm_stream_retry_on_malformed_chunk"
FIELD_SYSTEM_PROMPT_TOOL = "system_prompt_tool"
FIELD_SYSTEM_PROMPTS = "system_prompts"
FIELD_TOOL_DEFINITIONS = "tool_definitions"
FIELD_SEMANTIC_CACHE_THRESHOLD = "semantic_cache_threshold"
FIELD_SEMANTIC_CACHE_MAX_SIZE = "semantic_cache_max_size"
FIELD_USE_REFINER = "use_refiner"
FIELD_REFINER_MAX_TOKENS = "refiner_max_tokens"
FIELD_REFINER_TIMEOUT = "refiner_timeout"
FIELD_REFINER_MAX_CHARS_PER_CHUNK = "refiner_max_chars_per_chunk"
FIELD_APPROVAL_RISK_RULES = "approval_risk_rules"
FIELD_APPROVAL_PROTECTED_PATHS = "approval_protected_paths"
FIELD_APPROVAL_HIGH_RISK_BRANCHES = "approval_high_risk_branches"
FIELD_APPROVAL_SHELL_SAFE_PREFIXES = "approval_shell_safe_prefixes"
FIELD_APPROVAL_RESOURCE_KEYS = "approval_resource_keys"
FIELD_APPROVAL_DRY_RUN_TOOLS = "approval_dry_run_tools"
FIELD_TOOL_SAFETY_TIERS = "tool_safety_tiers"
FIELD_ALLOWED_ROOT = "allowed_root"
FIELD_APPROVAL_GITHUB_ALLOWED_REPOS = "approval_github_allowed_repos"
FIELD_GITOPS_PUSH_BLOCKED = "gitops_push_blocked"
FIELD_MEMORY_RETENTION_DAYS = "memory_retention_days"
FIELD_MEMORY_LOCAL_ONLY = "memory_local_only"
FIELD_SECURITY_PROFILE = "security_profile"
FIELD_SECURITY_LOCKDOWN_ENABLED = "security_lockdown_enabled"
FIELD_USE_MEMORY_LAYER = "use_memory_layer"
FIELD_ROUTING_DRIFT_STRICT = "routing_drift_strict"
FIELD_MEMORY_EMBED_ENABLED = "memory_embed_enabled"
```

#### Step 2: Unified field collector

Replace `_collect_request_values()` (line 221) and `_apply_llm_prompt_params()` (line 479) with a single method:

```python
def _collect_field_changes(
    self,
    new_cfg: dict[str, Any],
    llm_changes: dict[str, Any],
    rag_changes: dict[str, Any],
    tool_changes: dict[str, Any],
) -> None:
    """Collect field values from new_cfg into change dicts for validation.
    
    Replaces _collect_request_values() and _apply_llm_prompt_params().
    Populates one unified set of change dicts.
    """
    # LLM fields
    if (v := _get_float(new_cfg, FIELD_HTTP_TIMEOUT)) is not None:
        llm_changes[FIELD_HTTP_TIMEOUT] = v
    if (v := _get_int(new_cfg, FIELD_CONTEXT_TOKEN_LIMIT)) is not None:
        llm_changes[FIELD_CONTEXT_TOKEN_LIMIT] = v
    if (temperature := _get_float(new_cfg, FIELD_LLML_TEMPERATURE)) is not None:
        llm_changes[FIELD_LLML_TEMPERATURE] = temperature
    if (max_tokens := _get_int(new_cfg, FIELD_LLML_MAX_TOKENS)) is not None:
        llm_changes[FIELD_LLML_MAX_TOKENS] = max_tokens
    if (llm_url := _get_str(new_cfg, FIELD_LLML_URL)) is not None:
        llm_changes[FIELD_LLML_URL] = llm_url
    if (max_retries := _get_int(new_cfg, FIELD_LLML_MAX_RETRIES)) is not None:
        llm_changes[FIELD_LLML_MAX_RETRIES] = max_retries
    if (base_delay := _get_float(new_cfg, FIELD_LLML_RETRY_BASE_DELAY)) is not None:
        llm_changes[FIELD_LLML_RETRY_BASE_DELAY] = base_delay
    
    # SSE fields
    if (vf := _get_float(new_cfg, FIELD_SSE_HEARTBEAT_TIMEOUT)) is not None:
        llm_changes[FIELD_SSE_HEARTBEAT_TIMEOUT] = vf
    if (vi := _get_int(new_cfg, FIELD_SSE_MALFORMED_RETRY)) is not None:
        llm_changes[FIELD_SSE_MALFORMED_RETRY] = vi
    if (vi := _get_int(new_cfg, FIELD_SSE_RECONNECT_MAX)) is not None:
        llm_changes[FIELD_SSE_RECONNECT_MAX] = vi
    if (vb := _get_bool(new_cfg, FIELD_LLML_STREAM_RETRY_ON_HEARTBEAT_TIMEOUT)) is not None:
        llm_changes[FIELD_LLML_STREAM_RETRY_ON_HEARTBEAT_TIMEOUT] = vb
    if (vb := _get_bool(new_cfg, FIELD_LLML_STREAM_RETRY_ON_MALFORMED_CHUNK)) is not None:
        llm_changes[FIELD_LLML_STREAM_RETRY_ON_MALFORMED_CHUNK] = vb
    
    # RAG fields
    if (embed_url := _get_str(new_cfg, FIELD_EMBED_URL)) is not None:
        rag_changes[FIELD_EMBED_URL] = embed_url
    if (vb := _get_bool(new_cfg, FIELD_USE_SEMANTIC_CACHE)) is not None:
        rag_changes[FIELD_USE_SEMANTIC_CACHE] = vb
    if (web_search_url := _get_str(new_cfg, FIELD_WEB_SEARCH_URL)) is not None:
        rag_changes[FIELD_WEB_SEARCH_URL] = web_search_url
    if (vf := _get_float(new_cfg, FIELD_SEMANTIC_CACHE_THRESHOLD)) is not None:
        rag_changes[FIELD_SEMANTIC_CACHE_THRESHOLD] = vf
    if (vi := _get_int(new_cfg, FIELD_SEMANTIC_CACHE_MAX_SIZE)) is not None:
        rag_changes[FIELD_SEMANTIC_CACHE_MAX_SIZE] = vi
    if (vb := _get_bool(new_cfg, FIELD_USE_REFINER)) is not None:
        rag_changes[FIELD_USE_REFINER] = vb
    if (v := _get_int(new_cfg, FIELD_REFINER_MAX_TOKENS)) is not None:
        rag_changes[FIELD_REFINER_MAX_TOKENS] = v
    if (v := _get_float(new_cfg, FIELD_REFINER_TIMEOUT)) is not None:
        rag_changes[FIELD_REFINER_TIMEOUT] = v
    if (v := _get_int(new_cfg, FIELD_REFINER_MAX_CHARS_PER_CHUNK)) is not None:
        rag_changes[FIELD_REFINER_MAX_CHARS_PER_CHUNK] = v
    
    # Tool fields
    if (v := _get_int(new_cfg, FIELD_MAX_TOOL_TURNS)) is not None:
        tool_changes[FIELD_MAX_TOOL_TURNS] = v
    if (tool_result_max_chars := _get_int(new_cfg, FIELD_TOOL_RESULT_MAX_LLM_CHARS)) is not None:
        tool_changes[FIELD_TOOL_RESULT_MAX_LLM_CHARS] = tool_result_max_chars
    if (lst := _get_list_nonempty(new_cfg, FIELD_TOOL_DEFINITIONS)) is not None:
        tool_changes[FIELD_TOOL_DEFINITIONS] = list(lst)
    if (prompt_tool := _get_str_nonempty(new_cfg, FIELD_SYSTEM_PROMPT_TOOL)) is not None:
        tool_changes[FIELD_SYSTEM_PROMPT_TOOL] = prompt_tool
    if (sys_prompts := _get_dict_nonempty(new_cfg, FIELD_SYSTEM_PROMPTS)) is not None:
        tool_changes[FIELD_SYSTEM_PROMPTS] = dict(sys_prompts)
    if (vb := _get_bool(new_cfg, FIELD_SERIAL_TOOL_CALLS)) is not None:
        tool_changes[FIELD_SERIAL_TOOL_CALLS] = vb
    if (vb := _get_bool(new_cfg, FIELD_TOOL_DEFINITIONS_STRICT)) is not None:
        tool_changes[FIELD_TOOL_DEFINITIONS_STRICT] = vb
    if (lst := _get_list(new_cfg, FIELD_PLAN_BLOCKED_TOOLS)) is not None:
        tool_changes[FIELD_PLAN_BLOCKED_TOOLS] = list(lst)
```

Update `apply_config_dict()` call site: replace `self._collect_request_values(...)` + `self._apply_llm_prompt_params(...)` with `self._collect_field_changes(...)`.

#### Step 3: Remove pre-validation

Delete the entire `_validate_request()` method (line 151-218). Remove its call from `apply_config_dict()` line 127. The validation that was in `_validate_request()` will be handled by the post-application validators already present in `_apply_rag_tool_params()`.

Note: REQ-008 requires all existing validators still be called — verify that `_apply_rag_tool_params()` already covers all validator sets from `_validate_request()`:
- `validate_llm_http_timeout` — covered by `_apply_rag_tool_params()`'s `validate_llm_*` calls after replacement
- `validate_llm_context_token_limit` — covered by same
- `validate_rag_refiner_max_chars_per_chunk`, `validate_rag_refiner_max_tokens`, `validate_rag_refiner_timeout` — covered by same
- `validate_progress_stagnation_window`, `validate_tool_cycle_detect_window`, `validate_tool_dedup_max_repeats`, `validate_tool_error_max_consecutive`, `validate_tool_error_retry_max`, `validate_tool_max_tool_turns`, `validate_tool_result_max_llm_chars` — covered by same

#### Step 4: Extract parameterized reload helper

Add helper method:

```python
def _reload_section(
    self,
    ctx: AgentContext,
    new_cfg: dict[str, Any],
    section_name: str,
    field_mappings: list[tuple[str, str]],
) -> None:
    """Apply a batch of field updates to a config section.
    
    Args:
        ctx: AgentContext for accessing cfg
        new_cfg: New configuration dict
        section_name: Target section name (e.g., "approval", "tool")
        field_mappings: List of (new_cfg_key, target_path) tuples where
            target_path uses dot notation to reach the nested attribute
            (e.g., ("approval_risk_rules", "approval.approval_risk_rules"))
    """
    cfg = ctx.cfg
    for new_key, target_path in field_mappings:
        if new_key not in new_cfg:
            continue
        parts = target_path.split(".")
        obj = cfg
        for part in parts[:-1]:
            obj = getattr(obj, part)
        value = new_cfg[new_key]
        if isinstance(value, dict):
            setattr(obj, parts[-1], dict(value))
        elif isinstance(value, list):
            setattr(obj, parts[-1], list(value))
        else:
            setattr(obj, parts[-1], value)
```

Refactor each `_reload_*` method to use `_reload_section()`:

```python
def _reload_approval_config(self, ctx: AgentContext, new_cfg: dict[str, Any]) -> None:
    field_mappings = [
        ("approval_risk_rules", "approval.approval_risk_rules"),
        ("approval_protected_paths", "approval.approval_protected_paths"),
        ("approval_high_risk_branches", "approval.approval_high_risk_branches"),
        ("approval_shell_safe_prefixes", "approval.approval_shell_safe_prefixes"),
        ("approval_resource_keys", "approval.approval_resource_keys"),
        ("approval_dry_run_tools", "approval.approval_dry_run_tools"),
        ("tool_safety_tiers", "approval.tool_safety_tiers"),
        ("allowed_root", "approval.allowed_root"),
        ("approval_github_allowed_repos", "approval.approval_github_allowed_repos"),
        ("gitops_push_blocked", "approval.gitops_push_blocked"),
    ]
    self._reload_section(ctx, new_cfg, "approval", field_mappings)

def _reload_tool_allowlist(self, ctx: AgentContext, new_cfg: dict[str, Any]) -> None:
    self._reload_section(ctx, new_cfg, "tool", [("allowed_tools", "tool.allowed_tools")])

def _reload_memory_runtime(self, ctx: AgentContext, new_cfg: dict[str, Any]) -> None:
    field_mappings = [
        ("memory_retention_days", "memory.memory_retention_days"),
        ("memory_local_only", "memory.memory_local_only"),
    ]
    self._reload_section(ctx, new_cfg, "memory", field_mappings)

def _reload_security_profile(self, ctx: AgentContext, new_cfg: dict[str, Any]) -> None:
    if (vs := _get_str(new_cfg, FIELD_SECURITY_PROFILE)) is not None:
        try:
            from shared.mcp_config import SecurityProfile
            ctx.cfg.mcp.security_profile = SecurityProfile(vs)
        except ValueError:
            pass
    if (vb := _get_bool(new_cfg, FIELD_SECURITY_LOCKDOWN_ENABLED)) is not None:
        ctx.cfg.mcp.security_lockdown_enabled = vb
```

#### Step 5: Reduce AgentContext coupling

Refactor `_sync_services()` signature and body:

```python
def _sync_services(
    self,
    new_cfg: dict[str, Any],
    llm_service: object | None,
    hist_mgr_service: object | None,
    runtime_tools_service: object | None,
) -> ConfigReloadOutcome:
    """Apply new_cfg values to running service instances; return a report."""
    result = ConfigReloadOutcome()
    ctx = self._ctx

    if llm_service is not None:
        llm_service.apply_config(
            temperature=ctx.cfg.llm.llm_temperature,
            max_tokens=ctx.cfg.llm.llm_max_tokens,
            max_retries=ctx.cfg.llm.llm_max_retries,
            retry_base_delay=ctx.cfg.llm.llm_retry_base_delay,
            sse_heartbeat_timeout=ctx.cfg.llm.sse_heartbeat_timeout,
            sse_malformed_retry=ctx.cfg.llm.sse_malformed_retry,
            sse_reconnect_max=ctx.cfg.llm.sse_reconnect_max,
            stream_retry_on_heartbeat_timeout=ctx.cfg.llm.llm_stream_retry_on_heartbeat_timeout,
            stream_retry_on_malformed_chunk=ctx.cfg.llm.llm_stream_retry_on_malformed_chunk,
        )
        result.applied.append("llm")

    if hist_mgr_service is not None:
        hist_mgr_service.apply_config(
            char_limit=ctx.cfg.llm.context_char_limit,
            compress_turns=ctx.cfg.llm.context_compress_turns,
            token_limit=ctx.cfg.llm.context_token_limit,
            tokenize_url=ctx.cfg.llm.tokenize_url,
        )
        result.applied.append("hist_mgr")

    if runtime_tools_service is not None:
        runtime_tools_service.apply_policy(
            tier_map=cast(
                Mapping[str, "AgentSafetyTier"], ctx.cfg.approval.tool_safety_tiers
            ),
            allowed_tools=ctx.cfg.tool.allowed_tools,
        )
        result.applied.append("runtime_tools")

    if FIELD_SYSTEM_PROMPT_TOOL in new_cfg:
        ctx.conv.system_prompt_content = new_cfg[FIELD_SYSTEM_PROMPT_TOOL]

    return result
```

Update the call site in `apply_config_dict()` to pass explicit service references:

```python
service_result = self._sync_services(
    new_cfg,
    ctx.services_required.llm,
    ctx.services_required.hist_mgr,
    ctx.services_required.runtime_tools,
)
```

## Compatibility considerations

- Public API contract preserved: `apply_config(req: ConfigReloadRequest) -> ConfigReloadOutcome` and `apply_config_dict(new_cfg: dict[str, Any]) -> ConfigReloadOutcome` signatures unchanged (REQ-006)
- `ConfigReloadOutcome` field semantics intact (applied, needs_restart, skipped, startup_only, always_live) (REQ-007)
- MCP server classification logic (`_classify_mcp_server_changes()`) remains untouched (REQ-009)
- No behavioral changes to restart detection or live-field detection (REQ-010)

## Security considerations

- All existing validators must still be called; no validator removal (REQ-008)
- Post-application validation replaces pre-application — verify all validator scenarios are covered
- Retain existing `#nosec` justifications; document any new suppressions with rationale

## Rollback considerations

- If post-application validation does not cover all cases, revert to dual-validation pattern temporarily
- If `_reload_section()` introduces bugs, restore individual `_reload_*` methods
- Keep `_validate_request()` as an optional pre-validation layer until regression tests confirm equivalence

## Validation plan

- Run `ruff check scripts/agent/services/config_reload.py` (REQ-012)
- Run `mypy scripts/agent/services/config_reload.py` (REQ-012)
- Run `bandit -r scripts/agent/ -c pyproject.toml` verifying no new findings (REQ-012)
- Run `uv run pytest tests/agent/services/test_config_reload.py` comparing against baseline (REQ-013)
- Add regression tests for consolidated field collection path (REQ-001)
- Verify removing `_validate_request()` does not break mocked test assertions (REQ-002)

## Completion criteria

- Single `_collect_field_changes()` method replaces both `_collect_request_values()` and `_apply_llm_prompt_params()`
- `_validate_request()` is removed; all validation occurs in post-application phase
- At least one of the four `_reload_*` methods uses the extracted parameterized helper
- Magic string constants exist for all field names used across multiple methods
- `_sync_services()` receives explicit service parameters instead of accessing `ctx.services_required`
- `ruff`, `mypy`, and `bandit` are clean on modified file
- All existing tests pass without modification

## Out of scope

- MCP server lifecycle management changes
- Adding new validators
- Changing `ConfigReloadOutcome` field types or adding/removing fields
- Modifying `AgentContext` or `services_required` interfaces
- Performance optimization beyond what refactor naturally achieves

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Define module-level magic string constants | Pending | — | — | REQ-004 |
| 2 | Create _collect_field_changes() replacing _collect_request_values() + _apply_llm_prompt_params() | Pending | — | — | REQ-001 |
| 3 | Remove _validate_request() and its call from apply_config_dict() | Pending | — | — | REQ-002 |
| 4 | Extract _reload_section() helper for the four _reload_* methods | Pending | — | — | REQ-003 |
| 5 | Refactor _sync_services() to accept explicit service parameters | Pending | — | — | REQ-005 |
| 6 | Update call sites to match new method signatures | Pending | — | — | REQ-006 |
| 7 | Verify all validators still called in post-application phase | Pending | — | — | REQ-008 |
| 8 | Run validation sequence (ruff, mypy, bandit) | Pending | — | — | REQ-012 |
| 9 | Run regression tests | Pending | — | — | REQ-013 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability

- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001 through REQ-005, REQ-008 through REQ-012
- **Source issue**: issues/20260831-232522_refactor_001_config_reload_service_refactor.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260902-070422_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260903-125417
- **Related target files**: scripts/agent/services/config_reload.py
