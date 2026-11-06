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
  table has a mapping entry, and that every tool-backed ``.pre-commit-config.yaml`` hook has
  either a mapping entry or a reviewed ``COMMIT_ONLY_HOOKS`` allowlist entry. Exits non-zero
  on either drift (or an unreadable or malformed config), so ``routing.md`` and the hooks
  cannot advance ahead of this tool silently (REQ-006, hook parity).

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

import yaml

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools._tool_common import REPO_ROOT, run_git
from tools._validation_gate_defs import (
    _TOOL_PY_RE,
    MODE_FAST,
    MODE_FULL,
    ROUTING_GATES,
    SOURCE_ROUTING,
    SOURCE_TOOLCHAIN,  # noqa: F401 — re-exported for tests/tools/test_run_validation_gates.py
    TOOLCHAIN_GATES,
    Gate,
    _checker_id_from_command,
)

if TYPE_CHECKING:
    from subprocess import CompletedProcess

# Canonical Pass/Fail/Partial/Not available/Blocked vocabulary (rules/ai-execution.md item 11).
VOCAB = ("Pass", "Fail", "Partial", "Not available", "Blocked")


_ROUTING_HEADING = "### When to run which tool"
# The hook config the drift check compares against the gate mapping.
_PRECOMMIT_CONFIG = ".pre-commit-config.yaml"
# A `python -m tools.<name>` module token; rewritten to `tools/<name>.py` for id derivation.
_TOOL_MODULE_RE = re.compile(r"^tools\.([A-Za-z0-9_]+)$")

# Tool-backed pre-commit hooks that intentionally have no gate mapping: (hook id, reason).
# Reviewed text, not a silent default: the drift check rejects a blank reason and an entry
# whose hook id is absent from the config, so this list cannot go stale unnoticed.
COMMIT_ONLY_HOOKS: tuple[tuple[str, str], ...] = (
    (
        "check-compat-shims",
        "the hook runs --check-removed-names --check-doc-symbols, while the manual "
        "check_compat_shims gate runs the checker with defaults and has no path patterns",
    ),
)
# The orchestrator has its own row in that table, but it cannot be a gate of itself, so
# the drift check ignores that row.
_SELF_CHECKER_ID = Path(__file__).stem
# A git ref we will hand to `git diff`: alphanumerics plus . _ / -. Anything else is
# rejected before it reaches the subprocess so it cannot be read as a git option.
_REF_RE = re.compile(r"^[A-Za-z0-9._/-]+$")


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
    proc = run_git("diff", "--name-only", *extra_args)
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
            if gate.mode == MODE_FULL and mode != MODE_FULL:
                continue  # slow gate: full mode only (reason recorded on the gate)
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


def _hook_checker_id(entry: str) -> tuple[str | None, str | None]:
    """Derive ``(checker_id, error)`` from a pre-commit hook ``entry`` string.

    ``python -m tools.<name>`` tokens are rewritten to ``tools/<name>.py`` so the id uses the
    same rule as ``Gate.checker_id``. Returns ``(None, None)`` when the entry is not
    tool-backed (``bash -c ...``, ``uv run mypy ...``) and ``(None, message)`` when a token
    looks like a tool reference but matches neither form.
    """
    tokens: list[str] = []
    for tok in entry.split():
        module = _TOOL_MODULE_RE.match(tok)
        tokens.append(f"tools/{module.group(1)}.py" if module else tok)
    if not any(_TOOL_PY_RE.search(tok) for tok in tokens):
        if any(tok.startswith(("tools.", "tools/")) for tok in tokens):
            return None, f"unparseable tool-backed hook entry: {entry!r}"
        return None, None
    return _checker_id_from_command(tuple(tokens)), None


def parse_precommit_hooks(config_text: str) -> tuple[dict[str, str], list[str]]:
    """Parse a pre-commit config into ``({hook id: checker id}, errors)``.

    Only tool-backed hooks are returned. Hooks without an ``entry`` (remote repos such as
    ruff) and non-tool entries are skipped, as are hooks whose base tool is this
    orchestrator (the drift hook cannot be a gate of itself).
    """
    try:
        data = yaml.safe_load(config_text)
    except yaml.YAMLError as exc:
        return {}, [f"{_PRECOMMIT_CONFIG} is not valid YAML: {exc}"]
    if not isinstance(data, dict) or not isinstance(data.get("repos"), list):
        return {}, [f"{_PRECOMMIT_CONFIG} has no 'repos' list"]
    hooks: dict[str, str] = {}
    errors: list[str] = []
    for repo in data["repos"]:
        repo_hooks = repo.get("hooks") if isinstance(repo, dict) else None
        if not isinstance(repo_hooks, list):
            errors.append(f"{_PRECOMMIT_CONFIG}: a repo entry has no 'hooks' list")
            continue
        for hook in repo_hooks:
            hook_id = hook.get("id") if isinstance(hook, dict) else None
            if not isinstance(hook_id, str):
                errors.append(f"{_PRECOMMIT_CONFIG}: a hook has no string 'id'")
                continue
            entry = hook.get("entry")
            if not isinstance(entry, str):
                continue
            checker_id, error = _hook_checker_id(entry)
            if error is not None:
                errors.append(f"hook {hook_id}: {error}")
            elif checker_id is not None and (
                checker_id.split(":", 1)[0] != _SELF_CHECKER_ID
            ):
                hooks[hook_id] = checker_id
    return hooks, errors


def drift_report(
    routing_text: str, precommit_text: str | None = None
) -> tuple[int, list[str]]:
    """Compare routing.md's checkers, and optionally the hooks, against this tool's mapping.

    Returns ``(error_count, messages)``. Every routing.md checker must have a mapping entry
    and every mapping entry must come from routing.md; either drift is an error. The row
    that names this orchestrator itself is not a checker and is excluded. When
    ``precommit_text`` is given, every tool-backed hook must also have a mapping entry or a
    ``COMMIT_ONLY_HOOKS`` entry, and each allowlist entry needs a reason and a live hook.
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
    if precommit_text is not None:
        hooks, hook_errors = parse_precommit_hooks(precommit_text)
        errors += hook_errors
        allowed = {hook_id for hook_id, _ in COMMIT_ONLY_HOOKS}
        errors += [
            f"pre-commit hook has no gate mapping or allowlist entry: "
            f"{hook_id} ({checker_id})"
            for hook_id, checker_id in sorted(hooks.items())
            if checker_id not in actual and hook_id not in allowed
        ]
        errors += [
            f"COMMIT_ONLY_HOOKS entry has no reason: {hook_id}"
            for hook_id, reason in COMMIT_ONLY_HOOKS
            if not reason.strip()
        ]
        if not hook_errors:
            errors += [
                f"COMMIT_ONLY_HOOKS entry names no tool-backed hook in "
                f"{_PRECOMMIT_CONFIG}: {hook_id}"
                for hook_id in sorted(allowed - set(hooks))
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
    texts: dict[str, str] = {}
    for name in ("routing.md", _PRECOMMIT_CONFIG):
        try:
            texts[name] = (REPO_ROOT / name).read_text(encoding="utf-8")
        except OSError as exc:
            print(f"ERROR: cannot read {name}: {exc}", file=sys.stderr)
            return 1
    count, errors = drift_report(texts["routing.md"], texts[_PRECOMMIT_CONFIG])
    if count:
        for message in errors:
            print(message, file=sys.stderr)
        return 1
    print(
        f"OK: {len(ROUTING_GATES)} routing.md checker(s) all mapped; "
        f"pre-commit hooks in parity"
    )
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
        help=(
            "Verify every routing.md 'When to run which tool' checker and every "
            "tool-backed pre-commit hook has a mapping entry (or an allowlist entry)"
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.action == "drift":
        return _run_drift()
    return _run_gates(args.base, "full" if args.full else MODE_FAST)


_ALL_GATES: tuple[Gate, ...] = (*ROUTING_GATES, *TOOLCHAIN_GATES)


if __name__ == "__main__":
    sys.exit(main())
