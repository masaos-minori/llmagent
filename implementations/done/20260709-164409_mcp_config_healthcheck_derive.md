# Implementation: mcp_config.py — Remove healthcheck_mode="" auto-inference (Option B)

## Goal

Replace empty-string sentinel-based auto-inference in `_build_single_server()` with `_derive_healthcheck_mode(transport)` helper. Explicit `healthcheck_mode=""` becomes invalid.

## Scope

- `shared/mcp_config.py`: add `_derive_healthcheck_mode()`; restructure `_build_single_server()` healthcheck_mode resolution
- `tests/test_mcp_config.py`: add test for explicit empty string
- `docs/04_mcp_06_configuration_and_operations.md`: update field-table row and add deprecation note

## Implementation

### Target files

1. `shared/mcp_config.py`
2. `tests/test_mcp_config.py`
3. `docs/04_mcp_06_configuration_and_operations.md`

### Procedure

See plan design section for exact code.

## Validation plan

| Check | Tool / Command | Target |
|---|---|---|
| New test | `uv run pytest tests/test_mcp_config.py -k explicit_empty_healthcheck -v` | passes |
| Regression | `uv run pytest tests/test_mcp_config.py -v` | all pass |
| Lint | `uv run ruff check scripts/ tests/` | 0 errors |
