#!/usr/bin/env python3
"""check_rag_docs_consistency.py — CI check for RAG documentation drift.

Companion to check_mcp_docs_consistency.py / check_deployment_docs_consistency.py,
covering docs/03_rag_*.md. Grounded in confirmed findings from manual review
(docs_review_rag.md's "横断的な確定済み誤り" list):

  - docs/03_rag_01_system_overview-part2.md claims the crawler goes "最大6ホップ"
    / "最大500ページ", but config/crawler.toml actually sets max_depth=3,
    max_pages=200 (and docs/03_rag_02_02_ingestion_pipeline-crawler-part1.md
    already states the correct 3-hop figure -- an internal contradiction).
  - docs/03_rag_03_02_query_pipeline-rag-pipeline-class-part2.md and
    docs/03_rag_03_04_query_pipeline-search-stages.md both quote a literal
    `/rag search --debug` output containing "[debug] ...", but the string
    "[debug]" does not appear anywhere under scripts/ -- the example output
    does not exist.

The generic reference checks (file paths, function names) are shared with
check_mcp_docs_consistency.py via _docs_consistency_lib.py and already catch
several other confirmed findings from the same review (e.g. the nonexistent
`delete_existing_document()` method name in
docs/03_rag_02_04_ingestion_pipeline-ingester-part1.md, and the bare
`server.py`/`service.py`/`models.py` filenames in
docs/03_rag_05_1-configuration-reference.md).

Checks:
    --skip links        Skip broken internal Markdown link detection
    --skip removedfiles Skip removed-legacy-doc-file reference check
    --skip commanddrift Skip slash-command drift vs command_defs_list.py (WARNING)
    --skip filerefs     Skip scripts/-path reference existence check (WARNING)
    --skip funcrefs      Skip backtick-quoted function()-reference existence check (WARNING)
    --skip crawlerconfig Skip crawler max_depth/max_pages claim vs config/crawler.toml (ERROR)
    --skip debugoutput  Skip fabricated `[debug] ...` output example check (ERROR)

Usage:
    python tools/check_rag_docs_consistency.py
"""

from __future__ import annotations

import argparse
import re
import sys
import tomllib
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools._docs_consistency_lib import (
    DocFile,
    Issue,
    check_broken_internal_links,
    check_command_drift,
    check_file_path_references,
    check_function_references,
    check_removed_file_references,
    discover_md_files,
    is_historical_line,
    report_and_exit,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = REPO_ROOT / "docs"
CRAWLER_TOML = REPO_ROOT / "config" / "crawler.toml"

# ---------------------------------------------------------------------------
# Check: crawler max_depth/max_pages claim vs config/crawler.toml (ERROR)
# ---------------------------------------------------------------------------

_HOP_CLAIM_RE = re.compile(r"最大\s*(\d+)\s*ホップ")
_PAGE_CLAIM_RE = re.compile(r"最大\s*(\d+)\s*ページ")


def _crawler_config_values(repo_root: Path) -> tuple[int, int] | None:
    if not CRAWLER_TOML.is_file():
        return None
    with CRAWLER_TOML.open("rb") as f:
        cfg = tomllib.load(f)
    max_depth = cfg.get("max_depth")
    max_pages = cfg.get("max_pages")
    if not isinstance(max_depth, int) or not isinstance(max_pages, int):
        return None
    return max_depth, max_pages


def check_crawler_config_drift(
    docs_dir: Path, files: list[DocFile], repo_root: Path
) -> list[Issue]:
    """Flag "最大Nホップ"/"最大Nページ" claims that disagree with config/crawler.toml."""
    values = _crawler_config_values(repo_root)
    if values is None:
        return []
    max_depth, max_pages = values

    issues: list[Issue] = []
    for doc in files:
        for line_no, line in enumerate(doc.lines, start=1):
            if is_historical_line(line):
                continue
            hop_match = _HOP_CLAIM_RE.search(line)
            if hop_match and int(hop_match.group(1)) != max_depth:
                issues.append(
                    Issue(
                        file=doc.rel_path,
                        line_no=line_no,
                        severity="ERROR",
                        message=(
                            f"claims max depth {hop_match.group(1)!r} hops, but "
                            f"config/crawler.toml sets max_depth={max_depth}"
                        ),
                    )
                )
            page_match = _PAGE_CLAIM_RE.search(line)
            if page_match and int(page_match.group(1)) != max_pages:
                issues.append(
                    Issue(
                        file=doc.rel_path,
                        line_no=line_no,
                        severity="ERROR",
                        message=(
                            f"claims max {page_match.group(1)!r} pages, but "
                            f"config/crawler.toml sets max_pages={max_pages}"
                        ),
                    )
                )
    return issues


# ---------------------------------------------------------------------------
# Check: fabricated `[debug] ...` output example (ERROR)
# ---------------------------------------------------------------------------

_DEBUG_OUTPUT_RE = re.compile(r"`(\[debug\][^`]*)`")


def check_debug_output_existence(
    docs_dir: Path, files: list[DocFile], repo_root: Path
) -> list[Issue]:
    """Flag a literal `[debug] ...` output example when "[debug]" appears nowhere in scripts/."""
    scripts_dir = repo_root / "scripts"
    if not scripts_dir.is_dir():
        return []
    exists_in_code = any(
        "[debug]" in py_file.read_text(encoding="utf-8")
        for py_file in scripts_dir.rglob("*.py")
    )
    if exists_in_code:
        return []

    issues: list[Issue] = []
    for doc in files:
        for line_no, line in enumerate(doc.lines, start=1):
            if is_historical_line(line):
                continue
            for match in _DEBUG_OUTPUT_RE.finditer(line):
                issues.append(
                    Issue(
                        file=doc.rel_path,
                        line_no=line_no,
                        severity="ERROR",
                        message=(
                            f"quotes literal output {match.group(1)[:60]!r}, but "
                            f"the string '[debug]' does not appear anywhere "
                            f"under scripts/ (fabricated example output)"
                        ),
                    )
                )
    return issues


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check RAG documentation consistency.",
    )
    parser.add_argument(
        "--skip",
        nargs="+",
        choices=[
            "links",
            "removedfiles",
            "commanddrift",
            "filerefs",
            "funcrefs",
            "crawlerconfig",
            "debugoutput",
        ],
        help="Skip one or more checks",
    )
    args = parser.parse_args(argv)
    skip = set(args.skip or [])

    files = discover_md_files(DOCS_DIR, prefix="03_rag_")

    all_issues: list[Issue] = []
    if "links" not in skip:
        all_issues += check_broken_internal_links(DOCS_DIR, files)
    if "removedfiles" not in skip:
        all_issues += check_removed_file_references(DOCS_DIR, files)
    if "commanddrift" not in skip:
        all_issues += check_command_drift(DOCS_DIR, files, REPO_ROOT)
    if "filerefs" not in skip:
        all_issues += check_file_path_references(DOCS_DIR, files, REPO_ROOT)
    if "funcrefs" not in skip:
        all_issues += check_function_references(DOCS_DIR, files, REPO_ROOT)
    if "crawlerconfig" not in skip:
        all_issues += check_crawler_config_drift(DOCS_DIR, files, REPO_ROOT)
    if "debugoutput" not in skip:
        all_issues += check_debug_output_existence(DOCS_DIR, files, REPO_ROOT)

    return report_and_exit(all_issues)


if __name__ == "__main__":
    raise SystemExit(main())
