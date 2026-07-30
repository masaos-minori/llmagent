#!/usr/bin/env python3
"""check_deployment_docs_consistency.py — CI check for deployment documentation drift.

Companion to check_mcp_docs_consistency.py / check_agent_docs_consistency.py,
covering docs/02_deployment*.md. Grounded in confirmed findings from manual
review (docs_review_deployment.md):

  - docs/02_deployment-part2.md §3.0 claims "three SQLite databases" and its
    overview table lists rag.sqlite/session.sqlite/workflow.sqlite, omitting
    eventbus.sqlite -- scripts/db/config.py's DbConfig actually declares four
    `*_db_path` fields.
  - The same section claims all DB paths are "configured in agent.toml", but
    workflow_db_path has no literal entry in config/agent.toml (it silently
    falls back to DbConfig's Python-level default).
  - docs/02_deployment-part1.md states the MCP port range as "8004-8014"
    (matching config/agent.toml), while deploy/setup_services.sh's comments
    say "8004-8016" in three places -- no server is actually assigned ports
    8015/8016 (8015 is the separate Event Bus process).

Checks:
    --skip dbcount    Skip "N SQLite databases" claim vs scripts/db/config.py field count (ERROR)
    --skip dbtable    Skip DB-overview-table completeness vs known DB names (ERROR)
    --skip configkey  Skip cited `*_db_path` config key presence in config/agent.toml (WARNING)
    --skip portrange  Skip "ports NNNN-NNNN" MCP range vs config/agent.toml (ERROR)

Usage:
    python tools/check_deployment_docs_consistency.py
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools._docs_consistency_lib import (
    DocFile,
    Issue,
    discover_md_files,
    report_and_exit,
)
from tools.check_mcp_docs_consistency import _extract_authoritative_ports

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = REPO_ROOT / "docs"
DEPLOY_DIR = REPO_ROOT / "deploy"
AGENT_TOML = REPO_ROOT / "config" / "agent.toml"
DB_CONFIG_SRC = REPO_ROOT / "scripts" / "db" / "config.py"

_NUMBER_WORDS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
}


def _known_db_names(repo_root: Path) -> list[str]:
    """Return e.g. ['eventbus.sqlite', 'rag.sqlite', ...] from DbConfig's *_db_path fields."""
    if not DB_CONFIG_SRC.is_file():
        return []
    content = DB_CONFIG_SRC.read_text(encoding="utf-8")
    fields = re.findall(r"^\s+(\w+_db_path):\s*str", content, re.MULTILINE)
    return sorted(f"{f.removesuffix('_db_path')}.sqlite" for f in fields)


# ---------------------------------------------------------------------------
# Check: "N SQLite databases" claim vs actual DbConfig field count (ERROR)
# ---------------------------------------------------------------------------

_DB_COUNT_CLAIM_RE = re.compile(
    r"(?:uses|has)\s+(" + "|".join(_NUMBER_WORDS) + r")\s+SQLite databases?",
    re.IGNORECASE,
)


def check_db_count_claim(
    docs_dir: Path, files: list[DocFile], repo_root: Path
) -> list[Issue]:
    known = _known_db_names(repo_root)
    if not known:
        return []
    issues: list[Issue] = []
    for doc in files:
        for line_no, line in enumerate(doc.lines, start=1):
            match = _DB_COUNT_CLAIM_RE.search(line)
            if not match:
                continue
            declared = _NUMBER_WORDS[match.group(1).lower()]
            if declared != len(known):
                issues.append(
                    Issue(
                        file=doc.rel_path,
                        line_no=line_no,
                        severity="ERROR",
                        message=(
                            f"claims {match.group(1)!r} SQLite databases ({declared}), "
                            f"but scripts/db/config.py's DbConfig declares "
                            f"{len(known)}: {', '.join(known)}"
                        ),
                    )
                )
    return issues


# ---------------------------------------------------------------------------
# Check: DB-overview-table completeness (ERROR)
# ---------------------------------------------------------------------------

_TABLE_ROW_SQLITE_RE = re.compile(r"`([a-z]+\.sqlite)`")


def check_db_table_completeness(
    docs_dir: Path, files: list[DocFile], repo_root: Path
) -> list[Issue]:
    known = set(_known_db_names(repo_root))
    if not known:
        return []
    issues: list[Issue] = []
    for doc in files:
        block_start: int | None = None
        found: set[str] = set()
        for line_no, line in enumerate(doc.lines, start=1):
            if line.strip().startswith("|"):
                if block_start is None:
                    block_start = line_no
                found.update(_TABLE_ROW_SQLITE_RE.findall(line))
                continue
            if block_start is not None:
                if len(found) >= 2:
                    missing = sorted(known - found)
                    if missing:
                        issues.append(
                            Issue(
                                file=doc.rel_path,
                                line_no=block_start,
                                severity="ERROR",
                                message=(
                                    f"DB table lists {sorted(found)} but is missing "
                                    f"{missing} (known DBs per scripts/db/config.py)"
                                ),
                            )
                        )
                block_start = None
                found = set()
    return issues


# ---------------------------------------------------------------------------
# Check: cited `*_db_path` config key presence in config/agent.toml (WARNING)
# ---------------------------------------------------------------------------

_CONFIG_KEY_RE = re.compile(r"`(\w+_db_path)`")


def check_config_key_presence(
    docs_dir: Path, files: list[DocFile], repo_root: Path
) -> list[Issue]:
    if not AGENT_TOML.is_file():
        return []
    toml_content = AGENT_TOML.read_text(encoding="utf-8")
    toml_keys = set(re.findall(r"^(\w+)\s*=", toml_content, re.MULTILINE))

    issues: list[Issue] = []
    for doc in files:
        for line_no, line in enumerate(doc.lines, start=1):
            for key in _CONFIG_KEY_RE.findall(line):
                if key not in toml_keys:
                    issues.append(
                        Issue(
                            file=doc.rel_path,
                            line_no=line_no,
                            severity="WARNING",
                            message=(
                                f"doc cites config key `{key}` but it has no "
                                f"literal entry in config/agent.toml (may rely "
                                f"on a Python-level default; verify)"
                            ),
                        )
                    )
    return issues


# ---------------------------------------------------------------------------
# Check: MCP "ports NNNN-NNNN" range vs config/agent.toml (ERROR)
# ---------------------------------------------------------------------------

_PORT_RANGE_RE = re.compile(r"\b(80\d{2})\s*[-–]\s*(80\d{2})\b")


def _expected_mcp_port_range(repo_root: Path) -> tuple[int, int] | None:
    ports = _extract_authoritative_ports(repo_root)
    if not ports:
        return None
    values = [int(p) for p in ports.values()]
    return min(values), max(values)


def check_mcp_port_range(
    docs_dir: Path, files: list[DocFile], repo_root: Path
) -> list[Issue]:
    expected = _expected_mcp_port_range(repo_root)
    if expected is None:
        return []
    exp_min, exp_max = expected

    issues: list[Issue] = []

    def scan(rel_path: str, lines: list[str]) -> None:
        for line_no, line in enumerate(lines, start=1):
            if "mcp" not in line.lower():
                continue
            for match in _PORT_RANGE_RE.finditer(line):
                lo, hi = int(match.group(1)), int(match.group(2))
                if (lo, hi) != (exp_min, exp_max):
                    issues.append(
                        Issue(
                            file=rel_path,
                            line_no=line_no,
                            severity="ERROR",
                            message=(
                                f"states MCP port range {lo}-{hi}, but "
                                f"config/agent.toml's mcp_servers span "
                                f"{exp_min}-{exp_max}"
                            ),
                        )
                    )

    for doc in files:
        scan(doc.rel_path, doc.lines)
    if DEPLOY_DIR.is_dir():
        for sh_path in sorted(DEPLOY_DIR.glob("*.sh")):
            rel = f"deploy/{sh_path.name}"
            scan(rel, sh_path.read_text(encoding="utf-8").splitlines())

    return issues


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check deployment documentation consistency.",
    )
    parser.add_argument(
        "--skip",
        nargs="+",
        choices=["dbcount", "dbtable", "configkey", "portrange"],
        help="Skip one or more checks",
    )
    args = parser.parse_args(argv)
    skip = set(args.skip or [])

    files = discover_md_files(DOCS_DIR, prefix="02_deployment")

    all_issues: list[Issue] = []
    if "dbcount" not in skip:
        all_issues += check_db_count_claim(DOCS_DIR, files, REPO_ROOT)
    if "dbtable" not in skip:
        all_issues += check_db_table_completeness(DOCS_DIR, files, REPO_ROOT)
    if "configkey" not in skip:
        all_issues += check_config_key_presence(DOCS_DIR, files, REPO_ROOT)
    if "portrange" not in skip:
        all_issues += check_mcp_port_range(DOCS_DIR, files, REPO_ROOT)

    return report_and_exit(all_issues)


if __name__ == "__main__":
    raise SystemExit(main())
