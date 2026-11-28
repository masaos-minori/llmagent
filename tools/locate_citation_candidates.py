"""tools/locate_citation_candidates.py

Candidate line numbers for a citation that `tools/verify_procedure_citations.py` flags, so a
stale citation can be rewritten by content instead of by renumbering.

Renumbering only proves the cited content still exists at one position. When the symbol the
claim names is not at the cited line, the correct number is wherever that symbol is in the file,
and a claim whose symbol is nowhere in the file cannot be fixed by moving a number. This tool
prints each flagged citation with the lines where its symbol appears, so a single candidate can
be applied directly and a multi-candidate or no-candidate citation is read against the claim.

A citation is skipped when its symbol is already at the cited line, or when the symbol does not
appear anywhere in the cited file. Construct citations (a dict key, an assertion inside a method,
a field of a class, `markers = [`) name a symbol that is not on the cited line by design, so they
appear here only when the symbol also occurs elsewhere; those are accepted as written.

Read-only. Exit 1 when at least one flagged citation has a candidate position elsewhere in the
file, 0 when none does.

Usage:
    uv run python tools/locate_citation_candidates.py [--docs GLOB] [--plan PATH]
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
if __package__ in (None, ""):
    sys.path.insert(0, str(ROOT_DIR))

from tools.verify_procedure_citations import citations, source_lines

MAX_CANDIDATES = 12


def candidate_lines(path: str, symbol: str) -> list[int]:
    """1-based lines of `path` at current HEAD that contain `symbol`."""
    source = source_lines(path)
    return [number for number, line in enumerate(source, 1) if symbol in line]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="List candidate positions for citations the citation verifier flags."
    )
    parser.add_argument("--docs", default="implementations/20261128-*_*.md")
    parser.add_argument(
        "--plan",
        default="plans/done/20261127-203046_mdqmcp010_mdq-release-readiness.md",
    )
    args = parser.parse_args()

    documents = sorted(ROOT_DIR.glob(args.docs))
    if args.plan:
        documents.append(ROOT_DIR / args.plan)

    actionable = 0
    for doc in documents:
        text = doc.read_text(encoding="utf-8")
        match = re.search(r"### Target file\n`([^`]+)`", text)
        target = match.group(1) if match else None
        for number, line in enumerate(text.splitlines(), 1):
            for path, token, symbol in citations(line, target):
                if not symbol:
                    continue
                source = source_lines(path)
                if not source:
                    continue
                nums = [int(part) for part in re.findall(r"\d+", token)]
                start, end = nums[0], nums[1] if len(nums) > 1 else nums[0]
                window = source[start - 1 : max(start, end)]
                if symbol in "\n".join(window):
                    continue
                found = candidate_lines(path, symbol)
                if not found:
                    continue
                actionable += 1
                print(f"{doc.name}:{number}: {token} -> {path}:{start}")
                print(f"  symbol: {symbol} | candidates: {found[:MAX_CANDIDATES]}")
                print(f"  claim: {line.strip()[:140]}")

    print("actionable:", actionable)
    return 1 if actionable else 0


if __name__ == "__main__":
    raise SystemExit(main())
