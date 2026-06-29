# Implementation Design: create_directory Approval Dry-Run Consistency

## Goal

Add `create_directory` to `approval_dry_run_tools` in all configuration sources so that the approval-flow dry-run preview is consistent with the tool's actual `dry_run` implementation and documentation.

## Scope

- **In-Scope**:
  - Add `create_directory` to `config/security.toml` `approval_dry_run_tools` list
  - Add `create_directory` to `scripts/agent/config_builders.py` `_DEFAULT_DRY_RUN_TOOLS` list
  - Add `create_directory` to `scripts/agent/config_dataclasses.py` default `approval_dry_run_tools` list
  - Add `create_directory` to `config/agent.toml` `approval_dry_run_tools` list
  - Add test for `create_directory` dry-run in approval preflight flow
- **Out-of-Scope**:
  - Changes to `write_service.py`, `write_models.py`, `write_tools.py` (implementation already correct)
  - Changes to `04_mcp_04_server_catalog.md` (already lists `create_directory` with dry_run)
  - Changes to `04_mcp_05_security_and_safety_model.md` (Dry-Run Support table already lists `create_directory`)

## Affected Files

1. `config/security.toml` — add `"create_directory"` after `"edit_file"` in `approval_dry_run_tools`
2. `scripts/agent/config_builders.py` — add `"create_directory"` after `"edit_file"` in `_DEFAULT_DRY_RUN_TOOLS`
3. `scripts/agent/config_dataclasses.py` — add `"create_directory"` after `"edit_file"` in default_factory list
4. `config/agent.toml` — add `"create_directory"` after `"write_file"` in `approval_dry_run_tools`
5. `tests/test_tool_approval_preflight.py` — add `test_dry_run_for_create_directory` test

## Implementation Steps

1. Add `create_directory` to all four config locations (security.toml, config_builders.py, config_dataclasses.py, agent.toml)
2. Add test asserting that when `create_directory` is invoked via the approval flow, the preflight dry-run is triggered and no directory is created before user confirmation
3. Verify by running: `uv run pytest tests/test_tool_approval_preflight.py -v`

## Acceptance Criteria

- [x] `create_directory` appears in all four `approval_dry_run_tools` lists
- [x] New test confirms dry_run is triggered for `create_directory` in approval flow
- [x] No regressions in existing approval tests
