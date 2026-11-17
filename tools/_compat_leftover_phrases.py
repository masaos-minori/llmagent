#!/usr/bin/env python3
"""tools/_compat_leftover_phrases.py

Path-scoped leftover-phrase patterns and contract-guard rules for
``tools/check_compat_shims.py``.

Owns the eleven ``LEFTOVER_PHRASES`` entries, ``check_leftover_phrases``, and
``python_nodes`` (the parse the AST checkers share), and
``check_leftover_phrases`` returns issue strings in the same shape as
``check_compat_patterns`` in ``tools/check_compat_shims.py``. Called from
``check_all`` by plan 20261112-122408 (rmcompat008).

Also owns the compat004 contract-guard tables (``GUARDED_DATACLASS_DEFAULTS``,
``GUARDED_DEFAULTED_PARAMS``, ``GUARDED_DDL_NOT_NULL``,
``HISTORICAL_DOC_PHRASES``) and their rule functions, dispatched through
``check_contract_guards`` (plan 20261116-235333, REQ-001..REQ-004).

Each entry maps a human-readable phrase name to a compiled regex, the path
prefixes (relative to the repository root) it applies to, and a multi-line
flag. The regexes use character classes instead of plain spaces (for example
``Extracted[ ]from``) so ordinary words do not match and the checker does not
flag this module's own source. The module also skips its own file, mirroring
the ``[checker_self_reference]`` allowance in
``tools/compat_exceptions.toml`` without adding an entry there.
"""

from __future__ import annotations

import ast
import re
from functools import cache, lru_cache
from pathlib import Path

# Skip the helper's own source: its pattern-name labels are the leftover
# phrases themselves and would match their own regexes. This mirrors the
# checker's ``[checker_self_reference]`` allowance without widening
# compat_exceptions.toml (plan 20261112-122408 REQ-007 keeps that file
# unchanged).
_SELF_PATH = Path(__file__).resolve()

# name -- compiled regex -- path prefixes (relative to repo root) -- multiline
LEFTOVER_PHRASES: dict[str, tuple[re.Pattern[str], tuple[str, ...], bool]] = {
    "Extracted from": (re.compile(r"Extracted[ ]from"), ("scripts/",), False),
    "Refactored:": (re.compile(r"Refactored:"), ("scripts/",), False),
    "Precedent:": (re.compile(r"Precedent:"), ("scripts/",), False),
    "signature stability": (
        re.compile(r"signature stability"),
        ("scripts/",),
        False,
    ),
    "re-exported for": (re.compile(r"re-exported for"), ("scripts/",), False),
    "predates": (re.compile(r"predates"), ("scripts/",), False),
    "user-approved": (
        re.compile(r"user-approved"),
        ("scripts/", "docs/"),
        False,
    ),
    "pre-migration gate|database": (
        re.compile(r"pre-migration (?:gate|database)"),
        ("scripts/",),
        False,
    ),
    "additive (wire) field": (
        re.compile(r"additive (wire )?field"),
        ("scripts/",),
        False,
    ),
    "bypass(es) build_db_config": (
        re.compile(r"bypass(?:es|ed)?\s+build_db_config"),
        ("scripts/rag/",),
        False,
    ),
    "mirror... exactly": (
        re.compile(r"mirror.{1,50}exactly"),
        ("scripts/", "docs/"),
        True,
    ),
}

# Compat004 contract guards (plan 20261116-235333, REQ-001..REQ-004). The
# tables are content-keyed (class name, function name, table name) so each
# rule fires on the guarded definition itself, wherever it is parsed.
GUARDED_DATACLASS_DEFAULTS: dict[str, tuple[str, ...]] = {
    "WorkflowDef": ("stages", "retry_policy"),
    "RetryPolicy": ("retry_on",),
}

GUARDED_DEFAULTED_PARAMS: dict[str, tuple[str, ...]] = {
    "begin_stage_if_new": ("lease_duration_sec",),
}

GUARDED_DDL_NOT_NULL: dict[str, tuple[str, ...]] = {
    "attempts": ("owner_id", "lease_expires_at"),
}

HISTORICAL_DOC_PHRASES: dict[str, tuple[re.Pattern[str], tuple[str, ...]]] = {
    "legacy age threshold": (
        re.compile(r"legacy age threshold", re.IGNORECASE),
        ("docs/",),
    ),
}

# A historical claim in docs/ is allowed only when the matching line or one of
# the preceding lines within this window carries one of these markers
# (REQ-004; mirrors the checker's _is_historical_context shape — the helper
# must not import the checker, so the marker set lives here).
_HISTORICAL_DOC_MARKERS = re.compile(
    r"\b(?:removed|historical|withdrawn)\b", re.IGNORECASE
)
_HISTORICAL_LOOKBACK = 10


@lru_cache(maxsize=1)
def python_nodes(content: str) -> tuple[ast.AST, ...]:
    """Parse *content* once and return every node; empty on a syntax error.

    ``check_all`` runs several AST checkers over the same file in a row, so a
    one-entry cache lets them share one parse and one tree walk.
    """
    try:
        return tuple(ast.walk(ast.parse(content)))
    except SyntaxError:
        return ()


@cache
def _resolved(path: Path) -> Path:
    return path.resolve()


def _in_scope(file_posix: str, prefix: str) -> bool:
    """True when *file_posix* is under directory *prefix* (segment-aware).

    Matches both repository-relative paths (``scripts/x.py`` starts with the
    prefix) and arbitrary absolute paths (``/tmp/.../scripts/x.py`` contains
    ``/scripts/``), while rejecting look-alikes such as ``/x/myscripts/x.py``.
    """
    return file_posix.startswith(prefix) or f"/{prefix}" in file_posix


def _applicable_phrases(
    file_posix: str,
) -> list[tuple[str, re.Pattern[str], bool]]:
    """The (name, regex, multiline) entries whose path prefixes cover the file."""
    return [
        (name, pattern, multiline)
        for name, (pattern, prefixes, multiline) in LEFTOVER_PHRASES.items()
        if any(_in_scope(file_posix, p) for p in prefixes)
    ]


def check_leftover_phrases(
    content: str, filepath: Path, allowlist: set[Path]
) -> list[str]:
    """Check for path-scoped leftover phrases.

    Returns issue strings in the same format as
    ``check_compat_patterns`` in ``tools/check_compat_shims.py``. Skips
    allowlisted files and files outside every pattern's path prefixes; for a
    multi-line pattern tests each stripped line joined with its successor
    (REQ-002).
    """
    issues: list[str] = []
    resolved = filepath.resolve()
    if resolved in {_resolved(p) for p in allowlist}:
        return issues
    if resolved == _SELF_PATH:
        return issues

    applicable = _applicable_phrases(resolved.as_posix())
    if not applicable:
        return issues
    lines = content.split("\n")
    for idx, raw_line in enumerate(lines):
        lineno = idx + 1
        stripped = raw_line.strip()
        for name, pattern, multiline in applicable:
            if multiline:
                candidate = stripped
                if idx + 1 < len(lines):
                    candidate = f"{stripped} {lines[idx + 1].strip()}"
                if pattern.search(candidate):
                    issues.append(
                        f"{filepath}:{lineno}: backward compatibility leftover "
                        f"— '{name}': {stripped}"
                    )
            elif pattern.search(stripped):
                issues.append(
                    f"{filepath}:{lineno}: backward compatibility leftover "
                    f"— '{name}': {stripped}"
                )
    return issues


def check_dataclass_field_defaults(content: str, filepath: Path) -> list[str]:
    """Fail when a guarded dataclass field carries a default or factory (REQ-001)."""
    issues: list[str] = []
    for node in python_nodes(content):
        if not isinstance(node, ast.ClassDef):
            continue
        guarded = GUARDED_DATACLASS_DEFAULTS.get(node.name)
        if guarded is None:
            continue
        for stmt in node.body:
            if (
                isinstance(stmt, ast.AnnAssign)
                and isinstance(stmt.target, ast.Name)
                and stmt.target.id in guarded
                and stmt.value is not None
            ):
                issues.append(
                    f"{filepath}:{stmt.lineno}: backward compatibility leftover "
                    f"— reintroduced default on {node.name}.{stmt.target.id}"
                )
    return issues


def _allows_none(annotation: ast.expr | None) -> bool:
    """True when the annotation admits ``None`` (``X | None``, ``Optional[X]``, ``Union``)."""
    if annotation is None:
        return False
    if isinstance(annotation, ast.Constant) and annotation.value is None:
        return True
    if isinstance(annotation, ast.BinOp):
        return _allows_none(annotation.left) or _allows_none(annotation.right)
    if isinstance(annotation, ast.Subscript):
        base = annotation.value
        base_name = base.id if isinstance(base, ast.Name) else ""
        if base_name in {"Optional", "Union"}:
            if isinstance(annotation.slice, ast.Tuple):
                return any(_allows_none(elt) for elt in annotation.slice.elts)
            return _allows_none(annotation.slice)
    return False


def check_optional_guarded_params(content: str, filepath: Path) -> list[str]:
    """Fail when a guarded callable takes an optional or defaulted parameter (REQ-002)."""
    issues: list[str] = []
    for node in python_nodes(content):
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        guarded = GUARDED_DEFAULTED_PARAMS.get(node.name)
        if guarded is None:
            continue
        positional = node.args.posonlyargs + node.args.args
        defaulted = {
            arg.arg for arg in positional[len(positional) - len(node.args.defaults) :]
        }
        defaulted |= {
            arg.arg
            for arg, dflt in zip(node.args.kwonlyargs, node.args.kw_defaults)
            if dflt is not None
        }
        for arg in positional + node.args.kwonlyargs:
            if arg.arg not in guarded:
                continue
            if arg.arg in defaulted or _allows_none(arg.annotation):
                issues.append(
                    f"{filepath}:{arg.lineno}: backward compatibility leftover "
                    f"— optional or defaulted '{arg.arg}' in {node.name}()"
                )
    return issues


def check_attempts_ddl_nullability(content: str, filepath: Path) -> list[str]:
    """Fail when a guarded column of a guarded CREATE TABLE block lacks NOT NULL (REQ-003)."""
    issues: list[str] = []
    for table, columns in GUARDED_DDL_NOT_NULL.items():
        match = re.search(
            rf"CREATE TABLE(?: IF NOT EXISTS)? {table}\s*\(", content, re.IGNORECASE
        )
        if match is None:
            continue
        create_line = content[: match.end()].count("\n") + 1
        for offset, raw_line in enumerate(content[match.end() :].split("\n")):
            stripped = raw_line.strip()
            if stripped.startswith(")"):
                break
            first_token = stripped.split(maxsplit=1)[0] if stripped else ""
            if first_token in columns and not re.search(
                r"\bNOT[ ]+NULL\b", stripped, re.IGNORECASE
            ):
                issues.append(
                    f"{filepath}:{create_line + offset}: backward compatibility leftover "
                    f"— nullable {table}.{first_token} column"
                )
    return issues


def check_historical_doc_phrases(content: str, filepath: Path) -> list[str]:
    """Flag current-tense historical claims in docs/ unless marker-allowed (REQ-004)."""
    issues: list[str] = []
    posix = filepath.resolve().as_posix()
    lines = [line.strip() for line in content.split("\n")]
    for name, (pattern, prefixes) in HISTORICAL_DOC_PHRASES.items():
        if not any(_in_scope(posix, prefix) for prefix in prefixes):
            continue
        for idx, stripped in enumerate(lines):
            if not pattern.search(stripped):
                continue
            window = lines[max(0, idx - _HISTORICAL_LOOKBACK) : idx + 1]
            if any(_HISTORICAL_DOC_MARKERS.search(line) for line in window):
                continue
            issues.append(
                f"{filepath}:{idx + 1}: backward compatibility leftover "
                f"— '{name}': {stripped}"
            )
    return issues


_MCP_HEALTH_REEXPORT_NAMES = frozenset(
    {
        "McpServerHealthRegistry",
        "McpServerHealthState",
        "MCPHealthSnapshot",  # pre-rename name
        "ServerHealthState",  # pre-rename name
        "classify_server_failure",  # pre-rename name
    }
)


def check_mcp_health_reexport_import(content: str, filepath: Path) -> list[str]:
    """Flag an import of a Health name from the removed shared.mcp_config re-export.

    Moved here verbatim from ``tools/check_compat_shims.py`` (plan
    20261116-235333, UNK-04) so the checker stays under its size baseline;
    the checker re-imports the name and keeps calling it from ``check_all``.
    """
    if filepath.suffix != ".py":
        return []
    issues: list[str] = []
    for node in python_nodes(content):
        if isinstance(node, ast.ImportFrom) and node.module == "shared.mcp_config":
            for alias in node.names:
                if alias.name in _MCP_HEALTH_REEXPORT_NAMES:
                    issues.append(
                        f"{filepath}:{node.lineno}: Health name imported from the "
                        f"removed shared.mcp_config re-export path — import "
                        f"'{alias.name}' from shared.mcp_health instead"
                    )
    return issues


def check_contract_guards(content: str, filepath: Path) -> list[str]:
    """Dispatch every compat004 contract guard for one scanned file.

    Python files run the dataclass-default, lease-parameter, and attempts-DDL
    guards; markdown files run the historical doc-phrase guard. The helper's
    own source is skipped like ``check_leftover_phrases`` does.
    """
    if filepath.resolve() == _SELF_PATH:
        return []
    if filepath.suffix == ".py":
        issues = check_dataclass_field_defaults(content, filepath)
        issues += check_optional_guarded_params(content, filepath)
        issues += check_attempts_ddl_nullability(content, filepath)
        return issues
    if filepath.suffix == ".md":
        return check_historical_doc_phrases(content, filepath)
    return []


if __name__ == "__main__":
    # Standalone smoke use; the checker owns the real scan loop.
    import sys

    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path()
    print(check_leftover_phrases(target.read_text(encoding="utf-8"), target, set()))
