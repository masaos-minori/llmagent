# Implementation: test_agent_cmd_config.py — add enhanced reload output tests

## Goal

Add tests that verify the new structured output of `_cmd_reload()`.

## Scope

`tests/test_agent_cmd_config.py` — add new tests to the existing reload error section.

## Assumptions

1. The existing `_FakeCmd` fixture and mock pattern in `test_agent_cmd_config.py` can be reused.
2. Tests verify the new output lines: "Config reloaded from:", "Applied (runtime):", "Restart required:", "No changes detected."
3. The existing error path tests remain valid and unchanged.

## Implementation

### Target file

`tests/test_agent_cmd_config.py`

### Procedure

Add a `TestCmdReloadOutput` class with tests for the happy path, applied output, and restart required output.

### Method

Mock `ConfigLoader().load()` and `ConfigReloadService.apply_config_dict()` to control the `ConfigReloadOutcome` returned.

### Details

Tests to add (in new `TestCmdReloadOutput` class):

1. `test_reload_shows_source_files` — output includes "Config reloaded from: common.toml, agent.toml"
2. `test_reload_shows_applied_items` — when `applied=["llm", "hist_mgr"]`, output lists each with "  - "
3. `test_reload_shows_needs_restart` — when `needs_restart=["server1"]`, output shows "Restart required:" section
4. `test_reload_no_changes_shows_message` — when `applied=[]` and `needs_restart=[]`, shows "No changes detected."

## Validation plan

```bash
uv run pytest tests/test_agent_cmd_config.py -v
```
