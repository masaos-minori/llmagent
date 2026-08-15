"""
tests/test_file_write_mcp_service.py
Unit tests for WriteFileService dry_run paths (write_file, move_file).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from mcp_servers.file.common import FileAuthorizationError
from mcp_servers.file.write_models import (
    CreateDirectoryRequest,
    EditFileRequest,
    EditOperation,
    MoveFileRequest,
    WriteFileRequest,
)
from mcp_servers.file.write_service import WriteFileService


@pytest.fixture()
def service(tmp_path: Path) -> WriteFileService:
    return WriteFileService(
        allowed_dirs=[tmp_path],
        max_write_bytes=1024 * 1024,
    )


# ── write_file dry_run ────────────────────────────────────────────────────────


class TestWriteFileDryRun:
    def test_dry_run_new_file_does_not_create_file(
        self, service: WriteFileService, tmp_path: Path
    ) -> None:
        target = tmp_path / "new.txt"
        req = WriteFileRequest(path=str(target), content="hello", dry_run=True)
        result = service.write_file(req)
        assert not target.exists()
        assert result.applied is False
        assert result.diff == ""

    def test_dry_run_new_file_returns_correct_size(
        self, service: WriteFileService, tmp_path: Path
    ) -> None:
        target = tmp_path / "new.txt"
        req = WriteFileRequest(path=str(target), content="hello", dry_run=True)
        result = service.write_file(req)
        assert result.size == len(b"hello")

    def test_dry_run_existing_file_returns_diff(
        self, service: WriteFileService, tmp_path: Path
    ) -> None:
        target = tmp_path / "existing.txt"
        target.write_text("old content", encoding="utf-8")
        req = WriteFileRequest(path=str(target), content="new content", dry_run=True)
        result = service.write_file(req)
        assert not result.applied
        assert "old content" in result.diff or "new content" in result.diff

    def test_dry_run_existing_file_unchanged_no_diff(
        self, service: WriteFileService, tmp_path: Path
    ) -> None:
        target = tmp_path / "same.txt"
        target.write_text("same", encoding="utf-8")
        req = WriteFileRequest(path=str(target), content="same", dry_run=True)
        result = service.write_file(req)
        assert not result.applied
        assert result.diff == ""

    def test_dry_run_permission_error_raises_auth_error(
        self, service: WriteFileService, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """PermissionError when reading existing file for dry-run diff must raise FileAuthorizationError."""
        from pathlib import Path as _Path

        from mcp_servers.file.common import FileAuthorizationError

        target = tmp_path / "locked.txt"
        target.write_text("old", encoding="utf-8")

        original_read = _Path.read_text

        def _fail_read(self: _Path, **kwargs: object) -> str:
            if self.name == "locked.txt":
                raise PermissionError("no access")
            return original_read(self, **kwargs)  # type: ignore[arg-type]

        monkeypatch.setattr(_Path, "read_text", _fail_read)
        req = WriteFileRequest(path=str(target), content="new", dry_run=True)
        with pytest.raises(FileAuthorizationError):
            service.write_file(req)

    def test_dry_run_false_writes_file(
        self, service: WriteFileService, tmp_path: Path
    ) -> None:
        target = tmp_path / "written.txt"
        req = WriteFileRequest(path=str(target), content="written", dry_run=False)
        result = service.write_file(req)
        assert result.applied is True
        assert target.read_text(encoding="utf-8") == "written"


# ── edit_file dry_run (existing implementation) ───────────────────────────────


class TestEditFileDryRun:
    def test_dry_run_returns_diff_without_writing(
        self, service: WriteFileService, tmp_path: Path
    ) -> None:
        target = tmp_path / "f.txt"
        target.write_text("foo bar", encoding="utf-8")
        req = EditFileRequest(
            path=str(target),
            edits=[EditOperation(old_text="foo", new_text="baz")],
            dry_run=True,
        )
        result = service.edit_file(req)
        assert result.applied is False
        assert target.read_text(encoding="utf-8") == "foo bar"
        assert "foo" in result.diff or "baz" in result.diff


# ── move_file dry_run ─────────────────────────────────────────────────────────


class TestMoveFileDryRun:
    def test_dry_run_existing_source_no_dest(
        self, service: WriteFileService, tmp_path: Path
    ) -> None:
        src = tmp_path / "src.txt"
        src.write_text("x", encoding="utf-8")
        dest = tmp_path / "dest.txt"
        req = MoveFileRequest(source=str(src), destination=str(dest), dry_run=True)
        result = service.move_file(req)
        assert result.dry_run_info != ""
        assert "exists" in result.dry_run_info
        assert "free" in result.dry_run_info
        assert src.exists()

    def test_dry_run_missing_source(
        self, service: WriteFileService, tmp_path: Path
    ) -> None:
        src = tmp_path / "missing.txt"
        dest = tmp_path / "dest.txt"
        req = MoveFileRequest(source=str(src), destination=str(dest), dry_run=True)
        result = service.move_file(req)
        assert "not found" in result.dry_run_info

    def test_dry_run_dest_conflict(
        self, service: WriteFileService, tmp_path: Path
    ) -> None:
        src = tmp_path / "src.txt"
        src.write_text("x", encoding="utf-8")
        dest = tmp_path / "dest.txt"
        dest.write_text("y", encoding="utf-8")
        req = MoveFileRequest(source=str(src), destination=str(dest), dry_run=True)
        result = service.move_file(req)
        assert "conflict" in result.dry_run_info

    def test_dry_run_false_moves_file(
        self, service: WriteFileService, tmp_path: Path
    ) -> None:
        src = tmp_path / "src.txt"
        src.write_text("move me", encoding="utf-8")
        dest = tmp_path / "dest.txt"
        req = MoveFileRequest(source=str(src), destination=str(dest), dry_run=False)
        result = service.move_file(req)
        assert result.dry_run_info == ""
        assert not src.exists()
        assert dest.read_text(encoding="utf-8") == "move me"

    def test_dry_run_false_missing_source_raises(
        self, service: WriteFileService, tmp_path: Path
    ) -> None:
        src = tmp_path / "ghost.txt"
        dest = tmp_path / "dest.txt"
        req = MoveFileRequest(source=str(src), destination=str(dest), dry_run=False)
        with pytest.raises(FileNotFoundError):
            service.move_file(req)


# ── async fmt_* handlers ──────────────────────────────────────────────────────


# ── create_directory dry_run ──────────────────────────────────────────────────


class TestCreateDirectoryDryRun:
    def test_dry_run_nonexistent_path_returns_would_create(
        self, service: WriteFileService, tmp_path: Path
    ) -> None:
        target = tmp_path / "new_dir"
        req = CreateDirectoryRequest(path=str(target), dry_run=True)
        result = service.create_directory(req)
        assert not target.exists()
        assert "would create" in result.dry_run_info

    def test_dry_run_existing_path_returns_exists(
        self, service: WriteFileService, tmp_path: Path
    ) -> None:
        target = tmp_path / "existing_dir"
        target.mkdir()
        req = CreateDirectoryRequest(path=str(target), dry_run=True)
        result = service.create_directory(req)
        assert target.exists()
        assert "exists" in result.dry_run_info

    def test_dry_run_created_flag_is_false(
        self, service: WriteFileService, tmp_path: Path
    ) -> None:
        target = tmp_path / "new_dir"
        req = CreateDirectoryRequest(path=str(target), dry_run=True)
        result = service.create_directory(req)
        assert result.created is False

    def test_dry_run_false_creates_directory(
        self, service: WriteFileService, tmp_path: Path
    ) -> None:
        target = tmp_path / "new_dir"
        req = CreateDirectoryRequest(path=str(target), dry_run=False)
        result = service.create_directory(req)
        assert target.exists()
        assert result.created is True
        assert result.dry_run_info == ""


class TestFmtHandlersDryRun:
    @pytest.mark.asyncio
    async def test_fmt_write_file_dry_run_new_file(
        self, service: WriteFileService, tmp_path: Path
    ) -> None:
        target = tmp_path / "new.txt"
        result = await service.fmt_write_file(
            {"path": str(target), "content": "hi", "dry_run": True}
        )
        assert "Dry-run" in result
        assert "[new file]" in result

    @pytest.mark.asyncio
    async def test_fmt_write_file_dry_run_existing_file(
        self, service: WriteFileService, tmp_path: Path
    ) -> None:
        target = tmp_path / "existing.txt"
        target.write_text("old", encoding="utf-8")
        result = await service.fmt_write_file(
            {"path": str(target), "content": "new", "dry_run": True}
        )
        assert "Dry-run" in result
        assert "[new file]" not in result

    @pytest.mark.asyncio
    async def test_fmt_move_file_dry_run(
        self, service: WriteFileService, tmp_path: Path
    ) -> None:
        src = tmp_path / "s.txt"
        src.write_text("x", encoding="utf-8")
        dest = tmp_path / "d.txt"
        result = await service.fmt_move_file(
            {"source": str(src), "destination": str(dest), "dry_run": True}
        )
        assert "Dry-run" in result

    @pytest.mark.asyncio
    async def test_fmt_create_directory_dry_run_nonexistent(
        self, service: WriteFileService, tmp_path: Path
    ) -> None:
        target = tmp_path / "new_dir"
        result = await service.fmt_create_directory(
            {"path": str(target), "dry_run": True}
        )
        assert "Dry-run" in result
        assert "would create" in result

    @pytest.mark.asyncio
    async def test_fmt_create_directory_dry_run_existing(
        self, service: WriteFileService, tmp_path: Path
    ) -> None:
        target = tmp_path / "existing_dir"
        target.mkdir()
        result = await service.fmt_create_directory(
            {"path": str(target), "dry_run": True}
        )
        assert "Dry-run" in result
        assert "exists" in result

    @pytest.mark.asyncio
    async def test_fmt_create_directory_no_dry_run(
        self, service: WriteFileService, tmp_path: Path
    ) -> None:
        target = tmp_path / "new_dir"
        result = await service.fmt_create_directory({"path": str(target)})
        assert "created" in result
        assert "Dry-run" not in result


# ── path allowlist security ───────────────────────────────────────────────────


class TestPathAllowlist:
    def test_write_outside_allowed_dir_raises_403(
        self, service: WriteFileService, tmp_path: Path
    ) -> None:
        req = WriteFileRequest(path="/etc/passwd", content="x", dry_run=True)
        with pytest.raises(FileAuthorizationError):
            service.write_file(req)

    def test_write_inside_allowed_dir_succeeds(
        self, service: WriteFileService, tmp_path: Path
    ) -> None:
        target = tmp_path / "safe.txt"
        req = WriteFileRequest(path=str(target), content="ok", dry_run=True)
        result = service.write_file(req)
        assert result is not None


class TestWriteServiceErrorPaths:
    def test_content_exceeds_limit_raises_validation_error(
        self, tmp_path: Path
    ) -> None:
        from mcp_servers.file.common import FileValidationError

        svc = WriteFileService(allowed_dirs=[tmp_path], max_write_bytes=10)
        req = WriteFileRequest(path=str(tmp_path / "out.txt"), content="x" * 100)
        with pytest.raises(FileValidationError, match="write limit"):
            svc.write_file(req)

    def test_dry_run_non_utf8_existing_file_raises_validation_error(
        self, tmp_path: Path
    ) -> None:
        from mcp_servers.file.common import FileValidationError

        svc = WriteFileService(allowed_dirs=[tmp_path], max_write_bytes=1024 * 1024)
        target = tmp_path / "binary.bin"
        target.write_bytes(b"\xff\xfe bad bytes that cannot be decoded as utf-8")
        req = WriteFileRequest(path=str(target), content="new content", dry_run=True)
        with pytest.raises(FileValidationError, match="UTF-8"):
            svc.write_file(req)

    def test_write_file_atomic_creates_correct_content(
        self, service: WriteFileService, tmp_path: Path
    ) -> None:
        target = tmp_path / "atomic.txt"
        req = WriteFileRequest(path=str(target), content="atomic content")
        result = service.write_file(req)
        assert result.applied is True
        assert target.read_text(encoding="utf-8") == "atomic content"
        tmp = target.parent / f".tmp_{target.name}"
        assert not tmp.exists()

    def test_write_file_permission_error_raises_auth_error_and_cleans_tmp(
        self, service: WriteFileService, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """PermissionError during os.replace must raise FileAuthorizationError and remove the tmp file."""
        import os as _os

        target = tmp_path / "perm.txt"
        req = WriteFileRequest(path=str(target), content="x")

        def _fail_replace(_src: str, _dst: str) -> None:
            raise PermissionError("no access")

        monkeypatch.setattr(_os, "replace", _fail_replace)
        with pytest.raises(FileAuthorizationError):
            service.write_file(req)
        tmp = target.parent / f".tmp_{target.name}"
        assert not tmp.exists()
        assert not target.exists()

    def test_write_file_os_error_raises_validation_error_and_cleans_tmp(
        self, service: WriteFileService, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A generic OSError during os.replace must raise FileValidationError and remove the tmp file."""
        import os as _os

        from mcp_servers.file.common import FileValidationError

        target = tmp_path / "oserr.txt"
        req = WriteFileRequest(path=str(target), content="x")

        def _fail_replace(_src: str, _dst: str) -> None:
            raise OSError("disk full")

        monkeypatch.setattr(_os, "replace", _fail_replace)
        with pytest.raises(FileValidationError, match="disk full"):
            service.write_file(req)
        tmp = target.parent / f".tmp_{target.name}"
        assert not tmp.exists()


class TestEditFileErrorPaths:
    def test_edit_replacement_not_found_raises_validation_error(
        self, service: WriteFileService, tmp_path: Path
    ) -> None:
        from mcp_servers.file.common import FileValidationError

        target = tmp_path / "f.txt"
        target.write_text("foo bar", encoding="utf-8")
        req = EditFileRequest(
            path=str(target),
            edits=[EditOperation(old_text="missing", new_text="x")],
        )
        with pytest.raises(FileValidationError, match="replacement target not found"):
            service.edit_file(req)

    def test_edit_non_utf8_file_raises_validation_error(
        self, service: WriteFileService, tmp_path: Path
    ) -> None:
        from mcp_servers.file.common import FileValidationError

        target = tmp_path / "binary.bin"
        target.write_bytes(b"\xff\xfe bad bytes")
        req = EditFileRequest(
            path=str(target),
            edits=[EditOperation(old_text="a", new_text="b")],
        )
        with pytest.raises(FileValidationError, match="cannot be decoded as UTF-8"):
            service.edit_file(req)

    def test_edit_permission_error_on_read_raises_auth_error(
        self, service: WriteFileService, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from pathlib import Path as _Path

        target = tmp_path / "locked.txt"
        target.write_text("old", encoding="utf-8")
        original_read = _Path.read_text

        def _fail_read(self: _Path, **kwargs: object) -> str:
            if self.name == "locked.txt":
                raise PermissionError("no access")
            return original_read(self, **kwargs)  # type: ignore[arg-type]

        monkeypatch.setattr(_Path, "read_text", _fail_read)
        req = EditFileRequest(
            path=str(target),
            edits=[EditOperation(old_text="old", new_text="new")],
        )
        with pytest.raises(FileAuthorizationError):
            service.edit_file(req)

    def test_edit_dry_run_false_writes_file_to_disk(
        self, service: WriteFileService, tmp_path: Path
    ) -> None:
        """Non-dry-run edit_file must apply the change and report applied=True."""
        target = tmp_path / "apply.txt"
        target.write_text("foo bar", encoding="utf-8")
        req = EditFileRequest(
            path=str(target),
            edits=[EditOperation(old_text="foo", new_text="baz")],
            dry_run=False,
        )
        result = service.edit_file(req)
        assert result.applied is True
        assert target.read_text(encoding="utf-8") == "baz bar"

    def test_edit_write_permission_error_raises_auth_error(
        self, service: WriteFileService, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from pathlib import Path as _Path

        target = tmp_path / "readonly.txt"
        target.write_text("foo", encoding="utf-8")
        original_write = _Path.write_text

        def _fail_write(self: _Path, *args: object, **kwargs: object) -> int:
            if self.name == "readonly.txt":
                raise PermissionError("read-only filesystem")
            return original_write(self, *args, **kwargs)  # type: ignore[arg-type]

        monkeypatch.setattr(_Path, "write_text", _fail_write)
        req = EditFileRequest(
            path=str(target),
            edits=[EditOperation(old_text="foo", new_text="bar")],
            dry_run=False,
        )
        with pytest.raises(FileAuthorizationError):
            service.edit_file(req)


class TestCreateDirectoryErrorPaths:
    def test_permission_error_raises_auth_error(
        self, service: WriteFileService, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from pathlib import Path as _Path

        from mcp_servers.file.write_models import CreateDirectoryRequest

        target = tmp_path / "new_dir"

        def _fail_mkdir(self: _Path, **_kwargs: object) -> None:
            raise PermissionError("no access")

        monkeypatch.setattr(_Path, "mkdir", _fail_mkdir)
        req = CreateDirectoryRequest(path=str(target), dry_run=False)
        with pytest.raises(FileAuthorizationError):
            service.create_directory(req)

    def test_os_error_raises_validation_error(
        self, service: WriteFileService, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from pathlib import Path as _Path

        from mcp_servers.file.common import FileValidationError
        from mcp_servers.file.write_models import CreateDirectoryRequest

        target = tmp_path / "new_dir"

        def _fail_mkdir(self: _Path, **_kwargs: object) -> None:
            raise OSError("disk full")

        monkeypatch.setattr(_Path, "mkdir", _fail_mkdir)
        req = CreateDirectoryRequest(path=str(target), dry_run=False)
        with pytest.raises(FileValidationError, match="disk full"):
            service.create_directory(req)


class TestMoveFileErrorPaths:
    def test_permission_error_raises_auth_error(
        self, service: WriteFileService, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import shutil as _shutil

        src = tmp_path / "src.txt"
        src.write_text("x", encoding="utf-8")
        dest = tmp_path / "dest.txt"

        def _fail_move(_src: str, _dst: str) -> None:
            raise PermissionError("no access")

        monkeypatch.setattr(_shutil, "move", _fail_move)
        req = MoveFileRequest(source=str(src), destination=str(dest), dry_run=False)
        with pytest.raises(FileAuthorizationError):
            service.move_file(req)

    def test_os_error_raises_validation_error(
        self, service: WriteFileService, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import shutil as _shutil

        from mcp_servers.file.common import FileValidationError

        src = tmp_path / "src.txt"
        src.write_text("x", encoding="utf-8")
        dest = tmp_path / "dest.txt"

        def _fail_move(_src: str, _dst: str) -> None:
            raise OSError("cross-device link")

        monkeypatch.setattr(_shutil, "move", _fail_move)
        req = MoveFileRequest(source=str(src), destination=str(dest), dry_run=False)
        with pytest.raises(FileValidationError, match="cross-device link"):
            service.move_file(req)


class TestCleanupTmp:
    def test_cleanup_tmp_swallows_oserror(self, tmp_path: Path) -> None:
        """_cleanup_tmp must not propagate OSError raised by unlink (e.g. tmp is a directory)."""
        tmp_dir = tmp_path / "tmp_as_dir"
        tmp_dir.mkdir()
        WriteFileService._cleanup_tmp(tmp_dir)  # IsADirectoryError is swallowed
        assert tmp_dir.exists()

    def test_cleanup_tmp_missing_file_is_noop(self, tmp_path: Path) -> None:
        WriteFileService._cleanup_tmp(tmp_path / "does_not_exist.tmp")


class TestFmtEditFileHandler:
    @pytest.mark.asyncio
    async def test_fmt_edit_file_applies_and_formats(
        self, service: WriteFileService, tmp_path: Path
    ) -> None:
        target = tmp_path / "f.txt"
        target.write_text("foo bar", encoding="utf-8")
        result = await service.fmt_edit_file(
            {
                "path": str(target),
                "edits": [{"old_text": "foo", "new_text": "baz"}],
                "dry_run": False,
            }
        )
        assert target.read_text(encoding="utf-8") == "baz bar"
        assert isinstance(result, str)


class TestBuildService:
    def test_build_service_warns_when_allowed_dirs_empty(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        from mcp_servers.file.write_models import FileWriteConfig
        from mcp_servers.file.write_service import build_service

        cfg = FileWriteConfig(
            max_write_bytes=1024, allowed_dirs=[], supported_extensions=[]
        )
        with caplog.at_level("WARNING"):
            svc = build_service(cfg)
        assert svc._allowed_dirs == []
        assert any("ALLOWED_DIRS is empty" in r.message for r in caplog.records)
