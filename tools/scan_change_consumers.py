"""tools/scan_change_consumers.py
Lists CANDIDATE direct and indirect consumers of a planned change, so the
`Implementation Target Files` table of a Plan is complete at freeze time.

Motivating incident: three Frozen Plans were amended after freeze because a
file outside their target table had to change -- an inventory-style checker
that rejected a new table, a deploy test whose sandbox config pinned a key
inside a TOML table, and a mock-based integration test. Each omission was
found only by a full-suite run or a pre-commit hook, although a search at
planning time would have named it.

A seed is a symbol, a column or table name, a constant, or a file path. For
each seed the report lists, by category:

- `direct:<dir>`: lines naming the seed under `scripts/`, `tests/`, `tools/`,
  `deploy/`, and `docs/`.
- `patch-or-import`: test lines that import the seed's defining module or name
  it inside a quoted `patch(...)` target.
- `inventory`: lines naming the seed or its defining module in `tools/check_*.py`
  and in tracked baseline or inventory files. A line may also appear under a
  `direct:` category by design.
- `adr-test-citation`: `docs/10_adr/*.md` lines citing a test (`path.py::node`)
  whose file names the seed or its defining module.
- `testmon`: test files that executed the defining module, read from
  `.testmondata` only when that file exists and is fresh. The state line
  (`absent`, `stale`, `used`, or `unrecognized`) is printed in every report.

This is a heuristic text search, never a verdict: every result is a candidate
for the Plan author to classify, and a missing consumer is NOT evidence of
absence. The defining module is resolved by a text match of `def`, `class`,
and line-start assignment names, not by AST parsing, so a column or table
name resolves to no module and is reported as a limit.

Read-only: no network, and nothing is written except stdout and an optional
`--report` file. The testmon database is opened with `mode=ro&immutable=1`.

Usage:
    python tools/scan_change_consumers.py --seed SYMBOL [--seed OTHER ...]
    python tools/scan_change_consumers.py --seed SYMBOL --format json
    python tools/scan_change_consumers.py --seed SYMBOL --report /tmp/scan.txt

Exit code: 0 for a completed scan (report-only); 2 for an argument error.
"""

from __future__ import annotations

import argparse
import re
import sqlite3
import sys
import time
from collections import Counter
from collections.abc import Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path

import orjson

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools._tool_common import REPO_ROOT, run_git

ROOT_DIR = REPO_ROOT

NOTICE = "candidates only; a missing consumer is not evidence of absence"
DIRECT_DIRS = ("scripts", "tests", "tools", "deploy", "docs")
CAT_DIRECT = "direct:"
CAT_PATCH_IMPORT = "patch-or-import"
CAT_INVENTORY = "inventory"
CAT_ADR = "adr-test-citation"
CAT_TESTMON = "testmon"

STATE_ABSENT = "absent"
STATE_STALE = "stale"
STATE_USED = "used"
STATE_UNRECOGNIZED = "unrecognized"

TESTMON_FILE = ".testmondata"
TESTMON_TABLES = frozenset({"test_execution", "file_fp", "test_execution_file_fp"})
DEFAULT_TESTMON_MAX_AGE_DAYS = 7.0
MAX_FILE_BYTES = 1024 * 1024
MAX_TEXT_CHARS = 160
DEFAULT_MAX_LINES = 40
_SECONDS_PER_DAY = 86400.0

_ADR_CITATION_RE = re.compile(r"`([^`]+\.py)::([^`]+)`")


@dataclass(frozen=True)
class Candidate:
    category: str
    seed: str
    path: str
    line_no: int
    text: str


@dataclass(frozen=True)
class TestmonState:
    __test__ = False  # not a pytest class despite the name prefix

    state: str
    detail: str


@dataclass
class Report:
    seeds: list[str]
    testmon: TestmonState
    notice: str = NOTICE
    limits: list[str] = field(default_factory=list)
    candidates: list[Candidate] = field(default_factory=list)

    def categories(self) -> dict[str, int]:
        counts = Counter(c.category for c in self.candidates)
        return dict(sorted(counts.items()))


def list_tracked_files(root: Path) -> list[str]:
    """Return the repository-relative paths git tracks under `root`."""
    try:
        proc = run_git("ls-files", "-z", cwd=root, binary=True)
    except OSError as exc:
        raise SystemExit(f"cannot run git ls-files: {exc}") from exc
    if proc.returncode != 0:
        raise SystemExit(
            f"git ls-files failed in {root}: {proc.stderr.decode(errors='replace')}"
        )
    return sorted(p for p in proc.stdout.decode().split("\0") if p)


def _wants_text(path: str) -> bool:
    """True for files a finder may read: the five scan dirs, or a baseline file."""
    if path.split("/", 1)[0] in DIRECT_DIRS:
        return True
    name = path.rsplit("/", 1)[-1]
    return "baseline" in name or "inventory" in name


def read_texts(root: Path, files: Sequence[str]) -> tuple[dict[str, list[str]], int]:
    """Read each wanted file once; return `path -> lines` and the skipped count."""
    texts: dict[str, list[str]] = {}
    skipped = 0
    for rel in files:
        if not _wants_text(rel):
            continue
        path = root / rel
        try:
            if path.stat().st_size > MAX_FILE_BYTES:
                skipped += 1
                continue
            texts[rel] = path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError):
            skipped += 1
    return texts, skipped


def _is_path_seed(seed: str) -> bool:
    return "/" in seed or seed.endswith(".py")


def _dotted_module(rel: str) -> str:
    """`scripts/agent/mod.py` -> `agent.mod`; `tools/x.py` -> `tools.x`."""
    stem = rel[: -len(".py")] if rel.endswith(".py") else rel
    if stem.startswith("scripts/"):
        stem = stem[len("scripts/") :]
    return stem.replace("/", ".")


def _seed_matcher(seed: str) -> re.Pattern[str]:
    if _is_path_seed(seed):
        alternatives = [re.escape(seed)]
        if seed.endswith(".py"):
            alternatives.append(
                r"(?<![\w.])(?:scripts\.)?"
                + re.escape(_dotted_module(seed))
                + r"(?!\w)"
            )
        return re.compile("|".join(alternatives))
    return re.compile(r"(?<![A-Za-z0-9_])" + re.escape(seed) + r"(?![A-Za-z0-9_])")


def _defining_modules(seed: str, texts: dict[str, list[str]]) -> list[str]:
    """Tracked `scripts/` or `tools/` files that define the seed (text match)."""
    if _is_path_seed(seed):
        return [seed] if seed in texts and seed.endswith(".py") else []
    name = re.escape(seed)
    pattern = re.compile(rf"^\s*(?:async\s+def|def|class)\s+{name}\b|^{name}\s*[:=]")
    found: list[str] = []
    for rel, lines in texts.items():
        top = rel.split("/", 1)[0]
        if top not in ("scripts", "tools") or not rel.endswith(".py"):
            continue
        if any(pattern.search(line) for line in lines):
            found.append(rel)
    return sorted(found)


def _clip(line: str) -> str:
    stripped = line.strip()
    if len(stripped) > MAX_TEXT_CHARS:
        return stripped[: MAX_TEXT_CHARS - 3] + "..."
    return stripped


def _find_direct(
    seed: str, matcher: re.Pattern[str], texts: dict[str, list[str]]
) -> list[Candidate]:
    hits: list[Candidate] = []
    for rel, lines in texts.items():
        top = rel.split("/", 1)[0]
        if top not in DIRECT_DIRS:
            continue
        for number, line in enumerate(lines, start=1):
            if matcher.search(line):
                hits.append(Candidate(CAT_DIRECT + top, seed, rel, number, _clip(line)))
    return hits


def _module_line_matchers(module: str) -> tuple[re.Pattern[str], re.Pattern[str]]:
    """Patterns for a quoted dotted name or an import of the module."""
    dotted = _dotted_module(module)
    named = r"(?<![\w.])(?:scripts\.)?" + re.escape(dotted) + r"(?!\w)"
    quoted = re.compile(r"""["'][^"']*""" + named + r"""[^"']*["']""")
    imported = re.compile(r"^\s*(?:from|import)\s+(?:scripts\.)?" + re.escape(dotted))
    parent, _, leaf = dotted.rpartition(".")
    if parent:
        from_parent = re.compile(
            r"^\s*from\s+(?:scripts\.)?"
            + re.escape(parent)
            + r"\s+import\s+.*\b"
            + re.escape(leaf)
            + r"\b"
        )
        return quoted, re.compile(f"{imported.pattern}|{from_parent.pattern}")
    return quoted, imported


def _find_patch_or_import(
    seed: str, modules: list[str], texts: dict[str, list[str]]
) -> list[Candidate]:
    hits: list[Candidate] = []
    for module in modules:
        quoted, imported = _module_line_matchers(module)
        for rel, lines in texts.items():
            if rel.split("/", 1)[0] != "tests":
                continue
            for number, line in enumerate(lines, start=1):
                if quoted.search(line) or imported.search(line):
                    hits.append(
                        Candidate(CAT_PATCH_IMPORT, seed, rel, number, _clip(line))
                    )
    return hits


def _is_inventory_file(rel: str) -> bool:
    name = rel.rsplit("/", 1)[-1]
    if rel.startswith("tools/") and rel.count("/") == 1:
        if name.startswith("check_") and name.endswith(".py"):
            return True
    return "baseline" in name or "inventory" in name


def _find_inventory(
    seed: str,
    matcher: re.Pattern[str],
    modules: list[str],
    texts: dict[str, list[str]],
) -> list[Candidate]:
    hits: list[Candidate] = []
    for rel, lines in texts.items():
        if not _is_inventory_file(rel):
            continue
        for number, line in enumerate(lines, start=1):
            if matcher.search(line) or any(m in line for m in modules):
                hits.append(Candidate(CAT_INVENTORY, seed, rel, number, _clip(line)))
    return hits


def _find_adr_citations(
    seed: str,
    matcher: re.Pattern[str],
    modules: list[str],
    texts: dict[str, list[str]],
) -> list[Candidate]:
    module_names = [_dotted_module(m) for m in modules]
    hits: list[Candidate] = []
    for rel, lines in texts.items():
        if not (rel.startswith("docs/10_adr/") and rel.endswith(".md")):
            continue
        for number, line in enumerate(lines, start=1):
            for cited, node in _ADR_CITATION_RE.findall(line):
                body = "\n".join(texts.get(cited, []))
                if matcher.search(body) or any(n in body for n in module_names):
                    hits.append(
                        Candidate(CAT_ADR, seed, rel, number, _clip(f"{cited}::{node}"))
                    )
    return hits


def testmon_state(
    root: Path,
    now: float | None = None,
    max_age_days: float = DEFAULT_TESTMON_MAX_AGE_DAYS,
) -> TestmonState:
    """Classify `.testmondata`: absent, stale (not opened), used, or unrecognized."""
    path = root / TESTMON_FILE
    if not path.is_file():
        return TestmonState(STATE_ABSENT, f"no {TESTMON_FILE} in {root}")
    current = time.time() if now is None else now
    age_days = (current - path.stat().st_mtime) / _SECONDS_PER_DAY
    if age_days > max_age_days:
        return TestmonState(
            STATE_STALE,
            f"{TESTMON_FILE} is {age_days:.1f} days old (limit {max_age_days:g}); "
            "not opened",
        )
    try:
        conn = sqlite3.connect(f"file:{path}?mode=ro&immutable=1", uri=True)
        try:
            names = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
        finally:
            conn.close()
    except sqlite3.Error as exc:
        return TestmonState(STATE_UNRECOGNIZED, f"cannot read {TESTMON_FILE}: {exc}")
    missing = sorted(TESTMON_TABLES - names)
    if missing:
        return TestmonState(
            STATE_UNRECOGNIZED, f"{TESTMON_FILE} lacks tables: {', '.join(missing)}"
        )
    return TestmonState(STATE_USED, f"{TESTMON_FILE} is {age_days:.1f} days old")


_TESTMON_QUERY = (
    "SELECT DISTINCT te.test_name FROM file_fp f "
    "JOIN test_execution_file_fp l ON l.fingerprint_id = f.id "
    "JOIN test_execution te ON te.id = l.test_execution_id "
    "WHERE f.filename = ?"
)


def testmon_tests(root: Path, module: str) -> list[str]:
    """Test node ids whose recorded run executed `module` (read-only query)."""
    conn = sqlite3.connect(f"file:{root / TESTMON_FILE}?mode=ro&immutable=1", uri=True)
    try:
        return sorted(row[0] for row in conn.execute(_TESTMON_QUERY, (module,)))
    finally:
        conn.close()


def _find_testmon(
    seed: str, modules: list[str], root: Path, report: Report
) -> list[Candidate]:
    hits: list[Candidate] = []
    for module in modules:
        try:
            nodes = testmon_tests(root, module)
        except sqlite3.Error as exc:
            report.testmon = TestmonState(
                STATE_UNRECOGNIZED, f"{TESTMON_FILE} query failed: {exc}"
            )
            report.limits.append(f"testmon query failed, source skipped: {exc}")
            return hits
        per_file = Counter(node.split("::", 1)[0] for node in nodes)
        for test_file, count in sorted(per_file.items()):
            text = f"{count} recorded test(s) executed {module}"
            hits.append(Candidate(CAT_TESTMON, seed, test_file, 0, text))
    return hits


def scan(
    root: Path,
    files: Sequence[str],
    seeds: Sequence[str],
    *,
    now: float | None = None,
    max_age_days: float = DEFAULT_TESTMON_MAX_AGE_DAYS,
) -> Report:
    """Scan the tracked `files` under `root` for candidate consumers of `seeds`."""
    texts, skipped = read_texts(root, files)
    report = Report(seeds=list(seeds), testmon=testmon_state(root, now, max_age_days))
    if skipped:
        report.limits.append(
            f"{skipped} files skipped: binary, oversized, or unreadable"
        )
    for seed in seeds:
        matcher = _seed_matcher(seed)
        modules = _defining_modules(seed, texts)
        if not modules:
            report.limits.append(
                f"seed {seed} has no defining Python module; "
                "patch/import and testmon categories skipped for it"
            )
        report.candidates += _find_direct(seed, matcher, texts)
        report.candidates += _find_patch_or_import(seed, modules, texts)
        report.candidates += _find_inventory(seed, matcher, modules, texts)
        report.candidates += _find_adr_citations(seed, matcher, modules, texts)
        if report.testmon.state == STATE_USED:
            report.candidates += _find_testmon(seed, modules, root, report)
    report.limits.append(
        "text search only: indirect users through a mock, a config key, or a "
        "dynamic name are not detected; read the testmon state line"
    )
    return report


def render_text(report: Report, max_lines: int = DEFAULT_MAX_LINES) -> str:
    out = [
        f"Consumer scan for: {', '.join(report.seeds)}",
        f"Notice: {report.notice}",
        f"Testmon: {report.testmon.state} ({report.testmon.detail})",
    ]
    by_category: dict[str, list[Candidate]] = {}
    for cand in report.candidates:
        by_category.setdefault(cand.category, []).append(cand)
    for category in sorted(by_category):
        hits = by_category[category]
        out.append("")
        out.append(f"[{category}] {len(hits)} candidate(s)")
        for cand in hits[:max_lines]:
            location = f"{cand.path}:{cand.line_no}" if cand.line_no else cand.path
            out.append(f"  ({cand.seed}) {location}: {cand.text}")
        if len(hits) > max_lines:
            out.append(f"  ... {len(hits) - max_lines} more (use --format json)")
    if not by_category:
        out.append("")
        out.append("No candidates found.")
    out.append("")
    out.append("Limits:")
    out.extend(f"  - {limit}" for limit in report.limits)
    return "\n".join(out) + "\n"


def render_json(report: Report) -> str:
    payload = {
        "notice": report.notice,
        "seeds": report.seeds,
        "testmon": asdict(report.testmon),
        "limits": report.limits,
        "candidates": [asdict(c) for c in report.candidates],
        "categories": report.categories(),
    }
    return orjson.dumps(payload, option=orjson.OPT_INDENT_2).decode() + "\n"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="List candidate consumers of a planned change (read-only)."
    )
    parser.add_argument(
        "--seed",
        action="append",
        required=True,
        help="symbol, column/table name, constant, or file path (repeatable)",
    )
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--report", type=Path, help="also write the report here")
    parser.add_argument("--root", type=Path, default=ROOT_DIR, help="repository root")
    parser.add_argument(
        "--testmon-max-age-days",
        type=float,
        default=DEFAULT_TESTMON_MAX_AGE_DAYS,
        help="testmon data older than this is reported stale and not opened",
    )
    parser.add_argument(
        "--max-lines",
        type=int,
        default=DEFAULT_MAX_LINES,
        help="text output: candidate lines shown per category",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    root = args.root.resolve()
    report = scan(
        root,
        list_tracked_files(root),
        args.seed,
        max_age_days=args.testmon_max_age_days,
    )
    rendered = (
        render_json(report)
        if args.format == "json"
        else render_text(report, args.max_lines)
    )
    sys.stdout.write(rendered)
    if args.report is not None:
        args.report.write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
