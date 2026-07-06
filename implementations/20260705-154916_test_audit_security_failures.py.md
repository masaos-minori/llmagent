# Implementation: tests/test_audit_security_failures.py — Security audit fail-closed tests

## Goal

Verify that `audit_security_defaults()` raises `RuntimeError` in production mode when config load fails, and returns warnings in local mode.

## Scope

**In**: Tests for each of the 4 exception handler replacements (shell, git, github, cicd).

**Out**: Testing the GitHub write settings block (it remains non-fatal).

## Assumptions

1. `audit_security_defaults(ctx, production_mode=True/False)` signature exists.
2. `ctx` has `cfg` attribute with relevant config paths.
3. Config loader can be patched to raise specific exceptions.
4. `security_lockdown_enabled=True` does not suppress config load failures.

## Implementation

### Target file
`tests/test_audit_security_failures.py`

### Procedure
Write parametrized tests for each config block in both production and local modes.

### Method

```python
import pytest
from unittest.mock import MagicMock, patch


def _make_ctx(lockdown=False, production_mode=False):
    ctx = MagicMock()
    ctx.cfg.mcp.shell = MagicMock(security_lockdown_enabled=lockdown)
    ctx.cfg.mcp.git = MagicMock()
    ctx.cfg.mcp.github = MagicMock()
    ctx.cfg.mcp.cicd = MagicMock()
    ctx.production_mode = production_mode
    return ctx


# --- Shell config load failure ---

def test_shell_config_failure_production_raises():
    from agent.repl_health import audit_security_defaults
    ctx = _make_ctx()
    with patch("mcp.shell.models.ShellConfig.load", side_effect=OSError("disk fail")):
        with pytest.raises(RuntimeError, match="shell config"):
            audit_security_defaults(ctx, production_mode=True)


def test_shell_config_failure_local_warning():
    from agent.repl_health import audit_security_defaults
    ctx = _make_ctx()
    with patch("mcp.shell.models.ShellConfig.load", side_effect=OSError("disk fail")):
        warnings = audit_security_defaults(ctx, production_mode=False)
    assert any("shell config" in w for w in warnings)


# --- Git config load failure ---

def test_git_config_failure_production_raises():
    from agent.repl_health import audit_security_defaults
    ctx = _make_ctx()
    with patch("mcp.git.models.GitConfig.load", side_effect=FileNotFoundError("not found")):
        with pytest.raises(RuntimeError, match="git config"):
            audit_security_defaults(ctx, production_mode=True)


def test_git_config_failure_local_warning():
    from agent.repl_health import audit_security_defaults
    ctx = _make_ctx()
    with patch("mcp.git.models.GitConfig.load", side_effect=FileNotFoundError("not found")):
        warnings = audit_security_defaults(ctx, production_mode=False)
    assert any("git config" in w for w in warnings)


# --- GitHub config load failure ---

def test_github_config_failure_production_raises():
    from agent.repl_health import audit_security_defaults
    ctx = _make_ctx()
    with patch("mcp.github.models_config.GitHubConfig.load", side_effect=ValueError("bad value")):
        with pytest.raises(RuntimeError, match="GitHub config"):
            audit_security_defaults(ctx, production_mode=True)


def test_github_config_failure_local_warning():
    from agent.repl_health import audit_security_defaults
    ctx = _make_ctx()
    with patch("mcp.github.models_config.GitHubConfig.load", side_effect=ValueError("bad value")):
        warnings = audit_security_defaults(ctx, production_mode=False)
    assert any("GitHub config" in w for w in warnings)


# --- CI/CD config load failure ---

def test_cicd_config_failure_production_raises():
    from agent.repl_health import audit_security_defaults
    ctx = _make_ctx()
    with patch("mcp.cicd.models.CicdConfig.load", side_effect=OSError("io error")):
        with pytest.raises(RuntimeError, match="CI/CD config"):
            audit_security_defaults(ctx, production_mode=True)


def test_cicd_config_failure_local_warning():
    from agent.repl_health import audit_security_defaults
    ctx = _make_ctx()
    with patch("mcp.cicd.models.CicdConfig.load", side_effect=OSError("io error")):
        warnings = audit_security_defaults(ctx, production_mode=False)
    assert any("CI/CD config" in w for w in warnings)


# --- lockdown=True does not suppress config load failures ---

def test_lockdown_does_not_suppress_production_failure():
    from agent.repl_health import audit_security_defaults
    ctx = _make_ctx(lockdown=True)
    with patch("mcp.shell.models.ShellConfig.load", side_effect=OSError("fail")):
        with pytest.raises(RuntimeError, match="shell config"):
            audit_security_defaults(ctx, production_mode=True)


# --- ImportError from optional dependencies stays silent ---

def test_import_error_stays_silent():
    from agent.repl_health import audit_security_defaults
    ctx = _make_ctx()
    with patch("mcp.github.models_config.GitHubConfig.load", side_effect=ImportError("no module")):
        # should NOT raise in either mode
        warnings = audit_security_defaults(ctx, production_mode=True)
    assert not any("GitHub config" in w for w in (warnings or []))
```

## Validation plan

- `uv run pytest tests/test_audit_security_failures.py -v` — all pass.
- Verify: production mode + any config OSError → `RuntimeError`.
- Verify: local mode + any config OSError → warning in return list, no raise.
- Verify: `lockdown=True` + OSError in production → still raises.
- Verify: `ImportError` from optional dependency → silent in all modes.
- `ruff check tests/test_audit_security_failures.py` — 0 errors.
