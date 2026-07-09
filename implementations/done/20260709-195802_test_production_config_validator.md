# Implementation: tests/test_production_config_validator.py — comprehensive tests

## Goal

Add comprehensive tests for the refactored `ProductionConfigValidator` covering all checks with production/local discrimination.

## Scope

- `tests/test_production_config_validator.py` — add/update test cases

## Assumptions

1. `ProductionConfigValidator` already exists with `ConfigValidationResult` return type.
2. `SecurityProfile` enum with `PRODUCTION` and `LOCAL` values.
3. Test fixtures for config objects exist (or use inline dicts).

## Implementation

### Target file

`tests/test_production_config_validator.py`

### Procedure

Add test cases:

1. **Strict key tests:**
   - Production + `plugin_strict=false` → error in result
   - Production + `tool_definitions_strict=false` → error
   - Production + `routing_drift_strict=false` → error
   - Production + `use_tool_dag=false` → error
   - Production + all strict keys true → no errors
   - Local + any false → warning only

2. **Tool safety tier tests:**
   - Production + missing tier entry → error
   - Production + unknown tier key → error
   - Local + missing tier entry → warning
   - Local + unknown tier key → warning

3. **GitHub allowed_repos_mode tests:**
   - Production + `allowed_repos_mode="fail_open"` → error
   - Local + `allowed_repos_mode="fail_open"` → warning

4. **allowed_tools visibility tests:**
   - Production + `allowed_tools=[]` → explicit error/warning output

### Method

```python
def test_production_plugin_strict_false(self):
    result = validator.validate({"plugin_strict": False}, SecurityProfile.PRODUCTION)
    assert len(result.errors) >= 1

def test_local_plugin_strict_false(self):
    result = validator.validate({"plugin_strict": False}, SecurityProfile.LOCAL)
    assert len(result.warnings) >= 1
```

### Details

- Use `pytest.mark.parametrize` for strict key tests to reduce boilerplate.
- For GitHub check, mock `load_github_audit_config()` or inject the config.
- For safety tier checks, provide realistic `tool_safety_tiers` dicts.

## Validation plan

| Check | Tool / Command | Target |
|---|---|---|
| Validator tests | `uv run pytest tests/test_production_config_validator.py -v` | All pass |
| Lint | `uv run ruff check tests/` | 0 errors |
