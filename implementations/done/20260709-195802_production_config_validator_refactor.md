# Implementation: shared/production_config_validator.py — comprehensive refactor

## Goal

Refactor `ProductionConfigValidator` to detect all unsafe production settings and make them fatal in production while preserving warning-only for local/dev. Add bidirectional `tool_safety_tiers` validation, GitHub `allowed_repos_mode="fail_open"` check, `allowed_tools=[]` visibility, and fix `use_tool_dag` logic.

## Scope

- `shared/production_config_validator.py` — refactor validate() and add new checks
- `shared/tool_routing_validation.py` — add bidirectional safety tier validation helpers (if missing)
- `mcp/github/service_security.py` — may need validation hook
- `agent/security_audit_config.py` — may need audit additions

## Assumptions

1. `SecurityProfile` is the canonical discriminator (`shared/mcp_config.py`).
2. `check_tool_safety_tiers()` and `check_unknown_tool_safety_tiers()` already exist in `tool_routing_validation.py`.
3. `load_github_audit_config()` exists in `security_audit_config.py`.
4. `ProductionConfigValidator` already exists at `shared/production_config_validator.py` (39 lines) with basic strict-key checks.

## Implementation

### Target file

`scripts/shared/production_config_validator.py`

### Procedure

1. Add `security_profile: SecurityProfile` parameter to `validate()`.
2. Fix `use_tool_dag` logic: flag error only when `use_tool_dag=false` (reverse current condition `not config.get(key, False)`).
3. Add bidirectional `tool_safety_tiers` validation using existing helpers from `tool_routing_validation.py`:
   - Missing tiers → error (prod) / warning (local)
   - Unknown keys → error (prod) / warning (local)
4. Add GitHub `allowed_repos_mode="fail_open"` check via `load_github_audit_config()`.
5. Add `allowed_tools=[]` visibility check with distinct severity by profile.
6. Change return type: `ConfigValidationResult` with `errors` (fatal) and `warnings` (non-fatal).

### Method

```python
def validate(
    self,
    config: AgentConfig | dict[str, Any],
    security_profile: SecurityProfile,
) -> ConfigValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    # Strict key checks (fixed logic)
    for key in self._REQUIRED_STRICT_KEYS:
        if key == "use_tool_dag":
            if config.get(key, True) is False:
                (errors if security_profile == SecurityProfile.PRODUCTION else warnings).append(...)
        else:
            if not config.get(key, False):
                (errors if security_profile == SecurityProfile.PRODUCTION else warnings).append(...)

    # Bidirectional tool_safety_tiers validation
    # allowed_repos_mode check
    # allowed_tools check

    return ConfigValidationResult(errors=errors, warnings=warnings)
```

### Details

- `_REQUIRED_STRICT_KEYS` stays as `("plugin_strict", "tool_definitions_strict", "routing_drift_strict", "use_tool_dag")`.
- Bidirectional check: use `check_tool_safety_tiers()` from `tool_routing_validation` to find missing known tool entries; use `check_unknown_tool_safety_tiers()` to find unknown keys.
- GitHub check: compare `load_github_audit_config().allowed_repos_mode` against `"fail_open"`.
- `allowed_tools=[]` check: emit as warning in local, error in production.

## Validation plan

| Check | Tool / Command | Target |
|---|---|---|
| Validator unit tests | `uv run pytest tests/test_production_config_validator.py -v` | All pass |
| Architecture | `PYTHONPATH=scripts uv run lint-imports` | 0 violations |
| Lint | `uv run ruff check scripts/` | 0 errors |
| Type check | `uv run mypy scripts/` | No new errors |
