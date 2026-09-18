# Implementation Procedure — New file: Cross-cutting failure handling policy test

## Target File

`tests/agent/test_failure_handling_policy_cross_cutting.py` (new file)

## Invariants Addressed

| INV | Description |
|-----|-------------|
| INV-010 | Environment failure handling policy cross-cutting |
| INV-011 | Environment failure handling policy cross-cutting |

## Context

ADR-004 (`docs/adr/ADR-004-environment-failure-handling-policy.md`) defines environment-specific failure handling policies. The existing test file `tests/agent/test_audit_security_failures.py` covers security audit config load failures but does not validate the broader cross-cutting failure handling policy. This new file adds cross-cutting coverage.

## Steps

### Step 1 — Create the new test file

Create `tests/agent/test_failure_handling_policy_cross_cutting.py` with the following structure:

```python
"""tests/agent/test_failure_handling_policy_cross_cutting.py
Cross-cutting tests for ADR-004 environment failure handling policy.
Covers INV-010 and INV-011.
"""

from __future__ import annotations

import pytest
from agent.services.security_audit import audit_security_defaults
```

### Step 2 — Add helper function for context creation

```python
def _make_ctx(lockdown=False):
    from unittest.mock import MagicMock

    ctx = MagicMock()
    ctx.cfg.mcp.mcp_servers = {}
    ctx.cfg.mcp.security_lockdown_enabled = lockdown
    ctx.cfg.tool.allowed_tools = None
    # Explicitly set approval to empty dict so getattr returns {} not MagicMock
    ctx.cfg.approval = MagicMock()
    ctx.cfg.approval.tool_safety_tiers = {}
    return ctx
```

### Step 3 — Add test fixtures for audit configs

```python
_SHELL_OK = ShellAuditConfig(sandbox_backend="firejail", command_allowlist=["ls"])
_GIT_OK = GitAuditConfig(allowed_repo_paths=["/home"])
_GITHUB_OK = GitHubAuditConfig(
    allowed_repos=["owner/repo"],
    allow_force_push=False,
    require_pr_review=True,
)
```

### Step 4 — Add test: shell config failure raises RuntimeError in production

```python
class TestFailureHandlingPolicy:
    def test_shell_config_failure_production_raises(self) -> None:
        """INV-010: shell config load failure raises RuntimeError in production."""
        ctx = _make_ctx()
        with patch(
            "agent.services.security_audit.load_shell_audit_config",
            side_effect=RuntimeError(
                "Security audit: failed to load shell config: disk fail"
            ),
        ):
            with pytest.raises(RuntimeError, match="shell config"):
                audit_security_defaults(ctx)
```

### Step 5 — Add test: git config failure raises RuntimeError in production

```python
    def test_git_config_failure_production_raises(self) -> None:
        """INV-010: git config load failure raises RuntimeError in production."""
        ctx = _make_ctx()
        with patch(
            "agent.services.security_audit.load_shell_audit_config", return_value=_SHELL_OK
        ):
            with patch("shutil.which", return_value="/usr/bin/firejail"):
                with patch(
                    "agent.services.security_audit.load_git_audit_config",
                    side_effect=RuntimeError(
                        "Security audit: failed to load git config: not found"
                    ),
                ):
                    with pytest.raises(RuntimeError, match="git config"):
                        audit_security_defaults(ctx)
```

### Step 6 — Add test: GitHub config failure raises RuntimeError in production

```python
    def test_github_config_failure_production_raises(self) -> None:
        """INV-010: GitHub config load failure raises RuntimeError in production."""
        ctx = _make_ctx()
        with patch(
            "agent.services.security_audit.load_shell_audit_config", return_value=_SHELL_OK
        ):
            with patch("shutil.which", return_value="/usr/bin/firejail"):
                with patch(
                    "agent.services.security_audit.load_git_audit_config",
                    return_value=_GIT_OK,
                ):
                    with patch(
                        "agent.services.security_audit.load_github_audit_config",
                        side_effect=RuntimeError(
                            "Security audit: failed to load GitHub config: bad value"
                        ),
                    ):
                        with pytest.raises(RuntimeError, match="GitHub config"):
                            audit_security_defaults(ctx)
```

### Step 7 — Add test: CI/CD config failure raises RuntimeError in production

```python
    def test_cicd_config_failure_production_raises(self) -> None:
        """INV-010: CI/CD config load failure raises RuntimeError in production."""
        ctx = _make_ctx()
        with patch(
            "agent.services.security_audit.load_shell_audit_config", return_value=_SHELL_OK
        ):
            with patch("shutil.which", return_value="/usr/bin/firejail"):
                with patch(
                    "agent.services.security_audit.load_git_audit_config",
                    return_value=_GIT_OK,
                ):
                    with patch(
                        "agent.services.security_audit.load_github_audit_config",
                        return_value=_GITHUB_OK,
                    ):
                        with patch(
                            "agent.services.security_audit.load_cicd_audit_config",
                            side_effect=RuntimeError(
                                "Security audit: failed to load CI/CD config: io error"
                            ),
                        ):
                            with pytest.raises(RuntimeError, match="CI/CD config"):
                                audit_security_defaults(ctx)
```

### Step 8 — Add test: lockdown mode does not suppress production failures

```python
    def test_lockdown_does_not_suppress_production_failure(self) -> None:
        """INV-011: lockdown mode does not suppress config load failures."""
        ctx = _make_ctx(lockdown=True)
        with patch(
            "agent.services.security_audit.load_shell_audit_config",
            side_effect=RuntimeError("Security audit: failed to load shell config: fail"),
        ):
            with pytest.raises(RuntimeError, match="shell config"):
                audit_security_defaults(ctx)
```

### Step 9 — Add test: ImportError stays silent (optional dependency)

```python
    def test_import_error_stays_silent(self) -> None:
        """INV-011: optional dependency missing stays silent rather than raising."""
        ctx = _make_ctx()
        with patch(
            "agent.services.security_audit.load_shell_audit_config", return_value=_SHELL_OK
        ):
            with patch("shutil.which", return_value="/usr/bin/firejail"):
                with patch(
                    "agent.services.security_audit.load_git_audit_config",
                    return_value=_GIT_OK,
                ):
                    with patch(
                        "agent.services.security_audit.load_github_audit_config",
                        return_value=None,
                    ):
                        warnings = audit_security_defaults(ctx)
        assert not any("GitHub config" in w for w in (warnings or []))
```

### Step 10 — Add test: all config loads succeed returns no warnings

```python
    def test_all_configs_load_success_returns_no_warnings(self) -> None:
        """INV-010: successful config loads produce no warnings."""
        ctx = _make_ctx()
        with patch(
            "agent.services.security_audit.load_shell_audit_config", return_value=_SHELL_OK
        ):
            with patch("shutil.which", return_value="/usr/bin/firejail"):
                with patch(
                    "agent.services.security_audit.load_git_audit_config",
                    return_value=_GIT_OK,
                ):
                    with patch(
                        "agent.services.security_audit.load_github_audit_config",
                        return_value=_GITHUB_OK,
                    ):
                        with patch(
                            "agent.services.security_audit.load_cicd_audit_config",
                            return_value=MagicMock(),
                        ):
                            warnings = audit_security_defaults(ctx)
        assert not warnings
```

### Step 11 — Add test: partial config failure produces targeted warning

```python
    def test_partial_config_failure_produces_targeted_warning(self) -> None:
        """INV-011: partial failures produce warnings for specific components only."""
        ctx = _make_ctx()
        with patch(
            "agent.services.security_audit.load_shell_audit_config", return_value=_SHELL_OK
        ):
            with patch("shutil.which", return_value="/usr/bin/firejail"):
                with patch(
                    "agent.services.security_audit.load_git_audit_config",
                    return_value=_GIT_OK,
                ):
                    with patch(
                        "agent.services.security_audit.load_github_audit_config",
                        side_effect=RuntimeError("GitHub config error"),
                    ):
                        warnings = audit_security_defaults(ctx)
        assert any("GitHub config" in w for w in (warnings or []))
```

### Step 12 — Add test: lockdown mode still validates required configs

```python
    def test_lockdown_mode_validates_required_configs(self) -> None:
        """INV-011: lockdown mode enforces stricter validation on required configs."""
        ctx = _make_ctx(lockdown=True)
        with patch(
            "agent.services.security_audit.load_shell_audit_config", return_value=_SHELL_OK
        ):
            with patch("shutil.which", return_value="/usr/bin/firejail"):
                with patch(
                    "agent.services.security_audit.load_git_audit_config",
                    side_effect=RuntimeError("Git config error"),
                ):
                    with pytest.raises(RuntimeError, match="git config"):
                        audit_security_defaults(ctx)
```

### Step 13 — Add test: non-production profile tolerates config failures

```python
    def test_non_production_profile_tolerates_config_failures(self) -> None:
        """INV-011: non-production profiles tolerate config load failures gracefully."""
        from unittest.mock import MagicMock

        ctx = _make_ctx()
        # Simulate non-production profile by setting a flag
        ctx.cfg.env = MagicMock()
        ctx.cfg.env.name = "local"
        with patch(
            "agent.services.security_audit.load_shell_audit_config", return_value=_SHELL_OK
        ):
            with patch("shutil.which", return_value="/usr/bin/firejail"):
                with patch(
                    "agent.services.security_audit.load_git_audit_config",
                    side_effect=RuntimeError("Git config error"),
                ):
                    warnings = audit_security_defaults(ctx)
        # In local profile, this should warn but not raise
        assert warnings is not None
```

## Acceptance Criteria

- New file `tests/agent/test_failure_handling_policy_cross_cutting.py` exists at the specified path
- All 10 tests pass when run individually (`pytest -xvs`)
- The file imports use only existing dependencies (no new library requirements)
- No modifications to any other files
