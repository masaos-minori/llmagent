"""
tests/shared/test_config_loader.py

Characterization tests for ConfigLoader behavior.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from shared.config_loader import ConfigLoader, ConfigPermissionError


@pytest.fixture(autouse=True)
def reset_class_state():
    """Reset class-level state before and after each test."""
    ConfigLoader._allowed_files = None
    yield
    ConfigLoader._allowed_files = None


class TestMergeOrder:
    """Test file merge order — later files override earlier ones."""

    def test_later_file_overrides_earlier(self, tmp_path: Path) -> None:
        """Later files should override earlier ones for same keys."""
        (tmp_path / "a.toml").write_text("[section]\nfoo = 1\nbar = 2\n")
        (tmp_path / "b.toml").write_text("[section]\nfoo = 3\nbaz = 4\n")
        loader = ConfigLoader(config_dir=tmp_path)
        result = loader.load("a.toml", "b.toml")
        assert result["section"]["foo"] == 3
        assert result["section"]["bar"] == 2
        assert result["section"]["baz"] == 4

    def test_first_file_values_preserved_when_no_overlap(self, tmp_path: Path) -> None:
        """Values from first file preserved when no key overlap."""
        (tmp_path / "a.toml").write_text("[section]\nfoo = 1\n")
        (tmp_path / "b.toml").write_text("[other]\nbar = 2\n")
        loader = ConfigLoader(config_dir=tmp_path)
        result = loader.load("a.toml", "b.toml")
        assert result["section"]["foo"] == 1
        assert result["other"]["bar"] == 2

    def test_nested_dict_merge(self, tmp_path: Path) -> None:
        """Nested dicts should be merged, not replaced entirely."""
        (tmp_path / "a.toml").write_text(
            '[mcp_servers]\n[server_a]\nurl = "http://localhost:1"\n'
        )
        (tmp_path / "b.toml").write_text(
            '[mcp_servers]\n[server_b]\nurl = "http://localhost:2"\n'
        )
        loader = ConfigLoader(config_dir=tmp_path)
        result = loader.load("a.toml", "b.toml")
        assert result["mcp_servers"]["server_a"]["url"] == "http://localhost:1"
        assert result["mcp_servers"]["server_b"]["url"] == "http://localhost:2"

    def test_meta_keys_filtered_from_both_files(self, tmp_path: Path) -> None:
        """Keys starting with '_' should be filtered from both files."""
        (tmp_path / "a.toml").write_text("[section]\nfoo = 1\n_bar = 2\n")
        (tmp_path / "b.toml").write_text("[section]\nbaz = 3\n_qux = 4\n")
        loader = ConfigLoader(config_dir=tmp_path)
        result = loader.load("a.toml", "b.toml")
        assert result["section"]["foo"] == 1
        assert result["section"]["baz"] == 3
        assert "_bar" not in result["section"]
        assert "_qux" not in result["section"]


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

    def test_missing_json_extension_appended(self, tmp_path: Path) -> None:
        """Missing .json extension defaults to .toml."""
        (tmp_path / "test.toml").write_text("[section]\nfoo = 1\n")
        loader = ConfigLoader(config_dir=tmp_path)
        result = loader.load("test.json")
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
