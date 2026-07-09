# Implementation: test_cmd_config_refactor.py — Delete `TestCmdReloadDeferred`

## Goal

Delete the entire `TestCmdReloadDeferred` class from `test_cmd_config_refactor.py`, as it tests the now-removed `[DEFER]` rendering path.

## Scope

- `tests/test_cmd_config_refactor.py` only.
- Delete the `TestCmdReloadDeferred` class (the last class in the file).

## Implementation

### Target file

`tests/test_cmd_config_refactor.py`

### Procedure

Delete the `class TestCmdReloadDeferred` definition and all its methods.

## Validation plan

| Check | Tool / Command | Target |
|---|---|---|
| Class removed | `grep -n "TestCmdReloadDeferred" tests/test_cmd_config_refactor.py` | no matches |
| Lint | `uv run ruff check tests/test_cmd_config_refactor.py` | 0 errors |
