#!/usr/bin/env python3
"""tests/test_delete_service.py
Unit tests for DeleteFileService business logic, audit logging, and dispatch table.
"""

from __future__ import annotations

import logging
import stat as stat_module
import time
from pathlib import Path
from unittest.mock import patch

import pytest
from mcp_servers.file.common import FileAuthorizationError, FileValidationError


@pytest.fixture()
def service(tmp_path: Path) -> tuple:
    """Create a DeleteFileService with allowed_dirs pointing to tmp_path."""
    from mcp_servers.file.delete_service import DeleteFileService

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

    def test_write_audit_log_os_error_is_logged_not_raised(
        self, service: tuple, caplog: pytest.LogCaptureFixture
    ):
        """Real _write_audit_log call: OSError must be caught and logged, never propagated."""
        svc, _ = service
        svc._audit_log_path = "/nonexistent_dir_for_delete_audit/audit.log"
        with caplog.at_level(logging.ERROR):
            svc._write_audit_log("delete_file", "/some/path")
        assert "_write_audit_log: failed to write audit log" in caplog.text


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

    def test_delete_file_dry_run_stat_error(self, service: tuple):
        svc, tmp_path = service
        fpath = tmp_path / "test.txt"
        fpath.write_text("hello")

        with patch("pathlib.Path.stat") as mock_stat:
            mock_stat.side_effect = OSError("stat failed")
            result = svc.delete_file(
                type("Request", (), {"path": str(fpath), "dry_run": True})()
            )
        assert result.deleted is False
        assert result.file_info == "stat error: stat failed"

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

    def test_delete_directory_recursive_on_allowed_root_raises(self, service: tuple):
        """Security guard: recursive delete of an allowed root dir itself is forbidden."""
        svc, tmp_path = service
        with pytest.raises(FileAuthorizationError):
            svc.delete_directory(
                type(
                    "Request",
                    (),
                    {"path": str(tmp_path), "recursive": True, "dry_run": False},
                )()
            )
        assert tmp_path.exists()

    def test_delete_directory_dry_run_scan_error(self, service: tuple):
        svc, tmp_path = service
        dpath = tmp_path / "dry_scan_error_dir"
        dpath.mkdir()

        with patch.object(svc, "_scan_directory_for_dry_run") as mock_scan:
            mock_scan.side_effect = OSError("scan failed")
            result = svc.delete_directory(
                type(
                    "Request",
                    (),
                    {"path": str(dpath), "recursive": False, "dry_run": True},
                )()
            )
        assert result.deleted is False
        assert result.dir_info == "scan error: scan failed"

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

    def test_scan_skips_files_with_os_error(self, service: tuple):
        svc, tmp_path = service
        dpath = tmp_path / "flaky_scan_dir"
        dpath.mkdir()
        good = dpath / "good.txt"
        good.write_text("hello")
        bad = dpath / "bad.txt"
        bad.write_text("world!")

        real_stat = Path.stat

        def flaky_stat(self: Path, *args: object, **kwargs: object) -> object:
            if self.name == "bad.txt":
                raise OSError("stat failed for bad.txt")
            return real_stat(self, *args, **kwargs)

        with patch("pathlib.Path.stat", flaky_stat):
            file_count, total_size, truncated = svc._scan_directory_for_dry_run(dpath)
        assert file_count == 1
        assert total_size == len("hello")
        assert truncated is False


# ── Dispatch table ──


class TestDispatchTable:
    def test_get_dispatch_table_returns_tools(self, service: tuple):
        svc, _ = service
        table = svc.get_dispatch_table()
        assert "delete_file" in table
        assert "delete_directory" in table
        assert callable(table["delete_file"])
        assert callable(table["delete_directory"])


# ── Dispatch handlers ──


class TestDispatchHandlers:
    async def test_fmt_delete_file_formats_success(self, service: tuple):
        svc, tmp_path = service
        fpath = tmp_path / "afile.txt"
        fpath.write_text("data")

        result = await svc.fmt_delete_file({"path": str(fpath), "dry_run": False})
        assert result == f"Deleted: {fpath.resolve()}"
        assert not fpath.exists()

    async def test_fmt_delete_file_formats_dry_run(self, service: tuple):
        svc, tmp_path = service
        fpath = tmp_path / "afile.txt"
        fpath.write_text("data")

        result = await svc.fmt_delete_file({"path": str(fpath), "dry_run": True})
        assert result.startswith(f"Dry-run: {fpath.resolve()}")
        assert fpath.exists()

    async def test_fmt_delete_directory_formats_success(self, service: tuple):
        svc, tmp_path = service
        dpath = tmp_path / "adir"
        dpath.mkdir()

        result = await svc.fmt_delete_directory(
            {"path": str(dpath), "recursive": False, "dry_run": False}
        )
        assert result == f"Directory deleted: {dpath.resolve()}"
        assert not dpath.exists()

    async def test_fmt_delete_directory_formats_dry_run(self, service: tuple):
        svc, tmp_path = service
        dpath = tmp_path / "adir"
        dpath.mkdir()

        result = await svc.fmt_delete_directory(
            {"path": str(dpath), "recursive": False, "dry_run": True}
        )
        assert result.startswith(f"Dry-run: {dpath.resolve()}")
        assert dpath.exists()


# ── build_service factory ──


class TestBuildService:
    def test_build_service_empty_allowed_dirs_warns(
        self, caplog: pytest.LogCaptureFixture
    ):
        from mcp_servers.file.delete_models import FileDeleteConfig
        from mcp_servers.file.delete_service import build_service

        cfg = FileDeleteConfig(allowed_dirs=[])
        with caplog.at_level(logging.WARNING):
            svc = build_service(cfg)
        assert "ALLOWED_DIRS is empty" in caplog.text
        assert svc._allowed_dirs == []

    def test_build_service_with_allowed_dirs(self, tmp_path: Path):
        from mcp_servers.file.delete_models import FileDeleteConfig
        from mcp_servers.file.delete_service import build_service

        cfg = FileDeleteConfig(allowed_dirs=[str(tmp_path)])
        svc = build_service(cfg)
        assert svc._allowed_dirs == [Path(str(tmp_path))]
        assert svc._audit_log_path == "/opt/llm/logs/delete_audit.log"
