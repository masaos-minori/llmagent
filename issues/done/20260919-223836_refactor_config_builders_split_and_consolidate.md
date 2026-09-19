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
3. **Builder functions vary in complexity**: `_build_llm_config` (51 lines), `_build_tool_config` (49 lines), `_build_memory_config` (45 lines), and `_build_approval_config` (45 lines) extract 15-20 fields each and exceed typical function length guidelines; however, `_build_rag_config` (24 lines) and `_build_diagnostics_config` (15 lines) are within reasonable bounds.

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
- Decompose `_build_llm_config` (199-249), `_build_tool_config` (278-326), `_build_memory_config` (329-373), `_build_approval_config` (376-420) into smaller sub-functions (<30 lines each); exclude `_build_rag_config` (24 lines) and `_build_diagnostics_config` (15 lines) as they are already within reasonable length.
- Split `build_agent_config` (440-507) into three parts: (1) config loading + security profile computation, (2) production validation, (3) builder orchestration + AgentConfig assembly.
- Run `uv run pytest tests/agent/test_config_builders.py -q` and confirm zero failures.
- Run `uv run pytest tests/ -q` to confirm no regressions elsewhere.

## Constraints
- Preserve all locally-defined public exports: `build_agent_config`, `load_config`, `ConfigLoadError`.
- Do not change any error types, exception messages, or validation behavior.
- Do not change the default values — only move them to a shared location.
- All existing tests must continue to pass without modification.
- Do not introduce new dependencies or change the import graph beyond what is necessary for the split.
- When consolidating `_get_*_or_default` helpers, the empty-string semantics of `_get_str_or_default` (preserving `None vs ""` distinction) MUST NOT be lost. A single generic helper replacing all six is unsafe without explicit handling of this distinction.
- The `build_agent_config` split should produce three sub-functions: (1) config loading + security profile, (2) production validation, (3) builder orchestration + AgentConfig assembly.
- `_build_rag_config` (24 lines) and `_build_diagnostics_config` (15 lines) do not meet the >30-line threshold for decomposition and should be excluded.

## Acceptance Criteria
- `scripts/agent/config_builders.py` is under 200 lines (excluding `constants.py`).
- `scripts/agent/constants.py` exists and contains all `_DEFAULT_*` tables; `config_dataclasses.py` imports from it.
- No `_get_*_or_default` wrapper functions remain in `config_builders.py`; the empty-string `None vs ""` semantics of `_get_str_or_default` is preserved.
- Each decomposed `_build_*` function (excluding `_build_rag_config` and `_build_diagnostics_config`) in `config_builders.py` is under 30 lines.
- `build_agent_config` is split into three named sub-functions: (1) config loading + security profile, (2) production validation, (3) builder orchestration + AgentConfig assembly.
- `uv run pytest tests/agent/test_config_builders.py -q` passes with zero failures.
- `uv run pytest tests/ -q` passes with zero failures.
- Public API surface unchanged (verified by import check for `build_agent_config`, `load_config`, `ConfigLoadError`).

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

## Adversarial Validation (20260919-223836)

### Verified claims
- **File line count**: `config_builders.py` is indeed 507 lines.
- **Inline default duplication**: All 6 `_DEFAULT_*` tables (`_DEFAULT_PLAN_BLOCKED_TOOLS`, `_DEFAULT_APPROVAL_RISK_RULES`, `_DEFAULT_PROTECTED_PATHS`, `_DEFAULT_SHELL_SAFE_PREFIXES`, `_DEFAULT_RESOURCE_KEYS`, `_DEFAULT_DRY_RUN_TOOLS`) have exact copies in `config_dataclasses.py` dataclass defaults (lines 196-202, 293-311, 314-322, 330-343, 346-357, 359-367 respectively). Two sources of truth confirmed.

### Disputed / inaccurate claims
- **`_build_rag_config` length**: Claimed as part of the ~50-line builders but is actually 24 lines (252-275). It does not exceed typical function length guidelines and should not be decomposed.
- **`_build_diagnostics_config` omission**: At 15 lines (423-437), this is the shortest builder function but is not mentioned in the Problem section. The claim "each `_build_*` function" overstates the problem.
- **`_get_*_or_default` consolidation risk**: The generic helper proposal would conflate `_get_str_or_default`'s empty-string semantics (`v if v is not None else default`) with the five other helpers' semantics (`v or default`). This is not a minor nuance — it would silently break `memory_jsonl_dir` fallback logic at `config_builders.py:334` where `_get_str + or` is intentionally used instead. The Issue leaves this as an unresolved question but offers no concrete resolution path.
- **`build_agent_config` separation boundary**: "validation/registry resolution layer" conflates two distinct concerns. Production config validation and tool registry resolution are orthogonal operations with different failure modes and lifecycles. A cleaner split would be: (a) config loading + security profile computation, (b) production validation, (c) builder orchestration + AgentConfig assembly.
- **Public API preservation list**: `_build_mcp_servers` and `SecurityProfile` are imported from `shared/mcp_config.py`, not defined locally in `config_builders.py`. Including them in the "preserve" list misrepresents the scope of local changes needed.

### Acceptance Criteria concerns
- **"config_builders.py under 200 lines"**: Achievable by moving constants, but `constants.py` line count is not counted. Total code volume may increase due to module overhead.
- **"No `_get_*_or_default` wrappers remain"**: Would require careful handling of the empty-string semantics distinction. A generic helper alone cannot preserve both patterns safely.
- **"Each `_build_*` under 30 lines"**: Already satisfied by `_build_rag_config` (24 lines) and `_build_diagnostics_config` (15 lines). Applying this uniformly wastes effort on short functions.
- **"`build_agent_config` split into factory + validation"**: The term "validation" is ambiguous — validation and registry resolution should be separate sub-functions given their different responsibilities.
- **Test compatibility after internal restructuring**: Tests call `_build_*` directly, so they are weakly coupled to internal structure. Moving defaults to `constants.py` breaks the implicit assumption that defaults live in `config_dataclasses.py`. Tests will need updating even though behavior is unchanged.

### Updated constraints
- When consolidating `_get_*_or_default` helpers, the empty-string semantics of `_get_str_or_default` MUST be preserved as a separate code path or documented in the generic helper's contract. A single generic helper replacing all six is unsafe without explicit handling of the `None vs ""` distinction.
- The `build_agent_config` split should produce three sub-functions rather than two: (1) config loading + security profile, (2) production validation, (3) builder orchestration + AgentConfig assembly.
- `_build_rag_config` (24 lines) and `_build_diagnostics_config` (15 lines) do not meet the >30-line threshold for decomposition and should be excluded from the builder decomposition requirement.
- The public API preservation list should only include locally-defined exports: `build_agent_config`, `load_config`, `ConfigLoadError`.

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
