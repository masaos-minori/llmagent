#!/usr/bin/env python3
"""tests/test_delete_service.py
Unit tests for DeleteFileService business logic, audit logging, and dispatch table.
"""

from __future__ import annotations

import stat as stat_module
import time
from pathlib import Path
from unittest.mock import patch

import pytest
from mcp.file.common import FileAuthorizationError, FileValidationError


@pytest.fixture()
def service(tmp_path: Path) -> tuple:
    """Create a DeleteFileService with allowed_dirs pointing to tmp_path."""
    from mcp.file.delete_service import DeleteFileService

    svc = DeleteFileService(
        allowed_dirs=[tmp_path],
        audit_log_path=str(tmp_path / "audit.log"),
    )
    return svc, tmp_path


# ── Security wrappers ──


class TestSecurityWrappers:
    def test_resolve_safe_allows_under_allowed_dir(self, service: tuple):
        svc, tmp_path = service
        result = svc._resolve_safe(str(tmp_path / "sub" / "file.txt"))
        assert result == tmp_path / "sub" / "file.txt"

    def test_resolve_safe_rejects_outside_allowed_dir(self, service: tuple):
        svc, _ = service
        with pytest.raises(FileAuthorizationError):
            svc._resolve_safe("/etc/passwd")

    def test_require_file_raises_for_directory(self, service: tuple):
        svc, tmp_path = service
        (tmp_path / "adir").mkdir()
        with pytest.raises(FileValidationError):
            svc._require_file(tmp_path / "adir", str(tmp_path / "adir"))

    def test_require_dir_raises_for_file(self, service: tuple):
        svc, tmp_path = service
        fpath = tmp_path / "file.txt"
        fpath.write_text("x")
        with pytest.raises(FileValidationError):
            svc._require_dir(fpath, str(fpath))


# ── Audit log ──


class TestAuditLog:
    def test_write_audit_log_creates_file_and_appends(self, service: tuple):
        svc, tmp_path = service
        audit_path = tmp_path / "audit.log"
        assert not audit_path.exists()
        svc._write_audit_log("delete_file", "/some/path")
        assert audit_path.exists()
        lines = audit_path.read_text().splitlines()
        assert len(lines) == 1
        assert "op=delete_file" in lines[0]
        assert "path=/some/path" in lines[0]
        assert "user=llm-agent" in lines[0]

    def test_write_audit_log_multiple_records(self, service: tuple):
        svc, tmp_path = service
        svc._write_audit_log("delete_file", "/a")
        svc._write_audit_log("delete_directory", "/b")
        lines = (tmp_path / "audit.log").read_text().splitlines()
        assert len(lines) == 2

    def test_write_audit_log_handles_os_error(self, service: tuple):
        svc, _ = service
        svc._audit_log_path = "/nonexistent/dir/that/does/not/exist.log"
        with patch.object(svc, "_write_audit_log"):
            # Force an OSError by writing to a path that doesn't exist
            ts = time.strftime("%Y-%m-%dT%H:%M:%S+00:00")
            record = f"{ts} op=test path=/test user=llm-agent\n"
            with pytest.raises(OSError):
                with open(svc._audit_log_path, "a", encoding="utf-8") as fh:
                    fh.write(record)


# ── delete_file ──


class TestDeleteFile:
    def test_delete_file_success(self, service: tuple):
        svc, tmp_path = service
        fpath = tmp_path / "test.txt"
        fpath.write_text("hello")
        assert fpath.exists()

        result = svc.delete_file(
            type("Request", (), {"path": str(fpath), "dry_run": False})()
        )
        assert result.deleted is True
        assert result.path == str(fpath)
        assert not fpath.exists()

    def test_delete_file_dry_run_returns_info(self, service: tuple):
        svc, tmp_path = service
        fpath = tmp_path / "test.txt"
        fpath.write_text("hello world")
        st = fpath.stat()
        mode = oct(stat_module.S_IMODE(st.st_mode))

        result = svc.delete_file(
            type("Request", (), {"path": str(fpath), "dry_run": True})()
        )
        assert result.deleted is False
        assert fpath.exists()
        assert f"size={st.st_size}" in result.file_info
        assert f"mode={mode}" in result.file_info

    def test_delete_file_permission_error_raises_403(self, service: tuple):
        svc, tmp_path = service
        with patch("pathlib.Path.unlink") as mock_unlink:
            mock_unlink.side_effect = PermissionError("Permission denied")
            fpath = tmp_path / "test.txt"
            fpath.write_text("x")

            with pytest.raises(FileAuthorizationError):
                svc.delete_file(
                    type("Request", (), {"path": str(fpath), "dry_run": False})()
                )

    def test_delete_file_os_error_raises_400(self, service: tuple):
        svc, _ = service
        with (
            patch.object(svc, "_resolve_safe") as mock_resolve,
            patch.object(svc, "_require_file"),
            patch("pathlib.Path.unlink") as mock_unlink,
        ):
            mock_resolve.return_value = Path("/fake/path")
            mock_unlink.side_effect = OSError("fake os error")

            with pytest.raises(FileValidationError):
                svc.delete_file(
                    type("Request", (), {"path": "/fake/path", "dry_run": False})()
                )


# ── delete_directory ──


class TestDeleteDirectory:
    def test_delete_directory_non_recursive_empty(self, service: tuple):
        svc, tmp_path = service
        dpath = tmp_path / "empty_dir"
        dpath.mkdir()

        result = svc.delete_directory(
            type(
                "Request",
                (),
                {"path": str(dpath), "recursive": False, "dry_run": False},
            )()
        )
        assert result.deleted is True
        assert not dpath.exists()

    def test_delete_directory_non_recursive_not_empty_raises(self, service: tuple):
        svc, tmp_path = service
        dpath = tmp_path / "not_empty"
        dpath.mkdir()
        (dpath / "file.txt").write_text("x")

        with pytest.raises(FileValidationError):
            svc.delete_directory(
                type(
                    "Request",
                    (),
                    {"path": str(dpath), "recursive": False, "dry_run": False},
                )()
            )

    def test_delete_directory_recursive(self, service: tuple):
        svc, tmp_path = service
        dpath = tmp_path / "recursive_dir"
        inner = dpath / "subdir"
        inner.mkdir(parents=True)
        (inner / "file.txt").write_text("content")

        result = svc.delete_directory(
            type(
                "Request", (), {"path": str(dpath), "recursive": True, "dry_run": False}
            )()
        )
        assert result.deleted is True
        assert not dpath.exists()

    def test_delete_directory_dry_run(self, service: tuple):
        svc, tmp_path = service
        dpath = tmp_path / "dry_dir"
        dpath.mkdir()
        (dpath / "a.txt").write_text("aaa")
        (dpath / "b.txt").write_text("bbb")

        result = svc.delete_directory(
            type(
                "Request", (), {"path": str(dpath), "recursive": False, "dry_run": True}
            )()
        )
        assert result.deleted is False
        assert dpath.exists()
        assert "2 files" in result.dir_info

    def test_delete_directory_permission_error_raises_403(self, service: tuple):
        svc, tmp_path = service
        dpath = tmp_path / "readonly_dir"
        dpath.mkdir()

        with patch("shutil.rmtree") as mock_rmtree:
            mock_rmtree.side_effect = PermissionError("Permission denied")
            with pytest.raises(FileAuthorizationError):
                svc.delete_directory(
                    type(
                        "Request",
                        (),
                        {"path": str(dpath), "recursive": True, "dry_run": False},
                    )()
                )

    def test_delete_directory_os_error_raises_400(self, service: tuple):
        svc, tmp_path = service
        dpath = tmp_path / "error_dir"
        dpath.mkdir()

        with patch("pathlib.Path.rmdir") as mock_rmdir:
            mock_rmdir.side_effect = OSError("fake error")
            with pytest.raises(FileValidationError):
                svc.delete_directory(
                    type(
                        "Request",
                        (),
                        {"path": str(dpath), "recursive": False, "dry_run": False},
                    )()
                )


# ── _scan_directory_for_dry_run ──


class TestScanDirectoryDryRun:
    def test_scan_returns_counts(self, service: tuple):
        svc, tmp_path = service
        dpath = tmp_path / "scan_dir"
        dpath.mkdir()
        (dpath / "a.txt").write_text("12345")
        (dpath / "b.txt").write_text("67890")

        file_count, total_size, truncated = svc._scan_directory_for_dry_run(dpath)
        assert file_count == 2
        assert total_size == 10
        assert truncated is False

    def test_scan_respects_max_files(self, service: tuple):
        svc, tmp_path = service
        dpath = tmp_path / "big_dir"
        dpath.mkdir()
        for i in range(1500):
            (dpath / f"file_{i}.txt").write_text("x")

        file_count, total_size, truncated = svc._scan_directory_for_dry_run(dpath)
        assert file_count >= 1000
        assert truncated is True


# ── Dispatch table ──


class TestDispatchTable:
    def test_get_dispatch_table_returns_tools(self, service: tuple):
        svc, _ = service
        table = svc.get_dispatch_table()
        assert "delete_file" in table
        assert "delete_directory" in table
        assert callable(table["delete_file"])
        assert callable(table["delete_directory"])
