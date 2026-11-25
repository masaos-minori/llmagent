"""tests/test_config_reload_classification.py
Classification snapshot tests for /reload config fields.

Tests each field's classification bucket: startup_only, applied, deferred, needs_restart.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from agent.services.config_outcome_classification import classify_startup_only_fields
from agent.services.config_reload import ConfigReloadService

from tests.agent._config_test_defaults import reload_candidate, reload_fixture_ctx


@pytest.fixture
def ctx() -> MagicMock:
    """Live config built through the startup entry point, as the reload path expects."""
    return reload_fixture_ctx()


@pytest.fixture
def svc(ctx: MagicMock) -> ConfigReloadService:
    return ConfigReloadService(ctx)


# --- Direct unit tests of classify_startup_only_fields ---


def test_classify_startup_only_no_change(ctx: MagicMock) -> None:
    result = classify_startup_only_fields(ctx, reload_candidate(ctx))
    assert result == []


def test_classify_startup_only_hot_fields_not_reported(ctx: MagicMock) -> None:
    """A hot-reloadable change is applied, so it is never a pending startup-only record."""
    result = classify_startup_only_fields(
        ctx,
        reload_candidate(ctx, llm_temperature=0.3, llm_max_tokens=8192),
    )
    assert result == []


def test_classify_startup_only_hot_reload_false_detected(ctx: MagicMock) -> None:
    ctx.cfg.memory.use_memory_layer = False
    result = classify_startup_only_fields(
        ctx, reload_candidate(ctx, use_memory_layer=True)
    )
    assert [record.field_path for record in result] == ["use_memory_layer"]
    assert result[0].reason == "startup_only"


# --- Direct unit tests of _detect_diagnostics_live_fields ---


def test_detect_diagnostics_live_fields_empty_dict(svc: ConfigReloadService) -> None:
    result = svc._detect_diagnostics_live_fields({})
    assert result == []


def test_detect_diagnostics_live_fields_missing_key_returns_empty(
    svc: ConfigReloadService, ctx: MagicMock
) -> None:
    ctx.cfg.diagnostics.encryption_key = ""
    result = svc._detect_diagnostics_live_fields({"encryption_key": "new_key"})
    assert result == []


def test_detect_diagnostics_live_fields_change_detected(
    svc: ConfigReloadService, ctx: MagicMock
) -> None:
    ctx.cfg.diagnostics.encryption_key = "old_key"
    result: list[str] = svc._detect_diagnostics_live_fields(
        {"diagnostics": {"encryption_key": "new_key"}}
    )
    assert "diagnostics.encryption_key" in result


def test_detect_diagnostics_live_fields_unchanged_not_reported(
    svc: ConfigReloadService, ctx: MagicMock
) -> None:
    ctx.cfg.diagnostics.encryption_key = "same_key"
    result: list[str] = svc._detect_diagnostics_live_fields(
        {"diagnostics": {"encryption_key": "same_key"}}
    )
    assert result == []


def test_diagnostics_change_is_reported_as_always_live(
    svc: ConfigReloadService, ctx: MagicMock
) -> None:
    """REQ-009: a diagnostics change takes effect on the next save, so it is reported
    as always_live rather than as a pending record."""
    from cryptography.fernet import Fernet

    old_key = Fernet.generate_key().decode("utf-8")
    new_key = Fernet.generate_key().decode("utf-8")
    ctx.cfg.diagnostics.encryption_key = old_key
    outcome = svc.apply_config_dict({"diagnostics": {"encryption_key": new_key}})
    assert "diagnostics.encryption_key" in outcome.always_live
    assert ctx.cfg.diagnostics.encryption_key == old_key
