#!/usr/bin/env python3
"""tools/finalize_procedures.py
Run the procedure acceptance checks for every procedure of a Plan.

For a Plan the tool runs, with each checker's default arguments and unchanged exit
semantics:

- `tools/check_workitem_structure.py --file <procedure>` per procedure;
- `tools/stale_detector.py <procedure>` per procedure;
- `tools/check_workitem_traceability.py --plan-coverage <plan>` once.

Every check runs even after a failure. Only failing rows are printed
(`document | tool | exit N | first finding`), followed by the full output of each
failing check. When everything passes, exactly one `OK:` line is printed.

Each `symbol_missing` stale finding is classified:

- `created here`: the document itself defines the name (an assignment or
  annotation in backticks, a `def`/`class`, or a creating verb with a noun such as
  function, constant, or field); suggested action: add `(new)`;
- `not a code symbol`: every occurrence is attribute access, a quoted literal, or
  the value of `key=name`; suggested action: remove the backticks;
- `ambiguous`: anything else; reported, never edited.

The tool is read-only unless `--apply` is given. `--apply` performs only the
unambiguous actions through `tools/_atomic_write.py`, then re-runs the checks for
the changed documents; `--dry-run` prints the diff and writes nothing.

Usage:
    python tools/finalize_procedures.py plans/<plan>.md [--apply] [--dry-run]
        [--include-done] [--root DIR]

Exit codes: 0 every check passes; 1 a check fails or the Plan has no procedures;
2 usage error.
"""

from __future__ import annotations

import argparse
import re
import subprocess  # nosec B404 — fixed argv, no shell, standard input closed
import sys
from dataclasses import dataclass
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools._atomic_write import add_dry_run_argument, atomic_write_text, print_dry_run
from tools.mark_procedure_new_symbols import mark_names

ROOT_DIR = Path(__file__).resolve().parent.parent

CREATED = "created here"
NOT_SYMBOL = "not a code symbol"
AMBIGUOUS = "ambiguous"
ACTIONS = {
    CREATED: "add (new)",
    NOT_SYMBOL: "remove backticks",
    AMBIGUOUS: "report only",
}

_MISSING_RE = re.compile(r"Symbol '([A-Za-z_][A-Za-z0-9_]*)' not found in source")
_SOURCE_PLAN_RE = re.compile(r"^- \*\*Source plan\*\*: (\S+)", re.MULTILINE)
_SPAN_RE = re.compile(r"`([^`\n]+)`")
_CREATE_VERB_RE = re.compile(
    r"\b(create|creates|add|adds|define|defines|introduce)", re.I
)
_CREATE_NOUN_RE = re.compile(
    r"\b(function|constant|field|parameter|method|dataclass|class)\b", re.I
)
_IMPL_START_RE = re.compile(r"^## Implementation\s*$", re.MULTILINE)
_IMPL_END_RE = re.compile(r"^## Compatibility considerations", re.MULTILINE)


@dataclass(frozen=True)
class CheckResult:
    tool: str
    target: str
    exit_code: int
    output: str

    @property
    def failed(self) -> bool:
        return self.exit_code != 0

    @property
    def first_line(self) -> str:
        lines = [line for line in self.output.splitlines() if line.strip()]
        return lines[0] if lines else ""


def run_check(root: Path, tool: str, *args: str) -> CheckResult:
    """Run one checker with its default arguments and return its exit code."""
    completed = subprocess.run(  # nosec B603 — fixed argv, no shell
        [sys.executable, str(root / "tools" / tool), *args],
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
        check=False,
        cwd=root,
    )
    output = (completed.stdout + completed.stderr).strip()
    return CheckResult(tool, args[-1] if args else "", completed.returncode, output)


def find_procedures(plan: Path, root: Path, include_done: bool) -> list[Path]:
    """Procedures whose `Source plan` has the Plan's base name, in `seq` order."""
    directories = [root / "implementations"]
    if include_done:
        directories.append(root / "implementations" / "done")
    found: list[Path] = []
    for directory in directories:
        for path in sorted(directory.glob("*.md")):
            match = _SOURCE_PLAN_RE.search(path.read_text(encoding="utf-8"))
            if match and Path(match.group(1)).name == plan.name:
                found.append(path)
    return sorted(found, key=lambda p: p.name)


def parse_missing_symbols(output: str) -> tuple[list[str], list[str]]:
    """Split stale output into symbol names and other mismatch lines."""
    names: list[str] = []
    others: list[str] = []
    for line in output.splitlines():
        match = _MISSING_RE.search(line)
        if match:
            if match.group(1) not in names:
                names.append(match.group(1))
        elif line.lstrip().startswith("- "):
            others.append(line.strip())
    return names, others


def _implementation_scope(text: str) -> str:
    start = _IMPL_START_RE.search(text)
    if start is None:
        return text
    end = _IMPL_END_RE.search(text, start.end())
    return text[start.start() : end.start() if end else len(text)]


def _classify_span(span: str, line: str, name: str) -> str:
    """Return `created`, `not`, or `neutral` for one backticked span holding *name*."""
    word = re.escape(name)
    if re.search(rf"[\w)\]]\.{word}\b", span):
        return "not"
    if re.search(rf"[\"'][^\"']*\b{word}\b[^\"']*[\"']", span):
        return "not"
    if re.search(rf"[\w-]+=\s*{word}\b", span):
        return "not"
    if re.match(rf"\s*{word}\s*(=(?!=)|:)\s*\S", span):
        return "created"
    if re.search(rf"\b(def|class)\s+{word}\b", line):
        return "created"
    has_verb = bool(_CREATE_VERB_RE.search(line))
    plain = span == name or span.startswith(name + "(")
    if has_verb and plain and _CREATE_NOUN_RE.search(line):
        return "created"
    if has_verb and re.match(rf"\s*\w+\(.*\b{word}\b.*\)", span):
        return "created"
    return "neutral"


def classify_symbol(text: str, name: str) -> str:
    """Classify a missing symbol name from the document's Implementation section."""
    word = re.escape(name)
    counts = {"created": 0, "not": 0, "neutral": 0}
    for line in _implementation_scope(text).splitlines():
        for match in _SPAN_RE.finditer(line):
            if re.search(rf"\b{word}\b", match.group(1)):
                counts[_classify_span(match.group(1), line, name)] += 1
    if counts["created"] and not counts["not"]:
        return CREATED
    if counts["not"] and not counts["created"] and not counts["neutral"]:
        return NOT_SYMBOL
    return AMBIGUOUS


def apply_actions(text: str, classes: dict[str, str]) -> str:
    """Apply the unambiguous actions: `(new)` markers and un-backticking."""
    created = [name for name, kind in classes.items() if kind == CREATED]
    if created:
        text, _ = mark_names(text, created)
    for name, kind in classes.items():
        if kind == NOT_SYMBOL:
            text = re.sub(rf"`{re.escape(name)}`( ?\(new\))?", name, text)
    return text


def plan_row_count(plan_text: str) -> int:
    """Number of rows of the Plan's `Implementation Target Files` table."""
    in_section = False
    rows = 0
    skipped = 0
    for line in plan_text.splitlines():
        if line.startswith("## "):
            in_section = line.strip() == "## Implementation Target Files"
            continue
        if in_section and line.startswith("|"):
            skipped += 1
            if skipped > 2 and line.strip("| ").strip():
                rows += 1
    return rows


def _checks_for(root: Path, doc: Path) -> list[CheckResult]:
    rel = doc.relative_to(root).as_posix()
    return [
        run_check(root, "check_workitem_structure.py", "--file", rel),
        run_check(root, "stale_detector.py", rel),
    ]


def _print_failures(doc: str, results: list[CheckResult]) -> int:
    failing = [r for r in results if r.failed]
    for result in failing:
        print(f"{doc} | {result.tool} | exit {result.exit_code} | {result.first_line}")
        for line in result.output.splitlines()[1:]:
            print(f"    {line}")
    return len(failing)


def _classify_document(doc: Path, stale: CheckResult) -> dict[str, str]:
    names, _ = parse_missing_symbols(stale.output)
    text = doc.read_text(encoding="utf-8")
    classes = {name: classify_symbol(text, name) for name in names}
    for name, kind in classes.items():
        print(f"{doc.name}: {name} -> {kind}; suggested: {ACTIONS[kind]}")
    return classes


def _apply_document(doc: Path, classes: dict[str, str], dry_run: bool) -> bool:
    """Apply the unambiguous actions; return True when the file was rewritten."""
    old = doc.read_text(encoding="utf-8")
    new = apply_actions(old, classes)
    if new == old:
        return False
    if dry_run:
        print_dry_run(doc, old, new)
        return False
    atomic_write_text(doc, new)
    print(f"{doc.name}: applied; re-running checks")
    return True


def run(plan: Path, root: Path, apply: bool, dry_run: bool, include_done: bool) -> int:
    procedures = find_procedures(plan, root, include_done)
    if not procedures:
        print(f"no procedures found for {plan}")
        return 1
    failures = 0
    for doc in procedures:
        results = _checks_for(root, doc)
        if results[1].failed:
            classes = _classify_document(doc, results[1])
            if apply and classes and _apply_document(doc, classes, dry_run):
                results = _checks_for(root, doc)
        failures += _print_failures(doc.name, results)
    coverage = run_check(
        root, "check_workitem_traceability.py", "--plan-coverage", plan.as_posix()
    )
    failures += _print_failures(plan.name, [coverage])
    if failures:
        return 1
    rows = plan_row_count(plan.read_text(encoding="utf-8"))
    print(
        f"OK: {len(procedures)} procedure(s) checked, {rows} Plan row(s), "
        f"coverage exit {coverage.exit_code}"
    )
    return 0


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the procedure acceptance checks for a Plan."
    )
    parser.add_argument("plan", type=Path, help="plans/<plan>.md")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply only the unambiguous classification actions (default: read-only)",
    )
    parser.add_argument(
        "--include-done",
        action="store_true",
        help="Also run the per-document checks on implementations/done/",
    )
    parser.add_argument("--root", type=Path, default=ROOT_DIR, help="Repository root")
    add_dry_run_argument(parser)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    if not args.plan.is_file():
        print(f"error: not a file: {args.plan}", file=sys.stderr)
        return 2
    return run(args.plan, args.root, args.apply, args.dry_run, args.include_done)


if __name__ == "__main__":
    sys.exit(main())
