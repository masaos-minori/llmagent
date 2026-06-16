# Implementation: Require auth_token in production MCP deployments (req 13)

## Goal

Enforce Bearer-token authentication for HTTP MCP servers when the agent runs in production mode, while keeping auth optional for local/dev profiles.

## Scope

- `scripts/shared/mcp_config.py` — add `SecurityProfile` enum
- `scripts/agent/config_dataclasses.py` — add `security_profile` to `MCPConfig`
- `scripts/agent/config_builders.py` — read `security_profile` from config
- `scripts/agent/repl_health.py` — hard-fail in production mode for HTTP servers without auth_token
- `scripts/agent/repl.py` — pass security profile to audit function
- `tests/test_repl_health.py` — add tests for production-mode auth enforcement
- `config/agent.toml` — add `security_profile` field (default: "local")
- `docs/04_mcp_05_security_and_safety_model.md` — document production vs local security profiles

## Assumptions

1. `security_profile` is nested under `MCPConfig` (not top-level AgentConfig).
2. Default value is `"local"` to avoid breaking existing development workflows.
3. The existing `audit_security_defaults()` function in `repl_health.py` is the enforcement point.
4. "Hard failure" means raising `RuntimeError` during `_check_services()`, aborting REPL startup.

## Implementation

### Target files

| File | Step | Change |
|---|---|---|
| `scripts/shared/mcp_config.py` | 1 | Add `SecurityProfile` enum |
| `scripts/agent/config_dataclasses.py` | 2 | Add `security_profile` to `MCPConfig` |
| `scripts/agent/config_builders.py` | 3 | Read `security_profile` from config |
| `scripts/agent/repl_health.py` | 4 | Hard-fail in production mode |
| `scripts/agent/repl.py` | 5 | Pass security profile to audit function |
| `tests/test_repl_health.py` | 6 | Add tests |
| `config/agent.toml` | 7 | Add `security_profile = "local"` |
| `docs/04_mcp_05_security_and_safety_model.md` | 8 | Document security profile |

### Procedure

#### Step 1: Add `SecurityProfile` enum to `mcp_config.py`

**File:** `scripts/shared/mcp_config.py`

Add after the existing `HealthcheckMode` class (around line 35):

```python
class SecurityProfile(StrEnum):
    """Deployment security profile."""

    LOCAL = "local"
    PRODUCTION = "production"
```

No `__post_init__` needed on the enum itself. String-to-enum conversion will happen in `MCPConfig.__post_init__` or in the config builder.

#### Step 2: Add `security_profile` field to `MCPConfig`

**File:** `scripts/agent/config_dataclasses.py`

Add import at top (with existing imports from shared.mcp_config):
```python
from shared.mcp_config import McpServerConfig, SecurityProfile
```

In `MCPConfig` dataclass, add field after `github_url`:
```python
security_profile: SecurityProfile = SecurityProfile.LOCAL
```

Add `__post_init__` validation to handle str inputs from config files:
```python
def __post_init__(self) -> None:
    if not isinstance(self.security_profile, SecurityProfile):
        self.security_profile = SecurityProfile(self.security_profile)
```

#### Step 3: Read `security_profile` from config in `config_builders.py`

**File:** `scripts/agent/config_builders.py`

In the `_build_mcp_servers` import line, also import `SecurityProfile`:
```python
from shared.mcp_config import (
    _build_mcp_servers,  # noqa: F401 — re-exported via agent.config
    SecurityProfile,  # noqa: F401 — used by build_agent_config
)
```

In `build_agent_config()`, add `security_profile` to the `MCPConfig()` call (around line 261):
```python
mcp=MCPConfig(
    mcp_servers=_build_mcp_servers(cfg),
    mcp_watchdog_interval=float(cfg.get("mcp_watchdog_interval", 0.0)),
    mcp_watchdog_max_restarts=int(cfg.get("mcp_watchdog_max_restarts", 3)),
    github_url=cfg.get("github_server_url", "http://127.0.0.1:8006"),
    security_profile=SecurityProfile(cfg.get("security_profile", "local")),
),
```

#### Step 4: Modify `audit_security_defaults()` in `repl_health.py`

**File:** `scripts/agent/repl_health.py`

Add import at top:
```python
from shared.mcp_config import SecurityProfile
```

Update the function signature:
```python
def audit_security_defaults(ctx: AgentContext, production_mode: bool = False) -> list[str]:
    """Audit security-related configuration defaults and return warning strings.

    In production mode (production_mode=True), HTTP servers without auth_token
    raise RuntimeError instead of returning a warning.
    """
```

Log startup behavior at the start:
```python
    profile_label = "PRODUCTION" if production_mode else "LOCAL"
    logger.info("Security profile: %s — auth required for HTTP servers: %s",
                profile_label, "yes" if production_mode else "no")
```

In the auth_token check loop, replace warning-only behavior with hard-fail in production:
```python
    # Check auth_token settings
    violations: list[str] = []
    for key, srv_cfg in ctx.cfg.mcp.mcp_servers.items():
        if not srv_cfg.auth_token and srv_cfg.transport == "http" and srv_cfg.url:
            msg = f"{key}: no auth_token configured (auth disabled)"
            violations.append(msg)

    if production_mode and violations:
        servers_str = "; ".join(violations)
        raise RuntimeError(
            f"Production mode requires auth_token on all HTTP MCP servers. "
            f"Violations: {servers_str}"
        )

    for v in violations:
        logger.warning("Security: %s", v)
```

Remove the old `for w in warnings:` logging loop at the end of the function (since we now log per-violation above and return `warnings` list). Keep the `warnings` list return unchanged for backward compatibility.

#### Step 5: Update `repl.py`

**File:** `scripts/agent/repl.py`

In `_check_services()`, derive production mode and pass it:
```python
async def _check_services(self) -> None:
    """Probe LLM / Embed service health, validate tool definitions, and audit security defaults."""
    production_mode = self._ctx.cfg.mcp.security_profile == SecurityProfile.PRODUCTION
    audit_security_defaults(self._ctx, production_mode=production_mode)
```

Add import at top:
```python
from shared.mcp_config import SecurityProfile
```

#### Step 6: Add tests in `tests/test_repl_health.py`

**File:** `tests/test_repl_health.py`

Add new test class:
```python
class TestAuditSecurityDefaults:
    """Tests for audit_security_defaults with production mode enforcement."""

    def _make_ctx(
        self,
        servers: dict[str, dict] | None = None,
        security_profile: str = "local",
    ) -> AgentContext:
        """Build a minimal AgentContext for testing."""
        from agent.config_builders import build_agent_config
        from agent.context import AgentContext

        raw_servers: dict[str, Any] = {}
        if servers:
            for key, vals in servers.items():
                raw_servers[key] = {
                    "transport": vals.get("transport", "http"),
                    "url": vals.get("url", "http://127.0.0.1:8000"),
                    "auth_token": vals.get("auth_token", ""),
                    "openrc_service": "",
                    "startup_mode": "subprocess",
                }

        cfg_override = {
            "mcp_servers": raw_servers,
            "security_profile": security_profile,
            "tool_definitions": [],
        }
        agent_cfg = build_agent_config(cfg_override)
        ctx = AgentContext()
        ctx.cfg = agent_cfg
        return ctx

    def test_local_mode_no_auth_returns_warnings(self) -> None:
        """Local mode with missing auth_token returns warnings, no exception."""
        ctx = self._make_ctx(
            servers={"web_search": {"auth_token": ""}},
            security_profile="local",
        )
        warnings = audit_security_defaults(ctx, production_mode=False)
        assert len(warnings) == 1
        assert "web_search" in warnings[0]

    def test_production_mode_no_auth_raises(self) -> None:
        """Production mode with missing auth_token raises RuntimeError."""
        ctx = self._make_ctx(
            servers={"web_search": {"auth_token": ""}, "file_read": {"auth_token": ""}},
            security_profile="production",
        )
        with pytest.raises(RuntimeError, match="Production mode requires auth_token"):
            audit_security_defaults(ctx, production_mode=True)

    def test_production_mode_all_authed_no_error(self) -> None:
        """Production mode with all HTTP servers having auth_token → no error."""
        ctx = self._make_ctx(
            servers={
                "web_search": {"auth_token": "tok1"},
                "file_read": {"auth_token": "tok2"},
            },
            security_profile="production",
        )
        warnings = audit_security_defaults(ctx, production_mode=True)
        assert warnings == []

    def test_stdio_servers_ignored_in_production(self) -> None:
        """Stdio servers are not checked for auth_token even in production mode."""
        ctx = self._make_ctx(
            servers={
                "stdio_server": {"transport": "stdio", "auth_token": ""},
            },
            security_profile="production",
        )
        warnings = audit_security_defaults(ctx, production_mode=True)
        assert warnings == []

    def test_security_profile_enum_parsing(self) -> None:
        """SecurityProfile enum correctly parses string values."""
        assert SecurityProfile("local") == SecurityProfile.LOCAL
        assert SecurityProfile("production") == SecurityProfile.PRODUCTION
```

Also add a test for the `SecurityProfile` enum in `tests/test_mcp_config.py`:
```python
class TestSecurityProfile:
    def test_local_default(self) -> None:
        from shared.mcp_config import SecurityProfile
        assert SecurityProfile.LOCAL == "local"

    def test_production_value(self) -> None:
        from shared.mcp_config import SecurityProfile
        assert SecurityProfile.PRODUCTION == "production"

    def test_invalid_value_raises(self) -> None:
        from shared.mcp_config import SecurityProfile
        with pytest.raises(ValueError):
            SecurityProfile("invalid")
```

#### Step 7: Update `config/agent.toml`

**File:** `config/agent.toml`

Add near the `[mcp_servers]` section header (around line 294):
```toml
# ---- mcp_servers ----
# Security profile: "local" (auth optional) or "production" (auth required for HTTP).
security_profile = "local"
```

#### Step 8: Update documentation

**File:** `docs/04_mcp_05_security_and_safety_model.md`

Add a new section after the existing Authentication section (around line 153):

```markdown
## Security Profile (`security_profile`)

```toml
# In config/agent.toml [mcp_servers] section
security_profile = "local"   # or "production"
```

Controls whether Bearer-token authentication is required for HTTP MCP servers:

| Profile | Behavior |
|---|---|
| `local` (default) | Auth optional. Missing `auth_token` on HTTP servers produces a warning at startup. |
| `production` | Auth required. Startup fails with `RuntimeError` if any HTTP server lacks `auth_token`. |

Stdio servers are always exempt from this check regardless of profile.

**Enforcement point:** `audit_security_defaults()` in `agent/repl_health.py` raises during startup when `security_profile == "production"` and an HTTP server has an empty `auth_token`.
```

## Validation plan

| Check | Tool | Target |
|---|---|---|
| Format | `uv run ruff format scripts/` | clean |
| Lint | `uv run ruff check scripts/ --fix && uv run ruff check scripts/` | 0 errors |
| Type check | `uv run mypy scripts/shared/mcp_config.py scripts/agent/config_dataclasses.py scripts/agent/config_builders.py scripts/agent/repl_health.py scripts/agent/repl.py` | no new errors |
| Architecture | `PYTHONPATH=scripts uv run lint-imports` | 0 violations |
| Security | `uv run bandit -r scripts/` | no HIGH unaddressed |
| Tests | `uv run pytest tests/test_repl_health.py tests/test_mcp_config.py -v` | all pass |
| Pre-commit | `uv run pre-commit run --all-files` | pass |
