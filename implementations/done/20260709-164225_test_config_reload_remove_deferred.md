# Implementation: test_config_reload.py — Remove `.deferred` assertions

## Goal

Remove 4 `result.deferred` assertions from `TestMcpServerChangeClassification` that will raise `AttributeError` once the field is deleted.

## Scope

- `tests/test_config_reload.py` only.
- 4 lines in `TestMcpServerChangeClassification`.

## Implementation

### Target file

`tests/test_config_reload.py`

### Procedure

Remove these 4 lines:
1. `assert not any("url" in item for item in result.deferred)` in `test_url_change_reports_field_qualified_restart_entry`
2. `assert not any("auth_token" in item for item in result.deferred)` in `test_auth_token_change_reports_restart_not_deferred`
3. `assert not any("startup_mode" in item for item in result.deferred)` in `test_startup_mode_change_reports_restart_not_deferred`
4. `assert result.deferred == []` in `test_each_field_change_is_restart_required`

## Validation plan

| Check | Tool / Command | Target |
|---|---|---|
| No dangling refs | `grep -rn "\.deferred\b" tests/test_config_reload.py` | no matches |
| Lint | `uv run ruff check tests/test_config_reload.py` | 0 errors |
