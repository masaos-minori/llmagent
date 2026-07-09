"""tests/test_config_reload.py
Error-path tests for ConfigReloadService.apply_config().
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from shared.mcp_config import StartupMode


@pytest.fixture()
def svc() -> object:
    from agent.services.config_reload import ConfigReloadService

    ctx = MagicMock()
    ctx.cfg.tool.system_prompts = {}
    ctx.cfg.tool.masked_fields = []
    ctx.cfg.llm.llm_url = ""
    ctx.cfg.llm.llm_max_tokens = 1000
    ctx.cfg.llm.llm_temperature = 0.7
    ctx.cfg.llm.title_llm_temperature = 0.5
    ctx.cfg.llm.title_llm_max_tokens = 50
    ctx.cfg.llm.stream = True
    ctx.cfg.llm.stream_retry_limit = 3
    ctx.cfg.llm.sse_heartbeat_timeout = 30
    ctx.cfg.llm.sse_reconnect_max = 5
    ctx.cfg.llm.sse_reconnect_delay = 1.0
    ctx.cfg.llm.sse_malformed_retry = 1
    ctx.cfg.approval.tool_safety_tiers = {}
    ctx.cfg.approval.require_approval_for = []
    ctx.cfg.approval.plan_mode_enabled = False
    ctx.cfg.mcp.mcp_servers = {}
    ctx.services_required.memory = None
    ctx.services_required.embedding = None
    ctx.services_required.retriever = None
    ctx.services_required.llm = None
    return ConfigReloadService(ctx)


class TestApplyConfig:
    def test_invalid_masked_fields_type_raises(self, svc: object) -> None:
        from agent.services.exceptions import ConfigReloadValidationError
        from agent.services.models import ConfigReloadRequest

        req = ConfigReloadRequest(masked_fields="not-a-list")  # type: ignore[arg-type]
        with pytest.raises(ConfigReloadValidationError):
            svc.apply_config(req)  # type: ignore[attr-defined]

    def test_valid_masked_fields_does_not_raise(self, svc: object) -> None:
        from unittest.mock import patch

        from agent.services.config_reload import ConfigReloadOutcome
        from agent.services.models import ConfigReloadRequest

        req = ConfigReloadRequest(masked_fields=["api_key", "token"])
        with patch.object(
            type(svc), "apply_config_dict", return_value=ConfigReloadOutcome()
        ):
            result = svc.apply_config(req)  # type: ignore[attr-defined]
        assert result is not None

    def test_empty_request_does_not_raise(self, svc: object) -> None:
        from unittest.mock import patch

        from agent.services.config_reload import ConfigReloadOutcome
        from agent.services.models import ConfigReloadRequest

        req = ConfigReloadRequest()
        with patch.object(
            type(svc), "apply_config_dict", return_value=ConfigReloadOutcome()
        ):
            result = svc.apply_config(req)  # type: ignore[attr-defined]
        assert result is not None

    def test_req_to_dict_skips_none_fields(self) -> None:
        from agent.services.config_reload import ConfigReloadService
        from agent.services.models import ConfigReloadRequest

        req = ConfigReloadRequest(masked_fields=["key"])
        d = ConfigReloadService._req_to_dict(req)
        assert "masked_fields" in d
        assert "mcp_servers" not in d
        assert "approval" not in d


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
            ("tool_names", ["changed_tool"]),
            ("cmd", ["changed", "cmd"]),
            ("env", {"CHANGED": "1"}),
        ],
    )
    def test_single_field_change_detected(
        self, field_name: str, new_value: object
    ) -> None:
        from agent.services.config_reload import _diff_mcp_server_config

        old, new = self._make_pair()
        before_old = old.__dict__.copy()
        setattr(new, field_name, new_value)

        assert _diff_mcp_server_config(old, new) == [field_name]
        assert old.__dict__ == before_old  # never mutated

    def test_startup_mode_change_detected(self) -> None:
        from agent.services.config_reload import _diff_mcp_server_config
        from shared.mcp_config import StartupMode

        old, new = self._make_pair()
        new.startup_mode = StartupMode.SUBPROCESS
        assert _diff_mcp_server_config(old, new) == ["startup_mode"]



class TestMcpServerChangeClassification:
    """_classify_mcp_server_changes reports every MCP definition change as
    restart-required and never mutates ctx.cfg.mcp.mcp_servers (H-1/H-3/H-4/H-5/H-7)."""

    def _make_svc(self, old_auth: str = "", old_startup: str = "persistent") -> object:
        from agent.services.config_reload import ConfigReloadService
        from shared.mcp_config import McpServerConfig, StartupMode, TransportType

        cmd = ["python", "s.py"] if old_startup == "subprocess" else []
        old_srv = McpServerConfig(
            transport=TransportType.HTTP,
            url="http://localhost:8080",
            cmd=cmd,
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

    def test_auth_token_change_reports_restart_not_deferred(self) -> None:
        from shared.mcp_config import McpServerConfig, TransportType

        svc, old_srv = self._make_svc(old_auth="old_token")
        new_srv = McpServerConfig(
            transport=TransportType.HTTP, url="http://localhost:8080", cmd=[],
            auth_token="new_token",
        )
        result = self._run(svc, {"svc": new_srv})

        assert "mcp/svc.auth_token" in result.needs_restart
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
        cmd = ["python", "s.py"] if new_mode == StartupMode.SUBPROCESS else []
        new_srv = McpServerConfig(
            transport=TransportType.HTTP,
            url="http://localhost:8080",
            cmd=cmd,
            startup_mode=new_mode,
        )
        result = self._run(svc, {"svc": new_srv})

        assert "mcp/svc.startup_mode" in result.needs_restart
        assert not any("startup_mode" in item for item in result.applied)
        assert old_srv.startup_mode == old_mode

    def test_removed_server_reports_restart(self) -> None:
        svc, old_srv = self._make_svc()
        result = self._run(svc, {})  # new config has no servers at all

        assert "mcp/svc (removed server)" in result.needs_restart
        assert result.skipped == []

    def test_rename_reports_remove_and_add(self) -> None:
        from shared.mcp_config import McpServerConfig, TransportType

        svc, old_srv = self._make_svc()
        renamed_srv = McpServerConfig(
            transport=TransportType.HTTP, url="http://localhost:8080", cmd=[]
        )
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


class TestStartupOnlyDetection:
    """_detect_startup_only classifies use_memory_layer / plugin_strict changes."""

    def _make_svc(
        self, use_memory_layer: bool = False, plugin_strict: bool = False
    ) -> object:
        from agent.services.config_reload import ConfigReloadService

        ctx = MagicMock()
        ctx.cfg.memory.use_memory_layer = use_memory_layer
        ctx.cfg.tool.plugin_strict = plugin_strict
        return ConfigReloadService(ctx)

    def test_use_memory_layer_change_populates_startup_only(self) -> None:
        svc = self._make_svc(use_memory_layer=False)
        result = svc._detect_startup_only({"use_memory_layer": True})
        assert "use_memory_layer" in result

    def test_plugin_strict_change_populates_startup_only(self) -> None:
        svc = self._make_svc(plugin_strict=False)
        result = svc._detect_startup_only({"plugin_strict": True})
        assert "plugin_strict" in result

    def test_no_change_returns_empty(self) -> None:
        svc = self._make_svc(use_memory_layer=True, plugin_strict=True)
        result = svc._detect_startup_only(
            {"use_memory_layer": True, "plugin_strict": True}
        )
        assert result == []

    def test_missing_key_returns_empty(self) -> None:
        svc = self._make_svc(use_memory_layer=False, plugin_strict=False)
        result = svc._detect_startup_only({})
        assert result == []

    def test_both_changes_populates_both(self) -> None:
        svc = self._make_svc(use_memory_layer=False, plugin_strict=False)
        result = svc._detect_startup_only(
            {"use_memory_layer": True, "plugin_strict": True}
        )
        assert "use_memory_layer" in result
        assert "plugin_strict" in result
