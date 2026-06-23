## Goal

Change `init_sandbox()` in `scripts/mcp/shell/service_static_helpers.py` from a silent fallback to a fail-fast design: when `backend="firejail"` is configured but `firejail` is not installed, raise `RuntimeError` instead of warning and returning `"none"`.

## Scope

**In-Scope:**
- `scripts/mcp/shell/service_static_helpers.py` lines 20-27 — replace warning+fallback with `RuntimeError`
- Remove the docstring that says "fall back to 'none' if not found"

**Out-of-Scope:**
- No changes to `service.py`, `ShellService`, or any other file
- No changes when `backend="none"` — that path is unchanged

## Assumptions

1. `shutil.which("firejail")` returning `None` reliably indicates firejail is not installed.
2. The `_init_sandbox = init_sandbox` alias in `service.py` (line 48) means tests already import the function as `_init_sandbox` from `mcp.shell.service`; the alias continues to work after this change.
3. `init_sandbox("none")` must continue to return `"none"` — only the firejail-not-found branch changes.
4. The plan states that `ShellService` tests inject `svc._sandbox_backend = "firejail"` directly to bypass `init_sandbox` — those tests are unaffected.

## Implementation

### Target file
`scripts/mcp/shell/service_static_helpers.py`

### Procedure

1. Locate `init_sandbox` (lines 20-27).
2. Replace the function body with a `RuntimeError` raise.
3. Update (or remove) the docstring to reflect the new behavior.

### Method

Single `Edit` operation.

### Details

**Current (lines 20-27):**
```python
def init_sandbox(backend: str) -> str:
    """Validate firejail availability at startup; fall back to 'none' if not found."""
    if backend == "firejail" and shutil.which("firejail") is None:
        logger.warning(
            "firejail not found in PATH; shell_sandbox_backend falling back to 'none'",
        )
        return "none"
    return backend
```

**Replacement:**
```python
def init_sandbox(backend: str) -> str:
    if backend == "firejail" and shutil.which("firejail") is None:
        raise RuntimeError(
            "shell_sandbox_backend=firejail is configured but firejail is not found in PATH"
        )
    return backend
```

Changes:
- Remove docstring (no comment needed; behavior is self-evident from the RuntimeError message)
- Replace `logger.warning(...)` + `return "none"` with `raise RuntimeError(...)`
- `return backend` happy path unchanged

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| init_sandbox tests | `uv run pytest tests/test_shell_mcp_service.py::TestInitSandbox -v` | PASSED after test_shell_mcp_service.py is updated |
| Full shell service tests | `uv run pytest tests/test_shell_mcp_service.py -v` | No new failures |
| Type check | `uv run mypy scripts/mcp/shell/service_static_helpers.py` | No errors |
| Lint | `uv run ruff check scripts/mcp/shell/service_static_helpers.py` | 0 errors |
