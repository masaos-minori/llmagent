# Refactor config_builders.py — eliminate _extract fields anti-pattern and consolidate

## Summary

Eliminate the `_extract_*_fields` → dict → `{**...}` → dataclass constructor anti-pattern in `scripts/agent/config_builders.py`, consolidate default value sources, and separate concerns (loading, validation, building, assembly).

Evidence: `config_builders.py` line 126–146 (`_extract_llm_transport_fields`), line 149–166 (`_extract_llm_temperature_fields`), line 169–184 (`_extract_llm_context_fields`); line 222–246 (`_extract_tool_execution_fields`), line 249–268 (`_extract_tool_limits_fields`), line 271–282 (`_extract_tool_schema_fields`); line 294–319 (`_extract_memory_core_fields`), line 322–335 (`_extract_memory_embedding_fields`), line 338–351 (`_extract_memory_search_fields`); line 368–394 (`_extract_approval_risk_fields`), line 397–415 (`_extract_approval_tool_fields`), line 418–429 (`_extract_approval_github_fields`). Total: 13 `_extract_*_fields` functions.

## Background

`config_builders.py` has grown organically over time with multiple patterns introduced without architectural alignment. The primary anti-pattern is extracting config fields into intermediate dicts and then spreading them into dataclass constructors:

```python
def _extract_llm_transport_fields(cfg: dict[str, Any]) -> dict[str, Any]:
    return {
        "llm_url": _get_str_or_default(cfg, "llm_url", ""),
        "http_timeout": _get_or_default(cfg, "http_timeout", _get_float, 30.0),
        # ... more fields
    }

def _build_llm_config(cfg: dict[str, Any]) -> LLMConfig:
    transport = _extract_llm_transport_fields(cfg)
    temperature = _extract_llm_temperature_fields(cfg)
    context = _extract_llm_context_fields(cfg)
    all_fields = {**transport, **temperature, **context}
    return LLMConfig(**all_fields)
```

This pattern creates unnecessary indirection, makes it hard to see which defaults come from where, and breaks type safety.

## Problem

The `_extract_*_fields` → dict → `{**...}` → dataclass constructor anti-pattern makes it difficult to understand which defaults come from where, breaks type safety, and obscures the relationship between config keys and their destinations.

Evidence: 13 `_extract_*_fields` functions (lines 126–429) each return intermediate dicts that are spread via `{**a, **b, **c}` (6 occurrences at lines 192, 290, 359, 388, 437) before being passed to dataclass constructors. This creates a gap between config key names and their destination fields.

## Reason for Change

- **Maintainability risk**: 542 lines with mixed responsibilities (loading, validation helpers, builders, assembly)
- **Correctness risk**: Default values exist in two overlapping locations — `_extract_*_fields` extractors (e.g., line 129 `"llm_url": _get_str_or_default(cfg, "llm_url", "")`) and `constants.py` (canonical source for `_DEFAULT_APPROVAL_RISK_RULES`, `_DEFAULT_DRY_RUN_TOOLS`, etc.) — creating ambiguity about which defaults are authoritative
- **Testability risk**: Hard to verify individual config paths due to dict-spreading; mutations can silently alter behavior
- **Developer impact**: New contributors struggle to trace config value flow through the indirect dict-spreading pattern

## Implementation Intent

- Eliminate the `_extract_*_fields` → dict → spread anti-pattern entirely
- Move to direct field-by-field construction in builder functions
- Consolidate default value sources into a single location per config domain
- Separate concerns: loading, validation, building, assembly into distinct modules
- Preserve public API: `build_agent_config()`, `load_config()`, `ConfigLoadError` remain unchanged

## Target Files or Areas

- `scripts/agent/config_builders.py` (primary)
- `scripts/agent/config_dataclasses.py` (secondary — may need adjustments)
- `scripts/agent/constants.py` (secondary — default consolidation)

## Required Changes

- Remove all 13 `_extract_*_fields` functions (lines 126–429); replace with direct field extraction in builders
- Replace 6 `{**a, **b, **c}` spreading patterns (lines 192, 290, 359, 388, 437) with explicit keyword arguments to dataclass constructors
- Consolidate default values: move defaults from extractors to dataclass definitions or a dedicated defaults module
- Move inline validation from `_build_approval_config` (tier check at lines 406–411) and `_extract_approval_tool_fields` (dry-run validation at lines 399–402) to `ApprovalConfig.__post_init__` or dedicated validator functions
- Extract `_resolve_config_source_and_registry` import logic (line 464: `from shared.tool_registry import get_registry`) to top-level
- Remove `sys.exit(1)` side effect from `_run_production_validation` (line 491); return error results instead
- Consider splitting into separate modules (e.g., `config_loader.py`, `config_builders.py`, `config_validators.py`)

## Constraints

- Public API must remain unchanged: `build_agent_config()`, `load_config()`, `ConfigLoadError`
- All existing tests must pass
- Behavior must be identical: same config resolution order, same validation outcomes
- Cannot change dataclass field names or types

## Out of Scope

- Adding new configuration options
- Changing config file format or schema
- Modifying dataclass field names or types
- Adding new validators beyond what's needed for current fields

## Dependencies

- Requires understanding of how config values flow from YAML/JSON to AgentConfig
- Depends on `shared.config_loader.ConfigLoader` contract
- Depends on `shared.config_validator.RagConfigValidator` contract

## Acceptance Criteria

Baseline counts (from current state):
- `_extract_*_fields` functions: 13 (line 126, 149, 169, 222, 249, 271, 294, 322, 338, 368, 397, 418)
- `{**...}` spreading patterns: 6 (line 192, 290, 359, 388, 437)
- Inline validation in builders: 1 (`_validate_dry_run_tools` call at line 399-402, tier check at line 406-411)
- `sys.exit(1)` in config-building: 1 (line 491)
- Module-level imports inside functions: 1 (`from shared.tool_registry import get_registry` at line 464)

- [ ] `_extract_*_fields` function count = 0 (baseline: 13)
- [ ] `{**dict_a, **dict_b, ...}` spreading pattern count = 0 (baseline: 6)
- [ ] Each default value has exactly one source of truth
- [ ] Validation logic is in `__post_init__` or dedicated validator functions, not inline in builders (inline validation count = 0)
- [ ] No `sys.exit()` calls in config-building functions
- [ ] Imports are at module level, not inside functions (inline import count = 0)
- [ ] All existing unit tests pass (baseline: run `pytest tests/unit/test_config_builders.py` and record count)
- [ ] Integration test for `/reload` path passes
- [ ] Type checker (mypy/pyright) passes

## Testing Expectations

- Unit tests: all existing tests in `tests/unit/test_config_builders.py` (or equivalent) — baseline: record test count before changes, verify same count after
- Integration tests: reload path tests
- Mutation testing: verify no behavioral regressions
- Type checking: mypy/pyright pass
- Lint: ruff pass

## Documentation Impact

Update module docstring to reflect new architecture. Document the new default value ownership model.

## Unresolved Questions

- Which defaults should move to dataclass definitions vs. a dedicated defaults module?
- Should `_build_rag_config` validation logic also be moved to `RAGConfig.__post_init__`?
- What is the current test count baseline for `tests/unit/test_config_builders.py`?
- Are there any `__post_init__` methods in config dataclasses that currently exist?

## Priority

Medium

## AI Implementation Instruction

For AI coding agent:
- Do NOT rewrite unrelated files outside `scripts/agent/`
- Keep changes minimal: only modify config building logic
- Preserve public behavior: same config resolution, same validation outcomes
- Stop and report if requirements are unclear (which defaults should own which values)
- Do NOT add new features or configuration options
- Do NOT change dataclass field names or types
- Run type checker and tests after each step
