"""Tests for scripts/shared/runtime_paths.py resolvers.

Covers the config-dir resolver (REQ-001) and the Sudachi-dict resolver
(REQ-003): explicit override wins, env-set paths must exist (fail-fast with a
message naming the path), the uncompiled repository-root fallback, the
compiled-adjacent branch, and the Sudachi ``"core"`` literal vs compiled default.
"""

import sys
from pathlib import Path

import pytest
import shared.runtime_paths as rp
from shared.runtime_paths import resolve_config_dir, resolve_sudachi_dict_path


@pytest.fixture(autouse=True)
def _isolate_resolver_state(monkeypatch) -> None:
    """Each test starts with no ``__compiled__`` marker and no resolver env var."""
    rp.__dict__.pop("__compiled__", None)
    monkeypatch.delenv("LLMAGENT_CONFIG_DIR", raising=False)
    monkeypatch.delenv("LLMAGENT_SUDACHI_DICT", raising=False)
    yield
    rp.__dict__.pop("__compiled__", None)


class TestResolveConfigDir:
    def test_explicit_arg_wins(self) -> None:
        target = Path("/tmp/any-config")
        assert resolve_config_dir(target) == target

    def test_explicit_arg_accepts_string(self) -> None:
        assert resolve_config_dir("/tmp/any-config") == Path("/tmp/any-config")

    def test_env_existing_dir_is_used(self, monkeypatch, tmp_path) -> None:
        monkeypatch.setenv("LLMAGENT_CONFIG_DIR", str(tmp_path))
        result = resolve_config_dir()
        assert result == tmp_path
        assert isinstance(result, Path)

    def test_env_missing_dir_raises_naming_path(self, monkeypatch, tmp_path) -> None:
        missing = tmp_path / "does-not-exist"
        monkeypatch.setenv("LLMAGENT_CONFIG_DIR", str(missing))
        with pytest.raises(FileNotFoundError) as exc_info:
            resolve_config_dir()
        assert str(missing) in str(exc_info.value)

    def test_uncompiled_falls_back_to_repo_root(self) -> None:
        result = resolve_config_dir()
        assert result == rp._REPO_ROOT_CONFIG

    def test_compiled_uses_adjacent_config_root(self, monkeypatch, tmp_path) -> None:
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        bin_path = bin_dir / "agent"
        monkeypatch.setattr(sys, "argv", [str(bin_path)])
        # _COMPILED_CONFIG_ROOT is computed at import from sys.argv[0]; point it at
        # the synthetic install root so the compiled-adjacent branch resolves to it.
        monkeypatch.setattr(
            rp,
            "_COMPILED_CONFIG_ROOT",
            Path(str(bin_path)).resolve().parent.parent / "config",
        )
        rp.__dict__["__compiled__"] = True
        result = resolve_config_dir()
        assert result == rp._COMPILED_CONFIG_ROOT
        assert result.name == "config"


class TestResolveSudachiDictPath:
    def test_env_existing_file_is_used(self, monkeypatch, tmp_path) -> None:
        dic = tmp_path / "system.dic"
        dic.write_text("x")
        monkeypatch.setenv("LLMAGENT_SUDACHI_DICT", str(dic))
        result = resolve_sudachi_dict_path()
        assert result == dic
        assert isinstance(result, Path)

    def test_env_missing_file_raises_naming_path(self, monkeypatch, tmp_path) -> None:
        missing = tmp_path / "missing.dic"
        monkeypatch.setenv("LLMAGENT_SUDACHI_DICT", str(missing))
        with pytest.raises(FileNotFoundError) as exc_info:
            resolve_sudachi_dict_path()
        assert str(missing) in str(exc_info.value)

    def test_unset_uncompiled_returns_core_literal(self) -> None:
        assert resolve_sudachi_dict_path() == "core"

    def test_compiled_returns_default_when_exists(self, monkeypatch, tmp_path) -> None:
        dic = tmp_path / "system.dic"
        dic.write_text("x")
        monkeypatch.setattr(rp, "_COMPILED_SUDACHI_DICT", str(dic))
        rp.__dict__["__compiled__"] = True
        assert resolve_sudachi_dict_path() == dic

    def test_compiled_raises_when_default_missing(self, monkeypatch, tmp_path) -> None:
        missing = tmp_path / "missing.dic"
        monkeypatch.setattr(rp, "_COMPILED_SUDACHI_DICT", str(missing))
        rp.__dict__["__compiled__"] = True
        with pytest.raises(FileNotFoundError):
            resolve_sudachi_dict_path()
