#!/usr/bin/env python3
"""scripts/mcp_servers/mdq/index_scan.py

Indexable-file discovery for the mdq indexer — which files under a directory the
indexer may read, decided from the service's configured include_globs / exclude_globs.

Split out of mcp_servers.mdq.indexer: the indexer owns connections, tallies and the
index/refresh flow; this module owns only glob matching and directory scanning, and
holds no database access.

Dependency direction: index_scan → none at runtime (MdqService is TYPE_CHECKING-only)
Import from here:  from mcp_servers.mdq.index_scan import iter_indexable_files
"""

from __future__ import annotations

import fnmatch
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp_servers.mdq.mdq_service import MdqService


def _matches_any_glob(rel_posix: str, patterns: list[str]) -> bool:
    """Return True if rel_posix matches any of patterns, at any path depth.

    pathlib.Path.match() was tried first and rejected: it right-aligns only
    as many path segments as the pattern has, so ".git/**" (2 segments) does
    not match ".git/objects/pack/file.pack" (4 segments) -- verified
    empirically against the mdq service's default exclude_globs value
    ([".git/**", "__pycache__/**"]) on a real directory tree before choosing
    this implementation.

    fnmatch against the full relative path handles root-anchored occurrences
    (e.g. ".git/objects/pack/file.pack" against ".git/**") but still misses
    nested occurrences that don't start at the path root (e.g.
    "src/__pycache__/nested/a.pyc" against "__pycache__/**"). To catch both,
    fnmatch is applied against every path suffix (the substring starting at
    each path component), not just the full path.
    """
    parts = rel_posix.split("/")
    for i in range(len(parts)):
        suffix = "/".join(parts[i:])
        if any(fnmatch.fnmatch(suffix, pattern) for pattern in patterns):
            return True
    return False


def iter_indexable_files(service: MdqService, directory: Path) -> list[Path]:
    """Return indexable files under directory per service.include_globs/exclude_globs.

    Replaces hardcoded rglob("*.md") call sites so indexing honors the
    configured include_globs / exclude_globs (config/mdq_mcp_server.toml).
    """
    include_globs = service.include_globs
    exclude_globs = service.exclude_globs
    matched: dict[str, Path] = {}
    for pattern in include_globs:
        for f in directory.rglob(pattern):
            if not f.is_file():
                continue
            rel_posix = f.relative_to(directory).as_posix()
            if _matches_any_glob(rel_posix, exclude_globs):
                continue
            matched[str(f)] = f
    return sorted(matched.values())
