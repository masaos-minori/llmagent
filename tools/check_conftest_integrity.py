"""tools/check_conftest_integrity.py
Verifies `tests/conftest.py` exists and still defines every known-required
autouse fixture.

Motivating incident: `tests/conftest.py` was silently renamed to
`tests/conftest.py.bak` by an unrelated commit for roughly a month. Because
pytest simply stops collecting a conftest.py that is not named exactly
`conftest.py`, this produced no import error or collection failure -- it
silently disabled every autouse fixture defined there (e.g. the tool
registry reset between tests), which surfaced only much later as ~130
test-order-dependent pollution failures with no direct link back to the
rename. No existing tool checks for this class of problem: `pytest
--collect-only` succeeds either way, and a missing/renamed conftest.py is
not a Python import error.

This checker is deliberately narrow and cheap: it does not try to detect
every possible autouse-fixture regression, only two concrete signals that
would have caught the actual incident immediately:

1. conftest-missing: `tests/conftest.py` does not exist as a file.
2. conftest-suspicious-backup-file: a sibling file matching
   `conftest.py.<anything>` (e.g. `conftest.py.bak`, `.orig`, `.old`)
   exists next to it -- the exact shape of the incident.
3. conftest-missing-fixture: `tests/conftest.py` exists, but one of
   `REQUIRED_AUTOUSE_FIXTURES` is no longer defined as an
   `@pytest.fixture(autouse=True)` function in it.

`REQUIRED_AUTOUSE_FIXTURES` is a hardcoded manifest, not an auto-derived
list -- when a new load-bearing autouse fixture is added to
`tests/conftest.py`, add its name here too. This is a deliberate trade-off:
a hardcoded list requires a human to remember to update it, but a fully
automatic "diff against last known state" design would need its own state
file to compare against, which is more machinery than this narrow,
low-frequency check warrants.

Never writes, renames, moves, or deletes anything.

Usage:
    python tools/check_conftest_integrity.py
    python tools/check_conftest_integrity.py --format json
    python tools/check_conftest_integrity.py --format csv

Exit code: 1 if any finding exists (all three categories are hard failures,
unlike check_workitem_traceability.py's heuristic categories -- a missing
file, a suspicious backup sibling, or a missing required fixture are each
unambiguous, not candidates for human judgment); 0 otherwise.
"""

from __future__ import annotations

import argparse
import ast
import csv
import sys
from pathlib import Path

import orjson

ROOT_DIR = Path(__file__).resolve().parent.parent

CONFTEST_PATH = ROOT_DIR / "tests" / "conftest.py"

# Update this list whenever a new load-bearing autouse fixture is added to
# tests/conftest.py -- see this module's docstring for why it is not
# auto-derived.
REQUIRED_AUTOUSE_FIXTURES: tuple[str, ...] = (
    "_reset_tool_registry",
    "_reset_web_search_health_and_metrics",
)


def make_finding(category: str, file_path: str, detail: str) -> dict[str, str]:
    return {"category": category, "file": file_path, "detail": detail}


def find_suspicious_backup_files(conftest_path: Path) -> list[dict[str, str]]:
    """A sibling `conftest.py.<anything>` file is the exact shape of the
    historical incident: the real file renamed aside, leaving pytest to
    silently collect nothing where it used to collect autouse fixtures.
    """
    findings: list[dict[str, str]] = []
    parent = conftest_path.parent
    if not parent.is_dir():
        return findings
    for candidate in sorted(parent.glob("conftest.py.*")):
        if not candidate.is_file():
            continue
        rel_path = candidate.relative_to(ROOT_DIR).as_posix()
        findings.append(
            make_finding(
                "conftest-suspicious-backup-file",
                rel_path,
                f"looks like a renamed-aside copy of "
                f"{conftest_path.relative_to(ROOT_DIR).as_posix()} -- if "
                f"this was an accidental rename, autouse fixtures defined "
                f"in it have silently stopped running for every test",
            )
        )
    return findings


def extract_autouse_fixture_names(text: str) -> set[str]:
    """Return every function name decorated with
    `@pytest.fixture(..., autouse=True, ...)` (any argument order/position).
    """
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return set()

    names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue
            func = decorator.func
            is_fixture_call = (isinstance(func, ast.Name) and func.id == "fixture") or (
                isinstance(func, ast.Attribute) and func.attr == "fixture"
            )
            if not is_fixture_call:
                continue
            for keyword in decorator.keywords:
                if (
                    keyword.arg == "autouse"
                    and isinstance(keyword.value, ast.Constant)
                    and keyword.value.value is True
                ):
                    names.add(node.name)
    return names


def find_conftest_findings(
    conftest_path: Path, required_fixtures: tuple[str, ...]
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    findings.extend(find_suspicious_backup_files(conftest_path))

    rel_path = conftest_path.relative_to(ROOT_DIR).as_posix()
    if not conftest_path.is_file():
        findings.append(
            make_finding(
                "conftest-missing",
                rel_path,
                "file does not exist -- every autouse fixture normally "
                "defined here is silently not running for any test",
            )
        )
        return findings

    text = conftest_path.read_text(encoding="utf-8")
    found_fixtures = extract_autouse_fixture_names(text)
    for fixture_name in required_fixtures:
        if fixture_name not in found_fixtures:
            findings.append(
                make_finding(
                    "conftest-missing-fixture",
                    rel_path,
                    f"required autouse fixture '{fixture_name}' not found "
                    f"(removed, renamed, or its autouse=True dropped)",
                )
            )
    return findings


def render_text(findings: list[dict[str, str]]) -> str:
    if not findings:
        return "No findings.\n"
    lines = [f"[{f['category']}] {f['file']}: {f['detail']}" for f in findings]
    lines.append(f"\n{len(findings)} finding(s) total.")
    return "\n".join(lines) + "\n"


def render_json(findings: list[dict[str, str]]) -> str:
    return orjson.dumps(
        findings, option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS
    ).decode()


def render_csv(findings: list[dict[str, str]]) -> str:
    import io

    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=["category", "file", "detail"])
    writer.writeheader()
    writer.writerows(findings)
    return buffer.getvalue()


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Verify tests/conftest.py exists, has no suspicious renamed-"
            "aside sibling (conftest.py.*), and still defines every "
            "known-required autouse fixture."
        )
    )
    parser.add_argument(
        "--format",
        choices=["json", "csv"],
        default=None,
        help="Machine-readable output format (default: human-readable text)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    findings = find_conftest_findings(CONFTEST_PATH, REQUIRED_AUTOUSE_FIXTURES)

    if args.format == "json":
        print(render_json(findings))
    elif args.format == "csv":
        print(render_csv(findings), end="")
    else:
        print(render_text(findings), end="")

    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
