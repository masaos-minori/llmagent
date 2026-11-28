#!/usr/bin/env python3
"""Tests for index_scan.py discovery semantics (REQ-005, AC-4).

Matching is case-sensitive against the root-relative POSIX path, deduplication keys on
the canonical path, symlinked directories are not traversed, and a symlinked file
collapses to one canonical entry.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from mcp_servers.mdq.index_scan import iter_indexable_files
from mcp_servers.mdq.mdq_service import MdqService

from tests.mcp_servers.mdq._startup import make_startup


def _service(tmp_path: Path, **overrides: object) -> MdqService:
    service = MdqService(make_startup(str(tmp_path / "mdq.sqlite"), **overrides))
    service._allowed_dirs = [str(tmp_path)]
    return service


class TestGlobMatching:
    """include_globs / exclude_globs matching against the root-relative POSIX path."""

    @pytest.fixture()
    def service(self, tmp_path: Path) -> MdqService:
        return _service(tmp_path)

    def test_nested_exclude_matches_at_any_depth(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        nested = tmp_path / "src" / "__pycache__" / "nested"
        nested.mkdir(parents=True)
        (nested / "a.md").write_text("# A\n\nOne")
        (tmp_path / "src" / "keep.md").write_text("# K\n\nKeep")

        found = iter_indexable_files(service, tmp_path)

        assert [f.relative_to(tmp_path).as_posix() for f in found] == ["src/keep.md"]

    def test_exclude_is_case_sensitive(self, tmp_path: Path) -> None:
        service = _service(tmp_path, exclude_globs=["Secret/**"])
        secret = tmp_path / "Secret"
        secret.mkdir()
        (secret / "hidden.md").write_text("# H\n\nHidden")
        lower = tmp_path / "secret"
        lower.mkdir()
        (lower / "keep.md").write_text("# K\n\nKeep")

        found = iter_indexable_files(service, tmp_path)

        assert [f.relative_to(tmp_path).as_posix() for f in found] == ["secret/keep.md"]

    def test_include_is_case_sensitive(self, tmp_path: Path) -> None:
        service = _service(tmp_path)
        (tmp_path / "notes.md").write_text("# N\n\nNote")
        (tmp_path / "NOTES.MD").write_text("# X\n\nOther")

        found = iter_indexable_files(service, tmp_path)

        assert [f.name for f in found] == ["notes.md"]


class TestDeduplication:
    """Discovery reports each canonical path once."""

    @pytest.fixture()
    def service(self, tmp_path: Path) -> MdqService:
        return _service(tmp_path)

    def test_duplicate_include_patterns_yield_one_entry(self, tmp_path: Path) -> None:
        service = _service(tmp_path, include_globs=["*.md", "docs/*.md"])
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "a.md").write_text("# A\n\nOne")

        found = iter_indexable_files(service, tmp_path)

        assert [f.relative_to(tmp_path).as_posix() for f in found] == ["docs/a.md"]

    def test_symlinked_file_collapses_to_one_canonical_entry(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        target = tmp_path / "real.md"
        target.write_text("# R\n\nReal")
        os.symlink(target, tmp_path / "dup.md")

        found = iter_indexable_files(service, tmp_path)

        assert found == [target.resolve()]

    def test_symlinked_directory_is_not_traversed(
        self, service: MdqService, tmp_path: Path
    ) -> None:
        real = tmp_path / "real"
        real.mkdir()
        (real / "a.md").write_text("# A\n\nOne")
        os.symlink(real, tmp_path / "link")

        found = iter_indexable_files(service, tmp_path)

        assert [f.relative_to(real).as_posix() for f in found] == ["a.md"]
