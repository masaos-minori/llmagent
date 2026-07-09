# Implementation: agent/repl_health.py — audit_security_defaults() comprehensive update

## Goal

Update `audit_security_defaults()` in `repl_health.py` to pass `security_profile` to the refactored `ProductionConfigValidator`, handle both `errors` (fatal) and `warnings` (non-fatal) from the validator, and integrate GitHub `allowed_repos_mode` audit.

## Scope

- `scripts/agent/repl_health.py` — update `audit_security_defaults()`
- `scripts/agent/config_builders.py` — may need to expose config to validator

## Assumptions

1. `ProductionConfigValidator.validate()` now accepts `security_profile` and returns `ConfigValidationResult` with `errors` and `warnings`.
2. `SecurityProfile` import available in repl_health.py.
3. `audit_security_defaults()` already calls `ProductionConfigValidator().validate()` at line 763.

## Implementation

### Target file

`scripts/agent/repl_health.py`

### Procedure

1. Import `ProductionConfigValidator`, `ConfigValidationResult`, and `SecurityProfile` (if not already).
2. In `audit_security_defaults()`, construct or retrieve the config dict to pass to validator.
3. Get `security_profile` from the active config (e.g., `config.security_profile` or from MCP config).
4. Call `ProductionConfigValidator().validate(config_dict, security_profile)`.
5. Handle result:
   - Production: `errors` → `RuntimeError`; `warnings` → log as warning
   - Local: both `errors` and `warnings` → log as warning
6. Remove or consolidate duplicate checks in `audit_security_defaults()` that are now covered by the validator (e.g., `allowed_repos_mode` check at line 902).

### Method

```python
def audit_security_defaults(config: AgentConfig) -> None:
    from shared.production_config_validator import ProductionConfigValidator
    from shared.mcp_config import SecurityProfile

    validator = ProductionConfigValidator()
    result = validator.validate(config, config.security_profile)

    if config.security_profile == SecurityProfile.PRODUCTION:
        if result.errors:
            raise RuntimeError("; ".join(result.errors))
        for warning in result.warnings:
            logger.warning("Production config warning: %s", warning)
    else:
        for error in result.errors:
            logger.warning("Local config notice: %s", error)
        for warning in result.warnings:
            logger.warning("Local config warning: %s", warning)
```

### Details

- Remove the `allowed_repos_mode` check in `repl_health.py:902` (now handled by validator).
- Keep the `allowed_tools=[]` warning at `repl_health.py:847` or migrate to validator.
- Ensure `config_builders.py` provides the full config dict including `tool_safety_tiers`, `allowed_repos_mode`, `allowed_tools`.

## Validation plan

| Check | Tool / Command | Target |
|---|---|---|
| Integration tests | `uv run pytest tests/test_repl_health.py -v` | All pass |
| Production startup test | `uv run pytest tests/test_repl_health.py -k production_config -v` | Pass |
| Lint | `uv run ruff check scripts/` | 0 errors |
