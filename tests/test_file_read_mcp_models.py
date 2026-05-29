"""tests/test_file_read_mcp_models.py
Minimal coverage tests for mcp.file.read_models.
"""

import pytest
from mcp.file.read_models import (
    ListDirectoryRequest,
    ReadTextFileRequest,
    _get_cfg,
)


class TestReadModelsImport:
    def test_list_directory_request_instantiates(self) -> None:
        req = ListDirectoryRequest(path="/tmp")
        assert req.path == "/tmp"

    def test_read_text_request_head_tail_exclusive(self) -> None:
        with pytest.raises(ValueError, match="cannot be specified"):
            ReadTextFileRequest(path="/tmp/f.txt", head=5, tail=3)


class TestReadModelsGetCfg:
    def test_get_cfg_falls_back_to_empty_on_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import mcp.file.read_models as models_mod
        from shared.config_loader import ConfigLoader

        monkeypatch.setattr(models_mod, "_cfg", None)
        monkeypatch.setattr(
            ConfigLoader,
            "load",
            lambda self, *args: (_ for _ in ()).throw(OSError("no file")),
        )
        result = _get_cfg()
        assert result == {}
        monkeypatch.setattr(models_mod, "_cfg", None)
