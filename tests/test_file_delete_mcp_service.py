"""
tests/test_file_delete_mcp_service.py
Unit tests for DeleteFileService dry_run paths (delete_file, delete_directory).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from mcp.file.delete_models import (
    DeleteDirectoryRequest,
    DeleteFileRequest,
)
from mcp.file.delete_service import DeleteFileService


@pytest.fixture()
def service(tmp_path: Path) -> DeleteFileService:
    return DeleteFileService(
        allowed_dirs=[tmp_path],
        audit_log_path=str(tmp_path / "audit.log"),
    )


# ── delete_file dry_run ───────────────────────────────────────────────────────


class TestDeleteFileDryRun:
    def test_dry_run_does_not_delete_file(
        self, service: DeleteFileService, tmp_path: Path
    ) -> None:
        target = tmp_path / "keep.txt"
        target.write_text("keep", encoding="utf-8")
        req = DeleteFileRequest(path=str(target), dry_run=True)
        result = service.delete_file(req)
        assert target.exists()
        assert result.deleted is False

    def test_dry_run_returns_file_info(
        self, service: DeleteFileService, tmp_path: Path
    ) -> None:
        target = tmp_path / "info.txt"
        target.write_text("data", encoding="utf-8")
        req = DeleteFileRequest(path=str(target), dry_run=True)
        result = service.delete_file(req)
        assert "size=" in result.file_info
        assert "mtime=" in result.file_info

    def test_dry_run_false_deletes_file(
        self, service: DeleteFileService, tmp_path: Path
    ) -> None:
        target = tmp_path / "delete_me.txt"
        target.write_text("bye", encoding="utf-8")
        req = DeleteFileRequest(path=str(target), dry_run=False)
        result = service.delete_file(req)
        assert result.deleted is True
        assert not target.exists()

    def test_dry_run_stat_error_returns_error_info(
        self,
        service: DeleteFileService,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """OSError from stat() inside the dry_run block must return descriptive info."""
        from pathlib import Path as _Path

        target = tmp_path / "statfail.txt"
        target.write_text("x", encoding="utf-8")

        original_stat = _Path.stat
        # require_file() calls exists() → stat() (1st) and is_file() → stat() (2nd).
        # Fail only on the 3rd call so both exist/is_file checks pass before dry_run.
        call_count: list[int] = [0]

        def _bad_stat(self: _Path, **kwargs: object) -> object:
            if self.name == "statfail.txt":
                call_count[0] += 1
                if call_count[0] > 2:
                    raise OSError("no stat")
            return original_stat(self)

        monkeypatch.setattr(_Path, "stat", _bad_stat)
        req = DeleteFileRequest(path=str(target), dry_run=True)
        result = service.delete_file(req)
        assert result.deleted is False
        assert "stat error" in result.file_info


# ── delete_directory dry_run ──────────────────────────────────────────────────


class TestDeleteDirectoryDryRun:
    def test_dry_run_does_not_delete_directory(
        self, service: DeleteFileService, tmp_path: Path
    ) -> None:
        d = tmp_path / "mydir"
        d.mkdir()
        (d / "a.txt").write_text("a", encoding="utf-8")
        req = DeleteDirectoryRequest(path=str(d), dry_run=True)
        result = service.delete_directory(req)
        assert d.exists()
        assert result.deleted is False

    def test_dry_run_counts_files_and_sizes(
        self, service: DeleteFileService, tmp_path: Path
    ) -> None:
        d = tmp_path / "counted"
        d.mkdir()
        (d / "a.txt").write_text("aaa", encoding="utf-8")
        (d / "b.txt").write_text("bb", encoding="utf-8")
        req = DeleteDirectoryRequest(path=str(d), dry_run=True)
        result = service.delete_directory(req)
        assert "2 files" in result.dir_info
        assert "5 bytes" in result.dir_info

    def test_dry_run_empty_directory(
        self, service: DeleteFileService, tmp_path: Path
    ) -> None:
        d = tmp_path / "empty"
        d.mkdir()
        req = DeleteDirectoryRequest(path=str(d), dry_run=True)
        result = service.delete_directory(req)
        assert "0 files" in result.dir_info

    def test_dry_run_false_deletes_directory(
        self, service: DeleteFileService, tmp_path: Path
    ) -> None:
        d = tmp_path / "gone"
        d.mkdir()
        req = DeleteDirectoryRequest(path=str(d), recursive=False, dry_run=False)
        result = service.delete_directory(req)
        assert result.deleted is True
        assert not d.exists()

    def test_dry_run_truncation_at_max_files(
        self,
        service: DeleteFileService,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        import mcp.file.delete_service as svc_module

        monkeypatch.setattr(svc_module, "_DRY_RUN_MAX_FILES", 2)
        d = tmp_path / "many"
        d.mkdir()
        for i in range(5):
            (d / f"{i}.txt").write_text("x", encoding="utf-8")
        req = DeleteDirectoryRequest(path=str(d), dry_run=True)
        result = service.delete_directory(req)
        # Should show "2+" to indicate truncation
        assert "+" in result.dir_info

    def test_dry_run_file_stat_error_skipped(
        self,
        service: DeleteFileService,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """OSError from individual file stat() in walk must be skipped gracefully."""
        from pathlib import Path as _Path

        import mcp.file.delete_service as svc_module

        d = tmp_path / "walkdir"
        d.mkdir()
        (d / "ok.txt").write_text("ok", encoding="utf-8")

        original_stat = _Path.stat

        def _bad_stat(self: _Path, **kwargs: object) -> object:
            if self.name == "ok.txt":
                raise OSError("simulated stat error")
            return original_stat(self)

        monkeypatch.setattr(svc_module.Path, "stat", _bad_stat)
        req = DeleteDirectoryRequest(path=str(d), dry_run=True)
        result = service.delete_directory(req)
        # File with stat error should be skipped; no crash
        assert "files" in result.dir_info


# ── async fmt_* handlers ──────────────────────────────────────────────────────


class TestFmtHandlersDryRun:
    @pytest.mark.asyncio
    async def test_fmt_delete_file_dry_run(
        self, service: DeleteFileService, tmp_path: Path
    ) -> None:
        target = tmp_path / "f.txt"
        target.write_text("data", encoding="utf-8")
        result = await service.fmt_delete_file({"path": str(target), "dry_run": True})
        assert "Dry-run" in result
        assert str(target) in result

    @pytest.mark.asyncio
    async def test_fmt_delete_directory_dry_run(
        self, service: DeleteFileService, tmp_path: Path
    ) -> None:
        d = tmp_path / "dir"
        d.mkdir()
        result = await service.fmt_delete_directory({"path": str(d), "dry_run": True})
        assert "Dry-run" in result
        assert str(d) in result
