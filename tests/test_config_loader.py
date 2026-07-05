"""tests/test_config_loader.py
Unit tests for ConfigLoader: TOML and JSON loading, merging, and error cases.
"""

from pathlib import Path

import orjson
import pytest
from agent.config_dataclasses import MemoryConfig
from shared.config_loader import (
    ConfigLoader,
    ConfigMissingError,
    ConfigParseError,
    ConfigReadError,
)


@pytest.fixture
def tmp_cfg(tmp_path: Path) -> ConfigLoader:
    """ConfigLoader pointing at a temporary directory."""
    return ConfigLoader(config_dir=tmp_path)


class TestTOMLLoading:
    def test_loads_simple_toml(self, tmp_cfg: ConfigLoader, tmp_path: Path) -> None:
        (tmp_path / "test.toml").write_text(
            'key = "value"\nnum = 42\n', encoding="utf-8"
        )
        result = tmp_cfg.load("test.toml")
        assert result == {"key": "value", "num": 42}

    def test_loads_nested_toml(self, tmp_cfg: ConfigLoader, tmp_path: Path) -> None:
        (tmp_path / "nested.toml").write_text(
            '[section]\nfoo = "bar"\n', encoding="utf-8"
        )
        result = tmp_cfg.load("nested.toml")
        assert result == {"section": {"foo": "bar"}}

    def test_invalid_toml_raises_value_error(
        self, tmp_cfg: ConfigLoader, tmp_path: Path
    ) -> None:
        (tmp_path / "bad.toml").write_text("key = [unclosed", encoding="utf-8")
        with pytest.raises(ValueError, match="Invalid TOML"):
            tmp_cfg.load("bad.toml")

    def test_meta_keys_excluded_toml_via_comment(
        self, tmp_cfg: ConfigLoader, tmp_path: Path
    ) -> None:
        # TOML uses # comments; _doc keys are excluded from result
        (tmp_path / "meta.toml").write_text(
            '_doc = "desc"\nreal = true\n', encoding="utf-8"
        )
        result = tmp_cfg.load("meta.toml")
        assert "_doc" not in result
        assert result["real"] is True


class TestJSONLoading:
    def test_loads_simple_json(self, tmp_cfg: ConfigLoader, tmp_path: Path) -> None:
        (tmp_path / "test.json").write_bytes(orjson.dumps({"a": 1}))
        result = tmp_cfg.load("test.json")
        assert result == {"a": 1}

    def test_invalid_json_raises_value_error(
        self, tmp_cfg: ConfigLoader, tmp_path: Path
    ) -> None:
        (tmp_path / "bad.json").write_bytes(b"{bad json}")
        with pytest.raises(ValueError, match="Invalid JSON"):
            tmp_cfg.load("bad.json")

    def test_meta_keys_excluded_json(
        self, tmp_cfg: ConfigLoader, tmp_path: Path
    ) -> None:
        (tmp_path / "meta.json").write_bytes(orjson.dumps({"_doc": "desc", "x": 1}))
        result = tmp_cfg.load("meta.json")
        assert "_doc" not in result
        assert result["x"] == 1


class TestMerge:
    def test_merges_two_files(self, tmp_cfg: ConfigLoader, tmp_path: Path) -> None:
        (tmp_path / "a.toml").write_text("x = 1\n", encoding="utf-8")
        (tmp_path / "b.toml").write_text("y = 2\n", encoding="utf-8")
        result = tmp_cfg.load("a.toml", "b.toml")
        assert result == {"x": 1, "y": 2}

    def test_later_file_overrides_earlier(
        self, tmp_cfg: ConfigLoader, tmp_path: Path
    ) -> None:
        (tmp_path / "a.toml").write_text("x = 1\n", encoding="utf-8")
        (tmp_path / "b.toml").write_text("x = 99\n", encoding="utf-8")
        result = tmp_cfg.load("a.toml", "b.toml")
        assert result["x"] == 99


class TestErrors:
    def test_missing_file_raises_value_error(self, tmp_cfg: ConfigLoader) -> None:
        with pytest.raises(ValueError, match="Config file not found"):
            tmp_cfg.load("nonexistent.toml")

    def test_empty_names_raises_value_error(self, tmp_cfg: ConfigLoader) -> None:
        with pytest.raises(ValueError, match="At least one"):
            tmp_cfg.load()

    def test_non_string_name_raises_type_error(self, tmp_cfg: ConfigLoader) -> None:
        with pytest.raises(TypeError, match="non-empty str"):
            tmp_cfg.load(123)  # type: ignore[arg-type]

    def test_non_dict_toml_raises_value_error(
        self, tmp_cfg: ConfigLoader, tmp_path: Path
    ) -> None:
        # TOML top-level must be a table; arrays of tables would need to be accessed
        # via a key. Write raw bytes after manually constructing invalid top-level.
        # tomllib itself enforces top-level must be a table, so test JSON equivalent.
        (tmp_path / "array.json").write_bytes(b"[1, 2, 3]")
        with pytest.raises(ValueError, match="top-level mapping"):
            tmp_cfg.load("array.json")


class TestMemoryConfigValidation:
    def test_defaults_valid(self) -> None:
        cfg = MemoryConfig()
        assert cfg.memory_fts_limit == 50
        assert cfg.memory_rrf_k == 60
        assert cfg.memory_recency_days == 7.0

    def test_fts_limit_zero_raises(self) -> None:
        with pytest.raises(ValueError, match="memory_fts_limit must be >= 1"):
            MemoryConfig(memory_fts_limit=0)

    def test_rrf_k_zero_raises(self) -> None:
        with pytest.raises(ValueError, match="memory_rrf_k must be >= 1"):
            MemoryConfig(memory_rrf_k=0)

    def test_recency_days_zero_raises(self) -> None:
        with pytest.raises(ValueError, match="memory_recency_days must be > 0"):
            MemoryConfig(memory_recency_days=0.0)

    def test_recency_days_negative_raises(self) -> None:
        with pytest.raises(ValueError, match="memory_recency_days must be > 0"):
            MemoryConfig(memory_recency_days=-1.0)


class TestCustomExceptionTypes:
    def test_invalid_toml_raises_config_parse_error(
        self, tmp_cfg: ConfigLoader, tmp_path: Path
    ) -> None:
        (tmp_path / "bad.toml").write_text("key = [unclosed", encoding="utf-8")
        with pytest.raises(ConfigParseError, match="Invalid TOML"):
            tmp_cfg.load("bad.toml")

    def test_invalid_json_raises_config_parse_error(
        self, tmp_cfg: ConfigLoader, tmp_path: Path
    ) -> None:
        (tmp_path / "bad.json").write_bytes(b"{bad json}")
        with pytest.raises(ConfigParseError, match="Invalid JSON"):
            tmp_cfg.load("bad.json")

    def test_missing_file_raises_config_missing_error(
        self, tmp_cfg: ConfigLoader
    ) -> None:
        with pytest.raises(ConfigMissingError, match="Config file not found"):
            tmp_cfg.load("nonexistent.toml")

    def test_unreadable_file_raises_config_read_error(
        self, tmp_cfg: ConfigLoader, tmp_path: Path
    ) -> None:
        # Create a file and remove read permission to trigger OSError
        p = tmp_path / "unreadable.toml"
        p.write_text("x = 1\n", encoding="utf-8")
        p.chmod(0o000)
        with pytest.raises(ConfigReadError, match="Cannot read config file"):
            tmp_cfg.load("unreadable.toml")


class TestLoadAllStrictMode:
    def test_strict_false_skips_missing_files(
        self, tmp_cfg: ConfigLoader, tmp_path: Path
    ) -> None:
        """strict=False skips missing files without raising."""
        # No config files exist — should not raise
        result = tmp_cfg.load_all(strict=False)
        assert isinstance(result, dict)

    def test_strict_true_raises_on_missing_required_file(
        self, tmp_cfg: ConfigLoader, tmp_path: Path
    ) -> None:
        """strict=True raises ConfigMissingError for missing required files."""
        with pytest.raises(ConfigMissingError, match="Config file not found"):
            tmp_cfg.load_all(strict=True)

    def test_strict_true_allows_missing_optional_file(
        self, tmp_cfg: ConfigLoader, tmp_path: Path
    ) -> None:
        """strict=True allows missing *_mcp_server.toml files (all optional)."""
        # Create all required files; no *_mcp_server.toml files
        for name in [
            "common.toml",
            "llm.toml",
            "http.toml",
            "rag.toml",
            "context.toml",
            "tools.toml",
            "memory.toml",
            "otel.toml",
            "security.toml",
            "system_prompts.toml",
            "tools_definitions.toml",
        ]:
            (tmp_path / name).write_text(f"{name} = true\n", encoding="utf-8")
        # *_mcp_server.toml files are NOT created — should not raise
        result = tmp_cfg.load_all(strict=True)
        assert isinstance(result, dict)

    def test_strict_true_raises_on_missing_any_required(
        self, tmp_cfg: ConfigLoader, tmp_path: Path
    ) -> None:
        """strict=True raises if any single required file is missing."""
        # Create all required files except http.toml
        for name in [
            "common.toml",
            "llm.toml",
            "rag.toml",
            "context.toml",
            "tools.toml",
            "memory.toml",
            "otel.toml",
            "security.toml",
            "system_prompts.toml",
            "tools_definitions.toml",
        ]:
            (tmp_path / name).write_text(f"{name} = true\n", encoding="utf-8")
        # http.toml is missing — should raise
        with pytest.raises(ConfigMissingError, match="Config file not found"):
            tmp_cfg.load_all(strict=True)

    def test_load_all_meta_keys_filtered(
        self, tmp_cfg: ConfigLoader, tmp_path: Path
    ) -> None:
        """Meta keys starting with _ are still filtered in load_all()."""
        for name in [
            "common.toml",
            "llm.toml",
            "http.toml",
            "rag.toml",
            "context.toml",
            "tools.toml",
            "memory.toml",
            "otel.toml",
            "security.toml",
            "system_prompts.toml",
            "mdq_mcp_server.toml",
            "tools_definitions.toml",
        ]:
            (tmp_path / name).write_text(
                f'_doc = "desc"\n{name} = true\n', encoding="utf-8"
            )
        result = tmp_cfg.load_all(strict=True)
        assert "_doc" not in result

    def test_load_all_existing_behavior_unchanged(
        self, tmp_cfg: ConfigLoader, tmp_path: Path
    ) -> None:
        """Existing load() behavior is unchanged — strict=False skips missing files."""
        # Default (strict=False) should skip missing files
        result = tmp_cfg.load_all()
        assert isinstance(result, dict)
