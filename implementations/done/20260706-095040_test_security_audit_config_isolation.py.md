# Implementation: tests/test_security_audit_config_isolation.py — Static scan + audit API access tests

## Goal

Add a test file that (1) statically verifies no agent file other than `security_audit_config.py` imports directly from the 4 security-relevant MCP server config modules, and (2) tests the allowed/forbidden access patterns of the audit API itself.

## Scope

**In**: New file `tests/test_security_audit_config_isolation.py` with a static scan test and unit tests for the 4 loader functions.

**Out**: Tests for `repl_health.py` behaviour, integration tests, or cross-process runtime tests (separate phase).

## Assumptions

1. `scripts/agent/security_audit_config.py` has been created (Phase 1).
2. `repl_health.py` no longer imports from `mcp.shell.models` or `mcp.git.models` at module level (Phase 2).
3. The forbidden patterns are: `from mcp.shell.models`, `from mcp.git.models`, `from mcp.github.models_config`, `from mcp.cicd.models`.
4. `mcp.rag_pipeline.models` (used in `cmd_rag_export.py`) is explicitly excluded from the forbidden list per plan assumptions.
5. Tests use `pytest` with `unittest.mock.patch` for loader isolation.

## Implementation

### Target file

`tests/test_security_audit_config_isolation.py`

### Procedure

1. Write `test_only_audit_module_imports_security_server_config()` — scans `scripts/agent/` recursively, skips `security_audit_config.py`, fails if any forbidden pattern found.
2. Write `test_load_shell_audit_config_returns_none_on_import_error()` — patches `mcp.shell.models` to raise `ImportError`, asserts `None`.
3. Write `test_load_shell_audit_config_raises_runtime_error_on_load_failure()` — patches `ShellConfig.load` to raise `ValueError`, asserts `RuntimeError`.
4. Write `test_load_shell_audit_config_success()` — patches `ShellConfig.load` to return mock, asserts correct `ShellAuditConfig`.
5. Repeat steps 2–4 for `load_git_audit_config`, `load_github_audit_config`, `load_cicd_audit_config`.

### Method

```python
"""tests/test_security_audit_config_isolation.py
Static and unit tests for the security audit config isolation boundary.
"""

from __future__ import annotations

import pathlib
from unittest.mock import MagicMock, patch

import pytest

_FORBIDDEN_SECURITY_IMPORTS = [
    "from mcp.shell.models",
    "from mcp.git.models",
    "from mcp.github.models_config",
    "from mcp.cicd.models",
]
_AUDIT_MODULE = "security_audit_config.py"
_AGENT_DIR = pathlib.Path("scripts/agent")


def test_only_audit_module_imports_security_server_config() -> None:
    violations: list[str] = []
    for py_file in _AGENT_DIR.rglob("*.py"):
        if py_file.name == _AUDIT_MODULE:
            continue
        content = py_file.read_text()
        for pattern in _FORBIDDEN_SECURITY_IMPORTS:
            if pattern in content:
                violations.append(f"{py_file}: {pattern}")
    assert not violations, (
        f"Direct security server config imports outside audit module:\n"
        + "\n".join(violations)
    )


# --- load_shell_audit_config ---

def test_load_shell_audit_config_returns_none_on_import_error() -> None:
    with patch.dict("sys.modules", {"mcp.shell.models": None}):
        from agent.security_audit_config import load_shell_audit_config
        result = load_shell_audit_config()
    assert result is None


def test_load_shell_audit_config_raises_on_load_failure() -> None:
    mock_cls = MagicMock()
    mock_cls.load.side_effect = ValueError("bad config")
    with patch("agent.security_audit_config.ShellConfig", mock_cls, create=True):
        from agent.security_audit_config import load_shell_audit_config
        with pytest.raises(RuntimeError, match="shell config"):
            load_shell_audit_config()


def test_load_shell_audit_config_success() -> None:
    mock_cfg = MagicMock()
    mock_cfg.shell_sandbox_backend = "docker"
    mock_cfg.command_allowlist = ["git", "ls"]
    mock_cls = MagicMock()
    mock_cls.load.return_value = mock_cfg
    with patch("agent.security_audit_config.ShellConfig", mock_cls, create=True):
        from agent.security_audit_config import load_shell_audit_config, ShellAuditConfig
        result = load_shell_audit_config()
    assert result == ShellAuditConfig(sandbox_backend="docker", command_allowlist=["git", "ls"])


# --- load_git_audit_config ---

def test_load_git_audit_config_returns_none_on_import_error() -> None:
    with patch.dict("sys.modules", {"mcp.git.models": None}):
        from agent.security_audit_config import load_git_audit_config
        result = load_git_audit_config()
    assert result is None


def test_load_git_audit_config_raises_on_load_failure() -> None:
    mock_cls = MagicMock()
    mock_cls.load.side_effect = FileNotFoundError("missing")
    with patch("agent.security_audit_config.GitConfig", mock_cls, create=True):
        from agent.security_audit_config import load_git_audit_config
        with pytest.raises(RuntimeError, match="git config"):
            load_git_audit_config()


# --- load_github_audit_config and load_cicd_audit_config ---
# Follow the same pattern: ImportError → None, load failure → RuntimeError, success → correct DTO.
```

### Details

- `patch.dict("sys.modules", {"mcp.shell.models": None})` simulates missing optional dependency.
- The static scan uses `pathlib.Path.rglob("*.py")` — no subprocess needed.
- Tests for `load_github_audit_config` and `load_cicd_audit_config` follow the identical pattern; add them for completeness.
- Each test is self-contained; no shared fixtures needed.

## Validation plan

- `uv run pytest tests/test_security_audit_config_isolation.py -v` — all tests pass.
- Static scan test fails if `repl_health.py` is reverted to direct MCP imports (guard regression test).
- `mypy tests/test_security_audit_config_isolation.py` — no type errors.
