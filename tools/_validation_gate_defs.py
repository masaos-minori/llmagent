"""tools/_validation_gate_defs.py

Gate definitions of tools/run_validation_gates.py: the `Gate` type, the argv helpers it
depends on, the source and mode constants, and the toolchain and routing gate tables.
Not a CLI; the entry module imports these names and re-exports them.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


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


# Which source each gate was transcribed from; also the drift check's filter.
SOURCE_TOOLCHAIN = "toolchain"
SOURCE_ROUTING = "routing"


# Full mode adds the toolchain sequence; fast mode runs only the routing selection.
MODE_FAST = "fast"
MODE_FULL = "full"


# rules/toolchain.md section 4 bare-except check. A bare `--pattern 'except: $$$'` is not a
# valid ast-grep pattern (it parses as several nodes), and a plain `--pattern` run exits 0 even
# on matches. Scanning with an error-severity rule exits non-zero on a hit.
_BARE_EXCEPT_RULE = (
    "id: no-bare-except\n"
    "language: python\n"
    "severity: error\n"
    "message: bare except is prohibited (rules/coding.md)\n"
    "rule:\n"
    "  pattern: |\n"
    "    try:\n"
    "        $$$A\n"
    "    except:\n"
    "        $$$B\n"
)


# Tokens that mark a command as needing a concrete runtime argument.
_PLACEHOLDER_TOKEN_RE = re.compile(r"[<\[\]]|\.\.\.")


# argv token that names a tools/<name>.py the gate runs. Unanchored so it matches both
# repo-relative paths (``tools/foo.py``) and absolute paths (``/x/tools/foo.py``); git diff
# emits the former, so the old ``.*``-prefixed form never matched and every id collapsed.
_TOOL_PY_RE = re.compile(r"tools/([A-Za-z0-9_]+)\.py")
# Flags whose following value disambiguates two checkers that share a tool basename.
_VALUE_FLAG_RE = re.compile(r"^--(type|format|domain|kind|status)$")


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
        command=(
            (
                "uv",
                "run",
                "mypy",
                "--no-namespace-packages",
                "scripts/",
                "tests/eventbus",
                "tools",
            ),
        ),
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
                "scan",
                "--inline-rules",
                _BARE_EXCEPT_RULE,
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
        name="check_module_size_tools",
        command=(
            (
                "uv",
                "run",
                "python",
                "tools/check_module_size.py",
                "--scripts-dir",
                "tools",
                "--baseline",
                "tools/check_module_size_tools_baseline.txt",
            ),
        ),
        source=SOURCE_ROUTING,
        mode=MODE_FAST,
        patterns=("tools/*.py", "tools/check_module_size_tools_baseline.txt"),
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
    # Commit-split classifier: `<path>` is a runtime placeholder, so it reports `Not available`.
    Gate(
        name="classify_changes",
        command=(
            (
                "uv",
                "run",
                "python",
                "tools/classify_changes.py",
                "[--status-file",
                "<path>]",
            ),
        ),
        source=SOURCE_ROUTING,
        mode=MODE_FAST,
        patterns=("tools/classify_changes.py", "skills/git-commit-and-sync/**"),
    ),
    # Manual planning-time tool: `<plan>` and `<path>` are runtime placeholders.
    Gate(
        name="amend_plan",
        command=(
            (
                "uv",
                "run",
                "python",
                "tools/amend_plan.py",
                "<plan>",
                "--file",
                "<path>",
            ),
        ),
        source=SOURCE_ROUTING,
        mode=MODE_FAST,
        patterns=(),
    ),
    # Planning-time candidate scan: manual, `<seed>` is a runtime placeholder.
    Gate(
        name="scan_change_consumers",
        command=(
            (
                "uv",
                "run",
                "python",
                "tools/scan_change_consumers.py",
                "--seed",
                "<seed>",
            ),
        ),
        source=SOURCE_ROUTING,
        mode=MODE_FAST,
        patterns=(),
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
        name="plan_dependency_order",
        command=(
            (
                "uv",
                "run",
                "python",
                "tools/plan_dependency_order.py",
                "--plan",
                "<path>",
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
                "add-missing",
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
    # Content-based, so no patterns: routing.md applies this check only to an ADR that was
    # shortened or reworded without intending to change its decisions. It reports every
    # added or removed test citation as an ERROR, so auto-selecting it for any ADR edit made
    # a deliberate citation correction fail. Run it by hand for a size-reduction change.
    Gate(
        name="check_adr_preservation",
        command=(("uv", "run", "python", "tools/check_adr_preservation.py"),),
        source=SOURCE_ROUTING,
        mode=MODE_FAST,
    ),
    Gate(
        name="check_docs_japanese",
        command=(("uv", "run", "python", "tools/check_docs_japanese.py"),),
        source=SOURCE_ROUTING,
        mode=MODE_FAST,
        patterns=("docs/**",),
    ),
    Gate(
        name="check_adr_authority",
        command=(("uv", "run", "python", "tools/check_adr_authority.py"),),
        source=SOURCE_ROUTING,
        mode=MODE_FAST,
        patterns=("docs/10_adr/**", "config/adr_authority.toml"),
    ),
    Gate(
        name="generate_adr_authority",
        command=(("uv", "run", "python", "tools/generate_adr_authority.py"),),
        source=SOURCE_ROUTING,
        mode=MODE_FAST,
        patterns=("docs/10_adr/**", "config/adr_authority.toml"),
    ),
    # Hook-parity gates (flowimp005): each mirrors the same-named pre-commit hook's filter
    # (`types_or: [python, markdown]` becomes the .py and .md globs; `**/` needs a directory,
    # so root-level forms are listed explicitly, as check_module_size does).
    Gate(
        name="check_adr_invariant_matrix",
        command=(("uv", "run", "python", "tools/check_adr_invariant_matrix.py"),),
        source=SOURCE_ROUTING,
        mode=MODE_FAST,
        patterns=("*.py", "**/*.py", "*.md", "**/*.md"),
    ),
    Gate(
        name="check_adr_reference",
        command=(("uv", "run", "python", "tools/check_adr_reference.py"),),
        source=SOURCE_ROUTING,
        mode=MODE_FAST,
        patterns=("*.py", "**/*.py", "*.md", "**/*.md"),
    ),
    Gate(
        name="check_adr_structure",
        command=(("uv", "run", "python", "tools/check_adr_structure.py"),),
        source=SOURCE_ROUTING,
        mode=MODE_FAST,
        patterns=("*.py", "**/*.py", "*.md", "**/*.md"),
    ),
    Gate(
        name="check_known_deviation_sync",
        command=(("uv", "run", "python", "tools/check_known_deviation_sync.py"),),
        source=SOURCE_ROUTING,
        mode=MODE_FAST,
        patterns=("docs/*.md", "docs/**/*.md"),
    ),
    Gate(
        name="check_plan_target_overlaps",
        command=(("uv", "run", "python", "tools/check_plan_target_overlaps.py"),),
        source=SOURCE_ROUTING,
        mode=MODE_FAST,
        patterns=("plans/*.md",),
    ),
    Gate(
        name="check_conftest_integrity",
        command=(("uv", "run", "python", "tools/check_conftest_integrity.py"),),
        source=SOURCE_ROUTING,
        mode=MODE_FAST,
        patterns=("tests/*conftest*", "tests/**/*conftest*"),
    ),
    # Full mode only: measured about 6.5 seconds with the hook's --active-only flag (2026-11-02,
    # two runs), against 0.1 to 1.0 seconds for every other gate above (REQ-004). It is
    # report-only (exit 0 with findings), so skipping it in fast mode loses no hard failure.
    Gate(
        name="check_workitem_traceability",
        command=(
            (
                "uv",
                "run",
                "python",
                "tools/check_workitem_traceability.py",
                "--active-only",
            ),
        ),
        source=SOURCE_ROUTING,
        mode=MODE_FULL,
        patterns=(
            "issues/*.md",
            "issues/**/*.md",
            "plans/*.md",
            "plans/**/*.md",
            "implementations/*.md",
            "implementations/**/*.md",
        ),
    ),
)
