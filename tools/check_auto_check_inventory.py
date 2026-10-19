#!/usr/bin/env python3
"""tools/check_auto_check_inventory.py

Non-blocking, ``Warning``-level audit for GV-014: cross-reference every
auto-check documented as ``Auto`` against an actual runnable script under
``tools/`` or ``scripts/``, flagging documented-but-absent or name-drifted
entries.

The checker parses the authoritative enumeration of auto-checks (the Governance
Verification Matrix ``Method = Auto`` cells in
``docs/00_governance/governance_04_documentation-checks.md`` and the tool table in
``routing.md``), discovers the real tool scripts dynamically at runtime, and
resolves each documented token by basename or relative path. A token with no
match is flagged at ``Warning``; a token with only a close (edit-distance)
candidate is reported as a non-blocking drift hint. Nothing here is blocking.
"""

from __future__ import annotations

import argparse
import difflib
import re
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

# Default authoritative sources of "auto-check" claims (GV-014). Overridable via
# --root so the same logic can point at a fixture tree in tests.
DEFAULT_GOVERNANCE_DOC = "docs/00_governance/governance_04_documentation-checks.md"
DEFAULT_ROUTING_DOC = "routing.md"

# Directories scanned for real tool scripts. Discovered dynamically; nothing here
# is hardcoded per tool (REQ-002).
TOOL_DIRS = ("tools", "scripts")

# Tokens that look like file paths but are alternative invocation names rather
# than tool files: pre-commit hook names and CI job names referenced in prose.
# Kept narrow -- a genuinely absent check must still surface, so this only hides
# names known not to map to a script.
ALTERNATIVE_INVOCATIONS = frozenset(
    {
        # pre-commit hook names (see .pre-commit-config.yaml)
        "check-suppression-justification",
        "docs-japanese",
        "mock-patch-targets",
        # CI job names (see .github/workflows/ci.yml)
        "lint",
        "typecheck",
        "security",
        "tests",
    }
)

# A documented token that looks like a Python file path: a bare basename
# (``check_foo.py``) or a ``tools/`` / ``scripts/`` relative path.
_PATH_TOKEN_RE = re.compile(r"[A-Za-z0-9_][\w./-]*\.py")

# A document parser: given raw Markdown text, yield ``(token, line_no)`` pairs.
ParseFn = Callable[[str], list[tuple[str, int]]]


@dataclass
class Issue:
    """One finding, mirroring the string-severity ``Issue`` used by ``tools/check_*.py``."""

    file: str
    line_no: int
    severity: str
    message: str


@dataclass
class ToolIndex:
    """Discovered tool scripts: their base names and repo-relative paths."""

    basenames: set[str]
    rel_paths: set[str]

    @classmethod
    def discover(cls, root: Path) -> ToolIndex:
        basenames: set[str] = set()
        rel_paths: set[str] = set()
        for dir_name in TOOL_DIRS:
            directory = root / dir_name
            if not directory.is_dir():
                continue
            for py in directory.rglob("*.py"):
                if not py.is_file():
                    continue
                rel = py.relative_to(root).as_posix()
                rel_paths.add(rel)
                basenames.add(py.name)
        return cls(basenames=basenames, rel_paths=rel_paths)


def iter_table_rows(text: str):
    """Yield ``(line_no, cells)`` for each Markdown table row, skipping code fences."""
    in_fence = False
    for line_no, raw in enumerate(text.splitlines(), start=1):
        stripped = raw.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in raw.split("|")[1:-1]]
        yield line_no, cells


def parse_governance_rows(text: str):
    """Documented tool tokens from ``governance_04`` ``Method = Auto`` matrix rows."""
    findings: list[tuple[str, int]] = []
    for line_no, cells in iter_table_rows(text):
        if not any(cell.lower() == "auto" for cell in cells):
            continue
        findings.extend(_path_tokens(" ".join(cells), line_no))
    return findings


def parse_routing_rows(text: str):
    """Documented tool tokens from ``routing.md``'s tool-table rows."""
    findings: list[tuple[str, int]] = []
    for line_no, cells in iter_table_rows(text):
        findings.extend(_path_tokens(" ".join(cells), line_no))
    return findings


def _path_tokens(line: str, line_no: int):
    return [(token, line_no) for token in _PATH_TOKEN_RE.findall(line)]


def _classify(token: str, index: ToolIndex) -> tuple[str, str]:
    """Return ``(status, detail)``: ``ok``, ``absent``, or ``drift:<candidate>``."""
    rel = token.replace("\\", "/")
    if rel in index.rel_paths or token.split("/")[-1] in index.basenames:
        return "ok", ""
    base = token.split("/")[-1]
    best_candidate: str | None = None
    best_ratio = 0.0
    for candidate in index.basenames:
        ratio = difflib.SequenceMatcher(None, base, candidate).ratio()
        if ratio > best_ratio:
            best_ratio, best_candidate = ratio, candidate
    if (
        best_candidate is not None
        and best_ratio >= 0.8
        and abs(len(base) - len(best_candidate)) <= max(2, int(0.2 * len(base)))
    ):
        return "drift", best_candidate
    return "absent", ""


def audit(sources: list[tuple[Path, ParseFn]], index: ToolIndex) -> list[Issue]:
    """Parse each source and resolve its documented tokens against ``index``."""
    issues: list[Issue] = []
    for doc_path, parse_fn in sources:
        text = doc_path.read_text(encoding="utf-8")
        for token, line_no in parse_fn(text):
            if token in ALTERNATIVE_INVOCATIONS:
                continue
            status, detail = _classify(token, index)
            if status == "ok":
                continue
            if status == "drift":
                issues.append(
                    Issue(
                        str(doc_path),
                        line_no,
                        "WARNING",
                        f"name drift: `{token}` has no exact match; closest is `{detail}`",
                    )
                )
            else:
                issues.append(
                    Issue(
                        str(doc_path),
                        line_no,
                        "WARNING",
                        f"documented-but-absent: `{token}` has no matching script "
                        f"under {'/'.join(TOOL_DIRS)}",
                    )
                )
    return issues


def _default_sources(root: Path) -> list[tuple[Path, ParseFn]]:
    sources: list[tuple[Path, ParseFn]] = []
    governance = root / DEFAULT_GOVERNANCE_DOC
    routing = root / DEFAULT_ROUTING_DOC
    if governance.exists():
        sources.append((governance, parse_governance_rows))
    if routing.exists():
        sources.append((routing, parse_routing_rows))
    return sources


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Audit auto-checks documented as Auto against runnable tools.",
    )
    parser.add_argument(
        "--root",
        default=str(ROOT_DIR),
        help="Repository root to scan (default: the repo containing this tool).",
    )
    args = parser.parse_args(argv)

    root = Path(args.root)
    index = ToolIndex.discover(root)
    issues = audit(_default_sources(root), index)

    print(f"\n{'=' * 60}")
    print("Auto-Check Inventory Audit (GV-014)")
    print(f"{'=' * 60}")
    if issues:
        print(f"\n{len(issues)} finding(s):")
        for issue in sorted(issues, key=lambda x: (x.file, x.line_no)):
            print(f"[{issue.severity}] {issue.file}:{issue.line_no} — {issue.message}")
    else:
        print("\nNo documented-but-absent or drifted auto-checks found.")
    print(f"{'=' * 60}\n")

    # Non-blocking: findings are advisory (Warning-level), never fail the gate.
    return 0


if __name__ == "__main__":
    sys.exit(main())
