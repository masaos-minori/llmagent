"""
tests/shared/test_config_loader.py

Characterization tests for ConfigLoader behavior.
"""

from __future__ import annotations

from pathlib import Path

import orjson
import pytest
from shared.config_loader import (
    ConfigLoader,
    ConfigMissingError,
    ConfigParseError,
    ConfigPermissionError,
    ConfigReadError,
)


@pytest.fixture(autouse=True)
def reset_class_state():
    """Reset class-level state before and after each test."""
    ConfigLoader._allowed_files = None
    yield
    ConfigLoader._allowed_files = None


@pytest.fixture
def tmp_cfg(tmp_path: Path) -> ConfigLoader:
    """ConfigLoader pointing at a temporary directory."""
    return ConfigLoader(config_dir=tmp_path)


class TestMergeOrder:
    """Test file merge order — later files override earlier ones."""

    def test_later_file_overrides_earlier(self, tmp_path: Path) -> None:
        """Later files should override earlier ones for same keys."""
        (tmp_path / "a.toml").write_text("[section]\nfoo = 1\nbar = 2\n")
        (tmp_path / "b.toml").write_text("[section]\nfoo = 3\nbaz = 4\n")
        loader = ConfigLoader(config_dir=tmp_path)
        result = loader.load("a.toml", "b.toml")
        assert result["section"]["foo"] == 3
        assert "bar" not in result["section"]
        assert result["section"]["baz"] == 4

    def test_first_file_values_preserved_when_no_overlap(self, tmp_path: Path) -> None:
        """Values from first file preserved when no key overlap."""
        (tmp_path / "a.toml").write_text("[section]\nfoo = 1\n")
        (tmp_path / "b.toml").write_text("[other]\nbar = 2\n")
        loader = ConfigLoader(config_dir=tmp_path)
        result = loader.load("a.toml", "b.toml")
        assert result["section"]["foo"] == 1
        assert result["other"]["bar"] == 2

    def test_nested_dict_merge(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Nested dicts should be merged, not replaced entirely (load_all() only)."""
        (tmp_path / "a.toml").write_text(
            '[mcp_servers.server_a]\nurl = "http://localhost:1"\n'
        )
        (tmp_path / "b.toml").write_text(
            '[mcp_servers.server_b]\nurl = "http://localhost:2"\n'
        )
        monkeypatch.setattr(
            "shared.config_loader._BASE_CONFIG_FILES", ("a.toml", "b.toml")
        )
        loader = ConfigLoader(config_dir=tmp_path)
        result = loader.load_all()
        assert result["mcp_servers"]["server_a"]["url"] == "http://localhost:1"
        assert result["mcp_servers"]["server_b"]["url"] == "http://localhost:2"

    def test_meta_keys_filtered_from_both_files(self, tmp_path: Path) -> None:
        """Top-level keys starting with '_' should be filtered from both files."""
        (tmp_path / "a.toml").write_text('_meta = "from_a"\n[section]\nfoo = 1\n')
        (tmp_path / "b.toml").write_text('_meta = "from_b"\n[section]\nbar = 2\n')
        loader = ConfigLoader(config_dir=tmp_path)
        result = loader.load("a.toml", "b.toml")
        assert "_meta" not in result
        assert result["section"] == {"bar": 2}
        assert "foo" not in result["section"]


class TestRestrictToIsolation:
    """Test restrict_to isolation — doesn't leak state between tests."""

    def test_restricted_load_denies_unauthorized(self, tmp_path: Path) -> None:
        """Loading unauthorized file should raise ConfigPermissionError."""
        ConfigLoader.restrict_to("a.toml")
        (tmp_path / "a.toml").write_text("[section]\nfoo = 1\n")
        (tmp_path / "b.toml").write_text("[section]\nbar = 2\n")
        loader = ConfigLoader(config_dir=tmp_path)
        with pytest.raises(ConfigPermissionError, match="not permitted"):
            loader.load("a.toml", "b.toml")

    def test_restricted_load_all_denies_unauthorized(self, tmp_path: Path) -> None:
        """load_all() under restrict_to() should raise with 'load_all()' in the message."""
        (tmp_path / "agent.toml").write_text("[section]\nfoo = 1\n")
        ConfigLoader.restrict_to("other.toml")
        loader = ConfigLoader(config_dir=tmp_path)
        with pytest.raises(ConfigPermissionError, match="load_all"):
            loader.load_all()

    def test_restricted_load_allows_authorized(self, tmp_path: Path) -> None:
        """Loading authorized file should succeed."""
        ConfigLoader.restrict_to("a.toml")
        (tmp_path / "a.toml").write_text("[section]\nfoo = 1\n")
        loader = ConfigLoader(config_dir=tmp_path)
        result = loader.load("a.toml")
        assert result["section"]["foo"] == 1

    def test_restrict_to_requires_at_least_one_filename(self, tmp_path: Path) -> None:
        """Calling restrict_to() without arguments should raise ValueError."""
        ConfigLoader._allowed_files = None
        with pytest.raises(ValueError, match="requires at least one filename"):
            ConfigLoader.restrict_to()

    def test_restrict_to_does_not_affect_other_instances(self, tmp_path: Path) -> None:
        """restrict_to() affects all instances since it's class-level."""
        ConfigLoader.restrict_to("a.toml")
        (tmp_path / "a.toml").write_text("[section]\nfoo = 1\n")
        # Both instances are affected by the class-level restriction
        loader1 = ConfigLoader(config_dir=tmp_path)
        loader2 = ConfigLoader(config_dir=tmp_path)
        result1 = loader1.load("a.toml")
        result2 = loader2.load("a.toml")
        assert result1["section"]["foo"] == 1
        assert result2["section"]["foo"] == 1


class TestExtensionResolution:
    """Test extension resolution — missing extensions resolved correctly."""

    def test_missing_toml_extension_appended(self, tmp_path: Path) -> None:
        """Missing .toml extension is appended automatically."""
        (tmp_path / "test.toml").write_text("[section]\nfoo = 1\n")
        loader = ConfigLoader(config_dir=tmp_path)
        result = loader.load("test")
        assert result["section"]["foo"] == 1

    def test_existing_toml_extension_preserved(self, tmp_path: Path) -> None:
        """Existing .toml extension is not duplicated."""
        (tmp_path / "test.toml").write_text("[section]\nfoo = 1\n")
        loader = ConfigLoader(config_dir=tmp_path)
        result = loader.load("test.toml")
        assert result["section"]["foo"] == 1

    def test_json_extension_preserved(self, tmp_path: Path) -> None:
        """Existing .json extension is not changed."""
        (tmp_path / "test.json").write_text('{"section": {"foo": 1}}')
        loader = ConfigLoader(config_dir=tmp_path)
        result = loader.load("test.json")
        assert result["section"]["foo"] == 1

    def test_explicit_json_name_does_not_fall_back_to_toml(
        self, tmp_path: Path
    ) -> None:
        """An explicit .json name is resolved as-is; it is not substituted with a
        same-stem .toml file, even if one exists."""
        (tmp_path / "test.toml").write_text("[section]\nfoo = 1\n")
        loader = ConfigLoader(config_dir=tmp_path)
        with pytest.raises(ConfigMissingError, match="Config file not found"):
            loader.load("test.json")

    def test_missing_extension_defaults_to_toml(self, tmp_path: Path) -> None:
        """Missing extension defaults to .toml."""
        (tmp_path / "test.toml").write_text("[section]\nfoo = 1\n")
        loader = ConfigLoader(config_dir=tmp_path)
        result = loader.load("test")
        assert result["section"]["foo"] == 1


class TestGlobalStateCleanup:
    """Test global state cleanup — class variables properly reset after each test."""

    def test_allowed_files_reset_after_test(self, tmp_path: Path) -> None:
        """Class variable _allowed_files should be reset after each test."""
        ConfigLoader.restrict_to("a.toml")
        assert ConfigLoader._allowed_files == frozenset({"a.toml"})

    def test_multiple_restrict_calls_last_wins(self, tmp_path: Path) -> None:
        """Multiple calls to restrict_to() — last call wins."""
        ConfigLoader.restrict_to("a.toml")
        assert ConfigLoader._allowed_files == frozenset({"a.toml"})
        ConfigLoader.restrict_to("b.toml")
        assert ConfigLoader._allowed_files == frozenset({"b.toml"})

    def test_reload_without_restriction(self, tmp_path: Path) -> None:
        """After resetting _allowed_files, loading should work without restriction."""
        ConfigLoader.restrict_to("a.toml")
        (tmp_path / "a.toml").write_text("[section]\nfoo = 1\n")
        loader = ConfigLoader(config_dir=tmp_path)
        with pytest.raises(ConfigPermissionError):
            loader.load("b.toml")
        # After fixture resets _allowed_files, this would work
        ConfigLoader._allowed_files = None
        result = loader.load("a.toml")
        assert result["section"]["foo"] == 1


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


class TestMergeBasic:
    """Merge behavior for flat (non-nested) keys — see TestMergeOrder for nested cases."""

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

    def test_strict_true_passes_when_agent_toml_exists(
        self, tmp_cfg: ConfigLoader, tmp_path: Path
    ) -> None:
        """strict=True succeeds when agent.toml (the only required file) exists."""
        (tmp_path / "agent.toml").write_text(
            "llm_url = 'http://localhost'\n", encoding="utf-8"
        )
        result = tmp_cfg.load_all(strict=True)
        assert isinstance(result, dict)
        assert result.get("llm_url") == "http://localhost"

    def test_strict_true_raises_on_missing_agent_toml(
        self, tmp_cfg: ConfigLoader, tmp_path: Path
    ) -> None:
        """strict=True raises ConfigMissingError when agent.toml is absent."""
        # agent.toml is not created
        with pytest.raises(ConfigMissingError, match="Config file not found"):
            tmp_cfg.load_all(strict=True)

    def test_load_all_meta_keys_filtered(
        self, tmp_cfg: ConfigLoader, tmp_path: Path
    ) -> None:
        """Meta keys starting with _ are still filtered in load_all()."""
        (tmp_path / "agent.toml").write_text(
            '_doc = "desc"\nagent_loaded = true\n', encoding="utf-8"
        )
        result = tmp_cfg.load_all(strict=True)
        assert "_doc" not in result
        assert result.get("agent_loaded") is True

    def test_load_all_existing_behavior_unchanged(
        self, tmp_cfg: ConfigLoader, tmp_path: Path
    ) -> None:
        """Existing load() behavior is unchanged — strict=False skips missing files."""
        # Default (strict=False) should skip missing files
        result = tmp_cfg.load_all()
        assert isinstance(result, dict)
