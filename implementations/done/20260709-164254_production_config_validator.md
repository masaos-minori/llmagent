# Implementation: shared/production_config_validator.py — New validator + wiring

## Goal

Create `ProductionConfigValidator` in `shared/production_config_validator.py` that flags `plugin_strict`, `tool_definitions_strict`, and `routing_drift_strict` when falsy; wire it into `audit_security_defaults()` in `repl_health.py` with production/local branching.

## Scope

- `shared/production_config_validator.py` (new)
- `scripts/agent/repl_health.py` (wire validator call)
- `tests/test_production_config_validator.py` (new)
- `tests/test_repl_health.py` (add 5 tests)

## Implementation

### Target files

1. `shared/production_config_validator.py` (new)
2. `scripts/agent/repl_health.py`
3. `tests/test_production_config_validator.py` (new)
4. `tests/test_repl_health.py`

### Procedure

#### File 1: `shared/production_config_validator.py`

Create new file with `ProductionConfigValidator.validate()` method that checks `_REQUIRED_STRICT_KEYS` against a `dict[str, Any]` and returns `ConfigValidationResult`.

#### File 2: `repl_health.py`

Insert a call to `ProductionConfigValidator().validate(...)` in `audit_security_defaults()` after the `shell_sandbox_backend` check, raising `RuntimeError` in production mode, warning in local mode.

#### File 3: `tests/test_production_config_validator.py`

Add 3 unit tests:
- `plugin_strict=false` → 1 error
- all 3 `true` → no errors
- all 3 absent → 3 errors (defaults falsy)

#### File 4: `tests/test_repl_health.py`

Add 5 tests to `TestAuditSecurityDefaults`:
- production + `plugin_strict=false` → `RuntimeError`
- production + `tool_definitions_strict=false` → `RuntimeError`
- production + `routing_drift_strict=false` → `RuntimeError`
- local + any false → warning only
- production + all true → no raise

## Validation plan

| Check | Tool / Command | Target |
|---|---|---|
| New validator unit tests | `uv run pytest tests/test_production_config_validator.py -v` | all pass |
| Integration tests | `uv run pytest tests/test_repl_health.py -k production_config -v` | all pass |
| Architecture | `PYTHONPATH=scripts uv run lint-imports` | 0 violations |
| Lint | `uv run ruff check scripts/ tests/` | 0 errors |
