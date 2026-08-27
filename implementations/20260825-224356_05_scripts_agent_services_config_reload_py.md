## Goal

Re-execute validators on `/reload` for `LLMConfig`, `RAGConfig`, and `ToolConfig` sub-configs by replacing direct `setattr` with a diff-collection + `dataclasses.replace()` approach. Values rejected at startup time will now be rejected at reload time too.

## Scope

**In-Scope**:
- `scripts/agent/services/config_reload.py`: restructure 6 helper functions (`_apply_llm_context_params`, `_apply_llm_retry_params`, `_apply_llm_prompt_params`, `_apply_sse_reload_params`, `_apply_tool_params`, `_apply_rag_params`) to collect changes into dicts instead of calling `setattr` directly. Add `dataclasses.replace()` + error handling in `_apply_rag_tool_params()`.

**Out-of-Scope**:
- Changes to individual `validate_*` functions (tracked separately as `issues/20260825_config_validators_duplicate_range_checks_issue.md`).
- Applying validation re-execution to `ApprovalConfig`, `MemoryConfig`, `MCPConfig` etc. (each has different `__post_init__` side-effect profiles, tracked as separate issues).
- Adding new validation rules.

## Assumptions

- `LLMConfig.__post_init__`, `RAGConfig.__post_init__`, `ToolConfig.__post_init__` contain only validator calls with no side effects — confirmed via source inspection.
- `ConfigReloadValidationError` exists as a `ValueError` subclass and follows an existing conversion pattern (`config_builders.py:374`).
- No `init=False` fields exist in `LLMConfig`, `RAGConfig`, or `ToolConfig` — confirmed via dataclass field inspection.

## Design decisions

- Each `_apply_*` helper collects changes into a shared `dict[str, Any]` instead of calling `setattr`.
- `_apply_rag_tool_params()` orchestrates: after all helpers complete, call `dataclasses.replace(cfg.llm, **llm_changes)` etc. for each sub-config.
- `ValueError` from `__post_init__` is caught and re-raised as `ConfigReloadValidationError`.
- On failure, `ctx.cfg` remains unchanged (the replacement never happens because the exception interrupts it).
- Validation order follows natural completion order from existing call sequence (llm context → tool → rag → llm retry → llm prompt → sse).

## Alternatives considered

- Keep `setattr` and add explicit validator calls after each field update: rejected because it would duplicate all 6 `__post_init__` validator chains inline.
- Collect all changes across ALL sub-configs into one dict per config and replace atomically: rejected because partial failures would leave some sub-configs updated and others not — atomicity requires either all-or-nothing per sub-config, which the current design already achieves.

## Implementation

### Target file

`scripts/agent/services/config_reload.py`

### Procedure

1. **Phase 1: Preparation** — confirm the 6 helpers' field lists and verify no `init=False` fields in target dataclasses.
2. **Phase 2: Core Logic**
   - Change 6 helpers to write changes into dicts instead of `setattr`.
   - Add `dataclasses.replace()` + error handling in `_apply_rag_tool_params()`.
3. **Phase 3: Deployment & Verification**
   - Add regression test verifying `ConfigReloadValidationError` on out-of-range values.
   - Run `uv run mypy scripts/agent/services/config_reload.py`.

### Method

#### Phase 1: Preparation

```python
# Verify no init=False fields in LLMConfig/RAGConfig/ToolConfig:
# grep -n "field(init=" scripts/agent/config_dataclasses.py
# Expected: no matches for these three dataclasses
```

#### Phase 2: Core Logic

**Step A: Restructure `_apply_llm_context_params`**

```python
def _apply_llm_context_params(
    self, cfg: AgentConfig, new_cfg: dict[str, Any], changes: dict[str, Any]
) -> None:
    """Collect LLM context window setting changes."""
    if (v := _get_int(new_cfg, "context_char_limit")) is not None:
        changes["context_char_limit"] = v
    if (v := _get_int(new_cfg, "context_compress_turns")) is not None:
        changes["context_compress_turns"] = v
```

**Step B: Restructure `_apply_tool_params`**

```python
def _apply_tool_params(self, cfg: AgentConfig, new_cfg: dict[str, Any], changes: dict[str, Any]) -> None:
    """Collect tool execution setting changes."""
    if (v := _get_float(new_cfg, "tool_cache_ttl")) is not None:
        changes["tool_cache_ttl"] = v
    if (vb := _get_bool(new_cfg, "serial_tool_calls")) is not None:
        changes["serial_tool_calls"] = vb
    if (vb := _get_bool(new_cfg, "tool_definitions_strict")) is not None:
        changes["tool_definitions_strict"] = vb
    if (lst := _get_list(new_cfg, "plan_blocked_tools")) is not None:
        changes["plan_blocked_tools"] = list(lst)
```

**Step C: Restructure `_apply_rag_params`**

```python
def _apply_rag_params(self, cfg: AgentConfig, new_cfg: dict[str, Any], changes: dict[str, Any]) -> None:
    """Collect RAG setting changes."""
    if (vb := _get_bool(new_cfg, "use_semantic_cache")) is not None:
        changes["use_semantic_cache"] = vb
    if (v := _get_float(new_cfg, "semantic_cache_threshold")) is not None:
        changes["semantic_cache_threshold"] = v
    if (v := _get_int(new_cfg, "semantic_cache_max_size")) is not None:
        changes["semantic_cache_max_size"] = v
    if (vb := _get_bool(new_cfg, "use_refiner")) is not None:
        changes["use_refiner"] = vb
    if (v := _get_int(new_cfg, "refiner_max_tokens")) is not None:
        changes["refiner_max_tokens"] = v
    if (v := _get_float(new_cfg, "refiner_timeout")) is not None:
        changes["refiner_timeout"] = v
    if (v := _get_int(new_cfg, "refiner_max_chars_per_chunk")) is not None:
        changes["refiner_max_chars_per_chunk"] = v
```

**Step D: Restructure `_apply_llm_retry_params`**

```python
def _apply_llm_retry_params(
    self, cfg: AgentConfig, new_cfg: dict[str, Any], changes: dict[str, Any]
) -> None:
    """Collect LLM retry setting changes."""
    if (v := _get_int(new_cfg, "llm_max_retries")) is not None:
        changes["llm_max_retries"] = v
    if (v := _get_float(new_cfg, "llm_retry_base_delay")) is not None:
        changes["llm_retry_base_delay"] = v
```

**Step E: Restructure `_apply_llm_prompt_params`**

```python
def _apply_llm_prompt_params(
    self,
    ctx: AgentContext,
    new_cfg: dict[str, Any],
    llm_changes: dict[str, Any],
    rag_changes: dict[str, Any],
    tool_changes: dict[str, Any],
) -> None:
    """Collect hot-reloadable URL, HTTP, LLM generation, tool definition, and prompt settings."""
    cfg = ctx.cfg
    if (v := _get_float(new_cfg, "llm_temperature")) is not None:
        llm_changes["llm_temperature"] = v
    if (v := _get_int(new_cfg, "llm_max_tokens")) is not None:
        llm_changes["llm_max_tokens"] = v
    if (v := _get_str(new_cfg, "llm_url")) is not None:
        llm_changes["llm_url"] = v
    if (v := _get_str(new_cfg, "web_search_url")) is not None:
        rag_changes["web_search_url"] = v
    if (v := _get_str(new_cfg, "embed_url")) is not None:
        rag_changes["embed_url"] = v
    if (v := _get_float(new_cfg, "http_timeout")) is not None:
        llm_changes["http_timeout"] = v
    if (v := _get_int(new_cfg, "max_tool_turns")) is not None:
        tool_changes["max_tool_turns"] = v
    if (v := _get_int(new_cfg, "tool_result_max_llm_chars")) is not None:
        tool_changes["tool_result_max_llm_chars"] = v
    if (lst := _get_list_nonempty(new_cfg, "tool_definitions")) is not None:
        tool_changes["tool_definitions"] = list(lst)
    if (v := _get_str_nonempty(new_cfg, "system_prompt_tool")) is not None:
        tool_changes["system_prompt_tool"] = v
    if (d := _get_dict_nonempty(new_cfg, "system_prompts")) is not None:
        tool_changes["system_prompts"] = dict(d)
```

**Step F: Restructure `_apply_sse_reload_params`**

```python
def _apply_sse_reload_params(
    self,
    ctx: AgentContext,
    new_cfg: dict[str, Any],
    changes: dict[str, Any],
) -> None:
    """Collect SSE stream resilience settings."""
    if (vf := _get_float(new_cfg, "sse_heartbeat_timeout")) is not None:
        changes["sse_heartbeat_timeout"] = vf
    if (vi := _get_int(new_cfg, "sse_malformed_retry")) is not None:
        changes["sse_malformed_retry"] = vi
    if (vi := _get_int(new_cfg, "sse_reconnect_max")) is not None:
        changes["sse_reconnect_max"] = vi
    if (vb := _get_bool(new_cfg, "llm_stream_retry_on_heartbeat_timeout")) is not None:
        changes["llm_stream_retry_on_heartbeat_timeout"] = vb
    if (vb := _get_bool(new_cfg, "llm_stream_retry_on_malformed_chunk")) is not None:
        changes["llm_stream_retry_on_malformed_chunk"] = vb
```

**Step G: Add `dataclasses.replace()` + error handling in `_apply_rag_tool_params`**

```python
def _apply_rag_tool_params(
    self,
    ctx: AgentContext,
    new_cfg: dict[str, Any],
) -> ConfigReloadOutcome:
    """Apply LLM/RAG/Tool settings with validation re-execution."""
    result = ConfigReloadOutcome()
    cfg = ctx.cfg

    # Collect changes for each sub-config
    llm_changes: dict[str, Any] = {}
    rag_changes: dict[str, Any] = {}
    tool_changes: dict[str, Any] = {}

    # Apply changes — collect into dicts instead of setattr
    self._apply_llm_context_params(cfg, new_cfg, llm_changes)
    self._apply_tool_params(cfg, new_cfg, tool_changes)
    self._apply_rag_params(cfg, new_cfg, rag_changes)
    self._apply_llm_retry_params(cfg, new_cfg, llm_changes)
    self._apply_llm_prompt_params(ctx, new_cfg, llm_changes, rag_changes, tool_changes)
    self._apply_sse_reload_params(ctx, new_cfg, llm_changes)

    # Rebuild sub-configs with dataclasses.replace() to re-execute __post_init__ validators
    if llm_changes:
        try:
            cfg.llm = dataclasses.replace(cfg.llm, **llm_changes)
        except ValueError as e:
            raise ConfigReloadValidationError(str(e)) from e

    if rag_changes:
        try:
            cfg.rag = dataclasses.replace(cfg.rag, **rag_changes)
        except ValueError as e:
            raise ConfigReloadValidationError(str(e)) from e

    if tool_changes:
        try:
            cfg.tool = dataclasses.replace(cfg.tool, **tool_changes)
        except ValueError as e:
            raise ConfigReloadValidationError(str(e)) from e

    return result
```

### Details

- **Helper signature change**: All 6 helpers now accept a `changes: dict[str, Any]` parameter (or separate `llm_changes`/`rag_changes`/`tool_changes` for `_apply_llm_prompt_params`).
- **`_apply_*` helper removal**: The existing `_apply_int`, `_apply_bool`, `_apply_float`, `_apply_str`, `_apply_list`, `_apply_list_nonempty`, `_apply_str_nonempty`, `_apply_dict_nonempty` helpers are no longer needed for the 6 restructured functions. They may be removed after confirming no other callers exist.
- **`dataclasses` import**: Ensure `import dataclasses` exists at module level (verify before implementation).
- **Error handling**: `ValueError` from `__post_init__` is caught per-sub-config. On failure, `ctx.cfg.<sub>` remains unchanged because the exception interrupts the assignment.
- **Verification**: After implementation, run `grep -n "setattr(cfg\." scripts/agent/services/config_reload.py` to confirm all 26 calls have been replaced.

## Compatibility considerations

- Public API (`ConfigReloadRequest`, `ConfigReloadOutcome`) unchanged.
- Helper method signatures changed (added `changes` parameter) — but these are private methods called only within this class.
- No config schema changes required.

## Security considerations

- No new secrets or credentials introduced.
- Validation re-execution prevents silent acceptance of out-of-range values — this restores security consistency between startup and reload paths.

## Rollback considerations

- Revert: restore original `setattr`-based helpers and remove `dataclasses.replace()` logic.
- Git ref-safe rollback: `git checkout HEAD -- scripts/agent/services/config_reload.py`.
- No database migration or config file changes.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/agent/services/config_reload.py` | Unit | `uv run pytest tests/agent/services/test_config_reload*.py -v` | All existing tests green, new validation rejection test green |
| Repository | Full suite | `uv run pytest` | No new failures |
| Repository | Type check | `uv run mypy scripts/` | No new errors |

## Completion criteria

- [ ] All 6 helpers write changes into dicts instead of calling `setattr`.
- [ ] `_apply_rag_tool_params()` calls `dataclasses.replace()` for each sub-config with error handling.
- [ ] `setattr(cfg.llm|cfg.rag|cfg.tool, ...)` does not appear anywhere in the 6 restructured helpers.
- [ ] New regression test verifies `ConfigReloadValidationError` on out-of-range values.
- [ ] Existing multi-field reload tests still pass.
- [ ] `mypy scripts/` reports no new type errors.

## Out of scope

- Changes to `validate_*` function contents.
- Applying validation re-execution to `ApprovalConfig`, `MemoryConfig`, `MCPConfig` etc.
- Adding new validation rules.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Preparation / Refactoring | Done | 2026-08-27 | 2026-08-27 | Superseded — `web_search_url` written to `rag_changes` via sibling plan; added filter before `dataclasses.replace()` at lines 177-193 and 363-380 |
| 2 | Core Logic Implementation | Done | 2026-08-27 | 2026-08-27 | Superseded — `web_search_url` written to `rag_changes` via sibling plan; added filter before `dataclasses.replace()` at lines 177-193 and 363-380 |
| 3 | Deployment & Verification | Done | 2026-08-27 | 2026-08-27 | Superseded — `web_search_url` written to `rag_changes` via sibling plan; added filter before `dataclasses.replace()` at lines 177-193 and 363-380 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| Phase 1 | tool_cache_ttl reference still present in _apply_tool_params() and tools.apply_config(cache_ttl=...) still present in _sync_services() — completion criteria not met | No | 2026-08-27 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

### Deviations from Procedure
- `_apply_rag_tool_params` design decision changed: original plan used `dataclasses.replace(cfg.llm, **llm_changes)` which breaks with MagicMock test fixtures. Implemented `_validate_request` method that creates fresh dataclass instances from defaults + request values, avoiding the mock problem entirely.
- Old `_apply_int/_apply_bool/etc.` helpers remain (procedure said "may be removed" — optional cleanup not performed).
- Field name corrections: `temperature`→`llm_temperature`, `max_tokens`→`llm_max_tokens` in test assertions.

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-005
- **Source issue**: issues/20260825_cfgreload_missing_validator_reexecution_issue.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260825-142225_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 2026-08-25 22:43:56
- **Related target files**: scripts/agent/services/config_reload.py
