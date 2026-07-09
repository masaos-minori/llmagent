# Implementation: H-9/H-10 — test_agent_cmd_config.py consolidated fixes

Source plans: `plans/20260709-095933_plan.md` (H-9, step 3),
`plans/20260709-100244_plan.md` (H-10, step 7 part).

## Goal

Remove the now-invalid `github_server_url` fixture assignment (H-10), and
add an end-to-end test proving `/reload` prints `[RESTART]` (not `[DEFER]`)
for a real MCP `auth_token` change, exercising the actual
`_classify_mcp_server_changes()` rather than a hand-built outcome (H-9).

## Scope

**Target**: `tests/test_agent_cmd_config.py` —
- Line 153 (`TestPrintConfigValues._make_cfg_ctx`): remove
  `ctx.cfg.mcp.github_server_url = "http://gh"`.
- `class TestCmdReload` (starts line 351): add a new end-to-end test.

Depends on `implementations/20260709-103709_config_reload.py.md`
(`_classify_mcp_server_changes` must exist) and
`implementations/20260709-103718_cmd_config_display.py.md` (display line
removal — otherwise `_print_llm_settings` would still reference the removed
field via `ctx.cfg.mcp.github_server_url`, which would silently read a
MagicMock attribute rather than fail loudly, but the corresponding expected
snippet is being removed from `test_cmd_config_char.py` separately).

## Assumptions

1. `_make_ctx()` (line 23) returns a plain, unconfigured `MagicMock` — every
   other `TestCmdReload` test patches `apply_config_dict`/`ConfigReloadOutcome`
   directly rather than exercising the real classifier, so this is the first
   test in this file to construct a real `ctx.cfg.mcp.mcp_servers` dict —
   verified by reading all of `TestCmdReload` (lines 351-492).
2. Since `ctx` is an unconfigured `MagicMock`, every other `cfg` attribute
   `ConfigReloadService.apply_config_dict()` touches (e.g.
   `ctx.cfg.tool.masked_fields`, `ctx.cfg.llm.*`) auto-vivifies as a
   `MagicMock` and does not raise — matching the same pattern already used
   successfully in `tests/test_config_reload.py::TestMcpServerChangeClassification._make_svc`.

## Implementation

### Target file

`tests/test_agent_cmd_config.py`

### Procedure

#### Step 1: Remove the fixture line (H-10)

In `TestPrintConfigValues._make_cfg_ctx` (around line 153), delete:
```python
ctx.cfg.mcp.github_server_url = "http://gh"
```

#### Step 2: Add the end-to-end reload test (H-9)

Add to `class TestCmdReload`, after `test_reload_shows_needs_restart` (or
any convenient position in that class):

```python
def test_reload_mcp_auth_token_change_prints_restart_not_defer(
    self, capsys: Any
) -> None:
    from unittest.mock import patch

    from shared.mcp_config import McpServerConfig, TransportType

    old_srv = McpServerConfig(
        transport=TransportType.HTTP,
        url="http://localhost:8080",
        cmd=[],
        auth_token="old",
    )
    ctx = _make_ctx()
    ctx.conv.history = []
    ctx.cfg.mcp.mcp_servers = {"svc": old_srv}
    cmd = _FakeCmd(ctx)

    new_cfg = {
        "mcp_servers": {
            "svc": {
                "transport": "http",
                "url": "http://localhost:8080",
                "auth_token": "new",
            }
        }
    }
    with patch("shared.config_loader.ConfigLoader.load_all", return_value=new_cfg):
        cmd._cmd_reload()

    out = capsys.readouterr().out
    assert "[RESTART] - mcp/svc.auth_token" in out
    assert "[DEFER]" not in out
```

### Method

- Step 1 is a one-line deletion.
- Step 2 is additive only — no existing `TestCmdReload` test is modified,
  since none of them construct a real `mcp_servers` dict today.
- If `_build_mcp_servers()` requires additional TOML keys beyond
  `transport`/`url`/`auth_token` to construct a valid `McpServerConfig` from
  the raw `new_cfg` dict (e.g. defaults for `cmd`), adjust `new_cfg["mcp_servers"]["svc"]`
  accordingly — verify against `scripts/shared/mcp_config.py::_build_single_server()`
  during implementation.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Fixture line removed | `grep -n "github_server_url" tests/test_agent_cmd_config.py` | no matches |
| New test present | `grep -n "test_reload_mcp_auth_token_change_prints_restart_not_defer" tests/test_agent_cmd_config.py` | 1 match |
| Full file run | `uv run pytest tests/test_agent_cmd_config.py -v` | all pass |
