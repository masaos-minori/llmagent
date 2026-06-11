"""
tests/test_file_write_mcp_service.py
Unit tests for WriteFileService dry_run paths (write_file, move_file).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import HTTPException
from mcp.file.write_models import (
    EditFileRequest,
    EditOperation,
    MoveFileRequest,
    WriteFileRequest,
)
from mcp.file.write_service import WriteFileService


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

        from mcp.file.common import FileAuthorizationError

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
        with pytest.raises(HTTPException) as exc_info:
            service.move_file(req)
        assert exc_info.value.status_code == 404


# ── async fmt_* handlers ──────────────────────────────────────────────────────


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


# ── path allowlist security ───────────────────────────────────────────────────


class TestPathAllowlist:
    def test_write_outside_allowed_dir_raises_403(
        self, service: WriteFileService, tmp_path: Path
    ) -> None:
        from fastapi import HTTPException

        req = WriteFileRequest(path="/etc/passwd", content="x", dry_run=True)
        with pytest.raises(HTTPException) as exc_info:
            service.write_file(req)
        assert exc_info.value.status_code == 403

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
        from mcp.file.common import FileValidationError

        svc = WriteFileService(allowed_dirs=[tmp_path], max_write_bytes=10)
        req = WriteFileRequest(path=str(tmp_path / "out.txt"), content="x" * 100)
        with pytest.raises(FileValidationError, match="write limit"):
            svc.write_file(req)

    def test_dry_run_non_utf8_existing_file_raises_validation_error(
        self, tmp_path: Path
    ) -> None:
        from mcp.file.common import FileValidationError

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
