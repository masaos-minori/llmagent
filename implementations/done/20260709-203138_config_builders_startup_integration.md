# Implementation Procedure: ProductionConfigValidator Startup Integration

## Goal

Integrate `ProductionConfigValidator` into the agent startup path to validate configuration safety before REPL becomes available.

## Scope

### In scope

- Add call to `ProductionConfigValidator(config).validate()` in `build_agent_config()` in `agent/config_builders.py`
- Handle `FatalError` exceptions by exiting with error message
- Log warnings but continue startup for non-fatal issues

### Out of scope

- Modifying `ProductionConfigValidator` class itself (covered in separate procedure)
- Modifying test coverage for startup integration (covered in separate procedure)
- Documentation updates for production hardening (covered in separate procedure)

## Assumptions

1. `ProductionConfigValidator` class and `ValidationError`/`FatalError` hierarchy are already implemented in `shared/production_config_validator.py`.
2. `RagConfig` object is available at the point where `build_agent_config()` returns.
3. The startup path can safely exit via `sys.exit(1)` without breaking existing workflows.
4. Existing logging infrastructure supports `log.warning()` calls at the startup integration point.

## Implementation

### Target file

`agent/config_builders.py`

### Procedure

1. Import `ProductionConfigValidator` from `shared.production_config_validator`
2. Import `FatalError` from `shared.production_config_validator`
3. After config construction in `build_agent_config()`, add validation call before returning config
4. Wrap validation in try/except to catch `FatalError` and handle appropriately

### Method

Add the following code after all config construction logic and before the return statement in `build_agent_config()`:

```python
from shared.production_config_validator import ProductionConfigValidator, FatalError

def build_agent_config(...) -> RagConfig:
    # ... existing config construction logic ...
    
    # Production config validation (before REPL becomes available)
    validator = ProductionConfigValidator(config)
    results = validator.validate()
    
    if any(isinstance(r, FatalError) for r in results):
        fatal_messages = [r.message for r in results if isinstance(r, FatalError)]
        log.error("Production config validation failed:")
        for msg in fatal_messages:
            log.error(f"  - {msg}")
        sys.exit(1)
    
    # Log warnings but continue startup
    for result in results:
        if not isinstance(result, FatalError):
            log.warning(f"Config warning: {result.message}")
    
    return config
```

### Details

- **Placement**: The validation must occur after all configuration objects are constructed but before the config is returned and used by downstream components. This ensures validation happens before REPL becomes available.
- **FatalError handling**: If any `FatalError` is raised during validation, log all fatal messages and call `sys.exit(1)` immediately. Do not attempt partial recovery.
- **Warning handling**: Non-fatal warnings should be logged via `log.warning()` but startup should continue. This preserves local/development compatibility modes while making production issues visible.
- **Import placement**: Imports should follow project conventions (isort-compatible order, as enforced by ruff `I` rules).
- **Logging context**: Ensure log messages include sufficient context for debugging (e.g., which setting caused the issue).

## Validation Plan

### Unit tests

- Verify `build_agent_config()` exits with code 1 when `FatalError` is raised
- Verify `build_agent_config()` continues startup when only warnings are present
- Verify log messages contain expected content for both fatal and warning cases

### Integration testing

- Start agent with production config containing unsafe settings → verify startup failure
- Start agent with local config containing same settings → verify warnings logged, startup succeeds
- Verify no regression in existing startup behavior for valid configs

### Manual verification

- Review `build_agent_config()` for correct placement of validation call
- Verify no circular imports introduced by new imports
- Confirm logging output matches expected format
