"""tests/test_config_reload.py
Error-path tests for ConfigReloadService.apply_config().
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest


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
    ctx.services.memory = None
    ctx.services.embedding = None
    ctx.services.retriever = None
    ctx.services.llm = None
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


class TestDeferredReload:
    """_apply_mcp_url_reload classifies auth_token / startup_mode changes as deferred."""

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
        ctx.services.llm = None
        ctx.services.hist_mgr = None
        ctx.services.tools = None
        return ConfigReloadService(ctx), old_srv

    def _run(self, svc: object, new_mcp_servers: dict) -> object:  # type: ignore[type-arg]
        from unittest.mock import patch

        with patch(
            "agent.config._build_mcp_servers",
            return_value=new_mcp_servers,
        ):
            return svc._apply_mcp_url_reload(svc._ctx, {})  # type: ignore[attr-defined]

    def test_auth_token_change_populates_deferred(self) -> None:
        from shared.mcp_config import McpServerConfig, TransportType

        svc, _ = self._make_svc(old_auth="old_token")
        new_srv = McpServerConfig(
            transport=TransportType.HTTP,
            url="http://localhost:8080",
            cmd=[],
            auth_token="new_token",
        )
        result = self._run(svc, {"svc": new_srv})
        assert any("auth_token" in item for item in result.deferred)

    def test_startup_mode_change_populates_deferred(self) -> None:
        from shared.mcp_config import McpServerConfig, StartupMode, TransportType

        svc, _ = self._make_svc(old_startup="persistent")
        new_srv = McpServerConfig(
            transport=TransportType.HTTP,
            url="http://localhost:8080",
            cmd=[],
            startup_mode=StartupMode.ONDEMAND,
        )
        result = self._run(svc, {"svc": new_srv})
        assert any("startup_mode" in item for item in result.deferred)

    def test_no_credential_change_no_deferred(self) -> None:
        from shared.mcp_config import McpServerConfig, TransportType

        svc, _ = self._make_svc(old_auth="same_token")
        new_srv = McpServerConfig(
            transport=TransportType.HTTP,
            url="http://localhost:8080",
            cmd=[],
            auth_token="same_token",
        )
        result = self._run(svc, {"svc": new_srv})
        assert result.deferred == []

    def test_deferred_values_stored_in_cfg(self) -> None:
        from shared.mcp_config import McpServerConfig, TransportType

        svc, old_srv = self._make_svc(old_auth="old")
        new_srv = McpServerConfig(
            transport=TransportType.HTTP,
            url="http://localhost:8080",
            cmd=[],
            auth_token="updated",
        )
        self._run(svc, {"svc": new_srv})
        assert old_srv.auth_token == "updated"
