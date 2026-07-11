#!/usr/bin/env python3
"""Split docs/*.md files that exceed 8KB into two files at the H2 boundary
closest to the midpoint, using the "-partN" fallback naming convention.
Rewrites Front Matter for each half and updates every cross-reference to
the original filename across docs/*.md and routing.md.

Usage:
    uv run python tools/split_oversized_docs.py file1.md file2.md ...
    (paths relative to docs/, or bare filenames)
"""

from __future__ import annotations

import glob
import re
import sys
from pathlib import Path

import yaml

ROOT_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT_DIR / "docs"


def split_front_matter(content: str) -> tuple[dict, str, str]:
    assert content.startswith("---")
    end = content.find("\n---", 3)
    raw = content[3:end]
    data = yaml.safe_load(raw) or {}
    rest = content[end + 4 :]
    if rest.startswith("\n"):
        rest = rest[1:]
    return data, raw, rest


def find_h2_offsets(body: str) -> list[int]:
    return [m.start() for m in re.finditer(r"(?m)^## ", body)]


def strip_tail(body: str) -> tuple[str, str]:
    """Remove the trailing Related Documents/Keywords block, return (main, tail_text)."""
    m = re.search(r"\n## Related Documents\n", body)
    if not m:
        return body, ""
    return body[: m.start()], body[m.start() :]


def build_front_matter(data: dict, title_suffix: str, source: str) -> str:
    lines = ["---"]
    lines.append(f'title: "{data["title"]} {title_suffix}"')
    lines.append(f"category: {data['category']}")
    lines.append("tags:")
    for t in data.get("tags", []):
        lines.append(f"  - {t}")
    lines.append("related:")
    for r in data.get("related", []):
        lines.append(f"  - {r}")
    lines.append("source:")
    lines.append(f"  - {source}")
    lines.append("---\n")
    return "\n".join(lines)


def make_tail(related_extra: list[str], keywords: list[str]) -> str:
    related_lines = "\n".join(f"- `{r}`" for r in related_extra)
    keyword_lines = "\n".join(keywords)
    return (
        f"\n## Related Documents\n\n{related_lines}\n\n## Keywords\n\n{keyword_lines}\n"
    )


def split_one(name: str) -> tuple[str, str] | None:
    path = DOCS_DIR / name
    content = path.read_text(encoding="utf-8")
    data, _raw_fm, body = split_front_matter(content)
    main_body, tail = strip_tail(body)

    lines = main_body.split("\n")

    boundary_offsets = [i for i, line in enumerate(lines) if line.startswith("## ")]
    level_used = "H2"
    if len(boundary_offsets) < 2:
        # fall back to H3 boundaries (skipping the very first one, which
        # typically opens right after the lone H2/H1 preamble)
        boundary_offsets = [
            i for i, line in enumerate(lines) if line.startswith("### ")
        ]
        level_used = "H3"
    if len(boundary_offsets) < 2:
        print(f"SKIP {name}: fewer than 2 H2/H3 sections, cannot split")
        return None

    preamble = lines[: boundary_offsets[0]]
    total_len = len(main_body)
    half = total_len / 2
    candidates = boundary_offsets[1:]  # never split right at the first boundary
    best_idx = min(candidates, key=lambda i: abs(len("\n".join(lines[:i])) - half))
    print(f"  ({name}: split at {level_used} boundary)")

    part1_lines = preamble + lines[boundary_offsets[0] : best_idx]
    part2_lines = preamble + lines[best_idx:]

    stem = name[:-3]  # strip .md
    part1_name = f"{stem}-part1.md"
    part2_name = f"{stem}-part2.md"

    related = data.get("related", [])

    fm1 = build_front_matter(data, "(Part 1)", name)
    fm2 = build_front_matter(data, "(Part 2)", name)

    tail_keywords = re.search(r"## Keywords\n\n(.+)", tail, re.DOTALL)
    keywords = (
        [k for k in tail_keywords.group(1).strip().split("\n") if k]
        if tail_keywords
        else data.get("tags", [])
    )

    related1 = related + [part2_name]
    related2 = related + [part1_name]

    out1 = (
        fm1 + "\n".join(part1_lines).rstrip("\n") + "\n" + make_tail(related1, keywords)
    )
    out2 = (
        fm2 + "\n".join(part2_lines).rstrip("\n") + "\n" + make_tail(related2, keywords)
    )

    (DOCS_DIR / part1_name).write_text(out1, encoding="utf-8")
    (DOCS_DIR / part2_name).write_text(out2, encoding="utf-8")
    path.unlink()
    print(
        f"split {name} -> {part1_name} ({len(out1.encode('utf-8'))}B), "
        f"{part2_name} ({len(out2.encode('utf-8'))}B)"
    )
    return part1_name, part2_name


def update_references(mapping: dict[str, str]) -> None:
    keys_sorted = sorted(mapping.keys(), key=len, reverse=True)
    files = glob.glob(str(DOCS_DIR / "*.md")) + [str(ROOT_DIR / "routing.md")]
    changed = 0
    for fp in files:
        p = Path(fp)
        content = p.read_text(encoding="utf-8")
        orig = content
        for old in keys_sorted:
            content = content.replace(old, mapping[old])
        if content != orig:
            p.write_text(content, encoding="utf-8")
            changed += 1
    print(f"updated references in {changed} files")


def main() -> None:
    names = sys.argv[1:]
    if not names:
        print("usage: split_oversized_docs.py <file.md> [file2.md ...]")
        return
    mapping: dict[str, str] = {}
    for name in names:
        name = Path(name).name
        result = split_one(name)
        if result:
            part1_name, _part2_name = result
            mapping[name] = part1_name  # representative target for stale references
    if mapping:
        update_references(mapping)


if __name__ == "__main__":
    main()
