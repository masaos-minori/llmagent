"""tests/test_config_reload_classification.py
Classification snapshot tests for /reload config fields.

Tests each field's classification bucket: startup_only, applied, deferred, needs_restart.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from agent.services.config_reload import ConfigReloadOutcome, ConfigReloadService


def _make_ctx() -> MagicMock:
    ctx = MagicMock()
    ctx.cfg.memory.use_memory_layer = False
    ctx.cfg.tool.plugin_strict = False
    ctx.cfg.llm.llm_temperature = 0.7
    ctx.cfg.llm.llm_max_tokens = 4096
    ctx.cfg.llm.context_char_limit = 100_000
    ctx.cfg.tool.tool_cache_ttl = 60.0
    ctx.cfg.mcp.mcp_servers = {}
    ctx.cfg.tool.system_prompts = {}
    ctx.cfg.tool.masked_fields = []
    ctx.services_required.llm = None
    ctx.services_required.hist_mgr = None
    ctx.services_required.tools = None
    return ctx


@pytest.fixture
def ctx() -> MagicMock:
    return _make_ctx()


@pytest.fixture
def svc(ctx: MagicMock) -> ConfigReloadService:
    return ConfigReloadService(ctx)


# --- Direct unit tests of _detect_startup_only ---


@pytest.mark.parametrize(
    "key,new_val",
    [
        ("use_memory_layer", True),
        ("plugin_strict", True),
    ],
)
def test_detect_startup_only_changed_field(
    svc: ConfigReloadService, key: str, new_val: object
) -> None:
    result = svc._detect_startup_only({key: new_val})
    assert key in result


@pytest.mark.parametrize(
    "key,val",
    [
        ("use_memory_layer", False),
        ("plugin_strict", False),
    ],
)
def test_detect_startup_only_unchanged_not_reported(
    svc: ConfigReloadService, key: str, val: object
) -> None:
    result = svc._detect_startup_only({key: val})
    assert key not in result


def test_detect_startup_only_empty_dict(svc: ConfigReloadService) -> None:
    result = svc._detect_startup_only({})
    assert result == []


def test_detect_startup_only_non_startup_keys_ignored(svc: ConfigReloadService) -> None:
    result = svc._detect_startup_only({"llm_temperature": 0.3, "llm_max_tokens": 8192})
    assert result == []


# --- Integration: apply_config_dict correctly classifies fields ---


def test_apply_config_dict_use_memory_layer_in_startup_only(
    svc: ConfigReloadService, ctx: MagicMock
) -> None:
    ctx.cfg.memory.use_memory_layer = False
        outcome = svc.apply_config_dict({"use_memory_layer": True})
    assert "use_memory_layer" in outcome.startup_only


def test_apply_config_dict_plugin_strict_in_startup_only(
    svc: ConfigReloadService, ctx: MagicMock
) -> None:
    ctx.cfg.tool.plugin_strict = False
<<<<<<< HEAD
    with patch.object(
        svc, "_classify_mcp_server_changes", return_value=ConfigReloadOutcome()
    ):
=======
    with patch.object(svc, "_classify_mcp_server_changes", return_value=ConfigReloadOutcome()):
>>>>>>> 516c4f1c (refactor(mcp): replace mutating _apply_mcp_url_reload() with pure _classify_mcp_server_changes() + _diff_mcp_server_config())
