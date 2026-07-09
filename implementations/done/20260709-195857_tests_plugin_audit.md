# Implementation: tests — plugin audit source and distinguishability

## Goal

Add tests for plugin execution audit source field and plugin result distinguishability.

## Scope

- `tests/test_plugin_registry.py`
- `tests/test_plugin_contract.py`
- `tests/test_cmd_plugins.py` (if applicable)

## Assumptions

1. Phase 2 (audit source standardization) and Phase 3 (/plugin status) implementations are complete.

## Implementation

### Target files

1. `tests/test_plugin_registry.py`
2. `tests/test_plugin_contract.py`
3. `tests/test_cmd_plugins.py` (if applicable)

### Procedure

1. **Plugin registry tests**: add test that plugin tool audit events have `source="plugin"` and `server_key=""` / `request_id=""`.
2. **Plugin contract tests**: add test that plugin tool results are distinguishable from MCP tool results in audit log.
3. **Cmd plugins tests**: add test for new status output fields (if not already covered).

### Details

- Use existing test fixtures and patterns from `test_plugin_registry.py` and `test_plugin_contract.py`.
- Mock audit calls where appropriate to verify source field value.

## Validation plan

| Check | Tool / Command | Target |
|---|---|---|
| All plugin tests | `uv run pytest tests/test_plugin_registry.py tests/test_plugin_contract.py -v` | Pass |
