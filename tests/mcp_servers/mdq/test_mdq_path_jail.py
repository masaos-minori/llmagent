"""tests/test_mdq_path_jail.py
Fail-closed path authorization tests for MDQ path-accepting tools.

Verifies that index_paths, refresh_index (via _validate_paths), and
outline all raise MdqAuthorizationError instead of silently skipping
denied paths. Also pins the canonicalized-prefix cases for the SQL source
predicate (REQ-002): source
issues/20261119-142124_mdqmcp002_mdq-search-query-boundary.md.
"""

from __future__ import annotations

import os
from pathlib import Path
from tempfile import mkstemp

import pytest
from mcp_servers.mdq.auth import canonicalized_roots
from mcp_servers.mdq.indexer import index_paths
from mcp_servers.mdq.mdq_models import (
    IndexPathsRequest,
    MdqAuthorizationError,
    OutlineRequest,
    RefreshIndexRequest,
    SearchDocsRequest,
)
from mcp_servers.mdq.mdq_service import MdqService
from mcp_servers.mdq.search import _search_docs_structured

from tests.mcp_servers.mdq._startup import make_startup

# ── fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def allowed_service(tmp_path: Path) -> MdqService:
    """MdqService with tmp_path in allowed_dirs."""
    fd, db = mkstemp(suffix=".db", dir=str(tmp_path))
    os.close(fd)
    svc = MdqService(make_startup(db))
    svc._allowed_dirs = [str(tmp_path)]
    return svc


@pytest.fixture
def denied_service(tmp_path: Path) -> MdqService:
    """MdqService with empty allowed_dirs (deny-all)."""
    fd, db = mkstemp(suffix=".db", dir=str(tmp_path))
    os.close(fd)
    svc = MdqService(make_startup(db))
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
        text, _metadata = await index_paths(allowed_service, req)
        assert "complete" in text.lower()

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
        svc = MdqService(make_startup(db))
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
        svc = MdqService(make_startup(db))
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
        text, _metadata = await index_paths(allowed_service, req)
        assert "complete" in text.lower()


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
        text, metadata = await allowed_service.refresh_index(req)
        assert text is not None
        assert metadata is not None


# ── outline (regression guard) ────────────────────────────────────────────────


class TestOutlineAuthorization:
    async def test_denied_path_raises(
        self, denied_service: MdqService, md_file: Path
    ) -> None:
        """outline raises MdqAuthorizationError for denied path (regression guard)."""
        req = OutlineRequest(path=str(md_file))
        with pytest.raises(MdqAuthorizationError):
            await denied_service.outline(req)


# ── SQL source predicate (canonicalized roots) ────────────────────────────────


class TestSearchSourcePredicate:
    async def test_canonicalized_roots_resolves_allowlist_entries(
        self, tmp_path: Path
    ) -> None:
        """`canonicalized_roots()` returns the same resolved values the authorization
        decision compares, skipping entries that fail to resolve.
        """
        real_root = tmp_path / "real-root"
        real_root.mkdir()
        link_root = tmp_path / "link-root"
        link_root.symlink_to(real_root)

        roots = canonicalized_roots([str(link_root), str(real_root / ".." / "x")])
        assert roots == [
            str(real_root.resolve()),
            str((real_root / ".." / "x").resolve()),
        ]

    async def test_prefix_outside_allowed_dirs_excluded_by_the_predicate(
        self, tmp_path: Path
    ) -> None:
        """Fails first (recorded 20261128): the count query has no authorized-source
        predicate today, so a row in a sibling directory that shares the textual prefix
        of the allowlist root is reported. Post-change, the predicate must match the
        canonicalized root with the path separator boundary.
        """
        root = tmp_path / "root"
        sibling = tmp_path / "root_evil"
        root.mkdir()
        sibling.mkdir()
        (sibling / "evil.md").write_text(
            "# PrefixTrap\n\nUniformTrap content.", encoding="utf-8"
        )
        svc = MdqService(make_startup(str(tmp_path / "pred.db")))
        # Index with the sibling authorized, then narrow the allowlist to `root`: the row
        # shares the textual prefix of the root but is outside it.
        svc._allowed_dirs = [str(sibling)]
        await index_paths(svc, IndexPathsRequest(paths=[str(sibling / "evil.md")]))
        svc._allowed_dirs = [str(root)]
        result = _search_docs_structured(svc, SearchDocsRequest(query="UniformTrap"))
        assert result["matched_count"] == 0
        assert result["results"] == []

    async def test_symlinked_root_predicate_compares_canonicalized_values(
        self, tmp_path: Path
    ) -> None:
        """Guard (green today via the Python gate, green post-change through the predicate):
        rows stored under the canonicalized root stay visible when the allowlist entry is a
        symlink to that root.
        """
        real_root = tmp_path / "real-root"
        real_root.mkdir()
        link_root = tmp_path / "link-root"
        link_root.symlink_to(real_root)
        (real_root / "doc.md").write_text(
            "# Canonical\n\nCanonicalProbe content.", encoding="utf-8"
        )

        svc = MdqService(make_startup(str(tmp_path / "canon.db")))
        svc._allowed_dirs = [str(link_root)]
        await index_paths(svc, IndexPathsRequest(paths=[str(real_root)]))

        result = _search_docs_structured(svc, SearchDocsRequest(query="CanonicalProbe"))
        assert result["matched_count"] == 1
        assert len(result["results"]) == 1
        assert result["results"][0].source_path.startswith(str(real_root.resolve()))
