"""tools/_validation_gate_toolchain.py

Toolchain gate table and the bare-except rule of tools/run_validation_gates.py,
transcribed from rules/toolchain.md. Moved out of tools/_validation_gate_defs.py
so that module keeps room for the routing mappings. Not a CLI; the entry module
imports these names.
"""

from __future__ import annotations

from tools._validation_gate_defs import MODE_FULL, SOURCE_TOOLCHAIN, Gate

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

# --- Embedded gate inventory -----------------------------------------------------
# Transcribed from rules/toolchain.md (9-step sequence, full mode). Keep the commands
# equal to that source.

TOOLCHAIN_GATES: tuple[Gate, ...] = (
    Gate(
        name="ruff-format-lint",
        command=(
            ("uv", "run", "ruff", "format", "scripts/"),
            ("uv", "run", "ruff", "check", "scripts/"),
        ),
        source=SOURCE_TOOLCHAIN,
        mode=MODE_FULL,
        exclusive=True,
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
            (
                "uv",
                "run",
                "pytest",
                "tests/",
                "-n",
                "logical",
                "--cov=scripts",
                "--cov-report=",
                "-m",
                "not integration and not production_paths_allowed and not repo_scan",
            ),
            (
                "uv",
                "run",
                "pytest",
                "tests/mcp_servers/mdq/test_mdq_rag_boundary.py",
            ),
        ),
        source=SOURCE_TOOLCHAIN,
        mode=MODE_FULL,
        exclusive=True,
    ),
    Gate(
        name="diff-cover",
        command=(
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
        exclusive=True,
    ),
    Gate(
        name="pre-commit",
        command=(("uv", "run", "pre-commit", "run", "--all-files"),),
        source=SOURCE_TOOLCHAIN,
        mode=MODE_FULL,
        exclusive=True,
    ),
    Gate(
        name="reference-drift",
        command=(
            ("uv", "run", "python", "tools/generate_reference_table.py", "--check"),
        ),
        source=SOURCE_TOOLCHAIN,
        mode=MODE_FULL,
    ),
    Gate(
        name="cited-adr-tests",
        command=(("uv", "run", "python", ".github/run_cited_adr_tests.py"),),
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
