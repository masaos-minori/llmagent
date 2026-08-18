#!/usr/bin/env python3
"""tests/mcp_servers/file/test_read_security.py
Characterization tests for mcp_servers.file.read_security.ReadSecurityGuards.

Locks current behavior of the security-boundary mixin before a type-safety-only
refactor of `_validate_file`'s `expected_type` parameter (str -> Literal["file", "dir"]).
No runtime behavior is exercised here beyond what already exists.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from mcp_servers.file.common import FileValidationError
from mcp_servers.file.read_security import ReadSecurityGuards


@pytest.fixture()
def guards(tmp_path: Path) -> ReadSecurityGuards:
    return ReadSecurityGuards(allowed_dirs=[tmp_path], max_read_bytes=1024)


class TestProperties:
    def test_allowed_dirs_property(self, tmp_path: Path) -> None:
        g = ReadSecurityGuards(allowed_dirs=[tmp_path], max_read_bytes=1024)
        assert g.allowed_dirs == [tmp_path]

    def test_max_read_bytes_property(self, tmp_path: Path) -> None:
        g = ReadSecurityGuards(allowed_dirs=[tmp_path], max_read_bytes=2048)
        assert g.max_read_bytes == 2048


class TestValidateFileFileBranch:
    def test_validates_existing_file_within_limit(
        self, guards: ReadSecurityGuards, tmp_path: Path
    ) -> None:
        target = tmp_path / "a.txt"
        target.write_text("hello", encoding="utf-8")

        resolved, size = guards._validate_file(str(target), expected_type="file")

        assert resolved == target
        assert size == 5

    def test_default_expected_type_is_file(
        self, guards: ReadSecurityGuards, tmp_path: Path
    ) -> None:
        target = tmp_path / "b.txt"
        target.write_text("x", encoding="utf-8")

        resolved, size = guards._validate_file(str(target))

        assert resolved == target
        assert size == 1

    def test_directory_rejected_when_expecting_file(
        self, guards: ReadSecurityGuards, tmp_path: Path
    ) -> None:
        sub = tmp_path / "subdir"
        sub.mkdir()

        with pytest.raises(FileValidationError):
            guards._validate_file(str(sub), expected_type="file")

    def test_oversized_file_rejected(self, tmp_path: Path) -> None:
        g = ReadSecurityGuards(allowed_dirs=[tmp_path], max_read_bytes=2)
        target = tmp_path / "big.txt"
        target.write_text("xxxx", encoding="utf-8")

        with pytest.raises(FileValidationError):
            g._validate_file(str(target), expected_type="file")


class TestValidateFileDirBranch:
    def test_validates_existing_directory(
        self, guards: ReadSecurityGuards, tmp_path: Path
    ) -> None:
        sub = tmp_path / "subdir"
        sub.mkdir()

        resolved, size = guards._validate_file(str(sub), expected_type="dir")

        assert resolved == sub
        assert isinstance(size, int)

    def test_file_rejected_when_expecting_dir(
        self, guards: ReadSecurityGuards, tmp_path: Path
    ) -> None:
        target = tmp_path / "a.txt"
        target.write_text("hello", encoding="utf-8")

        with pytest.raises(FileValidationError):
            guards._validate_file(str(target), expected_type="dir")


class TestCheckSizeLimit:
    def test_returns_file_size(
        self, guards: ReadSecurityGuards, tmp_path: Path
    ) -> None:
        target = tmp_path / "c.txt"
        target.write_text("abc", encoding="utf-8")

        assert guards._check_size_limit(target) == 3

    def test_raises_when_over_limit(self, tmp_path: Path) -> None:
        g = ReadSecurityGuards(allowed_dirs=[tmp_path], max_read_bytes=1)
        target = tmp_path / "d.txt"
        target.write_text("abc", encoding="utf-8")

        with pytest.raises(FileValidationError):
            g._check_size_limit(target)
