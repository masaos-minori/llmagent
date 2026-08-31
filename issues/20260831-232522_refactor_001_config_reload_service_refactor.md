# Refactor ConfigReloadService: eliminate duplicate validation logic and field collection duplication

## Priority
Medium

## Summary
Refactor `scripts/agent/services/config_reload.py` to eliminate duplicate validation logic and field collection duplication, reduce tight coupling to AgentContext, parameterize repetitive reload methods, and centralize magic strings as constants.

## Background
N/A: covered by Summary

## Problem
`ConfigReloadService.apply_config_dict()` calls `_validate_request()` which validates LLM/RAG/Tool fields BEFORE applying changes, but then calls `_apply_rag_tool_params()` which ALSO collects and validates the same fields AFTER — using different validator sets. Additionally, `_collect_request_values()` and `_apply_llm_prompt_params()` both collect `embed_url`, `http_timeout`, `max_tool_turns`, and `tool_result_max_llm_chars` from the same request payload into separate change dicts, creating two independent paths for identical data.

## Reason for Change
The dual-validation pattern creates inconsistent coverage: `_validate_request()` validates `http_timeout` via `validate_llm_http_timeout()` and `context_token_limit` via `validate_llm_context_token_limit()`, while `_apply_rag_tool_params()` validates temperature, max_tokens, context_char_limit, etc. The field collection duplication means the same request values flow through two separate methods (`_collect_request_values()` vs `_apply_llm_prompt_params()`) without coordination, making it easy to miss validators or add redundant ones. Tight coupling to AgentContext makes unit testing difficult without full context mocking. Six private reload methods follow identical patterns that could be parameterized. Magic strings scattered throughout make maintenance error-prone.

## Implementation Intent
Consolidate field collection into a single method that populates one unified change dict. Move validation after application (not before). Extract a parameterized reload helper for the repetitive `_reload_*` methods. Replace magic strings with named constants. Reduce AgentContext coupling by passing only the specific service instances needed rather than the entire context object. Preserve public behavior: `apply_config()` and `apply_config_dict()` signatures must remain unchanged; `ConfigReloadOutcome` fields must maintain their documented semantics.

## Target Files or Areas
- `scripts/agent/services/config_reload.py` (primary)
- `scripts/agent/services/config_validators.py` (validator imports — may need consolidation)
- `tests/unit/test_config_reload.py` (existing tests — must pass after refactor)

## Required Changes
- Consolidate `_collect_request_values()` and `_apply_llm_prompt_params()` into a single `_collect_field_changes()` method that populates one unified `llm_changes`, `rag_changes`, `tool_changes` dict
- Remove `_validate_request()` pre-validation; move all validation to post-application phase inside `_apply_rag_tool_params()`
- Extract a parameterized `_reload_section()` helper that takes `(ctx, new_cfg, section_name, field_mappings)` and applies the common pattern used by `_reload_approval_config`, `_reload_tool_allowlist`, `_reload_memory_runtime`, `_reload_security_profile`
- Replace magic strings like `"context_char_limit"`, `"http_timeout"`, `"system_prompt_tool"` with named constants at module level
- Reduce `_sync_services()` coupling: pass only required service instances instead of accessing `ctx.services_required.llm`, `ctx.services_required.hist_mgr`, etc. directly
- Keep `ConfigReloadOutcome` field semantics intact (applied, needs_restart, skipped, startup_only, always_live)

## Constraints
- Public API contract: `apply_config(req: ConfigReloadRequest) -> ConfigReloadOutcome` and `apply_config_dict(new_cfg: dict[str, Any]) -> ConfigReloadOutcome` signatures must remain unchanged
- `ConfigReloadOutcome` field meanings must not change
- All existing validators must still be called; no validator removal
- MCP server classification logic (`_classify_mcp_server_changes()`) must remain untouched
- No behavioral changes to restart detection or live-field detection

## Acceptance Criteria
- [ ] Single `_collect_field_changes()` method replaces both `_collect_request_values()` and `_apply_llm_prompt_params()`
- [ ] `_validate_request()` is removed; all validation occurs in post-application phase
- [ ] At least one of the four `_reload_*` methods uses the extracted parameterized helper
- [ ] Magic string constants exist for all field names used across multiple methods
- [ ] `_sync_services()` receives explicit service parameters instead of accessing `ctx.services_required`
- [ ] All existing tests pass without modification

## Testing Expectations
- Run existing unit tests: `pytest tests/unit/test_config_reload.py` — must pass without modification
- Add regression tests for the consolidated field collection path to verify no validator is lost
- Verify that removing `_validate_request()` does not break any mocked test assertions that depend on pre-validation side effects
- Type-check: `mypy scripts/agent/services/config_reload.py`
- Lint: `ruff check scripts/agent/services/config_reload.py`

## Documentation Impact
Update module docstring to reflect new responsibility boundaries. Document that field collection is now centralized in `_collect_field_changes()`. Update `ConfigReloadOutcome` docstrings if field semantics clarification is needed.

## Out of Scope
- MCP server lifecycle management changes
- Adding new validators
- Changing `ConfigReloadOutcome` field types or adding/removing fields
- Modifying `AgentContext` or `services_required` interfaces
- Performance optimization beyond what the refactor naturally achieves

## Dependencies
- Existing tests in `tests/unit/test_config_reload.py` must pass after refactor
- `scripts/agent/services/config_validators.py` validators must remain callable with same signatures

## Unresolved Questions
- Should all four `_reload_*` methods use the parameterized helper, or just one as a proof-of-concept?
- Does `_validate_request()` pre-validation serve a purpose that post-validation cannot replicate (e.g., early failure for invalid input)?
- Are there any integration tests that depend on the exact order of validation vs. application?

## AI Implementation Instruction
Do not rewrite unrelated files. Keep changes minimal: consolidate field collection, remove pre-validation, extract one parameterized reload helper, replace magic strings with constants, reduce AgentContext coupling. Preserve all public APIs and ConfigReloadOutcome semantics. Stop and report open questions if requirements are unclear. Do not implement out-of-scope items.

## Evidence
- **Duplicate validation**: `config_reload.py:127` calls `_validate_request()` which validates `http_timeout`/`context_token_limit`; `config_reload.py:330-355` validates temperature/max_tokens/context_char_limit/etc. — different validator sets for overlapping fields
- **Field collection duplication**: `config_reload.py:162` calls `_collect_request_values()` which collects `embed_url`/`http_timeout`/`max_tool_turns`/`tool_result_max_llm_chars`; `config_reload.py:325-327` calls `_apply_llm_prompt_params()` which collects the same fields — confirmed by reading both methods' implementations
- **Tight coupling**: `config_reload.py:268-304` accesses `ctx.services_required.llm`, `ctx.services_required.hist_mgr`, `ctx.services_required.runtime_tools` directly — requires full AgentContext mock for unit testing
- **Repetitive reload methods**: `config_reload.py:537-600` — `_reload_approval_config`, `_reload_tool_allowlist`, `_reload_memory_runtime`, `_reload_security_profile` all follow identical pattern: iterate over `new_cfg` keys, call typed getters, assign to `ctx.cfg.*`
- **Magic strings**: `"context_char_limit"` at line 404, `"http_timeout"` at line 228/498, `"system_prompt_tool"` at line 301/509 — used in multiple places without centralization

## Markdown Safety Checklist
- [x] Each issue is actionable
- [x] Background, Problem, Reason for Change, and Implementation Intent meet Phase 3 requirements
- [x] Acceptance Criteria and Testing Expectations meet Phase 5 requirements
- [x] Constraints, Out of Scope, and Dependencies are explicit
- [x] Unresolved Questions reflects every open assumption from Phase 1
- [x] grouping follows Phase 2 criteria (all changes affect same file)
- [x] Markdown safety follows Phase 9 (no nested triple-backtick blocks, bullet lists used)
- [x] no secrets or sensitive data included
- [x] issue follows `templates/issue.md`'s field order and names exactly
