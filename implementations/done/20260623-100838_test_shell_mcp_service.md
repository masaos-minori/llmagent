## Goal

Update `TestInitSandbox.test_firejail_not_found_falls_back_to_none` in `tests/test_shell_mcp_service.py` to match the new fail-fast behavior of `init_sandbox()`: the test must assert that `RuntimeError` is raised instead of asserting the fallback return value `"none"`.

## Scope

**In-Scope:**
- `tests/test_shell_mcp_service.py` line 201-203 — rename and update one test method in `TestInitSandbox`

**Out-of-Scope:**
- No changes to other test methods (`test_none_backend_returns_none`, `test_firejail_found_returns_firejail`)
- No changes to any production file
- No new test classes

## Assumptions

1. `_init_sandbox` is imported from `mcp.shell.service` (line 21 of the test file), which re-exports `init_sandbox` from `service_static_helpers.py` as `_init_sandbox = init_sandbox`. The import does not need to change.
2. `pytest.raises(RuntimeError)` is the standard pattern already used in this project for startup-failure tests.
3. The test must verify that the error message contains enough context to diagnose the problem; a substring match on the error message string is sufficient.
4. Renaming the method from `test_firejail_not_found_falls_back_to_none` to `test_firejail_not_found_raises` makes the intent clear without breaking any external references.

## Implementation

### Target file
`tests/test_shell_mcp_service.py`

### Procedure

1. Locate `test_firejail_not_found_falls_back_to_none` (lines 201-203).
2. Replace the method body and rename the method.

### Method

Single `Edit` operation.

### Details

**Current (lines 201-203):**
```python
def test_firejail_not_found_falls_back_to_none(self) -> None:
    with patch("mcp.shell.service_static_helpers.shutil.which", return_value=None):
        assert _init_sandbox("firejail") == "none"
```

**Replacement:**
```python
def test_firejail_not_found_raises(self) -> None:
    with patch("mcp.shell.service_static_helpers.shutil.which", return_value=None):
        with pytest.raises(RuntimeError, match="firejail is not found in PATH"):
            _init_sandbox("firejail")
```

Changes:
- Method renamed from `..._falls_back_to_none` to `..._raises`
- `assert == "none"` replaced with `pytest.raises(RuntimeError, match=...)` context manager
- Match string verifies key diagnostic info without being fragile to exact phrasing

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| Target test | `uv run pytest tests/test_shell_mcp_service.py::TestInitSandbox -v` | 3 tests PASSED |
| Full shell service tests | `uv run pytest tests/test_shell_mcp_service.py -v` | No new failures |
| Lint | `uv run ruff check tests/test_shell_mcp_service.py` | 0 errors |
