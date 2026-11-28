"""Verify and renumber source-line citations in procedure documents after a rebase.

Procedure documents cite source lines as they were at the revision the pass verified them
against. When a later rebase moves or deletes those lines, the citation is stale. This tool
compares a base revision with the current HEAD for every file that differs between them, and
rewrites a citation only when the cited content is still present at a resolvable position.

Citation forms handled:
- `path.py:12` and `path.py:12-20`, including comma-separated lists. A file name without a
  directory is resolved against the file named earlier on the same line, then the document's
  `### Target file`, then the changed files that share the name.
- Bare "line 12", "lines 12-20", "at 12", attributed to the file named earlier in the same
  line, or to the document's `### Target file` when no file is named.
- `Name (12)`, attributed to the document's `### Target file`, when the name is present at the
  resolved line.

With `--accept-mapped`, a citation whose cited block still exists line by line but with
modified content is renumbered to the mapped position when the claim's symbol is still inside
that block; each such citation is still listed so the sentence can be re-read against the
current content, because a moved number does not by itself mean the claim is still true.

A citation whose content no longer exists, that matches more than one position, or whose file
does not exist in the base revision is reported for manual rewriting rather than renumbered:
a moved line number is not the same as a still-true claim, and a semantic claim can be wrong
even when the number matches.

Documents are read as they were written at `--doc-rev`, so the numbers being resolved are the
evidence-revision numbers, never numbers this tool already rewrote. Writes apply to the
working tree by substituting the citation string found there, so a line the previous pass
already corrected is left alone.

Usage:
    uv run python tools/fix_citation_drift.py --base <revision> [--docs GLOB] [--plan PATH] [--dry-run]
"""

from __future__ import annotations

import argparse
import collections
import pathlib
import re
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
CITE = re.compile(
    r"`?([A-Za-z0-9_./-]+\.(?:py|toml|md|importlinter)):(\d+)(?:-(\d+))?((?:,\d+(?:-\d+)?)*)`?"
)
PATH = re.compile(r"`?([A-Za-z0-9_./-]+\.(?:py|toml|md|importlinter))`?")
BARE = re.compile(r"(?:line|lines|at)\s+(\d{1,4})(?:-(\d{1,4}))?")
PAREN = re.compile(r"`([A-Za-z0-9_]+)`\s*\((\d{1,3})(?:-(\d{1,3}))?\)")
SYMBOL = re.compile(r"`([A-Za-z0-9_]{3,})`")


def git_show(rev: str, path: str) -> list[str] | None:
    result = subprocess.run(
        ["git", "show", f"{rev}:{path}"], capture_output=True, text=True, cwd=ROOT
    )
    if result.returncode != 0:
        return None
    return result.stdout.splitlines()


def current(path: str) -> list[str]:
    file_path = ROOT / path
    if not file_path.is_file():
        return []
    return file_path.read_text(encoding="utf-8").splitlines()


def diff_mapping(base: str, head: str, path: str) -> dict[int, int | None]:
    """Base line number to current line number, from the diff hunks."""
    diff = subprocess.run(
        ["git", "diff", base, head, "--unified=0", "--", path],
        capture_output=True,
        text=True,
        cwd=ROOT,
    ).stdout
    mapping: dict[int, int | None] = {}
    delta = 0
    prev_end = 0
    for hunk in re.finditer(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", diff, re.M):
        old_start = int(hunk.group(1))
        old_count = int(hunk.group(2) or 1)
        new_start = int(hunk.group(3))
        new_count = int(hunk.group(4) or 1)
        for line in range(prev_end + 1, old_start):
            mapping[line] = line + delta
        for offset in range(old_count):
            mapping[old_start + offset] = (
                new_start + offset if offset < new_count else None
            )
        delta += new_count - old_count
        prev_end = old_start + old_count - 1
    total_old = len(git_show(base, path) or [])
    for line in range(prev_end + 1, total_old + 1):
        mapping[line] = line + delta
    return mapping


def symbol_in_range(path: str, symbol: str, start: int, end: int) -> bool:
    """Whether the claim's symbol is still inside the cited block at the current HEAD."""
    lines = current(path)
    return any(symbol in line for line in lines[start - 1 : end])


def describe(
    base: str,
    head: str,
    path: str,
    start: int,
    end: int,
    status: str,
    symbol: str | None = None,
) -> str:
    """Show what the citation pointed at and what is there now, for manual rewriting."""
    old, new = git_show(base, path) or [], current(path)
    seen_old = old[start - 1][:80] if len(old) >= start else "beyond end of file"
    seen_new = new[start - 1][:80] if len(new) >= start else "beyond end of file"
    out = f"{status} | base: {seen_old} | current: {seen_new}"
    mapped = diff_mapping(base, head, path).get(start)
    if mapped:
        out += f" | mapped: {mapped}-{mapped + (end - start)}"
    if symbol:
        hits = [index + 1 for index, line in enumerate(new) if symbol in line][:6]
        out += f" | {symbol} at {hits}"
    return out


def resolve(
    base: str, head: str, path: str, start: int, end: int
) -> tuple[int | None, str]:
    """Resolve a cited block to its current position by content identity."""
    old, new = git_show(base, path), current(path)
    if old is None:
        return None, "no-base"
    if not new:
        return None, "no-current"
    block = [line.strip() for line in old[start - 1 : end]]
    if not any(block):
        return None, "empty-citation"
    mapping = diff_mapping(base, head, path)
    if len(block) == 1:
        hits = [index + 1 for index, line in enumerate(new) if line.strip() == block[0]]
    else:
        hits = [
            index + 1
            for index in range(len(new) - len(block) + 1)
            if [line.strip() for line in new[index : index + len(block)]] == block
        ]
    if not hits:
        span = [mapping.get(line) for line in range(start, end + 1)]
        if all(value is not None for value in span):
            # Every cited line still exists with modified content: the number can be
            # renumbered, but the claim itself must be read against the current content.
            return span[0], "mapped"
        return None, "removed"
    if len(hits) == 1:
        return hits[0], "moved"
    mapped = mapping.get(start)
    if mapped in hits:
        return mapped, "moved"
    return None, f"ambiguous({len(hits)})"


def resolve_name(
    base: str, head: str, path: str, name: str, start: int
) -> tuple[int | None, str]:
    """Resolve a `Name (line)` citation: the name must still appear at the resolved line."""
    old, new = git_show(base, path), current(path)
    if old is None:
        return None, "no-base"
    if not new:
        return None, "no-current"
    if len(new) >= start and name in new[start - 1]:
        return start, "ok"
    hits = [index + 1 for index, line in enumerate(new) if name in line]
    if not hits:
        return None, "removed"
    mapped = diff_mapping(base, head, path).get(start)
    if mapped in hits:
        return mapped, "moved"
    if len(hits) == 1:
        return hits[0], "moved"
    return None, f"ambiguous({len(hits)})"


def resolve_file(
    name: str, changed: set[str], context: str | None, target: str | None
) -> tuple[str | None, str, list[str]]:
    """Resolve a citation file name to a path that differs between base and head.

    A name with no directory is matched against the file named earlier on the same line,
    then the document's `### Target file`, then the changed files sharing the name. A name
    that resolves to nothing was not affected by the rebase, so its citation needs no pass.
    """
    if name in changed:
        return name, "ok", []
    if "/" in name:
        return None, "skip", []
    hits = sorted(c for c in changed if pathlib.Path(c).name == name)
    if not hits:
        return None, "skip", []
    for preferred in (context, target):
        if preferred in hits:
            return preferred, "ok", hits
    if len(hits) == 1:
        return hits[0], "ok", hits
    return None, "ambiguous-name", hits


def document_base(doc: pathlib.Path, plans: dict[str, str]) -> str | None:
    """Revision the document's citations were verified against, from its Traceability."""
    text = doc.read_text(encoding="utf-8")
    match = re.search(r"\*\*Source plan\*\*: `?([^`\n]+)`?", text)
    if not match:
        return None
    return plans.get(pathlib.Path(match.group(1)).name)


def process_document(
    doc: pathlib.Path,
    text: str,
    target: str | None,
    base: str,
    head: str,
    changed: set[str],
    dry_run: bool,
    accept_mapped: bool = False,
) -> tuple[int, list[tuple[int, str, str, str]], list[tuple[int, str, str]]]:
    out_lines: list[str] = []
    manual: list[tuple[int, str, str, str]] = []
    pending: list[tuple[int, str, str]] = []
    dirty = 0
    bullet_path: str | None = None
    for number, line in enumerate(text.splitlines(), 1):
        out_line = line
        # A citation with no file in its own line belongs to the file named by the bullet
        # it is written under, not necessarily to the document's `### Target file`.
        first = PATH.search(line)
        if line.lstrip().startswith("- ") and first:
            bullet_path = first.group(1)
        context_file = first.group(1) if first else bullet_path or target
        for match in CITE.finditer(line):
            path, status, alternatives = resolve_file(
                match.group(1), changed, context_file, target
            )
            if status == "skip":
                continue
            if status == "ambiguous-name":
                manual.append(
                    (
                        number,
                        match.group(1),
                        match.group(2),
                        "ambiguous-name: " + ", ".join(alternatives),
                    )
                )
                continue
            if path is None:
                continue
            raw = match.group(0)
            # Keep the first token's range end: dropping it would turn "96-99" into "96".
            tokens = [match.group(2) + (f"-{match.group(3)}" if match.group(3) else "")]
            tokens += [token for token in (match.group(4) or "").split(",") if token]
            new_tokens, moved = [], False
            for token in tokens:
                nums = re.findall(r"\d+", token)
                start = int(nums[0])
                end = int(nums[1]) if len(nums) > 1 else start
                new_start, status = resolve(base, head, path, start, end)
                names = SYMBOL.findall(line[: match.start()]) or SYMBOL.findall(line)
                if (
                    status == "mapped"
                    and accept_mapped
                    and new_start is not None
                    and names
                ):
                    # The cited block still exists line by line with modified content, so the
                    # number moves only when the claim's symbol is still inside it. The
                    # sentence itself still has to be re-read against the current content.
                    if symbol_in_range(
                        path, names[-1], new_start, new_start + end - start
                    ):
                        manual.append(
                            (
                                number,
                                path,
                                token,
                                f"mapped-symbol-accepted: {names[-1]}",
                            )
                        )
                        status = "moved"
                if new_start is None or (status != "ok" and status != "moved"):
                    manual.append(
                        (
                            number,
                            path,
                            token,
                            describe(
                                base,
                                head,
                                path,
                                start,
                                end,
                                status,
                                names[-1] if names else None,
                            ),
                        )
                    )
                    new_tokens.append(token)
                    continue
                new_tokens.append(
                    str(new_start)
                    + (f"-{new_start + end - start}" if end != start else "")
                )
                moved = moved or new_start != start
            if moved:
                dirty += 1
                rebuilt = f"`{path}:{','.join(new_tokens)}" + (
                    "`" if raw.startswith("`") else ""
                )
                out_line = out_line.replace(raw, rebuilt)
                pending.append((number, raw, rebuilt))
        for segment in BARE.finditer(line):
            context = PATH.search(line[: segment.start()])
            candidates = [
                resolved
                for resolved in (
                    resolve_file(candidate, changed, candidate, target)[0]
                    for candidate in (
                        context.group(1) if context else None,
                        context_file,
                        target,
                    )
                    if candidate
                )
                if resolved
            ]
            if not candidates:
                continue
            start = int(segment.group(1))
            end = int(segment.group(2)) if segment.group(2) else start
            path, new_start, status = candidates[0], None, ""
            for candidate in candidates:
                new_start, status = resolve(base, head, candidate, start, end)
                if status in ("ok", "moved"):
                    path = candidate
                    break
            names = SYMBOL.findall(line[: segment.start()]) or SYMBOL.findall(line)
            if status == "mapped" and accept_mapped and new_start is not None and names:
                if symbol_in_range(path, names[-1], new_start, new_start + end - start):
                    manual.append(
                        (
                            number,
                            path,
                            segment.group(0),
                            f"mapped-symbol-accepted: {names[-1]}",
                        )
                    )
                    status = "moved"
            if new_start is None or status not in ("ok", "moved"):
                manual.append(
                    (
                        number,
                        path,
                        segment.group(0),
                        describe(
                            base,
                            head,
                            path,
                            start,
                            end,
                            status,
                            names[-1] if names else None,
                        ),
                    )
                )
                continue
            if new_start != start:
                rebuilt = segment.group(0).replace(segment.group(1), str(new_start))
                if end != start:
                    rebuilt = rebuilt.replace(
                        segment.group(2), str(new_start + end - start)
                    )
                out_line = out_line.replace(segment.group(0), rebuilt)
                pending.append((number, segment.group(0), rebuilt))
                dirty += 1
        for segment in PAREN.finditer(line):
            name, start = segment.group(1), int(segment.group(2))
            end = int(segment.group(3)) if segment.group(3) else start
            # A `Name (line)` citation belongs to the file the document is about; the bullet
            # path is used only when that file cannot resolve the number.
            path, status, _ = resolve_file(
                target or context_file or "", changed, target, target
            )
            if not path:
                path, status, _ = resolve_file(
                    context_file or "", changed, context_file, target
                )
            if not path:
                continue
            new_start, status = resolve_name(base, head, path, name, start)
            if status != "ok" and status != "moved":
                alt_path = resolve_file(
                    context_file or "", changed, context_file, target
                )[0]
                if alt_path and alt_path != path:
                    alt_start, alt_status = resolve_name(
                        base, head, alt_path, name, start
                    )
                    if alt_status == "ok" or alt_status == "moved":
                        path, new_start, status = alt_path, alt_start, alt_status
            if status != "ok" and status != "moved":
                names = SYMBOL.findall(line[: segment.start()])
                manual.append(
                    (
                        number,
                        path,
                        segment.group(0),
                        describe(base, head, path, start, end, status, name),
                    )
                )
                continue
            if new_start != start:
                rebuilt = segment.group(0).replace(
                    f"({segment.group(2)}", f"({new_start}"
                )
                out_line = out_line.replace(segment.group(0), rebuilt)
                pending.append((number, segment.group(0), rebuilt))
                dirty += 1
        if out_line != line:
            print(f"  {doc.name}:{number}: {line.strip()[:120]}")
            if dry_run:
                print(f"    -> {out_line.strip()[:120]}")
        out_lines.append(out_line)
    return dirty, manual, pending


def apply_to_tree(
    doc: pathlib.Path, pending: list[tuple[int, str, str]]
) -> tuple[int, list[tuple[int, str]]]:
    """Substitute each citation in the working tree, leaving already-corrected lines alone."""
    text = doc.read_text(encoding="utf-8")
    newline = "\r\n" if "\r\n" in text else "\n"
    lines = text.splitlines()
    applied, unapplied = 0, []
    for number, raw, rebuilt in pending:
        index = number - 1
        if index < len(lines) and raw in lines[index]:
            lines[index] = lines[index].replace(raw, rebuilt, 1)
            applied += 1
            continue
        # The document may have gained lines since it was written, so the citation is
        # located by its content rather than by the line number it had at `--doc-rev`.
        found = next((i for i, line in enumerate(lines) if raw in line), None)
        if found is None:
            unapplied.append((number, raw))
            continue
        lines[found] = lines[found].replace(raw, rebuilt, 1)
        applied += 1
    if applied:
        doc.write_text(newline.join(lines) + newline, encoding="utf-8")
    return applied, unapplied


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify and renumber rebase-drifted line citations in procedure documents."
    )
    parser.add_argument(
        "--base", required=True, help="Revision the citations were verified against."
    )
    parser.add_argument("--head", default="HEAD")
    parser.add_argument(
        "--doc-rev", default="HEAD", help="Commit containing the documents as written."
    )
    parser.add_argument("--docs", default="implementations/20261128-*_*.md")
    parser.add_argument(
        "--plan",
        default="plans/done/20261127-203046_mdqmcp010_mdq-release-readiness.md",
    )
    parser.add_argument(
        "--accept-mapped",
        action="store_true",
        help="Renumber a citation whose block content changed, when the claim's symbol is "
        "still inside the block at the mapped position.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would change without writing files.",
    )
    args = parser.parse_args()

    documents = sorted(ROOT.glob(args.docs))
    if args.plan:
        documents.append(ROOT / args.plan)

    plans = {
        plan.name: match.group(1)
        for plan in sorted(ROOT.glob("plans/**/*.md"))
        for match in [
            re.search(
                r"\*\*Evidence revision\*\*: ([0-9a-f]{7,40})",
                plan.read_text(encoding="utf-8"),
            )
        ]
        if match
    }

    counts: collections.Counter[str] = collections.Counter()
    manual: list[tuple[str, int, str, str, str]] = []
    skipped: list[tuple[str, int, str]] = []
    changed: dict[str, set[str]] = {}
    for doc in documents:
        # Read the document as it was written, so a second run resolves from the same
        # numbers as the first: renumbering a citation that is already renumbered would
        # treat the current number as the evidence-revision number and shift it twice.
        lines = git_show(args.doc_rev, str(doc.relative_to(ROOT)))
        if lines is None:
            manual.append((doc.name, 0, "-", "-", f"not in {args.doc_rev}"))
            continue
        text = "\n".join(lines)
        match = re.search(r"### Target file\n`([^`]+)`", text)
        target = match.group(1) if match else None
        base = (
            plans.get(doc.name) or document_base(doc, plans)
            if args.base == "auto"
            else args.base
        )
        if not base:
            manual.append((doc.name, 0, "-", "-", "no-evidence-revision"))
            continue
        if base not in changed:
            changed[base] = {
                line.strip()
                for line in subprocess.run(
                    ["git", "diff", "--name-only", base, args.head],
                    capture_output=True,
                    text=True,
                    cwd=ROOT,
                ).stdout.splitlines()
                if line.strip()
            }
        dirty, found, pending = process_document(
            doc,
            text,
            target,
            base,
            args.head,
            changed[base],
            args.dry_run,
            args.accept_mapped,
        )
        counts["changes"] += dirty
        for number, path, token, status in found:
            manual.append((doc.name, number, path, token, status))
        if pending and not args.dry_run:
            applied, missing = apply_to_tree(doc, pending)
            counts["applied"] += applied
            for number, raw in missing:
                skipped.append((doc.name, number, raw))

    print("changes:", counts["changes"])
    print("applied:", counts["applied"])
    print("skipped (citation already rewritten in the working tree):", len(skipped))
    for item in skipped:
        print("  ", item)
    print("manual:", len(manual))
    for entry in manual:
        print("  ", entry)
    return 1 if manual else 0


if __name__ == "__main__":
    raise SystemExit(main())
