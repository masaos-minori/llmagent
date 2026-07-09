"""tests/test_cmd_config_refactor.py
Unit tests for refactored methods in _ConfigMixin:
  - _set_temperature: valid/invalid value handling, LLM sync
  - _set_max_tokens: valid/invalid value handling, LLM sync
  - _cmd_set: dispatch to setters and unknown parameter handling
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest
from agent.commands.cmd_config import _ConfigMixin


class _Config(_ConfigMixin):
    def __init__(self, ctx: Any) -> None:
        self._ctx = ctx  # type: ignore[assignment]


def _make_ctx() -> Any:
    ctx = MagicMock()
    ctx.cfg.llm.llm_temperature = 0.5
    ctx.cfg.llm.llm_max_tokens = 512
    ctx.services_required.llm = MagicMock()
    return ctx


class TestSetTemperature:
    def test_valid_value_updates_cfg(self, capsys: Any) -> None:
        ctx = _make_ctx()
        cmd = _Config(ctx)
        cmd._set_temperature(ctx, "1.0")
        assert ctx.cfg.llm.llm_temperature == 1.0
        ctx.services_required.llm._temperature == 1.0
        out = capsys.readouterr().out
        assert "temperature set to" in out

    def test_invalid_float_prints_error(self, capsys: Any) -> None:
        ctx = _make_ctx()
        cmd = _Config(ctx)
        cmd._set_temperature(ctx, "not_a_float")
        out = capsys.readouterr().out
        assert "must be a float" in out
        assert ctx.cfg.llm.llm_temperature == 0.5  # unchanged

    def test_out_of_range_prints_error(self, capsys: Any) -> None:
        ctx = _make_ctx()
        cmd = _Config(ctx)
        cmd._set_temperature(ctx, "3.0")
        out = capsys.readouterr().out
        assert "must be a float" in out
        assert ctx.cfg.llm.llm_temperature == 0.5

    def test_boundary_zero_is_valid(self, capsys: Any) -> None:
        ctx = _make_ctx()
        cmd = _Config(ctx)
        cmd._set_temperature(ctx, "0.0")
        assert ctx.cfg.llm.llm_temperature == 0.0

    def test_boundary_two_is_valid(self, capsys: Any) -> None:
        ctx = _make_ctx()
        cmd = _Config(ctx)
        cmd._set_temperature(ctx, "2.0")
        assert ctx.cfg.llm.llm_temperature == 2.0

    def test_llm_none_does_not_raise(self, capsys: Any) -> None:
        ctx = _make_ctx()
        ctx.services_required.llm = None
        cmd = _Config(ctx)
        cmd._set_temperature(ctx, "0.7")
        assert ctx.cfg.llm.llm_temperature == 0.7


class TestSetMaxTokens:
    def test_valid_value_updates_cfg(self, capsys: Any) -> None:
        ctx = _make_ctx()
        cmd = _Config(ctx)
        cmd._set_max_tokens(ctx, "256")
        assert ctx.cfg.llm.llm_max_tokens == 256
        out = capsys.readouterr().out
        assert "max_tokens set to" in out

    def test_invalid_int_prints_error(self, capsys: Any) -> None:
        ctx = _make_ctx()
        cmd = _Config(ctx)
        cmd._set_max_tokens(ctx, "abc")
        out = capsys.readouterr().out
        assert "positive integer" in out
        assert ctx.cfg.llm.llm_max_tokens == 512  # unchanged

    def test_zero_prints_error(self, capsys: Any) -> None:
        ctx = _make_ctx()
        cmd = _Config(ctx)
        cmd._set_max_tokens(ctx, "0")
        out = capsys.readouterr().out
        assert "positive integer" in out

    def test_negative_prints_error(self, capsys: Any) -> None:
        ctx = _make_ctx()
        cmd = _Config(ctx)
        cmd._set_max_tokens(ctx, "-1")
        out = capsys.readouterr().out
        assert "positive integer" in out

    def test_llm_none_does_not_raise(self, capsys: Any) -> None:
        ctx = _make_ctx()
        ctx.services_required.llm = None
        cmd = _Config(ctx)
        cmd._set_max_tokens(ctx, "1024")
        assert ctx.cfg.llm.llm_max_tokens == 1024


class TestCmdSet:
    def test_no_args_prints_current_values(self, capsys: Any) -> None:
        ctx = _make_ctx()
        cmd = _Config(ctx)
        cmd._cmd_set("")
        out = capsys.readouterr().out
        assert "temperature" in out
        assert "max_tokens" in out

    def test_wrong_arg_count_prints_usage(self, capsys: Any) -> None:
        ctx = _make_ctx()
        cmd = _Config(ctx)
        cmd._cmd_set("temperature")
        out = capsys.readouterr().out
        assert "Usage" in out

    def test_unknown_param_prints_error(self, capsys: Any) -> None:
        ctx = _make_ctx()
        cmd = _Config(ctx)
        cmd._cmd_set("unknown 1.0")
        out = capsys.readouterr().out
        assert "Unknown parameter" in out

    def test_dispatches_to_set_temperature(self, capsys: Any) -> None:
        ctx = _make_ctx()
        cmd = _Config(ctx)
        cmd._cmd_set("temperature 0.3")
        assert ctx.cfg.llm.llm_temperature == pytest.approx(0.3)

    def test_dispatches_to_set_max_tokens(self, capsys: Any) -> None:
        ctx = _make_ctx()
        cmd = _Config(ctx)
        cmd._cmd_set("max_tokens 2048")
        assert ctx.cfg.llm.llm_max_tokens == 2048
