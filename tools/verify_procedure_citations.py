"""Print each numeric citation in a procedure document with the source line it points at.

Content identity cannot confirm that a citation still states the same thing, so this tool
shows the citation and the source line it resolves to, and flags the cases where the symbol
named on the same document line is not present at the cited line. Use it to review citations
before rewriting them.

Usage:
    uv run python tools/verify_procedure_citations.py [--docs GLOB] [--plan PATH] [--mismatches-only]
"""

from __future__ import annotations

import argparse
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
CITE = re.compile(
    r"`?([A-Za-z0-9_./-]+\.(?:py|toml|md|importlinter)):(\d+)(?:-(\d+))?((?:,\d+(?:-\d+)?)*)`?"
)
PATH = re.compile(r"`?([A-Za-z0-9_./-]+\.(?:py|toml|md|importlinter))`?")
BARE = re.compile(r"(?:line|lines|at)\s+(\d{1,4})(?:-(\d{1,4}))?")
PAREN = re.compile(r"`([A-Za-z0-9_]+)`\s*\((\d{1,3})(?:-(\d{1,3}))?\)")
SYMBOL = re.compile(r"`([A-Za-z0-9_]{3,})`")


def source_lines(path: str) -> list[str]:
    file_path = ROOT / path
    if not file_path.is_file():
        return []
    return file_path.read_text(encoding="utf-8").splitlines()


def citations(line: str, target: str | None):
    for match in CITE.finditer(line):
        for token in [
            match.group(2) + (f"-{match.group(3)}" if match.group(3) else "")
        ] + [token for token in (match.group(4) or "").split(",") if token]:
            yield match.group(1), token, None
    for segment in BARE.finditer(line):
        context = PATH.search(line[: segment.start()])
        path = context.group(1) if context else target
        if path:
            names = SYMBOL.findall(line[: segment.start()])
            yield (
                path,
                segment.group(1) + (f"-{segment.group(2)}" if segment.group(2) else ""),
                names[-1] if names else None,
            )
    for segment in PAREN.finditer(line):
        if target:
            yield target, segment.group(1) + f"({segment.group(2)})", segment.group(1)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Show procedure-document citations against the source lines they point at."
    )
    parser.add_argument("--docs", default="implementations/20261128-*_*.md")
    parser.add_argument(
        "--plan",
        default="plans/done/20261127-203046_mdqmcp010_mdq-release-readiness.md",
    )
    parser.add_argument("--mismatches-only", action="store_true")
    args = parser.parse_args()

    documents = sorted(ROOT.glob(args.docs))
    if args.plan:
        documents.append(ROOT / args.plan)

    flagged = 0
    for doc in documents:
        text = doc.read_text(encoding="utf-8")
        match = re.search(r"### Target file\n`([^`]+)`", text)
        target = match.group(1) if match else None
        for number, line in enumerate(text.splitlines(), 1):
            for path, token, symbol in citations(line, target):
                numbers = re.findall(r"\d+", token)
                start = int(numbers[0])
                end = int(numbers[1]) if len(numbers) > 1 else start
                source = source_lines(path)
                seen = (
                    source[start - 1][:90]
                    if len(source) >= start
                    else "beyond end of file"
                )
                window = source[start - 1 : max(start, end)]
                if symbol and symbol not in "\n".join(source):
                    symbol = None
                mismatch = bool(symbol) and not any(symbol in row for row in window)
                if mismatch:
                    flagged += 1
                    print(f"{doc.name}:{number}: {token} -> {path}:{start} | {seen}")
                    print(f"  claim: {line.strip()[:140]}")
                elif not args.mismatches_only:
                    print(f"{doc.name}:{number}: {token} -> {path}:{start} | {seen}")

    print("flagged:", flagged)
    return 1 if flagged else 0


if __name__ == "__main__":
    raise SystemExit(main())
