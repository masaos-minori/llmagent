# Refactor ConfigReloadService.apply_config_dict method

## Priority
Medium

## Summary
Reduce complexity of `ConfigReloadService.apply_config_dict()` by extracting its five distinct responsibilities into smaller, focused private methods. Improve readability and testability without changing public behavior.

## Background
`ConfigReloadService` was previously part of `_ConfigMixin` in `scripts/agent/commands/cmd_config.py`. The migration extracted config handling into dedicated modules (`config_section_reload.py`, `config_outcome_classification.py`, `config_service_sync.py`). However, `apply_config_dict()` itself remains monolithic with multiple concerns mixed together.

## Problem
`apply_config_dict()` (~40 lines) performs five distinct operations:
1. Section-based reload via `reload_validated_section` / `reload_direct_fields` (lines 97-104)
2. Direct field updates for `system_prompt_tool`, `allowed_tools`, `masked_fields` (lines 105-110)
3. MCP server change classification + lifecycle cleanup (lines 111-121)
4. Service sync via `_sync_services()` (delegates to `ServiceSyncer.sync_all()`) (lines 122-129)
5. Outcome classification for startup-only and diagnostics fields (lines 130-131)

This violates the Single Responsibility Principle and makes the method hard to follow, test, and modify.

## Reason for Change
Maintainability risk: the method's size and mixed concerns make it difficult to add new configuration sections or modify existing ones without risking unintended side effects. Additionally, 14 existing tests fail due to CONFIG_FIELD_REGISTRY import issues, indicating structural problems that a refactoring can address.

## Implementation Intent
Extract each of the five responsibilities into separate private methods on `ConfigReloadService`:
- `_apply_sections(self, new_cfg)` — section-based reload logic (operations 1-2)
- `_apply_direct_fields(self, new_cfg)` — direct field updates (operation 3)
- `_handle_mcp_changes(self, ctx, new_cfg)` — MCP classification + lifecycle cleanup (operation 4)
- `_sync_and_classify(self, new_cfg, ctx)` — service sync + outcome classification (operations 5-6)

Each extracted method returns a partial `ConfigReloadOutcome` that gets merged into the final result. This preserves the current return contract while improving internal organization.

## Target Files or Areas
- `scripts/agent/services/config_reload.py`
- `tests/agent/services/test_config_reload.py`

## Required Changes
- Extract `_apply_sections(self, new_cfg)` from lines 97-104 of `apply_config_dict()`
- Extract `_apply_direct_fields(self, new_cfg)` from lines 105-110
- Extract `_handle_mcp_changes(self, ctx, new_cfg)` from lines 111-121
- Extract `_sync_and_classify(self, new_cfg, ctx)` from lines 122-131
- Simplify `apply_config_dict()` to call these four methods sequentially
- Update docstring of `apply_config_dict()` to reference the new internal structure
- Note: 14 pre-existing test failures exist (unrelated to this refactor); investigate separately

## Constraints
- Preserve the public API: `apply_config()`, `apply_config_dict()`, `ConfigReloadOutcome` fields unchanged
- Preserve the return contract: same tuple `(str | None, int | None, float)` for `call_rag_service` compatibility
- Do not change the semantics of any operation — only reorganize code
- Keep `_req_to_dict()` static method unchanged

## Acceptance Criteria
- [ ] `apply_config_dict()` reduced to approximately 10-15 lines (calling extracted methods)
- [ ] Each extracted method handles exactly one responsibility
- [ ] All existing tests pass after refactoring
- [ ] No behavioral changes — same inputs produce same outputs
- [ ] Docstring updated to reflect new internal structure

## Testing Expectations
- Run full test suite: `uv run pytest tests/agent/services/test_config_reload.py`
- Verify all 56 tests pass (currently 14 fail)
- Run type checker: `uv run mypy scripts/agent/services/config_reload.py`
- Run linter: `uv run ruff check scripts/agent/services/config_reload.py`

## Documentation Impact
Update `ConfigReloadService.apply_config_dict()` docstring to mention the extracted private methods. No external-facing documentation changes needed.

## Out of Scope
- Changes to `config_field_registry.py` (CONFIG_FIELD_REGISTRY structure)
- Changes to `config_validators.py` (validation functions)
- Changes to `config_section_reload.py` (section reload logic)
- Changes to `config_service_sync.py` (service sync logic)
- Changes to `config_outcome_classification.py` (outcome classification logic)
- Adding new features or changing public APIs

## Dependencies
- None

## Unresolved Questions
- Should `_handle_mcp_changes()` also handle lifecycle cleanup for removed servers, or should that be a separate method? Currently both are in the same block.
- Is the current 40-line threshold appropriate, or should we aim for even shorter methods (<20 lines)?

## AI Implementation Instruction
Keep changes minimal: extract existing code blocks into private methods, do not rewrite logic. Preserve all current behavior including error paths. After refactoring, verify all tests pass. Do not modify unrelated files (config_field_registry.py, config_validators.py, etc.). If any test failures appear after refactoring, investigate whether they were pre-existing (14 currently fail) or introduced by the refactor.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260919-112313
- **Related target files**: scripts/agent/services/config_reload.py
