"""tests/test_mdq_path_jail.py
Fail-closed path authorization tests for MDQ path-accepting tools.

Verifies that index_paths, refresh_index (via _validate_paths), and
outline all raise MdqAuthorizationError instead of silently skipping
denied paths.
"""

from __future__ import annotations

import os
from pathlib import Path
from tempfile import mkstemp

import pytest
from mcp.mdq.indexer import index_paths
from mcp.mdq.models import (
    IndexPathsRequest,
    MdqAuthorizationError,
    OutlineRequest,
    RefreshIndexRequest,
)
from mcp.mdq.service import MdqService

# ── fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def allowed_service(tmp_path: Path) -> MdqService:
    """MdqService with tmp_path in allowed_dirs."""
    fd, db = mkstemp(suffix=".db", dir=str(tmp_path))
    os.close(fd)
    svc = MdqService(db_path=db)
    svc._allowed_dirs = [str(tmp_path)]
    return svc


@pytest.fixture
def denied_service(tmp_path: Path) -> MdqService:
    """MdqService with empty allowed_dirs (deny-all)."""
    fd, db = mkstemp(suffix=".db", dir=str(tmp_path))
    os.close(fd)
    svc = MdqService(db_path=db)
    svc._allowed_dirs = []
    return svc


@pytest.fixture
def md_file(tmp_path: Path) -> Path:
    """A temporary Markdown file."""
    f = tmp_path / "doc.md"
    f.write_text("# Title\n\nContent.", encoding="utf-8")
    return f


@pytest.fixture
def md_dir(tmp_path: Path) -> Path:
    """A temporary directory with a Markdown file."""
    d = tmp_path / "docs"
    d.mkdir()
    (d / "a.md").write_text("# A\n\nAlpha.", encoding="utf-8")
    return d


# ── index_paths ───────────────────────────────────────────────────────────────


class TestIndexPathsAuthorization:
    async def test_allowed_path_accepted(
        self, allowed_service: MdqService, md_file: Path
    ) -> None:
        """Path within allowed_dirs completes without raising."""
        req = IndexPathsRequest(paths=[str(md_file)])
        result = await index_paths(allowed_service, req)
        assert "complete" in result.lower()

    async def test_denied_path_raises(
        self, denied_service: MdqService, md_file: Path
    ) -> None:
        """Path outside allowed_dirs raises MdqAuthorizationError."""
        req = IndexPathsRequest(paths=[str(md_file)])
        with pytest.raises(MdqAuthorizationError, match="Access denied"):
            await index_paths(denied_service, req)

    async def test_dotdot_traversal_denied(self, tmp_path: Path, md_file: Path) -> None:
        """../escape path is resolved and denied when outside allowed_dirs."""
        allowed_subdir = tmp_path / "allowed"
        allowed_subdir.mkdir()
        fd, db = mkstemp(suffix=".db", dir=str(tmp_path))
        os.close(fd)
        svc = MdqService(db_path=db)
        svc._allowed_dirs = [str(allowed_subdir)]

        traversal = str(allowed_subdir / ".." / "doc.md")
        req = IndexPathsRequest(paths=[traversal])
        with pytest.raises(MdqAuthorizationError, match="Access denied"):
            await index_paths(svc, req)

    async def test_symlink_escape_denied(self, tmp_path: Path, md_file: Path) -> None:
        """Symlink pointing outside allowed_dirs is resolved and denied."""
        allowed_subdir = tmp_path / "allowed"
        allowed_subdir.mkdir()
        fd, db = mkstemp(suffix=".db", dir=str(tmp_path))
        os.close(fd)
        svc = MdqService(db_path=db)
        svc._allowed_dirs = [str(allowed_subdir)]

        link = allowed_subdir / "escape.md"
        link.symlink_to(md_file)  # points to tmp_path/doc.md, outside allowed_subdir

        req = IndexPathsRequest(paths=[str(link)])
        with pytest.raises(MdqAuthorizationError, match="Access denied"):
            await index_paths(svc, req)

    async def test_empty_allowlist_denies_all(
        self, denied_service: MdqService, md_file: Path
    ) -> None:
        """Empty allowed_dirs denies every path."""
        req = IndexPathsRequest(paths=[str(md_file)])
        with pytest.raises(MdqAuthorizationError):
            await index_paths(denied_service, req)

    async def test_allowed_directory_accepted(
        self, allowed_service: MdqService, md_dir: Path
    ) -> None:
        """Directory within allowed_dirs completes without raising."""
        req = IndexPathsRequest(paths=[str(md_dir)])
        result = await index_paths(allowed_service, req)
        assert "complete" in result.lower()


# ── refresh_paths / _validate_paths ──────────────────────────────────────────


class TestRefreshIndexAuthorization:
    async def test_denied_path_raises(
        self, denied_service: MdqService, md_file: Path
    ) -> None:
        """refresh_index raises MdqAuthorizationError for denied path."""
        req = RefreshIndexRequest(paths=[str(md_file)], force=False)
        with pytest.raises(MdqAuthorizationError, match="Access denied"):
            await denied_service.refresh_index(req)

    async def test_allowed_path_accepted(
        self, allowed_service: MdqService, md_file: Path
    ) -> None:
        """refresh_index accepts path within allowed_dirs."""
        req = RefreshIndexRequest(paths=[str(md_file)], force=False)
        result = await allowed_service.refresh_index(req)
        assert result is not None


# ── outline (regression guard) ────────────────────────────────────────────────


class TestOutlineAuthorization:
    async def test_denied_path_raises(
        self, denied_service: MdqService, md_file: Path
    ) -> None:
        """outline raises MdqAuthorizationError for denied path (regression guard)."""
        req = OutlineRequest(path=str(md_file))
        with pytest.raises(MdqAuthorizationError):
            await denied_service.outline(req)
