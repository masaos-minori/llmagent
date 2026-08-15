#!/usr/bin/env python3
"""scripts/tools/fix_scripts_docstring_paths.py

One-shot normalizer for module-level docstring header paths under scripts/.

For every scripts/**/*.py with a module-level docstring, rewrites the
self-referencing filename/path on the docstring's first line to the file's
true path relative to the repo root, in the form `scripts/<relpath>`
(matching the convention enforced by tools/check_all_docstrings.py's
`expected_prefix`). Handles headers that are already correct (no-op),
missing the `scripts/` prefix, missing intermediate folders, using a stale
basename, using dotted-module notation, or missing entirely with a stray
`scripts/` glued onto free-text description from a prior partial edit.

Files with a docstring that has no recognizable self-reference (pure prose, e.g.
"AgentREPL") get the real path prepended as a new first line, description kept
verbatim below it. Files with no module docstring at all get a new one-line
docstring containing just `scripts/<relpath>` inserted (after a shebang line,
if present).

Usage:
    python tools/fix_scripts_docstring_paths.py --dry-run
    python tools/fix_scripts_docstring_paths.py --apply
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

# Two dotted-module headers (mcp_servers.rag_pipeline.{models,server}) are the
# only observed instances of this style; handled explicitly rather than via a
# generic dotted-path regex that could misfire on prose.
DOTTED_HEADER_RE = re.compile(r"^[A-Za-z_][\w]*(?:\.[A-Za-z_][\w]*)+\b")

PY_PATH_RE = re.compile(r"^(?:scripts/)?[\w\-./]+\.py\b")

# A scripts/-prefixed path with 2+ segments but no .py extension (e.g.
# "scripts/agent/workflow/task_ops — ..."): this is a real path missing only
# its extension, not prose glued after a stray "scripts/" -- genuine broken
# glue is always a single bare word (see repair fallback in
# compute_new_header). Requiring a slash after "scripts/" is what tells the
# two apart.
MULTI_SEGMENT_NO_EXT_RE = re.compile(r"^scripts/[\w\-]+(?:/[\w\-]+)+\b")


def get_module_docstring_span(tree: ast.Module) -> tuple[int, int, int, int] | None:
    if not tree.body:
        return None
    first = tree.body[0]
    if not (
        isinstance(first, ast.Expr)
        and isinstance(first.value, ast.Constant)
        and isinstance(first.value.value, str)
    ):
        return None
    node = first.value
    return node.lineno, node.col_offset, node.end_lineno, node.end_col_offset


def span_to_byte_offsets(
    lines_bytes: list[bytes],
    start_line: int,
    start_col: int,
    end_line: int,
    end_col: int,
) -> tuple[int, int]:
    # ast column offsets are UTF-8 byte offsets, not character offsets, so any
    # line containing non-ASCII text (e.g. the em-dash separator) must be
    # resolved against the byte-encoded source, not the decoded str.
    abs_start = sum(len(b) for b in lines_bytes[: start_line - 1]) + start_col
    abs_end = sum(len(b) for b in lines_bytes[: end_line - 1]) + end_col
    return abs_start, abs_end


def build_init_candidates(parent_rel_posix: str, correct: str) -> list[str]:
    dotted = parent_rel_posix.replace("/", ".")
    return [
        correct,  # already-fixed form; must be tried first so re-runs are no-ops
        f"scripts/{parent_rel_posix}",
        f"{parent_rel_posix}/",
        parent_rel_posix,
        dotted,
    ]


def compute_new_header(
    header: str, correct: str, is_init: bool, parent_rel_posix: str
) -> tuple[str, str] | None:
    """Returns (new_header_first_line, mode) or None if no self-reference found.

    mode is "inline" (simple substitution within the first line) or
    "repair" (the whole first line was a broken scripts/+description glue
    with no real path -- caller must insert a blank line before the rest).
    """
    m = PY_PATH_RE.match(header)
    if m:
        return header[: m.start()] + correct + header[m.end() :], "inline"

    m2 = MULTI_SEGMENT_NO_EXT_RE.match(header)
    if m2 and not is_init:
        return header[: m2.start()] + correct + header[m2.end() :], "inline"

    if is_init:
        candidates = sorted(
            build_init_candidates(parent_rel_posix, correct), key=len, reverse=True
        )
        prefix_m = re.match(r"^(Package:\s*)", header)
        search_from = prefix_m.end() if prefix_m else 0
        for cand in candidates:
            if header[search_from:].startswith(cand):
                end = search_from + len(cand)
                # avoid partial-word match, e.g. "db" inside "database"
                if end < len(header) and (header[end].isalnum() or header[end] == "_"):
                    continue
                return header[:search_from] + correct + header[end:], "inline"

    dm = DOTTED_HEADER_RE.match(header)
    if dm and not is_init:
        return correct + header[dm.end() :], "inline"

    if header.startswith("scripts/"):
        remainder = header[len("scripts/") :]
        return remainder, "repair"

    # Pure prose with no self-reference at all (e.g. "AgentREPL"): treat the
    # whole existing header as the description and prepend the real path,
    # same construction as the "repair" case above.
    return header, "repair"


def insert_new_docstring(path: Path, source: str, correct: str, apply: bool) -> str:
    """Adds a `\"\"\"scripts/<relpath>\"\"\"` docstring to a file that has none."""
    if source.strip() == "":
        new_source = f'"""{correct}"""\n'
    else:
        shebang, rest = "", source
        if source.startswith("#!"):
            nl = source.find("\n")
            if nl == -1:
                shebang, rest = source + "\n", ""
            else:
                shebang, rest = source[: nl + 1], source[nl + 1 :]
        new_source = f'{shebang}"""{correct}"""\n\n{rest}'

    try:
        ast.parse(new_source)
    except SyntaxError as e:
        return f"SKIP (new docstring would break syntax): {path}: {e}"

    summary = f"{correct} [new]:\n  + {correct!r}"
    if apply:
        path.write_text(new_source, encoding="utf-8")
    return summary


def process_file(path: Path, scripts_root: Path, apply: bool) -> str | None:
    """Returns a human-readable diff summary if changed, None if untouched."""
    source = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return f"SKIP (syntax error): {path}: {e}"

    span = get_module_docstring_span(tree)
    if span is None:
        relpath = path.relative_to(scripts_root).as_posix()
        return insert_new_docstring(path, source, f"scripts/{relpath}", apply)
    start_line, start_col, end_line, end_col = span

    source_bytes = source.encode("utf-8")
    lines_bytes = [line.encode("utf-8") for line in source.splitlines(keepends=True)]
    abs_start, abs_end = span_to_byte_offsets(
        lines_bytes, start_line, start_col, end_line, end_col
    )
    raw = source_bytes[abs_start:abs_end].decode("utf-8")

    if raw.startswith('"""') and raw.endswith('"""') and len(raw) >= 6:
        quote = '"""'
    elif raw.startswith("'''") and raw.endswith("'''") and len(raw) >= 6:
        quote = "'''"
    else:
        return f"SKIP (unsupported quote style): {path}"

    body = raw[3:-3]
    header, sep, rest = body.partition("\n")
    if header.strip() == "":
        return f"SKIP (blank first docstring line, needs manual review): {path}"

    relpath = path.relative_to(scripts_root).as_posix()
    correct = f"scripts/{relpath}"
    is_init = path.name == "__init__.py"
    parent_rel_posix = path.parent.relative_to(scripts_root).as_posix()

    result = compute_new_header(header, correct, is_init, parent_rel_posix)
    if result is None:
        return None
    new_header, mode = result

    if mode != "repair" and new_header == header:
        return None  # already correct

    if mode == "repair":
        new_body = correct + "\n\n" + new_header + (sep + rest if sep else "")
    else:
        new_body = new_header + (sep + rest if sep else "")

    new_raw = quote + new_body + quote
    new_source = (
        source_bytes[:abs_start] + new_raw.encode("utf-8") + source_bytes[abs_end:]
    ).decode("utf-8")

    try:
        ast.parse(new_source)
    except SyntaxError as e:
        return f"SKIP (edit would break syntax): {path}: {e}"

    summary_new = new_body.strip().split("\n", 1)[0][:100]
    summary = f"{relpath}:\n  - {header.strip()[:100]!r}\n  + {summary_new!r}"
    if apply:
        path.write_text(new_source, encoding="utf-8")
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scripts-dir", default=None)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dry-run", action="store_true")
    group.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)

    scripts_dir = (
        Path(args.scripts_dir)
        if args.scripts_dir
        else Path(__file__).resolve().parent.parent / "scripts"
    )
    if not scripts_dir.is_dir():
        print(f"ERROR: scripts directory not found: {scripts_dir}", file=sys.stderr)
        return 1

    changed = 0
    skipped = 0
    for py_file in sorted(scripts_dir.rglob("*.py")):
        result = process_file(py_file, scripts_dir, apply=args.apply)
        if result is None:
            continue
        if result.startswith("SKIP"):
            print(result)
            skipped += 1
        else:
            print(result)
            changed += 1

    action = "changed" if args.apply else "would change"
    print(f"\n{changed} file(s) {action}; {skipped} file(s) need manual review.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
