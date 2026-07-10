"""tests/test_file_read_mcp_models.py
Minimal coverage tests for mcp_servers.file.read_models.
"""

import dataclasses

import pytest
from mcp_servers.file.read_models import (
    FileReadConfig,
    ListDirectoryRequest,
    ReadTextFileRequest,
)


class TestReadModelsImport:
    def test_list_directory_request_instantiates(self) -> None:
        req = ListDirectoryRequest(path="/tmp")
        assert req.path == "/tmp"

    def test_read_text_request_head_tail_exclusive(self) -> None:
        with pytest.raises(ValueError, match="cannot be specified"):
            ReadTextFileRequest(path="/tmp/f.txt", head=5, tail=3)


class TestFileReadConfig:
    def test_from_dict_defaults(self) -> None:
        cfg = FileReadConfig.from_dict({})
        assert cfg.max_file_size_kb == 1000
        assert cfg.allowed_dirs == []
        assert cfg.max_depth == 5
        assert cfg.max_files_per_batch == 100

    def test_from_dict_custom_values(self) -> None:
        cfg = FileReadConfig.from_dict(
            {
                "max_read_bytes": 2097152,
                "allowed_dirs": ["/data", "/tmp"],
                "max_tree_depth": 10,
                "max_search_results": 200,
            },
        )
        assert cfg.max_file_size_kb == 2048
        assert cfg.allowed_dirs == ["/data", "/tmp"]
        assert cfg.max_depth == 10
        assert cfg.max_files_per_batch == 200

    def test_dataclass_fields(self) -> None:
        fields = {f.name for f in dataclasses.fields(FileReadConfig)}
        assert fields == {
            "max_file_size_kb",
            "allowed_dirs",
            "max_depth",
            "max_files_per_batch",
        }
