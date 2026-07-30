#!/usr/bin/env python3
"""check_overview_docs_consistency.py — CI check for Overview/Architecture doc drift.

Companion to check_mcp_docs_consistency.py / check_deployment_docs_consistency.py,
covering docs/01_overview*.md. Currently a thin wrapper around
_docs_consistency_lib.check_directory_listing_completeness(), proving out that
shared check against the one concrete, confirmed drift found in the Overview
review (docs_review_overview_architecture.md): the repo-root `conf.d/`
directory tree in docs/01_overview-files-06-misc.md lists only `github-mcp`,
while `conf.d/` on disk also has `cicd-mcp`, `git-mcp`, and `web-search-mcp`.

Deliberately does *not* attempt to enforce completeness of the hand-maintained
scripts/ file trees in docs/01_overview-files-03-*.md /
01_overview-files-04-shared-part2.md -- the Overview review's own
recommendation for those was to delete the manually-kept listing in favor of
"see the implementation tree" (maintenance cost of keeping a full file
inventory in sync was judged not worth it), not to keep policing it.

Usage:
    python tools/check_overview_docs_consistency.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools._docs_consistency_lib import (
    Issue,
    check_directory_listing_completeness,
    discover_md_files,
    report_and_exit,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = REPO_ROOT / "docs"
CONF_D_DOC = "01_overview-files-06-misc.md"

_TREE_BRANCH_RE = re.compile(r"[├└]─\s*([A-Za-z0-9_.-]+)")


def check_conf_d_listing(docs_dir: Path, repo_root: Path) -> list[Issue]:
    files = discover_md_files(docs_dir, prefix=CONF_D_DOC.split("_", 1)[0])
    doc = next((f for f in files if f.rel_path == CONF_D_DOC), None)
    if doc is None:
        return []

    for line_no, line in enumerate(doc.lines, start=1):
        if line.strip() == "conf.d/":
            listed: set[str] = set()
            block_start = line_no
            for later_line in doc.lines[line_no:]:
                match = _TREE_BRANCH_RE.search(later_line)
                if match:
                    listed.add(match.group(1))
                    continue
                break
            return check_directory_listing_completeness(
                doc.rel_path,
                block_start,
                frozenset(listed),
                repo_root / "conf.d",
                label="conf.d/",
            )
    return []


def main() -> int:
    all_issues: list[Issue] = check_conf_d_listing(DOCS_DIR, REPO_ROOT)
    return report_and_exit(all_issues)


if __name__ == "__main__":
    raise SystemExit(main())
