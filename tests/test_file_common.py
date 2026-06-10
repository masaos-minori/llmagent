"""tests/test_file_common.py
Unit tests for mcp.file.common — shared security helpers for file-read/write/delete MCP servers.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from mcp.file.common import (
    FileAuthorizationError,
    FileValidationError,
    check_size_limit,
    format_permissions,
    require_dir,
    require_file,
    resolve_safe,
)


class TestResolveSafe:
    def test_resolves_path_inside_allowed_dir(self, tmp_path: Path) -> None:
        sub = tmp_path / "sub"
        sub.mkdir()
        target = sub / "file.txt"
        target.write_text("x", encoding="utf-8")
        result = resolve_safe(str(target), [tmp_path])
        assert result == target

    def test_resolves_symlink_inside_allowed_dir(self, tmp_path: Path) -> None:
        real = tmp_path / "real"
        real.write_text("x", encoding="utf-8")
        link = tmp_path / "link"
        link.symlink_to(real)
        result = resolve_safe(str(link), [tmp_path])
        assert result == real

    def test_outside_allowed_dir_raises_403(self, tmp_path: Path) -> None:
        other = Path("/tmp/other_dir_xyz")
        with pytest.raises(FileAuthorizationError):
            resolve_safe(str(other), [tmp_path])

    def test_parent_of_allowed_dir_raises_403(self, tmp_path: Path) -> None:
        parent = tmp_path.parent
        with pytest.raises(FileAuthorizationError):
            resolve_safe(str(parent), [tmp_path])

    def test_multiple_allowed_dirs_first_match(self, tmp_path: Path) -> None:
        a = tmp_path / "a"
        b = tmp_path / "b"
        a.mkdir()
        b.mkdir()
        target = a / "file.txt"
        target.write_text("x", encoding="utf-8")
        result = resolve_safe(str(target), [b, a])
        assert result == target

    def test_multiple_allowed_dirs_second_match(self, tmp_path: Path) -> None:
        a = tmp_path / "a"
        b = tmp_path / "b"
        a.mkdir()
        b.mkdir()
        target = b / "file.txt"
        target.write_text("x", encoding="utf-8")
        result = resolve_safe(str(target), [a, b])
        assert result == target

    def test_empty_allowed_dirs_raises_403(self, tmp_path: Path) -> None:
        with pytest.raises(FileAuthorizationError):
            resolve_safe(str(tmp_path / "x"), [])


class TestRequireFile:
    def test_existing_file_passes(self, tmp_path: Path) -> None:
        target = tmp_path / "f.txt"
        target.write_text("x", encoding="utf-8")
        require_file(target, str(target))

    def test_nonexistent_file_raises_404(self, tmp_path: Path) -> None:
        target = tmp_path / "missing.txt"
        with pytest.raises(FileNotFoundError):
            require_file(target, str(target))

    def test_directory_raises_400(self, tmp_path: Path) -> None:
        sub = tmp_path / "subdir"
        sub.mkdir()
        with pytest.raises(FileValidationError):
            require_file(sub, str(sub))


class TestRequireDir:
    def test_existing_directory_passes(self, tmp_path: Path) -> None:
        sub = tmp_path / "subdir"
        sub.mkdir()
        require_dir(sub, str(sub))

    def test_nonexistent_directory_raises_404(self, tmp_path: Path) -> None:
        target = tmp_path / "missing_dir"
        with pytest.raises(FileNotFoundError):
            require_dir(target, str(target))

    def test_file_raises_400(self, tmp_path: Path) -> None:
        target = tmp_path / "file.txt"
        target.write_text("x", encoding="utf-8")
        with pytest.raises(FileValidationError):
            require_dir(target, str(target))


class TestCheckSizeLimit:
    def test_under_limit_returns_size(self, tmp_path: Path) -> None:
        target = tmp_path / "small.txt"
        target.write_text("hello", encoding="utf-8")
        result = check_size_limit(target, 1024)
        assert result == 5

    def test_exact_limit_returns_size(self, tmp_path: Path) -> None:
        target = tmp_path / "exact.txt"
        target.write_text("hello", encoding="utf-8")
        result = check_size_limit(target, 5)
        assert result == 5

    def test_over_limit_raises_413(self, tmp_path: Path) -> None:
        target = tmp_path / "big.txt"
        target.write_text("hello world", encoding="utf-8")
        with pytest.raises(ValueError):
            check_size_limit(target, 5)

    def test_error_message_contains_sizes(self, tmp_path: Path) -> None:
        target = tmp_path / "big.txt"
        target.write_text("hello world", encoding="utf-8")
        with pytest.raises(ValueError) as exc_info:
            check_size_limit(target, 5)
        assert "11" in str(exc_info.value)


class TestFormatPermissions:
    def test_regular_file_returns_9_char_string(self) -> None:
        result = format_permissions(0o100644)
        assert len(result) == 9
        assert result == "rw-r--r--"

    def test_directory_returns_9_char_string(self) -> None:
        result = format_permissions(0o040755)
        assert len(result) == 9
        assert result == "rwxr-xr-x"

    def test_executable_returns_correct_mode(self) -> None:
        result = format_permissions(0o100755)
        assert result == "rwxr-xr-x"

    def test_setuid_file(self) -> None:
        result = format_permissions(0o406755)
        assert len(result) == 9
        assert "s" in result.lower()

    def test_all_bits_set(self) -> None:
        result = format_permissions(0o100777)
        assert result == "rwxrwxrwx"

    def test_no_permissions(self) -> None:
        result = format_permissions(0o100000)
        assert result == "---------"
