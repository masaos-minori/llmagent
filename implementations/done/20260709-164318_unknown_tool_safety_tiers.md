# Implementation: Detect unknown tool_safety_tiers keys

## Goal

Detect `tool_safety_tiers` keys that are not real registered tool names, warn in local, fail in production. Clean up stale `mdq` key in `config/agent.toml`.

## Scope

- `shared/tool_routing_validation.py`: add `check_unknown_tool_safety_tiers()`
- `shared/production_config_validator.py`: add `validate_unknown_tool_safety_tiers()` method
- `scripts/agent/repl_health.py`: wire into `audit_security_defaults()`
- `config/agent.toml`: replace `mdq` with 9 individual tool entries
- `tests/test_production_config_validator.py`: add tests
- `docs/05_agent_08_configuration.md`, `docs/04_mcp_05_security_and_safety_model.md`: doc updates

## Implementation

### Target files

1. `shared/tool_routing_validation.py`
2. `shared/production_config_validator.py`
3. `scripts/agent/repl_health.py`
4. `config/agent.toml`
5. `tests/test_production_config_validator.py`
6. Docs

### Procedure

See plan design section for exact code for each file.

## Validation plan

| Check | Tool / Command | Target |
|---|---|---|
| New helper unit test | `uv run pytest tests/test_production_config_validator.py -k unknown_tool_safety_tiers -v` | passes |
| Integration tests | `uv run pytest tests/test_repl_health.py -k unknown_tool_safety_tiers -v` | passes |
| Lint | `uv run ruff check scripts/ tests/` | 0 errors |
