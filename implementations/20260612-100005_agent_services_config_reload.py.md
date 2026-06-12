# Goal

Eliminate `dict[str, Any]` from all private `_apply_*` helpers in
`config_reload.py` by replacing the intermediate `_req_to_dict()` conversion with
typed sub-DTOs, and making `apply_config_dict()` an internal-only method that
accepts a typed object.

# Scope

- `scripts/agent/services/config_reload.py`

# Assumptions

1. `apply(req: ConfigReloadRequest)` already exists and is the public API.
2. `apply_config_dict(new_cfg: dict[str, Any])` is called internally via
   `_req_to_dict(req)`. This internal method will be refactored but kept for now as
   an adapter if any test calls it directly; eventually remove it.
3. The `_apply_*` private methods currently each receive `new_cfg: dict[str, Any]`
   and access it with `.get("key")`. These are converted to accept typed sub-DTOs.
4. Typed sub-DTOs are defined in `agent/services/models.py` (or inline in this
   file as private dataclasses). Use `agent/services/models.py` if the DTOs need
   to be tested independently; otherwise define them as private classes here.
5. Fields read from `new_cfg` by each helper:
   - `_apply_rag_tool_params`: `top_k_search`, `top_k_rerank`, `max_chunks_per_doc`,
     `use_search`, `use_rerank`, `tool_cache_ttl`, `max_tool_turns`, `serial_tool_calls`,
     `use_tool_summarize`, `tool_summarize_threshold`, `auto_inject_notes`,
     `tool_definitions_strict`, `allowed_tools`, `plan_blocked_tools`,
     `system_prompts`
   - `_reload_approval_settings`: `approval_risk_rules`, `approval_protected_paths`,
     `approval_high_risk_branches`, `approval_dry_run_tools`,
     `approval_github_allowed_repos`, `allowed_root`
   - `_apply_mcp_url_reload`: `mcp_servers`
   - `_apply_llm_prompt_params`: `llm_url`, `http_timeout`, `llm_max_retries`,
     `llm_retry_base_delay`, `llm_temperature`, `llm_max_tokens`,
     `context_char_limit`, `context_compress_turns`, `context_token_limit`,
     `tokenize_url`, `web_search_url`, `web_search_max_results`,
     `github_server_url`, `mcp_watchdog_interval`, `mcp_watchdog_max_restarts`,
     `system_prompts`, `tools_definitions`
   - `_apply_sse_reload_params`: `sse_heartbeat_timeout`, `sse_malformed_retry`,
     `sse_reconnect_max`, `llm_stream_retry_on_heartbeat_timeout`,
     `llm_stream_retry_on_malformed_chunk`
   - `_sync_services`: reads from `ctx.cfg.*` (already typed) — no dict access here
6. The external caller (`cmd_config._cmd_reload`) calls `ConfigReloadService(ctx).apply(req)`.
   If `apply_config_dict()` is removed as public API, the caller is unaffected.

# Implementation

## Target file

`scripts/agent/services/config_reload.py`
(may also touch `scripts/agent/services/models.py` if sub-DTOs are added there)

## Procedure

1. Define private sub-DTOs in `config_reload.py` (or `models.py`):

```python
@dataclass(frozen=True)
class _RagToolParams:
    top_k_search: int | None = None
    top_k_rerank: int | None = None
    max_chunks_per_doc: int | None = None
    use_search: bool | None = None
    use_rerank: bool | None = None
    tool_cache_ttl: float | None = None
    max_tool_turns: int | None = None
    serial_tool_calls: bool | None = None
    use_tool_summarize: bool | None = None
    tool_summarize_threshold: int | None = None
    auto_inject_notes: bool | None = None
    tool_definitions_strict: bool | None = None
    allowed_tools: list[str] | None = None
    plan_blocked_tools: list[str] | None = None
    system_prompts: dict[str, str] | None = None

@dataclass(frozen=True)
class _ApprovalParams:
    approval_risk_rules: dict[str, str] | None = None
    approval_protected_paths: list[str] | None = None
    approval_high_risk_branches: list[str] | None = None
    approval_dry_run_tools: list[str] | None = None
    approval_github_allowed_repos: list[str] | None = None
    allowed_root: str | None = None

@dataclass(frozen=True)
class _SseParams:
    sse_heartbeat_timeout: float | None = None
    sse_malformed_retry: int | None = None
    sse_reconnect_max: int | None = None
    llm_stream_retry_on_heartbeat_timeout: bool | None = None
    llm_stream_retry_on_malformed_chunk: bool | None = None
```

2. Add a `_req_to_params(req: ConfigReloadRequest)` method that returns each
   sub-DTO built from the fields of `req` (with explicit `isinstance` validation
   for each field that may come from raw config).

3. Rewrite each `_apply_*` helper to accept its typed sub-DTO instead of
   `dict[str, Any]`. Each field access becomes `params.field_name` (attribute)
   instead of `new_cfg.get("field_name")`.

4. Update `apply_config_dict()` to build sub-DTOs from the incoming dict via explicit
   isinstance checks:
   ```python
   def apply_config_dict(self, new_cfg: dict[str, Any]) -> ConfigReloadOutcome:
       # Extract and validate each field group explicitly
       rag_params = _RagToolParams(
           top_k_search=_get_int(new_cfg, "top_k_search"),
           ...
       )
       ...
   ```
   where `_get_int(d, key)` does `isinstance` check and raises `ConfigurationSchemaError`
   on type mismatch.

5. Run ruff + mypy.

## Method

Replace all `new_cfg.get("key")` accesses with typed sub-DTO field access.
Validate types at the boundary (`apply_config_dict` / `_req_to_params`) rather than
silently coercing.

## Details

Helper for safe extraction from raw dict:
```python
def _get_int(d: dict[str, Any], key: str) -> int | None:
    v = d.get(key)
    if v is None:
        return None
    if not isinstance(v, int):
        raise ConfigurationSchemaError(
            f"config key {key!r} must be int, got {type(v).__name__}"
        )
    return v

def _get_float(d: dict[str, Any], key: str) -> float | None:
    v = d.get(key)
    if v is None:
        return None
    if not isinstance(v, (int, float)):
        raise ConfigurationSchemaError(
            f"config key {key!r} must be float, got {type(v).__name__}"
        )
    return float(v)

def _get_bool(d: dict[str, Any], key: str) -> bool | None:
    v = d.get(key)
    if v is None:
        return None
    if not isinstance(v, bool):
        raise ConfigurationSchemaError(
            f"config key {key!r} must be bool, got {type(v).__name__}"
        )
    return v
```

# Validation plan

- `grep -n "\.get(" scripts/agent/services/config_reload.py` → only `new_cfg.get()` at
  the single boundary extraction point, not scattered through private helpers
- `uv run ruff check scripts/agent/services/config_reload.py`
- `uv run mypy scripts/agent/services/config_reload.py`
- `uv run pytest tests/ -k "config_reload or cmd_config" --ignore=tests/test_create_schema.py -v`
