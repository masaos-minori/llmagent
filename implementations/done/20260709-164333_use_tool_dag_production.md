# Implementation: Restrict use_tool_dag=false in production

## Goal

Add `"use_tool_dag"` to `ProductionConfigValidator._REQUIRED_STRICT_KEYS` and pass the config value through. Fail startup in production when `use_tool_dag=false`.

## Scope

- `shared/production_config_validator.py`: add `"use_tool_dag"` to tuple
- `scripts/agent/repl_health.py`: add key to validator call dict
- `tests/test_production_config_validator.py`: add `use_tool_dag` test cases
- `tests/test_repl_health.py`: add 2 integration tests
- Docs updates

## Implementation

### Target files

1. `shared/production_config_validator.py`
2. `scripts/agent/repl_health.py`
3. `tests/test_production_config_validator.py`
4. `tests/test_repl_health.py`
5. `docs/05_agent_08_configuration.md`
6. `docs/04_mcp_06_configuration_and_operations.md`

### Procedure

See plan design section for exact edits.

## Validation plan

| Check | Tool / Command | Target |
|---|---|---|
| Validator tests | `uv run pytest tests/test_production_config_validator.py -k use_tool_dag -v` | pass |
| Integration tests | `uv run pytest tests/test_repl_health.py -k use_tool_dag -v` | pass |
| Lint | `uv run ruff check scripts/ tests/` | 0 errors |
