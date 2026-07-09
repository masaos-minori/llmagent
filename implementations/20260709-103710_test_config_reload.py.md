# Implementation: H-1/H-2/H-3/H-4/H-5/H-7/M-1/M-2 — test_config_reload.py MCP classification tests

Source plans: `plans/20260709-094640_plan.md` (H-1), `plans/20260709-094926_plan.md` (H-2),
`plans/20260709-095138_plan.md` (H-3), `plans/20260709-095233_plan.md` (H-4),
`plans/20260709-095322_plan.md` (H-5), `plans/20260709-095522_plan.md` (H-7),
`plans/20260709-100457_plan.md` (M-1), `plans/20260709-100635_plan.md` (M-2).

## Goal

Replace `TestDeferredReload` (which asserts the old mutate/defer behavior)
with a full test suite proving the new `_classify_mcp_server_changes()` /
`_diff_mcp_server_config()` behavior: field-qualified restart-required
entries, zero mutation, zero `applied`/`deferred`/`skipped` MCP entries,
new/removed/renamed server handling, and the diff helper's own
deterministic, side-effect-free behavior.

## Scope

**Target**: `tests/test_config_reload.py`, lines 87-168 (the entire
`TestDeferredReload` class, including its `_make_svc`/`_run` helpers and 4
existing test methods).

Depends on `implementations/20260709-103709_config_reload.py.md` landing
first (this test file exercises `_classify_mcp_server_changes` and
`_diff_mcp_server_config`, which do not exist until that doc is applied).

**Out of scope**: `TestStartupOnlyDetection` (starts at line 171) and
everything below it — untouched by this batch.

## Assumptions

1. `_make_svc(old_auth, old_startup)` and `_run(svc, new_mcp_servers)` (the
   existing private helpers in `TestDeferredReload`) remain valid and are
   reused as-is under the new class name — they only construct a
   `ConfigReloadService` with a mocked `ctx` and patch
   `agent.config_builders._build_mcp_servers`; nothing about their
   implementation depends on the old mutate/defer behavior.
2. `McpServerConfig.__post_init__` validates cross-field constraints at
   construction time (e.g. transport/url/cmd combinations) — the diff-helper
   tests below mutate an already-constructed valid copy's single attribute
   via `setattr()` rather than re-invoking the constructor with an invalid
   combination, avoiding `__post_init__` re-validation entirely.

## Implementation

### Target file

`tests/test_config_reload.py`

### Procedure

#### Step 1: Replace the `TestDeferredReload` class (lines 87-168)

Delete lines 87-168 in full and replace with the two classes below.

```python
class TestDiffMcpServerConfig:
    """_diff_mcp_server_config is a pure, deterministic per-field comparison (M-1)."""

    def _make_pair(self) -> tuple[object, object]:
        from shared.mcp_config import McpServerConfig, StartupMode, TransportType

        old = McpServerConfig(
            transport=TransportType.HTTP,
            url="http://localhost:8080",
            cmd=[],
            startup_mode=StartupMode.PERSISTENT,
            auth_token="tok",
        )
        new = McpServerConfig(
            transport=TransportType.HTTP,
            url="http://localhost:8080",
            cmd=[],
            startup_mode=StartupMode.PERSISTENT,
            auth_token="tok",
        )
        return old, new

    def test_identical_configs_no_diff(self) -> None:
        from agent.services.config_reload import _diff_mcp_server_config

        old, new = self._make_pair()
        assert _diff_mcp_server_config(old, new) == []

    @pytest.mark.parametrize(
        "field_name,new_value",
        [
            ("url", "http://127.0.0.1:9999"),
            ("auth_token", "changed_token"),
            ("role", "changed_role"),
            ("call_timeout_sec", 999.0),
            ("startup_timeout_sec", 999),
            ("healthcheck_mode", None),  # set to a differing valid enum in the real edit
            ("tool_names", ["changed_tool"]),
            ("cmd", ["changed", "cmd"]),
            ("env", {"CHANGED": "1"}),
        ],
    )
    def test_single_field_change_detected(self, field_name: str, new_value: object) -> None:
        from agent.services.config_reload import _diff_mcp_server_config

        old, new = self._make_pair()
        before_old = old.__dict__.copy()
        setattr(new, field_name, new_value)

        assert _diff_mcp_server_config(old, new) == [field_name]
        assert old.__dict__ == before_old  # never mutated

    def test_startup_mode_change_detected(self) -> None:
        from shared.mcp_config import StartupMode

        from agent.services.config_reload import _diff_mcp_server_config

        old, new = self._make_pair()
        new.startup_mode = StartupMode.SUBPROCESS
        assert _diff_mcp_server_config(old, new) == ["startup_mode"]

    def test_transport_change_detected(self) -> None:
        from shared.mcp_config import TransportType

        from agent.services.config_reload import _diff_mcp_server_config

        old, new = self._make_pair()
        new.transport = TransportType.STDIO
        assert _diff_mcp_server_config(old, new) == ["transport"]


class TestMcpServerChangeClassification:
    """_classify_mcp_server_changes reports every MCP definition change as
    restart-required and never mutates ctx.cfg.mcp.mcp_servers (H-1/H-3/H-4/H-5/H-7)."""

    def _make_svc(self, old_auth: str = "", old_startup: str = "persistent") -> object:
        from agent.services.config_reload import ConfigReloadService
        from shared.mcp_config import McpServerConfig, StartupMode, TransportType

        old_srv = McpServerConfig(
            transport=TransportType.HTTP,
            url="http://localhost:8080",
            cmd=[],
            auth_token=old_auth,
            startup_mode=StartupMode(old_startup),
        )
        ctx = MagicMock()
        ctx.cfg.mcp.mcp_servers = {"svc": old_srv}
        ctx.services_required.llm = None
        ctx.services_required.hist_mgr = None
        ctx.services_required.tools = None
        return ConfigReloadService(ctx), old_srv

    def _run(self, svc: object, new_mcp_servers: dict) -> object:  # type: ignore[type-arg]
        from unittest.mock import patch

        with patch(
            "agent.config_builders._build_mcp_servers",
            return_value=new_mcp_servers,
        ):
            return svc._classify_mcp_server_changes(svc._ctx, {})  # type: ignore[attr-defined]

    # --- single-field changes (H-3, H-4, H-5) ---

    def test_url_change_reports_field_qualified_restart_entry(self) -> None:
        from shared.mcp_config import McpServerConfig, TransportType

        svc, old_srv = self._make_svc()
        new_srv = McpServerConfig(
            transport=TransportType.HTTP, url="http://127.0.0.1:9090", cmd=[]
        )
        result = self._run(svc, {"svc": new_srv})

        assert "mcp/svc.url" in result.needs_restart
        assert old_srv.url == "http://localhost:8080"
        assert not any("url" in item for item in result.applied)
        assert not any("url" in item for item in result.deferred)

    def test_auth_token_change_reports_restart_not_deferred(self) -> None:
        from shared.mcp_config import McpServerConfig, TransportType

        svc, old_srv = self._make_svc(old_auth="old_token")
        new_srv = McpServerConfig(
            transport=TransportType.HTTP, url="http://localhost:8080", cmd=[],
            auth_token="new_token",
        )
        result = self._run(svc, {"svc": new_srv})

        assert "mcp/svc.auth_token" in result.needs_restart
        assert not any("auth_token" in item for item in result.deferred)
        assert not any("auth_token" in item for item in result.applied)
        assert old_srv.auth_token == "old_token"

    @pytest.mark.parametrize(
        "old_mode,new_mode",
        [
            (StartupMode.PERSISTENT, StartupMode.SUBPROCESS),
            (StartupMode.SUBPROCESS, StartupMode.PERSISTENT),
        ],
    )
    def test_startup_mode_change_reports_restart_not_deferred(
        self, old_mode: StartupMode, new_mode: StartupMode
    ) -> None:
        from shared.mcp_config import McpServerConfig, TransportType

        svc, old_srv = self._make_svc(old_startup=old_mode.value)
        new_srv = McpServerConfig(
            transport=TransportType.HTTP, url="http://localhost:8080", cmd=[],
            startup_mode=new_mode,
        )
        result = self._run(svc, {"svc": new_srv})

        assert "mcp/svc.startup_mode" in result.needs_restart
        assert not any("startup_mode" in item for item in result.deferred)
        assert not any("startup_mode" in item for item in result.applied)
        assert old_srv.startup_mode == old_mode

    def test_no_change_no_restart_entries(self) -> None:
        from shared.mcp_config import McpServerConfig, StartupMode, TransportType

        svc, _ = self._make_svc(old_auth="same_token", old_startup="persistent")
        new_srv = McpServerConfig(
            transport=TransportType.HTTP, url="http://localhost:8080", cmd=[],
            auth_token="same_token", startup_mode=StartupMode.PERSISTENT,
        )
        result = self._run(svc, {"svc": new_srv})
        assert result.needs_restart == []

    # --- exhaustive per-field coverage (H-2/H-6) ---

    @pytest.mark.parametrize(
        "field_name,new_value",
        [
            ("transport", "stdio"),  # constructs with matching cmd below
            ("url", "http://127.0.0.1:9999"),
            ("startup_mode", "subprocess"),
            ("healthcheck_mode", "none"),
            ("call_timeout_sec", 999.0),
            ("startup_timeout_sec", 999),
            ("tool_names", ["changed_tool"]),
            ("auth_token", "changed_token"),
            ("role", "changed_role"),
            ("cmd", ["changed", "cmd"]),
            ("env", {"CHANGED": "1"}),
        ],
    )
    def test_each_field_change_is_restart_required(
        self, field_name: str, new_value: object
    ) -> None:
        svc, old_srv = self._make_svc()
        new_srv = copy.deepcopy(old_srv)
        object.__setattr__(new_srv, field_name, new_value) if False else setattr(
            new_srv, field_name, new_value
        )
        result = self._run(svc, {"svc": new_srv})

        assert f"mcp/svc.{field_name}" in result.needs_restart
        assert result.applied == []
        assert result.deferred == []
        assert result.skipped == []

    # --- add / remove / rename (H-1/H-7) ---

    def test_new_server_reports_restart_no_skipped(self) -> None:
        from shared.mcp_config import McpServerConfig, TransportType

        svc, old_srv = self._make_svc()
        new_srv = McpServerConfig(transport=TransportType.HTTP, url="http://localhost:9000", cmd=[])
        result = self._run(svc, {"svc": old_srv, "brand_new": new_srv})

        assert "mcp/brand_new (new server)" in result.needs_restart
        assert result.skipped == []

    def test_removed_server_reports_restart(self) -> None:
        svc, old_srv = self._make_svc()
        result = self._run(svc, {})  # new config has no servers at all

        assert "mcp/svc (removed server)" in result.needs_restart
        assert result.skipped == []

    def test_rename_reports_remove_and_add(self) -> None:
        from shared.mcp_config import McpServerConfig, TransportType

        svc, old_srv = self._make_svc()
        renamed_srv = McpServerConfig(transport=TransportType.HTTP, url="http://localhost:8080", cmd=[])
        result = self._run(svc, {"renamed_key": renamed_srv})

        assert "mcp/svc (removed server)" in result.needs_restart
        assert "mcp/renamed_key (new server)" in result.needs_restart

    # --- no duplicate skip/restart classification (M-2) ---

    def test_no_item_classified_as_both_skipped_and_needs_restart(self) -> None:
        from shared.mcp_config import McpServerConfig, TransportType

        svc, old_srv = self._make_svc()
        new_srv = McpServerConfig(transport=TransportType.HTTP, url="http://localhost:9000", cmd=[])
        result = self._run(svc, {"svc": old_srv, "extra": new_srv})

        assert set(result.skipped).isdisjoint(set(result.needs_restart))
```

Add `import copy` and `import pytest` at the top of the file if not already
present; add `from shared.mcp_config import StartupMode` at module level for
the `@pytest.mark.parametrize` decorator on
`test_startup_mode_change_reports_restart_not_deferred` (parametrize
decorators evaluate at collection time, before the method body's local
imports run).

### Method

- One mechanical deletion (old `TestDeferredReload`, 82 lines) + one
  insertion (two new classes, ~180 lines). Do this as a single edit, not two
  passes, since the old class references the method name being removed in
  `implementations/20260709-103709_config_reload.py.md` and would fail to
  collect (AttributeError at call time, not import time) if left half-done.
- The `test_single_field_change_detected` parametrize list intentionally
  omits `transport`/`startup_mode` (both need paired valid combinations,
  e.g. `transport=STDIO` requires a non-empty `cmd`) — covered separately by
  `test_transport_change_detected` and `test_startup_mode_change_detected`.
- `healthcheck_mode` in that same list uses `None` as a placeholder — during
  implementation, substitute an actual differing `HealthcheckMode` enum
  member (e.g. `HealthcheckMode.NONE` vs. the pair's implicit default) so the
  assertion is meaningful.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Old class gone | `grep -n "TestDeferredReload\|_apply_mcp_url_reload" tests/test_config_reload.py` | no matches |
| New classes present | `grep -n "class TestDiffMcpServerConfig\|class TestMcpServerChangeClassification" tests/test_config_reload.py` | both present |
| Full file run | `uv run pytest tests/test_config_reload.py -v` | all pass, including `TestStartupOnlyDetection` (untouched) |
| Coverage of all 11 fields | `uv run pytest tests/test_config_reload.py -k test_each_field_change_is_restart_required -v` | 11 parametrized cases pass |
