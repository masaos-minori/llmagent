# Implementation: tests/test_config_permission_cross_server.py — ConfigPermissionError cross-server boundary tests

## Goal

Verify that `ConfigLoader.restrict_to()` blocks an agent process from loading a different server's config file, and confirm `ConfigPermissionError` is raised rather than a generic error. Add a test for the agent-process restriction scenario.

## Scope

**In**: New file `tests/test_config_permission_cross_server.py` with tests covering: agent process with `restrict_to("agent.toml")` attempting to load `shell.toml` → `ConfigPermissionError`; correct own-file access → succeeds.

**Out**: Changes to `config_loader.py` itself. Tests for MCP server isolation (covered by existing tests).

## Assumptions

1. `ConfigLoader.restrict_to(*filenames)` sets a class-level allowlist; attempts to load files outside the set raise `ConfigPermissionError`.
2. `ConfigPermissionError` is defined in `scripts/shared/config_errors.py`.
3. `ConfigLoader` is a class with class-level state (`_allowed_files` or similar).
4. Tests must reset `ConfigLoader` state after each test (teardown or `monkeypatch`).
5. In production, the agent process calls `ConfigLoader.restrict_to("agent.toml")` at startup. Shell config is in `shell.toml`.

## Implementation

### Target file

`tests/test_config_permission_cross_server.py`

### Procedure

1. Import `ConfigLoader`, `ConfigPermissionError` from `shared`.
2. Write fixture to reset `ConfigLoader._allowed_files` after each test using `monkeypatch`.
3. Write `test_cross_server_config_load_raises_config_permission_error()` — restrict to `"agent.toml"`, attempt to load `"shell.toml"`, assert `ConfigPermissionError`.
4. Write `test_own_config_load_allowed()` — restrict to `"agent.toml"`, attempt to load `"agent.toml"`, no error (mock file read if needed).
5. Write `test_unrestricted_allows_any_file()` — no `restrict_to()` called, attempt any file load, no permission error.
6. Write `test_security_audit_config_blocked_in_restricted_agent_process()` — confirm that calling `load_shell_audit_config()` raises `RuntimeError` (wrapping `ConfigPermissionError`) when `restrict_to("agent.toml")` is active.

### Method

```python
"""tests/test_config_permission_cross_server.py
Verify ConfigLoader.restrict_to() prevents cross-server config file access.
"""

from __future__ import annotations

import pytest
from shared.config_errors import ConfigPermissionError
from shared.config_loader import ConfigLoader


@pytest.fixture(autouse=True)
def reset_config_loader(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reset ConfigLoader class-level allowlist after each test."""
    monkeypatch.setattr(ConfigLoader, "_allowed_files", None)


def test_cross_server_config_load_raises_config_permission_error(tmp_path) -> None:
    ConfigLoader.restrict_to("agent.toml")
    # Attempt to load a different server's config file
    with pytest.raises(ConfigPermissionError):
        ConfigLoader.load(tmp_path / "shell.toml")


def test_own_config_load_allowed(tmp_path) -> None:
    agent_toml = tmp_path / "agent.toml"
    agent_toml.write_text("")
    ConfigLoader.restrict_to("agent.toml")
    # Should not raise ConfigPermissionError (may raise other errors if file is empty/malformed)
    try:
        ConfigLoader.load(agent_toml)
    except ConfigPermissionError:
        pytest.fail("Own config file load raised ConfigPermissionError unexpectedly")


def test_unrestricted_allows_any_file(tmp_path) -> None:
    # No restrict_to() call; any filename is permitted
    any_file = tmp_path / "shell.toml"
    any_file.write_text("")
    try:
        ConfigLoader.load(any_file)
    except ConfigPermissionError:
        pytest.fail("Unrestricted ConfigLoader raised ConfigPermissionError")


def test_security_audit_config_blocked_in_restricted_agent_process() -> None:
    """Calling load_shell_audit_config() under restrict_to('agent.toml') raises RuntimeError."""
    ConfigLoader.restrict_to("agent.toml")
    from agent.security_audit_config import load_shell_audit_config
    with pytest.raises(RuntimeError, match="shell config"):
        load_shell_audit_config()
```

### Details

- `monkeypatch.setattr(ConfigLoader, "_allowed_files", None)` resets class-level state; adjust attribute name to match actual implementation in `config_loader.py`.
- `test_own_config_load_allowed` may need to handle non-permission errors (e.g. empty TOML); wrap in broader `except` only for `ConfigPermissionError`.
- `test_security_audit_config_blocked_in_restricted_agent_process` validates the end-to-end isolation: the agent process restriction propagates through the audit API layer.
- Read `scripts/shared/config_loader.py` to confirm the class-level state attribute name before implementing.

## Validation plan

- `uv run pytest tests/test_config_permission_cross_server.py -v` — all pass.
- `mypy tests/test_config_permission_cross_server.py` — no type errors.
- `uv run pytest tests/ -x -q` — no regressions.
