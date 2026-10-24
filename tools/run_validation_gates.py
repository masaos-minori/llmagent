#!/usr/bin/env python3
"""tools/run_validation_gates.py — Run the validation gates a change needs.

Given a base ref, discover the changed files (staged plus unstaged), map them to the
validation gates each change needs, run those gates in the documented order, and print
one ``Pass``/``Fail``/``Partial``/``Not available``/``Blocked`` summary.

The gates come from two sources that feed one embedded data structure:

- ``rules/toolchain.md`` "Standard validation sequence" — a linear 9-step order used by
  full mode (and as the canonical run). The embedded commands mirror it verbatim; they are
  not independently editable anywhere else, so ``rules/toolchain.md`` stays the canonical
  command list.
- ``routing.md`` "When to run which tool" — ~29 path-keyed conditional checkers used by
  fast mode to select only what the changed files trigger.

Fast mode runs only the routing gates the changed files match. Full mode runs the same
routing selection plus every toolchain gate (which adds the full ``pytest`` suite and
``diff-cover``). Fast mode is therefore a subset of full mode.

Result classification uses the canonical vocabulary from
``rules/ai-execution.md`` Repository Tool Usage item 11. A skipped or unavailable gate is
reported as ``Not available`` (or its real status), never as ``Pass``.

Two sub behaviours:

- default (no subcommand): run the selected gates. ``--base`` selects the git ref to diff
  against (default ``master``); ``--full`` selects full mode (default is fast mode).
- ``drift``: verify that every checker named in ``routing.md``'s "When to run which tool"
  table has a mapping entry. Exits non-zero when a listed checker has no mapping entry, so
  ``routing.md`` cannot advance ahead of this tool silently (REQ-006).

Gates whose command carries a runtime placeholder (any argv token containing ``<``, ``[``,
``]``, or ``...``) cannot be auto-invoked without a concrete argument and are reported as
``Not available`` at run time while still keeping their mapping entry (so the drift check
still passes). External commands are always run as subprocesses with a list argument (no
shell) so this tool cannot silently disagree with the real checkers.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from subprocess import CompletedProcess

# Canonical Pass/Fail/Partial/Not available/Blocked vocabulary (rules/ai-execution.md item 11).
VOCAB = ("Pass", "Fail", "Partial", "Not available", "Blocked")

# Which source each gate was transcribed from; also the drift check's filter.
SOURCE_TOOLCHAIN = "toolchain"
SOURCE_ROUTING = "routing"

# Full mode adds the toolchain sequence; fast mode runs only the routing selection.
MODE_FAST = "fast"
MODE_FULL = "full"

_ROUTING_HEADING = "### When to run which tool"
# The orchestrator has its own row in that table, but it cannot be a gate of itself, so
# the drift check ignores that row.
_SELF_CHECKER_ID = Path(__file__).stem
# Tokens that mark a command as needing a concrete runtime argument.
_PLACEHOLDER_TOKEN_RE = re.compile(r"[<\[\]]|\.\.\.")
# A git ref we will hand to `git diff`: alphanumerics plus . _ / -. Anything else is
# rejected before it reaches the subprocess so it cannot be read as a git option.
_REF_RE = re.compile(r"^[A-Za-z0-9._/-]+$")
# argv token that names a tools/<name>.py the gate runs. Unanchored so it matches both
# repo-relative paths (``tools/foo.py``) and absolute paths (``/x/tools/foo.py``); git diff
# emits the former, so the old ``.*``-prefixed form never matched and every id collapsed.
_TOOL_PY_RE = re.compile(r"tools/([A-Za-z0-9_]+)\.py")
# Flags whose following value disambiguates two checkers that share a tool basename.
_VALUE_FLAG_RE = re.compile(r"^--(type|format|domain|kind|status)$")


@dataclass(frozen=True)
class Gate:
    """One validation gate: what it is, how to run it, and when it applies.

    ``command`` is a tuple of argv tuples (a gate may run several commands in order, e.g.
    ``ruff format`` then ``ruff check``). ``patterns`` are path globs that select a gate in
    fast mode; a gate with no patterns is a manual/content-based checker that fast mode
    never auto-selects. ``env`` is extra environment as ``(key, value)`` pairs.
    """

    name: str
    command: tuple[tuple[str, ...], ...]
    source: str
    mode: str
    patterns: tuple[str, ...] = ()
    env: tuple[tuple[str, str], ...] = ()

    @property
    def requires_context(self) -> bool:
        """True when any argv token carries a runtime placeholder (cannot auto-invoke)."""
        for cmd in self.command:
            if any(_PLACEHOLDER_TOKEN_RE.search(tok) for tok in cmd):
                return True
        return False

    @property
    def display_command(self) -> str:
        """Single-line rendering of the gate's sequential commands."""
        return " && ".join(" ".join(cmd) for cmd in self.command)

    @property
    def checker_id(self) -> str:
        """Stable per-checker id derived from the first command's argv.

        Used by the drift check to compare this tool's mapping against ``routing.md``. Two
        checkers that share a tool basename are disambiguated by their subcommand or flag
        value, so the id is unique per routing.md row.
        """
        return _checker_id_from_command(self.command[0]) if self.command else ""


@dataclass(frozen=True)
class GateResult:
    """Outcome of running one gate, using the canonical vocabulary."""

    name: str
    status: str
    command: str
    detail: str = ""


Runner = Callable[[list[str], dict[str, str] | None], "CompletedProcess"]


def _validate_ref(base: str) -> None:
    """Reject a base ref that is not a safe git revision before it reaches subprocess."""
    if not _REF_RE.match(base):
        raise ValueError(
            f"invalid git ref '{base}': only letters, digits, '.', '_', '/', '-' allowed"
        )


def _git_diff_name_only(extra_args: list[str]) -> list[str]:
    """Return repo-relative paths from `git diff --name-only <extra_args>`."""
    proc = subprocess.run(
        ["git", "diff", "--name-only", *extra_args],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"git diff failed (exit {proc.returncode}): {proc.stderr.strip()}"
        )
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def _changed_files(base: str) -> list[str]:
    """Discover changed repo-relative paths: staged plus unstaged, relative to ``base``.

    Staged changes are diffed against ``base``; unstaged (working-tree vs index) changes
    are diffed against the index. The union is de-duplicated preserving first-seen order.
    """
    _validate_ref(base)
    staged = _git_diff_name_only(["--staged", "--diff-filter=AMRC", base])
    unstaged = _git_diff_name_only(["--diff-filter=AMRC"])
    seen: set[str] = set()
    ordered: list[str] = []
    for path in (*staged, *unstaged):
        if path and path not in seen:
            seen.add(path)
            ordered.append(path)
    return ordered


def _glob_to_regex(pattern: str) -> re.Pattern[str]:
    """Translate a glob (supporting ``**``) into an anchored regex.

    ``*`` matches within a path segment; ``**`` spans directories; ``?`` matches one
    non-slash character.
    """
    out: list[str] = []
    i = 0
    n = len(pattern)
    while i < n:
        char = pattern[i]
        if char == "*":
            if i + 1 < n and pattern[i + 1] == "*":
                out.append(".*")
                i += 2
                if i < n and pattern[i] == "/":
                    out.append("/")
                    i += 1
                continue
            out.append("[^/]*")
            i += 1
            continue
        if char == "?":
            out.append("[^/]")
            i += 1
            continue
        out.append(re.escape(char))
        i += 1
    return re.compile("^" + "".join(out) + "$")


def _matches(changed: Iterable[str], patterns: tuple[str, ...]) -> bool:
    """True when any changed path matches any of ``patterns``."""
    compiled = [_glob_to_regex(p) for p in patterns]
    return any(rx.match(path) for path in changed for rx in compiled)


def _merge_env(env: tuple[tuple[str, str], ...]) -> dict[str, str] | None:
    """Return an environment dict with ``env`` layered over the inherited one.

    Returns ``None`` (subprocess inherits the current environment) when there is nothing to
    layer, so a plain gate never runs with an emptied environment.
    """
    if not env:
        return None
    new_env = dict(os.environ)
    new_env.update(dict(env))
    return new_env


def select_gates(changed: Iterable[str], mode: str) -> list[Gate]:
    """Return the gates to run for ``changed`` paths in ``mode``, in documented order.

    Fast mode selects the routing gates whose patterns match a changed path. Full mode adds
    every toolchain gate on top of that selection. Routing gates with no patterns (manual
    or content-based checkers) are never auto-selected.
    """
    changed_list = list(changed)
    selected: list[Gate] = []
    for gate in _ALL_GATES:
        if gate.source == SOURCE_ROUTING:
            if not gate.patterns:
                continue
            if not _matches(changed_list, gate.patterns):
                continue
            if mode in (MODE_FAST, MODE_FULL):
                selected.append(gate)
        elif mode == MODE_FULL:
            selected.append(gate)
    return selected


def classify(returncode: int | None, *, unavailable: bool) -> str:
    """Map a gate's execution outcome onto the canonical vocabulary.

    An unavailable gate (missing local tool, or a command needing a runtime argument) is
    ``Not available`` and is never collapsed into ``Pass``.
    """
    if unavailable or returncode is None:
        return "Not available"
    if returncode == 0:
        return "Pass"
    return "Fail"


def _subprocess_runner(argv: list[str], env: dict[str, str] | None) -> CompletedProcess:
    """Default runner: execute ``argv`` with no shell and an optional environment layer."""
    return subprocess.run(argv, capture_output=True, text=True, check=False, env=env)


def run_gate(gate: Gate, *, runner: Runner | None = None) -> GateResult:
    """Run one gate and classify its result.

    Runs each of the gate's commands in order, stopping at the first non-zero exit (a
    ``Fail``). A missing local tool (e.g. ``ast-grep``/``diff-cover``) is ``Not available``,
    never ``Pass``. ``runner`` is injectable for tests.
    """
    effective_runner: Runner = runner or _subprocess_runner
    if gate.requires_context:
        return GateResult(
            gate.name,
            "Not available",
            gate.display_command,
            "needs a runtime argument (placeholder in command)",
        )
    env = _merge_env(gate.env)
    try:
        for cmd in gate.command:
            proc = effective_runner(list(cmd), env)
            if proc.returncode != 0:
                return GateResult(
                    gate.name,
                    "Fail",
                    gate.display_command,
                    f"exit code {proc.returncode}",
                )
    except FileNotFoundError as exc:
        return GateResult(
            gate.name,
            "Not available",
            gate.display_command,
            f"command not found: {exc.filename}",
        )
    except OSError as exc:
        return GateResult(
            gate.name,
            "Not available",
            gate.display_command,
            str(exc),
        )
    return GateResult(gate.name, "Pass", gate.display_command)


def _checker_id_from_command(argv: tuple[str, ...]) -> str:
    """Derive a stable per-checker id from a command's argv (see ``Gate.checker_id``)."""
    tokens = list(argv)
    base: str = ""
    base_idx: int = -1
    for i, tok in enumerate(tokens):
        m = _TOOL_PY_RE.search(tok)
        if m:
            base = m.group(1)
            base_idx = i
            break
    if not base:
        return tokens[0] if tokens else ""
    rest = tokens[base_idx + 1 :]
    # A value flag (--type/--format/...) consumes the following token as its value; skip
    # those values when looking for a positional subcommand so "--type mcp" is not read as
    # the positional "mcp".
    positional: str | None = None
    skip_next = False
    for tok in rest:
        if skip_next:
            skip_next = False
            continue
        if _VALUE_FLAG_RE.match(tok):
            skip_next = True
            continue
        if not tok.startswith("-"):
            positional = tok
            break
    if positional is not None:
        return f"{base}:{positional.replace(chr(92), '')}"
    for i, tok in enumerate(rest):
        if _VALUE_FLAG_RE.match(tok):
            value = rest[i + 1] if i + 1 < len(rest) else ""
            return f"{base}:{tok}:{value.replace(chr(92), '')}"
    bare_flag = next((tok for tok in rest if tok.startswith("--")), None)
    return f"{base}:{bare_flag}" if bare_flag is not None else base


def _checker_id_from_cell(run_cell: str) -> str:
    """Derive the same id from a raw ``routing.md`` "Run" cell (strips markdown escaping)."""
    cleaned = run_cell.replace(chr(92), "").replace("`", "").strip()
    return _checker_id_from_command(tuple(cleaned.split()))


def _split_md_row(row: str) -> list[str]:
    """Split a markdown table row into cells.

    Splits on ``|`` only when it sits outside a backtick-quoted code span and is not escaped
    (``\\|``). Escaped pipes collapse to a literal ``|`` so downstream id derivation sees the
    real argument value (e.g. ``--format json|csv``). This is required because the "Trigger"
    column also contains code spans and escaped pipes, so a naive ``str.split("|")`` fragments
    those cells and truncates the "Run" cell.
    """
    cells: list[str] = []
    buf: list[str] = []
    in_code = False
    i = 0
    n = len(row)
    while i < n:
        ch = row[i]
        if ch == "`":
            in_code = not in_code
            buf.append(ch)
            i += 1
        elif ch == "\\" and i + 1 < n and row[i + 1] == "|":
            buf.append("|")
            i += 2
        elif ch == "|" and not in_code:
            cells.append("".join(buf))
            buf = []
            i += 1
        else:
            buf.append(ch)
            i += 1
    cells.append("".join(buf))
    return cells


def _parse_routing_run_cells(text: str) -> list[str]:
    """Return the "Run" cell of each data row in routing.md's "When to run which tool" table."""
    lines = text.splitlines()
    start = next(
        (i for i, line in enumerate(lines) if line.strip() == _ROUTING_HEADING),
        None,
    )
    if start is None:
        raise RuntimeError(
            f"{_ROUTING_HEADING!r} heading not found in routing.md; cannot run drift check"
        )
    run_idx: int | None = None
    in_table = False
    cells: list[str] = []
    results: list[str] = []
    for line in lines[start + 1 :]:
        stripped = line.strip()
        if not stripped.startswith("|"):
            if in_table:
                break
            continue
        cells = [cell.strip() for cell in _split_md_row(stripped.strip("|"))]
        if not in_table:
            if "Run" in cells:
                run_idx = cells.index("Run")
                in_table = True
            continue
        if all(re.fullmatch(r"-+", cell) for cell in cells):
            continue  # separator row
        if run_idx is None or len(cells) <= run_idx:
            continue
        results.append(cells[run_idx])
    return results


def drift_report(routing_text: str) -> tuple[int, list[str]]:
    """Compare routing.md's checkers against this tool's mapping.

    Returns ``(error_count, messages)``. Every routing.md checker must have a mapping entry
    and every mapping entry must come from routing.md; either drift is an error. The row
    that names this orchestrator itself is not a checker and is excluded.
    """
    expected = {
        _checker_id_from_cell(cell) for cell in _parse_routing_run_cells(routing_text)
    } - {_SELF_CHECKER_ID}
    actual = {gate.checker_id for gate in ROUTING_GATES}
    errors: list[str] = [
        f"routing.md checker has no mapping entry: {missing}"
        for missing in sorted(expected - actual)
    ]
    errors += [
        f"mapping entry is not a routing.md checker: {extra}"
        for extra in sorted(actual - expected)
    ]
    return len(errors), errors


def _print_summary(results: list[GateResult], changed: list[str], mode: str) -> None:
    """Print the per-gate summary table and the changed-file/mode header."""
    print(
        f"Validation gates — mode: {mode}, base: master, changed files: {len(changed)}"
    )
    if changed:
        print(", ".join(changed))
    print()
    if not results:
        print("No gates selected for these changed files.")
        return
    name_width = max(len(r.name) for r in results)
    status_width = max(len(r.status) for r in results)
    for res in results:
        name = res.name.ljust(name_width)
        status = res.status.ljust(status_width)
        print(f"  {name}  {status}  {res.command}")
        if res.detail:
            print(f"          ({res.detail})")


def _run_gates(base: str, mode: str) -> int:
    changed = _changed_files(base)
    gates = select_gates(changed, mode)
    results = [run_gate(gate) for gate in gates]
    _print_summary(results, changed, mode)
    return 1 if any(res.status == "Fail" for res in results) else 0


def _run_drift() -> int:
    routing_path = Path(__file__).resolve().parent.parent / "routing.md"
    try:
        text = routing_path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"ERROR: cannot read routing.md: {exc}", file=sys.stderr)
        return 1
    count, errors = drift_report(text)
    if count:
        for message in errors:
            print(message, file=sys.stderr)
        return 1
    print(f"OK: {len(ROUTING_GATES)} routing.md checker(s) all mapped")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run the validation gates a change needs, chosen from the changed files, "
            "and print one Pass/Fail/Partial/Not available/Blocked summary."
        )
    )
    parser.add_argument(
        "--base",
        default="master",
        help="Git ref to diff against for changed files (default: master)",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Full mode: also run the rules/toolchain.md sequence (full pytest + "
        "diff-cover). Default is fast mode (changed-file gates only).",
    )
    subparsers = parser.add_subparsers(dest="action")
    subparsers.add_parser(
        "drift",
        help="Verify every routing.md 'When to run which tool' checker has a mapping entry",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.action == "drift":
        return _run_drift()
    return _run_gates(args.base, "full" if args.full else MODE_FAST)


# --- Embedded gate inventory -----------------------------------------------------
# Transcribed from rules/toolchain.md (9-step sequence, full mode) and routing.md
# "When to run which tool" (path-keyed checkers, fast mode). Keep the commands equal to
# those sources; the drift check fails if routing.md gains a checker without a matching
# entry here.

TOOLCHAIN_GATES: tuple[Gate, ...] = (
    Gate(
        name="ruff-format-lint",
        command=(
            ("uv", "run", "ruff", "format", "scripts/"),
            ("uv", "run", "ruff", "check", "scripts/"),
        ),
        source=SOURCE_TOOLCHAIN,
        mode=MODE_FULL,
    ),
    Gate(
        name="mypy",
        command=(("uv", "run", "mypy", "--no-namespace-packages", "scripts/"),),
        source=SOURCE_TOOLCHAIN,
        mode=MODE_FULL,
    ),
    Gate(
        name="lint-imports",
        command=(("uv", "run", "lint-imports"),),
        source=SOURCE_TOOLCHAIN,
        mode=MODE_FULL,
        env=(("PYTHONPATH", "scripts"),),
    ),
    Gate(
        name="ast-grep",
        command=(
            (
                "ast-grep",
                "--pattern",
                "except: $$$",
                "--lang",
                "python",
                "scripts/",
            ),
        ),
        source=SOURCE_TOOLCHAIN,
        mode=MODE_FULL,
    ),
    Gate(
        name="bandit",
        command=(
            (
                "uv",
                "run",
                "bandit",
                "-r",
                "scripts/",
                "-c",
                "pyproject.toml",
                "-ll",
            ),
        ),
        source=SOURCE_TOOLCHAIN,
        mode=MODE_FULL,
    ),
    Gate(
        name="pytest",
        command=(
            ("uv", "run", "pytest", "tests/"),
            (
                "uv",
                "run",
                "pytest",
                "tests/mcp_servers/mdq/test_mdq_rag_boundary.py",
            ),
        ),
        source=SOURCE_TOOLCHAIN,
        mode=MODE_FULL,
    ),
    Gate(
        name="diff-cover",
        command=(
            ("uv", "run", "coverage", "run", "-m", "pytest", "tests/"),
            ("uv", "run", "coverage", "xml"),
            (
                "uv",
                "run",
                "diff-cover",
                "coverage.xml",
                "--compare-branch",
                "master",
                "--fail-under",
                "90",
            ),
        ),
        source=SOURCE_TOOLCHAIN,
        mode=MODE_FULL,
    ),
    Gate(
        name="pre-commit",
        command=(("uv", "run", "pre-commit", "run", "--all-files"),),
        source=SOURCE_TOOLCHAIN,
        mode=MODE_FULL,
    ),
    Gate(
        name="diff-review",
        command=(("git", "diff"),),
        source=SOURCE_TOOLCHAIN,
        mode=MODE_FULL,
    ),
)

ROUTING_GATES: tuple[Gate, ...] = (
    Gate(
        name="check_docs_quality",
        command=(("uv", "run", "python", "tools/check_docs_quality.py"),),
        source=SOURCE_ROUTING,
        mode=MODE_FAST,
        patterns=("docs/**",),
    ),
    Gate(
        name="check_docs_structure",
        command=(
            (
                "uv",
                "run",
                "python",
                "tools/check_docs_structure.py",
                "[glob",
                "...]",
            ),
        ),
        source=SOURCE_ROUTING,
        mode=MODE_FAST,
        patterns=("docs/**",),
    ),
    Gate(
        name="check_db_separation",
        command=(("uv", "run", "python", "tools/check_db_separation.py"),),
        source=SOURCE_ROUTING,
        mode=MODE_FAST,
        patterns=("scripts/db/schema_sql.py", "scripts/eventbus/schema.sql"),
    ),
    Gate(
        name="check_module_size",
        command=(("uv", "run", "python", "tools/check_module_size.py"),),
        source=SOURCE_ROUTING,
        mode=MODE_FAST,
        patterns=("scripts/*.py", "scripts/**/*.py"),
    ),
    Gate(
        name="check_docs_content_policy",
        command=(("uv", "run", "python", "tools/check_docs_content_policy.py"),),
        source=SOURCE_ROUTING,
        mode=MODE_FAST,
        patterns=("docs/**",),
    ),
    Gate(
        name="check_docs_consistency",
        command=(
            (
                "uv",
                "run",
                "python",
                "tools/check_docs_consistency.py",
                "--domain",
                "<domain>",
            ),
        ),
        source=SOURCE_ROUTING,
        mode=MODE_FAST,
        patterns=("docs/**",),
    ),
    Gate(
        name="check_needs_confirmation_inventory",
        command=(
            (
                "uv",
                "run",
                "python",
                "tools/check_needs_confirmation_inventory.py",
            ),
        ),
        source=SOURCE_ROUTING,
        mode=MODE_FAST,
        patterns=("docs/**",),
    ),
    Gate(
        name="check_tool_descriptions_sync",
        command=(("uv", "run", "python", "tools/check_tool_descriptions_sync.py"),),
        source=SOURCE_ROUTING,
        mode=MODE_FAST,
        patterns=("tools/**",),
    ),
    Gate(
        name="rename_doc",
        command=(
            (
                "uv",
                "run",
                "python",
                "tools/rename_doc.py",
                "<old>",
                "<new>",
            ),
        ),
        source=SOURCE_ROUTING,
        mode=MODE_FAST,
        patterns=("docs/**",),
    ),
    Gate(
        name="check_skills_references",
        command=(("uv", "run", "python", "tools/check_skills_references.py"),),
        source=SOURCE_ROUTING,
        mode=MODE_FAST,
        patterns=("skills/**", "rules/**", "prompts/**", "templates/**"),
    ),
    Gate(
        name="check_skills_heading_cycles",
        command=(("uv", "run", "python", "tools/check_skills_heading_cycles.py"),),
        source=SOURCE_ROUTING,
        mode=MODE_FAST,
        patterns=("AGENTS.md", "routing.md", "skills/**", "rules/**", "prompts/**"),
    ),
    Gate(
        name="check_workitem_structure",
        command=(
            (
                "uv",
                "run",
                "python",
                "tools/check_workitem_structure.py",
                "--file",
                "<path>",
            ),
        ),
        source=SOURCE_ROUTING,
        mode=MODE_FAST,
        patterns=("plans/**", "issues/**", "implementations/**"),
    ),
    Gate(
        name="manage_workitem_stage_detect_stale",
        command=(
            (
                "uv",
                "run",
                "python",
                "tools/manage_workitem_stage.py",
                "detect-stale",
                "--days",
                "<N>",
            ),
        ),
        source=SOURCE_ROUTING,
        mode=MODE_FAST,
        patterns=("plans/**", "implementations/**"),
    ),
    Gate(
        name="manage_workitem_stage_list",
        command=(
            (
                "uv",
                "run",
                "python",
                "tools/manage_workitem_stage.py",
                "list",
                "--kind",
                "<kind>",
                "--status",
                "<status>",
            ),
        ),
        source=SOURCE_ROUTING,
        mode=MODE_FAST,
        patterns=("plans/**", "implementations/**"),
    ),
    Gate(
        name="check_canonical_source_registry",
        command=(
            (
                "uv",
                "run",
                "python",
                "tools/check_canonical_source_registry.py",
            ),
        ),
        source=SOURCE_ROUTING,
        mode=MODE_FAST,
        patterns=("config/documentation_canonical_sources.toml",),
    ),
    Gate(
        name="check_compat_shims",
        command=(("uv", "run", "python", "tools/check_compat_shims.py"),),
        source=SOURCE_ROUTING,
        mode=MODE_FAST,
    ),
    Gate(
        name="check_mock_patch_targets",
        command=(("uv", "run", "python", "tools/check_mock_patch_targets.py"),),
        source=SOURCE_ROUTING,
        mode=MODE_FAST,
        patterns=("tests/**", "scripts/**"),
    ),
    Gate(
        name="check_suppression_justification",
        command=(("uv", "run", "python", "tools/check_suppression_justification.py"),),
        source=SOURCE_ROUTING,
        mode=MODE_FAST,
    ),
    Gate(
        name="generate_reference_table_check",
        command=(
            (
                "uv",
                "run",
                "python",
                "tools/generate_reference_table.py",
                "--check",
            ),
        ),
        source=SOURCE_ROUTING,
        mode=MODE_FAST,
        patterns=(
            "scripts/agent/**",
            "scripts/eventbus/**",
            "scripts/agent/memory/**",
            "scripts/mcp_servers/**",
            "scripts/db/config.py",
            "config/agent.toml",
        ),
    ),
    Gate(
        name="generate_reference_table_mcp",
        command=(
            (
                "uv",
                "run",
                "python",
                "tools/generate_reference_table.py",
                "--type",
                "mcp",
            ),
        ),
        source=SOURCE_ROUTING,
        mode=MODE_FAST,
    ),
    Gate(
        name="generate_reference_table_rag",
        command=(
            (
                "uv",
                "run",
                "python",
                "tools/generate_reference_table.py",
                "--type",
                "rag",
            ),
        ),
        source=SOURCE_ROUTING,
        mode=MODE_FAST,
    ),
    Gate(
        name="generate_reference_table_deployment",
        command=(
            (
                "uv",
                "run",
                "python",
                "tools/generate_reference_table.py",
                "--type",
                "deployment",
            ),
        ),
        source=SOURCE_ROUTING,
        mode=MODE_FAST,
    ),
    Gate(
        name="generate_mcp_inventory",
        command=(
            (
                "uv",
                "run",
                "python",
                "tools/generate_mcp_inventory.py",
                "--format",
                "json|csv",
            ),
        ),
        source=SOURCE_ROUTING,
        mode=MODE_FAST,
    ),
    Gate(
        name="fix_docstring_paths",
        command=(
            (
                "uv",
                "run",
                "python",
                "tools/fix_docstring_paths.py",
                "--dry-run",
            ),
        ),
        source=SOURCE_ROUTING,
        mode=MODE_FAST,
    ),
    Gate(
        name="check_docstrings",
        command=(("uv", "run", "python", "tools/check_docstrings.py"),),
        source=SOURCE_ROUTING,
        mode=MODE_FAST,
        patterns=("scripts/**",),
    ),
    Gate(
        name="manage_frontmatter",
        command=(
            (
                "uv",
                "run",
                "python",
                "tools/manage_frontmatter.py",
                "add-missing|dedupe-lists",
            ),
        ),
        source=SOURCE_ROUTING,
        mode=MODE_FAST,
        patterns=("docs/**",),
    ),
    Gate(
        name="check_metadata_field_policy",
        command=(("uv", "run", "python", "tools/check_metadata_field_policy.py"),),
        source=SOURCE_ROUTING,
        mode=MODE_FAST,
        patterns=("docs/**", "plans/**", "issues/**", "implementations/**"),
    ),
    Gate(
        name="check_adr_preservation",
        command=(("uv", "run", "python", "tools/check_adr_preservation.py"),),
        source=SOURCE_ROUTING,
        mode=MODE_FAST,
        patterns=("docs/10_adr/*.md", "docs/10_adr/**/*.md"),
    ),
    Gate(
        name="check_docs_japanese",
        command=(("uv", "run", "python", "tools/check_docs_japanese.py"),),
        source=SOURCE_ROUTING,
        mode=MODE_FAST,
        patterns=("docs/**",),
    ),
)

_ALL_GATES: tuple[Gate, ...] = (*ROUTING_GATES, *TOOLCHAIN_GATES)


if __name__ == "__main__":
    sys.exit(main())
