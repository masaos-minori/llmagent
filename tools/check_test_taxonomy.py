#!/usr/bin/env python3
"""tools/check_test_taxonomy.py

Enforces the test-taxonomy classification rule (cliplc012, REQ-003, REQ-004, REQ-005).

The rule, as recorded in `docs/00_governance/governance_01_documentation-policy.md`: a test module is
`contract` when its assertions are traceable to a requirement source and it carries that citation,
otherwise it is `characterization`. The classification unit is the module: `pytestmark` decides the module
kind, and only a module that mixes both kinds marks individual tests.

The checker reads `pytestmark` and test decorators from the AST, never by importing the module, so it stays
read-only and cannot execute test code.

Scope: the classified areas (`tests/agent`, `tests/shared`) must classify every module or track it in the
baseline; a module outside those areas is checked only when it carries a taxonomy marker.

Findings (hard failures):
1. unclassified-module: a module in a classified area with no taxonomy marker and no baseline entry.
2. contract-without-citation: a `contract` module that carries no requirement citation.
3. module-level-both-kinds: `pytestmark` that claims both taxonomy kinds.
4. baseline-entry-classified: a baseline module that now carries a marker (the baseline must shrink).
5. marker-not-registered: a taxonomy marker not registered in `pyproject.toml`.
6. test-claims-both-kinds: an individual test that carries both taxonomy markers, which REQ-003's
   per-test-marker rule cannot resolve.

Report mode (`--junit-xml <file>`) prints a characterization section and a contract section with counts
grouped by the JUnit testcase classname, which is the module. Parametrized testcase ids do not match
AST-derived ids, so grouping is by module and a parametrized id falls back to the module kind.

Requirement citation forms (REQ-002's three kinds, read from the module source text):
- a requirement number (`REQ-NNN`),
- an Accepted ADR path (`docs/10_adr/adr_02_*.md`),
- an archived backlog issue path (`issues/done/...md`),
- a path registered in the Canonical Source Registry (`config/documentation_canonical_sources.toml`).

Baseline file (`tools/test_taxonomy_baseline.txt`): one entry per line as the module path, a tab, and a
reason that names an issue (`issues/...md`); `#` lines and blank lines are ignored.

Usage:
    python tools/check_test_taxonomy.py [--root PATH] [--baseline PATH]
    python tools/check_test_taxonomy.py --junit-xml <file> [--root PATH] [--baseline PATH]

Exit codes: 0 no finding and no blocking failure, 1 a rule violation or a contract failure (report mode),
2 a usage or input error (including an invalid baseline or an unusable XML file). In report mode a
characterization failure is report-only; a contract failure, and a failure in a module that is neither
suite, exit non-zero.
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
import tomllib
import xml.etree.ElementTree as ET  # nosec B405 — reads the local XML file the caller's own pytest run wrote
from dataclasses import dataclass
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_BASELINE = Path(__file__).resolve().parent / "test_taxonomy_baseline.txt"

CLASSIFIED_AREAS: tuple[str, ...] = ("tests/agent", "tests/shared")
TAXONOMY_MARKERS: tuple[str, ...] = ("characterization", "contract")

ISSUE_PATH_RE = re.compile(r"issues/(?:done/)?[\w.-]+\.md")
ADR_PATH_RE = re.compile(r"docs/10_adr/adr_02_[\w.-]+\.md")
REQUIREMENT_RE = re.compile(r"REQ-\d+")


class InputError(Exception):
    """The XML file, the baseline file, or the pytest configuration is unusable."""


class BaselineError(Exception):
    """A baseline line is invalid; carries its 1-based line number."""

    def __init__(self, line_no: int, message: str) -> None:
        super().__init__(f"baseline line {line_no}: {message}")
        self.line_no = line_no


@dataclass(frozen=True)
class ModuleScan:
    """One test module as the AST sees it."""

    path: str
    module_markers: frozenset[str]
    test_markers: dict[str, frozenset[str]]
    has_citation: bool

    @property
    def classified(self) -> bool:
        return bool(self.module_markers or self.test_markers)

    def kinds(self) -> set[str]:
        kinds = set(self.module_markers)
        for markers in self.test_markers.values():
            kinds |= markers
        return kinds


@dataclass(frozen=True)
class RunResult:
    """One pytest run as JUnit recorded it: test id -> module path."""

    cases: dict[str, str]
    failing: frozenset[str]
    total: int


def make_finding(category: str, file_path: str, detail: str) -> dict[str, str]:
    return {"category": category, "file": file_path, "detail": detail}


def load_registered_markers(pyproject: Path) -> frozenset[str]:
    """Read `[tool.pytest.ini_options] markers` names from `pyproject.toml`."""
    try:
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise InputError(f"{pyproject}: cannot read pytest markers ({exc})") from exc
    entries = (
        data.get("tool", {}).get("pytest", {}).get("ini_options", {}).get("markers", [])
    )
    names = {str(entry).partition(":")[0].strip() for entry in entries}
    return frozenset(name for name in names if name)


def load_registry_paths(root: Path) -> frozenset[str]:
    """Source paths registered in the Canonical Source Registry; an absent registry is an empty set."""
    path = root / "config" / "documentation_canonical_sources.toml"
    if not path.is_file():
        return frozenset()
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise InputError(
            f"{path}: cannot read the Canonical Source Registry ({exc})"
        ) from exc
    paths: set[str] = set()
    for entry in data.get("canonical_sources", []):
        for source in entry.get("source_paths", []):
            text = str(source).strip()
            if text:
                paths.add(text)
    return frozenset(paths)


def has_requirement_citation(text: str, registry_paths: frozenset[str]) -> bool:
    """True when the module source names one of REQ-002's requirement-source kinds."""
    if (
        REQUIREMENT_RE.search(text)
        or ADR_PATH_RE.search(text)
        or ISSUE_PATH_RE.search(text)
    ):
        return True
    return any(source and source in text for source in registry_paths)


def _marker_names(node: ast.AST) -> set[str]:
    """Taxonomy marker names in a `pytestmark` assignment value or a decorator."""
    return {
        child.attr
        for child in ast.walk(node)
        if isinstance(child, ast.Attribute) and child.attr in TAXONOMY_MARKERS
    }


def scan_module(path: Path, root: Path, registry_paths: frozenset[str]) -> ModuleScan:
    """Read the module's taxonomy markers from its AST; the module is never imported."""
    text = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        raise InputError(f"{path}: cannot parse ({exc})") from exc

    module_markers: set[str] = set()
    for statement in tree.body:
        if isinstance(statement, ast.Assign):
            targets = [
                t
                for t in statement.targets
                if isinstance(t, ast.Name) and t.id == "pytestmark"
            ]
            if targets:
                module_markers |= _marker_names(statement.value)

    test_markers: dict[str, frozenset[str]] = {}
    for candidate in ast.walk(tree):
        if not isinstance(candidate, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not candidate.name.startswith("test"):
            continue
        found: set[str] = set()
        for decorator in candidate.decorator_list:
            found |= _marker_names(decorator)
        if found:
            test_markers[candidate.name] = frozenset(found)

    return ModuleScan(
        path=path.relative_to(root).as_posix(),
        module_markers=frozenset(module_markers),
        test_markers=test_markers,
        has_citation=has_requirement_citation(text, registry_paths),
    )


def scan_modules(root: Path, registry_paths: frozenset[str]) -> list[ModuleScan]:
    """Scan every test module under `tests/`, sorted by path."""
    tests_dir = root / "tests"
    if not tests_dir.is_dir():
        raise InputError(f"{tests_dir}: tests directory not found")
    return [
        scan_module(candidate, root, registry_paths)
        for candidate in sorted(tests_dir.rglob("test_*.py"))
        if "__pycache__" not in candidate.parts
    ]


def in_classified_area(module_path: str) -> bool:
    return any(module_path.startswith(f"{area}/") for area in CLASSIFIED_AREAS)


def find_findings(
    modules: list[ModuleScan],
    baseline: dict[str, str],
    registered: frozenset[str],
) -> list[dict[str, str]]:
    """Apply the classification rule to the scanned modules."""
    findings: list[dict[str, str]] = []
    for module in modules:
        unregistered = module.kinds() - set(registered)
        if unregistered:
            findings.append(
                make_finding(
                    "marker-not-registered",
                    module.path,
                    f"uses {', '.join(sorted(unregistered))}, which is not registered in pyproject.toml",
                )
            )
        if not module.classified:
            if in_classified_area(module.path) and module.path not in baseline:
                findings.append(
                    make_finding(
                        "unclassified-module",
                        module.path,
                        "no taxonomy marker and no baseline entry",
                    )
                )
            continue
        if module.path in baseline:
            findings.append(
                make_finding(
                    "baseline-entry-classified",
                    module.path,
                    f"now carries {'/'.join(sorted(module.module_markers))} -- remove the baseline entry",
                )
            )
        if len(module.module_markers) > 1:
            findings.append(
                make_finding(
                    "module-level-both-kinds",
                    module.path,
                    f"pytestmark claims {' and '.join(sorted(module.module_markers))}",
                )
            )
        if "contract" in module.kinds() and not module.has_citation:
            findings.append(
                make_finding(
                    "contract-without-citation",
                    module.path,
                    "contract marker with no requirement citation",
                )
            )
        for name, markers in sorted(module.test_markers.items()):
            if len(markers) > 1:
                findings.append(
                    make_finding(
                        "test-claims-both-kinds",
                        module.path,
                        f"{name} carries {' and '.join(sorted(markers))}",
                    )
                )
    return findings


def render_findings(findings: list[dict[str, str]]) -> str:
    if not findings:
        return "test taxonomy: no findings\n"
    lines = [f"test taxonomy: {len(findings)} finding(s)"]
    for finding in findings:
        lines.append(
            f"  {finding['category']}: {finding['file']} -- {finding['detail']}"
        )
    return "\n".join(lines) + "\n"


def load_baseline(path: Path) -> dict[str, str]:
    """Return {module path: reason}; an invalid line raises BaselineError."""
    entries: dict[str, str] = {}
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise InputError(f"{path}: cannot read baseline ({exc})") from exc
    for line_no, line in enumerate(text.splitlines(), start=1):
        if not line.strip() or line.startswith("#"):
            continue
        module_path, sep, reason = line.partition("\t")
        if not sep or not module_path.strip():
            raise BaselineError(line_no, "expected '<module path><TAB><reason>'")
        if not ISSUE_PATH_RE.search(reason):
            raise BaselineError(
                line_no, "the reason must name an issue path (issues/...md)"
            )
        if module_path.strip() in entries:
            raise BaselineError(line_no, f"duplicate entry {module_path.strip()}")
        entries[module_path.strip()] = reason.strip()
    return entries


def read_junit(path: Path) -> RunResult:
    """Read one run; a missing, unparsable, or empty file is an InputError."""
    try:
        root = ET.parse(path).getroot()  # nosec B314 — same local, trusted file
    except (OSError, ET.ParseError) as exc:
        raise InputError(f"{path}: cannot read JUnit XML ({exc})") from exc
    cases: dict[str, str] = {}
    failing: set[str] = set()
    total = 0
    for case in root.iter("testcase"):
        total += 1
        classname = case.get("classname") or ""
        name = case.get("name") or ""
        test_id = f"{classname}::{name}" if classname else name
        module_path = classname.replace(".", "/") + ".py" if classname else ""
        cases[test_id] = module_path
        if {child.tag for child in case} & {"failure", "error"}:
            failing.add(test_id)
    if total == 0:
        raise InputError(f"{path}: no testcase found (an interrupted or empty run)")
    return RunResult(cases, frozenset(failing), total)


def kind_of_case(module: ModuleScan, name: str) -> str:
    """Per-test marker when the AST knows the test name, otherwise the module kind."""
    markers = module.test_markers.get(name)
    if markers:
        return sorted(markers)[0]
    if module.module_markers:
        return sorted(module.module_markers)[0]
    return "unclassified"


def group_by_module(
    run: RunResult, modules: list[ModuleScan]
) -> dict[str, dict[str, list[int]]]:
    """Counts per module per kind: {kind: {module path: [tests, failures]}}."""
    by_path = {module.path: module for module in modules}
    grouped: dict[str, dict[str, list[int]]] = {}
    for test_id, module_path in run.cases.items():
        module = by_path.get(module_path)
        if module is None:
            kind = "unclassified"
        else:
            kind = kind_of_case(module, test_id.partition("::")[2].partition("[")[0])
        row = grouped.setdefault(kind, {}).setdefault(module_path, [0, 0])
        row[0] += 1
        if test_id in run.failing:
            row[1] += 1
    return {
        kind: {path: counts for path, counts in sorted(rows.items())}
        for kind, rows in grouped.items()
    }


def render_report(grouped: dict[str, dict[str, list[int]]]) -> str:
    lines: list[str] = []
    for kind in ("characterization", "contract", "unclassified"):
        rows = grouped.get(kind)
        if not rows:
            continue
        tests = sum(counts[0] for counts in rows.values())
        failures = sum(counts[1] for counts in rows.values())
        lines.append(f"{kind}: {tests} tests, {failures} failure(s)")
        for path, counts in rows.items():
            if counts[1]:
                lines.append(f"  {path}: {counts[1]} failure(s)")
    return "\n".join(lines) + "\n"


def blocking_failure(grouped: dict[str, dict[str, list[int]]]) -> bool:
    """REQ-006: only the characterization section is report-only."""
    return any(
        counts[1]
        for kind, rows in grouped.items()
        if kind != "characterization"
        for counts in rows.values()
    )


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Enforce the test-taxonomy classification rule and report the two suites."
    )
    parser.add_argument("--root", type=Path, default=ROOT_DIR, help="repository root")
    parser.add_argument(
        "--baseline", type=Path, default=DEFAULT_BASELINE, help="baseline file"
    )
    parser.add_argument(
        "--junit-xml",
        type=Path,
        metavar="FILE",
        help="JUnit XML of one pytest run; prints the two suite sections grouped by module",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        registered = load_registered_markers(args.root / "pyproject.toml")
        registry_paths = load_registry_paths(args.root)
        baseline = load_baseline(args.baseline)
        modules = scan_modules(args.root, registry_paths)
        findings = find_findings(modules, baseline, registered)
        print(render_findings(findings), end="")
        exit_code = 1 if findings else 0
        if args.junit_xml is not None:
            run = read_junit(args.junit_xml)
            grouped = group_by_module(run, modules)
            print(render_report(grouped), end="")
            if blocking_failure(grouped):
                exit_code = 1
    except (InputError, BaselineError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
