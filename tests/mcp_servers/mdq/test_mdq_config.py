"""tests/test_mdq_config.py

Tests covering `MdqConfig` construction/validation, both directly and via
`MdqService.__init__` (config-driven fail-fast on invalid values).

Written in Phase 1 before the production change: the construction and boolean
assertions describe the strict boundary REQ-007 requires and fail against current
source, which supplies field defaults and coerces recognized boolean tokens. Each
assertion names the disagreement it pins. They pass after seq 06 lands.
"""

from __future__ import annotations

import os
from pathlib import Path
from tempfile import mkstemp
from types import MappingProxyType

import pydantic
import pytest
from mcp_servers.mdq.mdq_models import MdqConfig
from mcp_servers.mdq.mdq_service import MdqService
from mcp_servers.mdq.startup_config import StartupConfig

from tests.mcp_servers.mdq._startup import make_startup


def _explicit(**overrides: object) -> dict[str, object]:
    """The full explicit payload REQ-007 requires: every key supplied, no defaults.

    The rejection tests build on this so a failure is the field under test rather than
    a missing key.
    """
    payload: dict[str, object] = {
        "allowed_dirs": ["/srv/docs"],
        "include_globs": ["*.md"],
        "exclude_globs": [".git/**", "__pycache__/**"],
        "max_snippet_chars": 500,
        "max_chunk_chars": 10000,
        "max_file_chars": 100000,
        "search_timeout_sec": 30,
        "max_results_limit": 100,
        "max_chars_per_chunk": 10000,
        "max_total_result_chars": 100000,
        "max_outline_items": 500,
        "max_grep_matches": 200,
        "max_chars_per_match": 500,
        "context_before": 2,
        "context_after": 2,
        "enable_grep": True,
        "max_outline_depth": 6,
        "sqlite_busy_timeout": 5000,
    }
    payload.update(overrides)
    return payload


class TestMdqConfigExplicitValues:
    """REQ-007: construction takes explicit values; no field has an implicit default."""

    def test_explicit_values_construct_successfully(self) -> None:
        cfg = MdqConfig(**_explicit())
        assert cfg.allowed_dirs == ["/srv/docs"]
        assert cfg.include_globs == ["*.md"]
        assert cfg.exclude_globs == [".git/**", "__pycache__/**"]
        assert cfg.max_snippet_chars == 500
        assert cfg.max_chunk_chars == 10000
        assert cfg.max_file_chars == 100000
        assert cfg.search_timeout_sec == 30
        assert cfg.enable_grep is True
        assert cfg.max_grep_matches == 200
        assert cfg.max_chars_per_match == 500
        assert cfg.context_before == 2
        assert cfg.context_after == 2
        assert cfg.max_results_limit == 100
        assert cfg.max_chars_per_chunk == 10000
        assert cfg.max_total_result_chars == 100000
        assert cfg.max_outline_items == 500
        assert cfg.max_outline_depth == 6
        assert cfg.sqlite_busy_timeout == 5000

    def test_construction_requires_every_key(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            MdqConfig()

        # The values below are the ones the model supplies today; REQ-007 removes them,
        # so a payload that omits one key is refused instead of silently defaulted.
        for field in _explicit():
            payload = dict(_explicit())
            del payload[field]
            with pytest.raises(pydantic.ValidationError) as excinfo:
                MdqConfig(**payload)
            missing = [e for e in excinfo.value.errors() if e["loc"] == (field,)]
            assert missing, f"{field} is still defaulted, so omitting it constructs"


class TestMdqConfigNumericValidation:
    @pytest.mark.parametrize(
        "field",
        [
            "max_snippet_chars",
            "max_chunk_chars",
            "max_file_chars",
            "search_timeout_sec",
            "max_results_limit",
            "max_chars_per_chunk",
            "max_total_result_chars",
            "max_outline_items",
            "max_grep_matches",
            "max_chars_per_match",
            "max_outline_depth",
            "sqlite_busy_timeout",
        ],
    )
    @pytest.mark.parametrize("bad_value", [0, -1])
    def test_rejects_non_positive(self, field: str, bad_value: int) -> None:
        with pytest.raises(pydantic.ValidationError):
            MdqConfig(**_explicit(**{field: bad_value}))

    @pytest.mark.parametrize("field", ["context_before", "context_after"])
    def test_rejects_negative_but_allows_zero(self, field: str) -> None:
        with pytest.raises(pydantic.ValidationError):
            MdqConfig(**_explicit(**{field: -1}))
        cfg = MdqConfig(**_explicit(**{field: 0}))
        assert getattr(cfg, field) == 0


class TestMdqConfigListValidation:
    @pytest.mark.parametrize(
        "field", ["allowed_dirs", "include_globs", "exclude_globs"]
    )
    def test_rejects_non_list(self, field: str) -> None:
        with pytest.raises(pydantic.ValidationError):
            MdqConfig(**_explicit(**{field: "not-a-list"}))


class TestMdqConfigBoolValidation:
    """REQ-007: a declared bool accepts only a bool; nothing is coerced."""

    def test_rejects_non_bool_enable_grep(self) -> None:
        with pytest.raises(pydantic.ValidationError):
            MdqConfig(**_explicit(enable_grep="not-a-bool"))

    def test_recognized_boolean_tokens_are_rejected_not_coerced(self) -> None:
        for bad_value in ("true", 1):
            with pytest.raises(pydantic.ValidationError) as excinfo:
                MdqConfig(**_explicit(enable_grep=bad_value))
            errors = [e for e in excinfo.value.errors() if e["loc"] == ("enable_grep",)]
            assert errors, f"{bad_value!r} is still coerced instead of rejected"
            # pydantic's error dict names the key `msg`; `message` is the JSON form.
            message = errors[0]["msg"]
            assert "enable_grep" in message
            assert str(bad_value) not in message, (
                "the error text names the field path only, never the configured value (AC-6)"
            )


class TestMdqServiceConfigValidation:
    """The service consumes the validated result; it reads no configuration and defaults nothing.

    Patching `ConfigLoader` here would assert a read that no longer exists, so the service tests
    supply the result explicitly (the same rule seq 23 records for the model tests).
    """

    def test_valid_explicit_values_construct_service(self, tmp_path: Path) -> None:
        fd, db = mkstemp(suffix=".db", dir=str(tmp_path))
        try:
            svc = MdqService(
                make_startup(db, max_snippet_chars=250, allowed_dirs=[str(tmp_path)])
            )
            assert svc.max_snippet_chars == 250
            assert svc.allowed_dirs == [str(tmp_path)]
        finally:
            os.close(fd)

    def test_invalid_config_value_fails_construction(self, tmp_path: Path) -> None:
        fd, db = mkstemp(suffix=".db", dir=str(tmp_path))
        try:
            with pytest.raises(pydantic.ValidationError):
                MdqService(make_startup(db, max_snippet_chars=-5))
        finally:
            os.close(fd)

    def test_missing_key_fails_construction(self, tmp_path: Path) -> None:
        """A result that omits a declared key is a construction failure, not a default (REQ-007)."""
        fd, db = mkstemp(suffix=".db", dir=str(tmp_path))
        try:
            payload = dict(_explicit())
            del payload["max_snippet_chars"]
            startup = StartupConfig(
                values=MappingProxyType(payload), db_path=db, auth_token="test-token"
            )
            with pytest.raises(pydantic.ValidationError):
                MdqService(startup)
        finally:
            os.close(fd)
