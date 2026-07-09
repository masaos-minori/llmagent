# Implementation: H-10 — config_dataclasses.py remove github_server_url field

Source plan: `plans/20260709-100244_plan.md` (H-10, Implementation step 1).

## Goal

Remove the legacy `MCPConfig.github_server_url` field, since the GitHub MCP
endpoint's single canonical source is `mcp_servers.github.url`.

## Scope

**Target**: `scripts/agent/config_dataclasses.py`, line 353
(`MCPConfig` dataclass).

Must land together with (or after) `implementations/20260709-103717_config_builders.py.md`
and `implementations/20260709-103709_config_reload.py.md` — both reference
this field and must stop doing so in the same change window, or `mypy` will
fail on the dangling reference.

## Assumptions

1. `cfg.mcp.github_server_url` is read nowhere in `scripts/` besides
   `config_dataclasses.py` (this field), `config_builders.py` (construction),
   `config_reload.py` (reload wiring), and `cmd_config_display.py` (display)
   — verified by `grep -rn "github_server_url" scripts/ --include=*.py`
   while planning H-10.

## Implementation

### Target file

`scripts/agent/config_dataclasses.py`

### Procedure

#### Step 1: Delete the field

Current (`MCPConfig`, around line 349-357):
```python
@dataclass
class MCPConfig:
    """MCP server lifecycle and watchdog settings."""

    mcp_servers: dict[str, McpServerConfig] = field(default_factory=dict)
    # Probe interval in seconds; 0 disables watchdog. Default 30s for production self-healing.
    mcp_watchdog_interval: float = 30.0
    mcp_watchdog_max_restarts: int = 3
    github_server_url: str = "http://127.0.0.1:8006"
    # Deployment security profile: "local" (auth optional) or "production" (auth required for HTTP).
    security_profile: SecurityProfile = SecurityProfile.LOCAL
    # Set to True to suppress deny-all startup warnings when deny-all is intentional.
    security_lockdown_enabled: bool = False
```

Delete the `github_server_url: str = "http://127.0.0.1:8006"` line only —
all other fields unchanged.

### Method

- Single-line deletion.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Field removed | `grep -n "github_server_url" scripts/agent/config_dataclasses.py` | no matches |
| Type check (after all github_server_url docs land) | `uv run mypy scripts/agent/config_dataclasses.py scripts/agent/config_builders.py scripts/agent/services/config_reload.py scripts/agent/commands/cmd_config_display.py` | no new errors |
