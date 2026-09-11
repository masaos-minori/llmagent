"""tools/check_mock_patch_targets.py
Static lint checker for `unittest.mock.patch("module.Symbol")` calls in
`tests/` whose target module is not where the code under test actually
looks the symbol up.

Motivating bug pattern (found repeatedly in this repository, e.g.
`tests/agent/test_diagnostic_store.py` patching `db.helper.SQLiteHelper` /
`shared.config_loader.ConfigLoader` instead of
`agent.diagnostic_store.SQLiteHelper` / `agent.diagnostic_store.ConfigLoader`):
a test patches `patch("origin_module.Symbol")`, but the module actually under
test imports `Symbol` at module level via `from origin_module import Symbol`
into its OWN namespace. Once that import executes, the module-under-test
holds its own already-resolved binding for `Symbol` — patching the origin
module's attribute never touches that binding, so the mock silently has no
effect and the test exercises the real `Symbol` instead.

This distinguishes module-level imports (a direct child of a module's
`ast.Module` body) from deferred/local imports (inside a function body, or
guarded by `if TYPE_CHECKING:`): only a module-level import creates this
resolve-once binding. A deferred import inside a function re-resolves
`origin_module.Symbol` on every call, so patching the origin there still
works — such cases are correctly not flagged.

How the check works:
1. Walk every real source module under `scripts/{agent,db,eventbus,
   mcp_servers,rag,shared}/` and `tools/`, and record each module-level
   `from origin_module import Symbol` statement as
   `(origin_module, Symbol) -> {importer_module}`.
2. For each `tests/**/test_*.py` file, collect the set of "candidate SUT
   modules" it imports directly (`import X` / `from X import ...` at any
   scope, where `X` is a known source module) -- this is the module (or
   modules) the test file is plausibly exercising.
3. For each `patch("module.Symbol")` call literal found anywhere in the
   test file (decorator, context manager, or plain call), split the target
   into `(module_path, symbol_name)`. If a candidate SUT module `M != module_path`
   imports `symbol_name` from `module_path` at module level (per step 1's
   index), the patch call is flagged: it targets the origin, but `M` holds
   its own bound reference and will never see the mock.

This is a heuristic, report-only lint: candidate-SUT-module detection can
both over- and under-approximate the module a given patch call actually
means to intercept (a test file may legitimately import multiple modules
for unrelated reasons). Every finding names the exact evidence (the
importer's own `from` statement) so a human can quickly confirm or dismiss
it -- same "candidate, not verdict" posture as
`check_workitem_traceability.py`'s `stale-target-heuristic` category. Findings
never gate this tool's exit code.

Never writes, renames, moves, or deletes anything.

Usage:
    python tools/check_mock_patch_targets.py
    python tools/check_mock_patch_targets.py --format json
    python tools/check_mock_patch_targets.py --format csv

Exit code: always 0 (report-only; see the heuristic-posture note above).
"""

from __future__ import annotations

import argparse
import ast
import csv
import sys
from dataclasses import dataclass
from pathlib import Path

import orjson

ROOT_DIR = Path(__file__).resolve().parent.parent

_SOURCE_PACKAGE_DIRS: tuple[str, ...] = (
    "agent",
    "db",
    "eventbus",
    "mcp_servers",
    "rag",
    "shared",
)


def _dotted_path_for(rel_parts: tuple[str, ...]) -> str | None:
    parts = list(rel_parts)
    if not parts:
        return None
    if parts[-1] == "__init__.py":
        parts = parts[:-1]
    elif parts[-1].endswith(".py"):
        parts[-1] = parts[-1][: -len(".py")]
    else:
        return None
    if not parts:
        return None
    return ".".join(parts)


def discover_source_modules() -> dict[str, Path]:
    """Map every real source module's dotted path to its file.

    Mirrors `[tool.setuptools.packages.find]` in `pyproject.toml`
    (`where = ["scripts", "."]`, `include = [...]`): `scripts/agent/x.py` is
    importable as `agent.x`, and `tools/x.py` as `tools.x`.
    """
    modules: dict[str, Path] = {}
    scripts_dir = ROOT_DIR / "scripts"
    for pkg_name in _SOURCE_PACKAGE_DIRS:
        pkg_dir = scripts_dir / pkg_name
        if not pkg_dir.is_dir():
            continue
        for py_path in sorted(pkg_dir.rglob("*.py")):
            if "__pycache__" in py_path.parts:
                continue
            dotted = _dotted_path_for(py_path.relative_to(scripts_dir).parts)
            if dotted is not None:
                modules[dotted] = py_path

    tools_dir = ROOT_DIR / "tools"
    if tools_dir.is_dir():
        for py_path in sorted(tools_dir.rglob("*.py")):
            if "__pycache__" in py_path.parts:
                continue
            dotted = _dotted_path_for(py_path.relative_to(ROOT_DIR).parts)
            if dotted is not None:
                modules[dotted] = py_path

    return modules


def _resolve_relative_module(current_dotted: str, node: ast.ImportFrom) -> str | None:
    """Best-effort resolution of `from . import x` / `from ..y import x`
    relative to the importing module's own dotted path.
    """
    if node.level == 0:
        return node.module
    parts = current_dotted.split(".")[:-1]
    for _ in range(node.level - 1):
        if not parts:
            return None
        parts = parts[:-1]
    if node.module:
        parts = parts + node.module.split(".")
    return ".".join(parts) if parts else None


@dataclass(frozen=True)
class ModuleLevelImport:
    origin_module: str
    imported_name: str


def extract_module_level_imports(
    dotted_path: str, tree: ast.Module
) -> list[ModuleLevelImport]:
    """Direct children of `tree.body` only -- this is what excludes
    function-local (deferred) imports and `if TYPE_CHECKING:`-guarded
    imports (both live inside a nested node, never as a direct `Module.body`
    child), matching this checker's module-level-only scope.
    """
    imports: list[ModuleLevelImport] = []
    for node in tree.body:
        if not isinstance(node, ast.ImportFrom):
            continue
        origin = _resolve_relative_module(dotted_path, node)
        if origin is None:
            continue
        for alias in node.names:
            if alias.name == "*":
                continue
            imports.append(ModuleLevelImport(origin, alias.name))
    return imports


ReverseImportIndex = dict[tuple[str, str], set[str]]


def build_reverse_import_index(
    source_modules: dict[str, Path],
) -> ReverseImportIndex:
    """Map `(origin_module, imported_name) -> {importer modules}`."""
    index: ReverseImportIndex = {}
    for dotted_path, file_path in source_modules.items():
        try:
            tree = ast.parse(
                file_path.read_text(encoding="utf-8"), filename=str(file_path)
            )
        except (SyntaxError, UnicodeDecodeError):
            continue
        for imp in extract_module_level_imports(dotted_path, tree):
            key = (imp.origin_module, imp.imported_name)
            index.setdefault(key, set()).add(dotted_path)
    return index


def candidate_sut_modules(tree: ast.Module, known_modules: set[str]) -> set[str]:
    """Modules a test file imports (at any scope) that are known real
    source modules -- a proxy for "what this test file plausibly exercises".
    """
    candidates: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            if node.module in known_modules:
                candidates.add(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in known_modules:
                    candidates.add(alias.name)
    return candidates


def _is_patch_call(node: ast.Call) -> bool:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id == "patch"
    if isinstance(func, ast.Attribute):
        return func.attr == "patch"
    return False


def extract_patch_targets(tree: ast.Module) -> list[tuple[int, str]]:
    """Return (line_number, target_string) for every `patch("a.b.C")`-style
    call with a literal string first argument, wherever it appears
    (decorator, `with` context manager, or plain call).
    """
    targets: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not _is_patch_call(node):
            continue
        if not node.args:
            continue
        first_arg = node.args[0]
        if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
            targets.append((node.lineno, first_arg.value))
    return targets


def make_finding(category: str, location: str, detail: str) -> dict[str, str]:
    return {"category": category, "file": location, "detail": detail}


def find_ineffective_patch_targets(
    test_files: list[Path],
    reverse_index: ReverseImportIndex,
    known_modules: set[str],
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for py_path in test_files:
        text = py_path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(text, filename=str(py_path))
        except SyntaxError:
            continue

        rel_path = py_path.relative_to(ROOT_DIR).as_posix()
        candidates = candidate_sut_modules(tree, known_modules)
        if not candidates:
            continue

        for lineno, target in extract_patch_targets(tree):
            module_path, sep, symbol_name = target.rpartition(".")
            if not sep or not module_path or not symbol_name:
                continue
            importers = reverse_index.get((module_path, symbol_name), set())
            affected = sorted(m for m in (candidates & importers) if m != module_path)
            for importer in affected:
                findings.append(
                    make_finding(
                        "ineffective-patch-target",
                        f"{rel_path}:{lineno}",
                        f'patch("{target}") targets the origin module, but '
                        f"'{importer}' imports {symbol_name} via "
                        f"'from {module_path} import {symbol_name}' at "
                        f"module level -- patching '{module_path}.{symbol_name}' "
                        f"will not affect what '{importer}' sees; consider "
                        f"patching '{importer}.{symbol_name}' instead",
                    )
                )
    return findings


def discover_test_files(tests_dir: Path) -> list[Path]:
    if not tests_dir.is_dir():
        return []
    return [
        p for p in sorted(tests_dir.rglob("test_*.py")) if "__pycache__" not in p.parts
    ]


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
            "Report-only heuristic scan of tests/**/test_*.py for "
            "unittest.mock.patch(...) calls whose string target is a "
            "source module that a candidate module-under-test re-imports "
            "the same symbol away from at module level -- such a patch "
            "never affects what the module-under-test sees."
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

    source_modules = discover_source_modules()
    reverse_index = build_reverse_import_index(source_modules)
    test_files = discover_test_files(ROOT_DIR / "tests")
    findings = find_ineffective_patch_targets(
        test_files, reverse_index, set(source_modules)
    )

    if args.format == "json":
        print(render_json(findings))
    elif args.format == "csv":
        print(render_csv(findings), end="")
    else:
        print(render_text(findings), end="")

    return 0


if __name__ == "__main__":
    sys.exit(main())
