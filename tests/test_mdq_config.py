"""tests/test_mdq_config.py

Tests covering `MdqConfig` construction/validation, both directly and via
`MdqService.__init__` (config-driven fail-fast on invalid values).
"""

from __future__ import annotations

from pathlib import Path
from tempfile import mkstemp
from unittest.mock import patch

import pydantic
import pytest
from mcp_servers.mdq.mdq_models import MdqConfig
from mcp_servers.mdq.mdq_service import MdqService


class TestMdqConfigDefaults:
    def test_all_defaults_construct_successfully(self) -> None:
        cfg = MdqConfig()
        assert cfg.allowed_dirs == []
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
            MdqConfig(**{field: bad_value})

    @pytest.mark.parametrize("field", ["context_before", "context_after"])
    def test_rejects_negative_but_allows_zero(self, field: str) -> None:
        with pytest.raises(pydantic.ValidationError):
            MdqConfig(**{field: -1})
        cfg = MdqConfig(**{field: 0})
        assert getattr(cfg, field) == 0


class TestMdqConfigListValidation:
    @pytest.mark.parametrize(
        "field", ["allowed_dirs", "include_globs", "exclude_globs"]
    )
    def test_rejects_non_list(self, field: str) -> None:
        with pytest.raises(pydantic.ValidationError):
            MdqConfig(**{field: "not-a-list"})


class TestMdqConfigBoolValidation:
    def test_rejects_non_bool_enable_grep(self) -> None:
        """An arbitrary non-boolean-like string is rejected."""
        with pytest.raises(pydantic.ValidationError):
            MdqConfig(enable_grep="not-a-bool")

    def test_recognized_boolean_tokens_coerce(self) -> None:
        """Pydantic's lax bool parsing accepts recognized truthy tokens ('true', 1) —
        this is the actually-observed coercion behavior, documented rather than
        assumed; a plain unrecognized string is still rejected (see above)."""
        assert MdqConfig(enable_grep="true").enable_grep is True
        assert MdqConfig(enable_grep=1).enable_grep is True


class TestMdqServiceConfigValidation:
    def test_valid_config_constructs_service(self, tmp_path: Path) -> None:
        fd, db = mkstemp(suffix=".db", dir=str(tmp_path))
        try:
            with patch("shared.config_loader.ConfigLoader") as MockConfig:
                MockConfig.return_value.load.return_value = {
                    "db_path": db,
                    "allowed_dirs": [str(tmp_path)],
                    "max_snippet_chars": 250,
                }
                svc = MdqService(db_path=db)
            assert svc.max_snippet_chars == 250
            assert svc.allowed_dirs == [str(tmp_path)]
        finally:
            import os

            os.close(fd)

    def test_invalid_config_value_fails_construction(self, tmp_path: Path) -> None:
        fd, db = mkstemp(suffix=".db", dir=str(tmp_path))
        try:
            with patch("shared.config_loader.ConfigLoader") as MockConfig:
                MockConfig.return_value.load.return_value = {
                    "db_path": db,
                    "max_snippet_chars": -5,
                }
                with pytest.raises(pydantic.ValidationError):
                    MdqService(db_path=db)
        finally:
            import os

            os.close(fd)

    def test_missing_config_file_falls_back_to_defaults(self, tmp_path: Path) -> None:
        fd, db = mkstemp(suffix=".db", dir=str(tmp_path))
        try:
            with patch("shared.config_loader.ConfigLoader") as MockConfig:
                MockConfig.return_value.load.side_effect = FileNotFoundError(
                    "no config"
                )
                svc = MdqService(db_path=db)
            assert svc.max_snippet_chars == 500
            assert svc.allowed_dirs == []
        finally:
            import os

            os.close(fd)
