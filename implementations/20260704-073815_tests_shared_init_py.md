# Implementation: Create `tests/shared/__init__.py`

## Goal

Create an empty `tests/shared/__init__.py` to make `tests/shared/` a proper Python package,
enabling pytest to collect `tests/shared/test_plugin_tool_invoker.py` correctly.

## Scope

- In-Scope: Create empty file `tests/shared/__init__.py`.
- Out-of-Scope: No changes to `tests/conftest.py` or any other file.

## Assumptions

1. `tests/shared/` directory does not yet exist.
2. `tests/conftest.py` already adds `scripts/` and `tests/` to `sys.path`; no extra `conftest.py`
   is needed inside `tests/shared/`.
3. An empty `__init__.py` is sufficient for pytest collection — no imports needed.

## Implementation

### Target file

`tests/shared/__init__.py` (new empty file)

### Procedure

1. Create directory `tests/shared/` if it does not exist.
2. Create empty file `tests/shared/__init__.py`.
3. Verify pytest can collect the directory:
   ```bash
   uv run pytest tests/shared/ --collect-only
   ```
   Expected: no errors (0 tests collected if test file not yet created, or collected tests if it exists).

### Method

File content: empty (0 bytes), or optionally a single docstring comment:
```python
"""tests/shared — Unit tests for shared/ modules."""
```

Either is acceptable. An empty file is preferred to keep it consistent with other `__init__.py`
files in the test tree.

### Details

- This file is a prerequisite for `tests/shared/test_plugin_tool_invoker.py`.
- Creating the directory and file does not affect existing tests.

## Validation plan

```bash
# Confirm directory and file created
ls tests/shared/__init__.py

# Confirm no pytest collection errors
uv run pytest tests/shared/ --collect-only
```
