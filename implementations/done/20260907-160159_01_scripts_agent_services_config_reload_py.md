# Implementation Procedure: config_reload.py

## Goal

Move three inline validator import blocks inside `_apply_rag_tool_params()` to module level. All other planned changes were already applied by prior refactoring.

## Scope

- Move three inline `from agent.services.config_validators import (...)` blocks inside `_apply_rag_tool_params()` (lines 426-437, 464-468, 483-491) to module level alongside existing imports (line 36-52)
- Do NOT modify any other aspect of this file

## Assumptions

- `config_validators.py` has zero runtime imports (only `TYPE_CHECKING`-gated import) — confirmed via direct read this cycle
- Module-level imports from `config_validators.py` already exist at line 36-52
- The three inline import blocks import validators not yet imported at module level: `validate_progress_stagnation_window`, `validate_tool_cycle_detect_window`, `validate_tool_dedup_max_repeats`, `validate_tool_error_max_consecutive`, `validate_tool_error_retry_max`
- Moving these imports to module level will not introduce circular-import issues

## Design decisions

- Consolidate all validator imports into the existing module-level import block rather than creating a separate one — keeps import organization simple and avoids duplicate import paths

## Alternatives considered

- Leaving inline imports untouched — rejected because they violate the project's convention of module-level imports and increase cognitive load when scanning the file
- Creating a separate module-level import block — rejected because it fragments the import section unnecessarily

## Implementation

### Target file

`scripts/agent/services/config_reload.py`

### Procedure

Phase 1: Identify the five validators not yet imported at module level. Phase 2: Add them to the existing module-level import block. Phase 3: Remove the three inline import blocks.

### Method

#### Phase 1: Identify missing validators

1. Compare the five validators used in inline imports against the module-level import list (line 36-52)
   - Missing: `validate_progress_stagnation_window`, `validate_tool_cycle_detect_window`, `validate_tool_dedup_max_repeats`, `validate_tool_error_max_consecutive`, `validate_tool_error_retry_max`

#### Phase 2: Add missing validators to module-level import

1. Extend the existing `from agent.services.config_validators import (...)` block (line 36-52) with the five missing validators

#### Phase 3: Remove inline import blocks

1. Delete the inline import block at lines 426-437 (LLM validators)
2. Delete the inline import block at lines 464-468 (RAG validators)
3. Delete the inline import block at lines 483-491 (Tool validators)

### Details

**Phase 1 — Identify missing validators:**

Module-level import (line 36-52) currently imports:
- `validate_llm_context_char_limit`, `validate_llm_context_token_limit`, `validate_llm_http_timeout`, `validate_llm_max_retries`, `validate_llm_max_tokens`, `validate_llm_retry_base_delay`, `validate_llm_sse_heartbeat_timeout`, `validate_llm_sse_malformed_retry`, `validate_llm_sse_reconnect_max`, `validate_llm_temperature`
- `validate_rag_refiner_max_chars_per_chunk`, `validate_rag_refiner_max_tokens`, `validate_rag_refiner_timeout`
- `validate_tool_max_tool_turns`, `validate_tool_result_max_llm_chars`

Missing validators used in inline imports:
- `validate_progress_stagnation_window` (line 498)
- `validate_tool_cycle_detect_window` (line 495)
- `validate_tool_dedup_max_repeats` (line 494)
- `validate_tool_error_max_consecutive` (line 496)
- `validate_tool_error_retry_max` (line 497)

**Phase 2 — Extend module-level import:**

Add the five missing validators to the existing module-level import block.

**Phase 3 — Remove inline imports:**

- Lines 426-437: `from agent.services.config_validators import (...)` — remove entirely
- Lines 464-468: `from agent.services.config_validators import (...)` — remove entirely
- Lines 483-491: `from agent.services.config_validators import (...)` — remove entirely

## Compatibility considerations

- `apply_config()`, `apply_config_dict()`, and `ConfigReloadOutcome`'s fields must remain unchanged
- `apply_config_dict()`'s live behavior must be identical to pre-change behavior
- The sole external caller (`cmd_config.py`) imports only `ConfigReloadService` class
- No reference to `_collect_field_changes` or any `FIELD_*` constant exists in production code (these were removed by prior refactor)

## Security considerations

- Moving validator imports to module level has no security impact
- No sensitive data or credentials involved in the changed imports

## Rollback considerations

- If circular-import issues arise after moving imports, revert by restoring the inline import blocks
- Given `config_validators.py` has zero runtime imports, this is unlikely

## Validation plan

- `uv run pytest tests/agent/services/test_config_reload.py -v` — all remaining tests pass unmodified
- `rg "from agent.services.config_validators import" scripts/agent/services/config_reload.py` — exactly one match at module level
- `uv run ruff check scripts/agent/services/config_reload.py`; `uv run mypy scripts/agent/services/config_reload.py`; `uv run bandit -r scripts/agent/services/config_reload.py -c pyproject.toml` — baseline unchanged

## Completion criteria

- [ ] `config_reload.py` contains exactly one `from agent.services.config_validators import (...)` block at module level, including the five previously-inline validators
- [ ] No inline `from agent.services.config_validators import (...)` statements remain inside `_apply_rag_tool_params()`
- [ ] `apply_config()`, `apply_config_dict()`, and `ConfigReloadOutcome`'s fields are unchanged
- [ ] `uv run ruff check scripts/agent/services/config_reload.py` reports no new finding
- [ ] All remaining tests pass unmodified

## Out of scope

- Introducing a new `FieldKeyRegistry` or any other abstraction layer
- Modifying `config_validators.py`'s own content (only where `config_reload.py` imports from it changes)
- Modifying `ConfigReloadRequest`/`ConfigReloadOutcome` or any public method signature
- Modifying `_classify_mcp_server_changes()`/MCP server lifecycle handling
- Adding new config fields
- Removing the `CONFIG_FIELD_REGISTRY` entries (they serve a real purpose: parse-time `NameError` safety vs. silently-ignored key typo)

### Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Identify missing validators | Completed | — | — | REQ-004 |
| 2 | Add missing validators to module-level import | Completed | — | — | REQ-004 |
| 3 | Remove inline import blocks | Completed | — | — | REQ-004 |
| 4 | Run validation sequence | Completed | — | — | AC-1 through AC-5 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | N/A: not applicable | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability

- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-004
- **Source issue**: issues/20260905-192444_refactor_config_reload_deduplicate_field_collection.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260906-142824_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260907-160159
- **Related target files**: scripts/agent/services/config_reload.py
