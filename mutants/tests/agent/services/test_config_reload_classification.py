"""tests/test_config_reload_classification.py
Classification snapshot tests for /reload config fields.

Tests each field's classification bucket: startup_only, applied, deferred, needs_restart.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from agent.services.config_reload import ConfigReloadService


def _make_ctx() -> MagicMock:
    ctx = MagicMock()
    ctx.cfg.memory.use_memory_layer = False
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


def test_detect_startup_only_empty_dict(svc: ConfigReloadService) -> None:
    result = svc._detect_startup_only({})
    assert result == []


def test_detect_startup_only_non_startup_keys_ignored(svc: ConfigReloadService) -> None:
    result = svc._detect_startup_only({"llm_temperature": 0.3, "llm_max_tokens": 8192})
    assert result == []
