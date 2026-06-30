## Goal
- Verify deprecation warning behavior for deprecated Event Bus config fields and document validation behavior

## Findings

### Current state
- `scripts/eventbus/config.py:L71-83`: DeprecationWarning emitted when non-default values set for both fields
- `scripts/eventbus/config.py:L59-65`: ValueError raised when values < 1 for both deprecated fields
- `docs/06_eventbus_05_configuration_deploy_and_operations.md:L31-36`: Deprecated section exists, mentions DeprecationWarning but not validation behavior (0 or less → ValueError)
- `tests/test_eventbus_config.py:L145,162`: DeprecationWarning tests exist for non-default values
- `tests/test_eventbus_config.py:L50,63`: ValueError tests exist for 0 values

### Gap: Docs don't mention validation behavior
The deprecated fields section mentions "Setting them to non-default values emits a DeprecationWarning" but doesn't mention that values <1 raise ValueError. This is an important distinction — the validation applies even to deprecated fields.

## Changes
- `docs/06_eventbus_05_configuration_deploy_and_operations.md:L35-36`: Added note that "Non-default values emit DeprecationWarning; values <1 raise ValueError" for both deprecated fields
