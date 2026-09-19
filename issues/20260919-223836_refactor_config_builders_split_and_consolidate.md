# Refactor scripts/agent/config_builders.py: split large file, centralize defaults, reduce repetition

## Priority
Medium

## Summary
`scripts/agent/config_builders.py` is a 507-line monolith mixing config loading, inline default constant tables, typed-extraction helpers, five builder functions, and the top-level `build_agent_config` entry point. The inline defaults (lines 71-127) duplicate dataclass defaults, the `_get_*_or_default` helpers (lines 135-177) are structurally identical wrappers around `_get_*`, and each `_build_*` function repeats the same extract-validate-construct pattern across ~50 lines. This makes review, maintenance, and adding new config sections error-prone.

## Background
The file was written incrementally over multiple iterations (see `implementations/done/*config_builders*` history). Each iteration added fields and builders without restructuring, resulting in a file where responsibility boundaries are unclear and the cognitive load per function exceeds what is reasonable for a single reviewer.

## Problem
Three concrete problems:
1. **Inline default tables duplicate dataclass defaults** (lines 71-127): `_DEFAULT_PLAN_BLOCKED_TOOLS`, `_DEFAULT_APPROVAL_RISK_RULES`, `_DEFAULT_PROTECTED_PATHS`, `_DEFAULT_SHELL_SAFE_PREFIXES`, `_DEFAULT_RESOURCE_KEYS`, `_DEFAULT_DRY_RUN_TOOLS` — these are defined here but also exist as dataclass defaults, creating two sources of truth.
2. **Structural repetition in `_get_*_or_default` helpers** (lines 135-177): six nearly-identical wrapper functions (`_get_list_or_default`, `_get_dict_or_default`, `_get_str_or_default`, `_get_int_or_default`, `_get_float_or_default`, `_get_bool_or_default`) that differ only in type and return annotation.
3. **Each `_build_*` function is too long** (199-249, 278-326, 329-373, 376-420): each extracts 15-20 fields, validates them, and constructs a dataclass — exceeding typical function length guidelines and making it hard to verify correctness of individual field mappings.

## Reason for Change
- Maintainability: a 507-line file with 6+ distinct responsibilities is difficult to review and extend safely.
- Correctness risk: duplicated defaults between inline tables and dataclasses can drift apart silently.
- Testability: the tight coupling between extraction, validation, and construction in each `_build_*` function means tests must cover every path through every builder rather than testing concerns independently.
- Medium priority: this affects developer experience and future feature velocity but does not impact runtime correctness today.

## Implementation Intent
Split the file into focused modules with clear responsibility boundaries:

1. **Constants module** — Move all `_DEFAULT_*` tables to a dedicated module (e.g., `constants.py`). Have the dataclasses import these as their defaults instead of defining inline literals. Remove the duplicates from `config_builders.py`.

2. **Extraction helpers consolidation** — Replace the six `_get_*_or_default` wrappers with a single generic helper (e.g., `_get_or_default(cfg, key, getter, default)`) or inline the `v if v is not None else default` pattern directly in callers. The `_get_str_or_default` docstring already notes special semantics for empty-string defaults — preserve that distinction.

3. **Builder function decomposition** — Reduce each `_build_*` function to under 30 lines by extracting field-group logic into private helpers (e.g., `_extract_llm_fields`, `_validate_llm_fields`). Each helper should handle one cohesive group (e.g., LLM transport fields vs. LLM context fields).

4. **`build_agent_config` separation** — Split the top-level function into two parts: a factory orchestration layer (responsible for calling builders and assembling `AgentConfig`) and a validation/registry resolution layer (production config validation, tool registry resolution). These are separate concerns that currently share the same scope.

Preserve: public API surface (`build_agent_config`, `load_config`, `ConfigLoadError`), all existing behavior and error types, test compatibility.

## Target Files or Areas
- `scripts/agent/config_builders.py` (primary refactor target)
- `scripts/agent/constants.py` (new — move `_DEFAULT_*` tables here)
- `scripts/agent/config_dataclasses.py` (update to import defaults from `constants.py`)
- `tests/agent/test_config_builders.py` (verify tests still pass after refactor)

## Required Changes
- Create `scripts/agent/constants.py` containing all `_DEFAULT_*` constant tables currently in `config_builders.py` (lines 71-127).
- Update `config_dataclasses.py` to import defaults from `constants.py` instead of defining inline literals.
- Remove `_DEFAULT_*` constants from `config_builders.py`.
- Consolidate `_get_*_or_default` helpers (lines 135-177) into a single generic helper or inline pattern.
- Decompose `_build_llm_config` (199-249), `_build_tool_config` (278-326), `_build_memory_config` (329-373), `_build_approval_config` (376-420) into smaller sub-functions (<30 lines each).
- Split `build_agent_config` (440-507) into factory orchestration and validation layers.
- Run `uv run pytest tests/agent/test_config_builders.py -q` and confirm zero failures.
- Run `uv run pytest tests/ -q` to confirm no regressions elsewhere.

## Constraints
- Preserve all public exports: `build_agent_config`, `load_config`, `ConfigLoadError`, `_build_mcp_servers`, `SecurityProfile`.
- Do not change any error types, exception messages, or validation behavior.
- Do not change the default values — only move them to a shared location.
- All existing tests must continue to pass without modification.
- Do not introduce new dependencies or change the import graph beyond what is necessary for the split.

## Acceptance Criteria
- `scripts/agent/config_builders.py` is under 200 lines.
- `scripts/agent/constants.py` exists and contains all `_DEFAULT_*` tables; `config_dataclasses.py` imports from it.
- No `_get_*_or_default` wrapper functions remain in `config_builders.py`.
- Each `_build_*` function in `config_builders.py` is under 30 lines.
- `build_agent_config` is split into at least two named sub-functions (factory + validation).
- `uv run pytest tests/agent/test_config_builders.py -q` passes with zero failures.
- `uv run pytest tests/ -q` passes with zero failures.
- Public API surface unchanged (verified by import check).

## Testing Expectations
- `uv run pytest tests/agent/test_config_builders.py -q` — unit tests for config builders.
- `uv run pytest tests/ -q` — full suite regression.
- Import verification: `python -c "from agent.config_builders import build_agent_config, load_config, ConfigLoadError"` succeeds.

## Documentation Impact
Update module docstrings in `config_builders.py` and `constants.py` to reflect the new structure. Document the import relationship: `config_dataclasses.py` depends on `constants.py` for defaults.

## Out of Scope
- Adding new config sections or fields.
- Changing the TOML configuration schema.
- Modifying `shared/` modules.
- Performance optimization of config loading.
- Any other failing test files identified in unrelated investigations.

## Dependencies
N/A: none.

## Unresolved Questions
- Should `_get_str_or_default`'s special empty-string-default semantics be preserved as a separate helper or documented in the generic helper's signature? Not decided — left for the implementer to evaluate.
- Is there value in moving `_validate_dry_run_tools` to `constants.py` alongside the dry-run tools table, or should it stay in `config_builders.py` since it references the constant? Not decided — left for the implementer.

## AI Implementation Instruction
Refactor `scripts/agent/config_builders.py` following the Implementation Intent above. Do not add new features, change default values, or modify the public API. After each step, run `uv run pytest tests/agent/test_config_builders.py -q` to verify no regressions. If any test fails, revert the last change before proceeding. Keep the diff minimal and focused on structural changes only.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260919-223836
- **Related target files**: scripts/agent/config_builders.py, scripts/agent/constants.py, scripts/agent/config_dataclasses.py, tests/agent/test_config_builders.py
