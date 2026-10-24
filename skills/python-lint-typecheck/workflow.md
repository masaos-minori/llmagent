# Lint Typecheck — Detailed Workflow

## Toolchain

| Tool | Goal | Role |
|---|---|---|
| `ruff` | repository convention enforcement | Format and lint; auto-fix safe violations |
| `ast-grep` | convention enforcement, architecture integrity | Structural search and pattern enforcement |
| `mypy` | type flow analysis | Primary static type checker |
| `pyright` | type flow analysis | Alternate type checker; cross-validates mypy |
| `pyre` | type flow analysis | Strict inference on protocols/TypedDict |
| `bandit` | static security validation | Vulnerability scan |
| `diff-cover` | diff scope enforcement | Coverage gate scoped to changed lines |
| `tox` | CI consistency validation | Runs full check suite in isolated envs |
| `libcst` | semantic refactor safety | CST-based transforms preserving comments |
| `pre-commit` | CI consistency validation | Aggregated hook runner; final gate |

Run every Python tool through `uv run` (`uv run mypy`, `uv run pyright`, `uv run ruff`, ...); the
commands below carry the prefix. Check availability the same way, e.g.
`uv run pyright --version`; `command -v` is wrong for `pyright`, `pyre`, and `tox`, which are not
on PATH here but run under `uv run`. If a tool fails to start under `uv run`, apply `skills/DESIGN.md`
Tool availability guard and record the check as `Needs confirmation`.

## Step failure handling

Apply `rules/ai-execution.md` Step-Level Failure Triage (Base) to every Step below. On a
task-caused failure, stop and report `Blocked: {step} — {error}` once Attempt Limit (3
attempts) is reached. Apply `rules/ai-execution.md` Tool Usage's idempotent-command
rule: MUST NOT re-run a Step's validation command against a file whose content has not
changed since that command last ran in this cycle.

---

## Step 1: Identify Failure Source

**Fast path** — see `SKILL.md` Routing (Fast Path Assessment) for the failure-type → step mapping.

**Full diagnosis** — if the cause is unknown, run all tools first, in their check-only forms
(the CI `lint` job's commands in the table below; they do not modify files): `rules/toolchain.md`
sections 1 (ruff), 2 (mypy), 3 (lint-imports), and 5 (bandit), each scoped to `scripts/`. Do not
use the section 1 forms `uv run ruff format scripts/` or `ruff check --fix` for diagnosis: they
rewrite files before you know what failed. Before the first edit, record `git status --short`;
changes already in the working tree are not this task's (Step 10).
When the failure is in `tools/` or `tests/`, scope the commands to those paths explicitly:
`mypy`'s configured `files` covers only `scripts/` and CI's `ruff`/`bandit` steps also run on
`scripts/` only, so a bare run says nothing about `tools/` (use `routing.md` "Adding a new tool"
for a `tools/` file) or `tests/`; pre-commit hooks do cover those files.

**Map a failing CI step to a Step** (the `lint` job in `.github/workflows/ci.yml` is the
source of truth; re-read it if this table looks stale):

| Failing CI step | Command | Go to |
|---|---|---|
| Format check | `uv run ruff format --check scripts/` | Step 2 |
| Lint check | `uv run ruff check scripts/` | Step 2 |
| Type check | `uv run mypy --no-namespace-packages scripts/` | Step 6 |
| Security scan | `uv run bandit -r scripts/ -c pyproject.toml -ll` | Step 7 |
| Architecture check | `PYTHONPATH=scripts uv run lint-imports` | Step 3 |
| SQLite 4DB separation check, reference-docs drift, docstring format, module size | `tools/check_db_separation.py`, `tools/generate_reference_table.py --check`, `tools/check_docstrings.py`, `tools/check_module_size.py` | Step 9 (CI-only gates) |
| Pre-commit | `uv run pre-commit run --all-files` (the failing hook's id names the check) | Step 9 |
| Cited ADR invariant tests | `uv run python .github/run_cited_adr_tests.py` | `python-test-and-fix` |

Per `rules/ai-execution.md` Repository Tool Usage #8: a clean (0-finding) result from any
of the above is evidence only after confirming `scripts/` exists and is non-empty — not
proof by itself, since a mistyped path or an empty target produces the same output.

Classify the failure type: lint / type error / import boundary / security finding / suppression violation.
MUST NOT fix any issue until you know which tool found it and why.

---

## Step 2: Repository Convention Enforcement

#### ruff — format and lint

See `rules/toolchain.md` section 1 for the standard format/lint sequence. To narrow to one file,
pass the path and keep the project configuration (`pyproject.toml` selects `E, W, F, I, UP, BLE001`;
MUST NOT override it with `--select`, which would drop `BLE001` and miss broad `except` handlers):

```bash
uv run ruff check scripts/<file>.py
uv run ruff format --check scripts/<file>.py
```

After auto-fix, review the diff. For each changed hunk, confirm the fixed line evaluates
to the same result as the original for every input the surrounding code handles — accept
it only then. A hunk touching a lambda, a chained comprehension, or an expression with
more than one boolean operator needs this check most; a simple import-sort or
whitespace-only hunk needs no such re-derivation. If a hunk fails this check, revert only
that hunk (`git diff` shows it in isolation) and fix the line by hand — MUST NOT accept a
semantically-changed auto-fix and MUST NOT re-run `ruff check --fix` on the same input. Revert
the hunk by editing those lines back to the original text (interactive `git checkout -p` is not
available here, and `git stash`/reset would touch other sessions' edits); then confirm with
`git diff <path>`.

#### ast-grep — structural pattern enforcement

See `rules/coding.md` Constraint checks for the bare-except / print() / json.load checks.
Additional pattern specific to this skill:

```bash
# module-level mutable globals only: ast-grep's '$VAR = []' also matches local variables,
# so anchor on column 0 with ripgrep instead
rg -n '^[A-Za-z_][A-Za-z0-9_]* *(: [^=]+)?= *(\[\]|\{\}|set\(\))\s*$' scripts/
```

Treat a match as a Finding to inspect, not an automatic defect (constants and registries are legitimate).

---

## Step 3: Architecture Integrity

See `rules/toolchain.md` section 3 for the `lint-imports` command.

If `lint-imports` reports a violation:

1. Read the failing contract in `.importlinter`
2. Determine if the import is intentional or accidental
3. If accidental: remove the import and refactor
4. If intentional: update the contract definition in `.importlinter` (see
   `rules/coding.md` Prohibited behavior) — this is the only way to resolve a
   `lint-imports` violation without removing the import; a suppression comment does
   not apply to this checker.

Cross-reference with ast-grep to find all call sites before removing an import:

```bash
rg "from agent.repl import" scripts/
ast-grep --pattern 'import $MOD' --lang python scripts/agent/commands/registry.py
```

Then check for backward-compatibility leftovers in source and docs:

```bash
uv run python tools/check_compat_shims.py
```

**Completed when**: `lint-imports` reports no violation, either because no accidental
import remained or because every intentional import is now covered by an explicit
`.importlinter` contract update, and `check_compat_shims.py` reports no new finding.

---

## Step 4: Suppression Governance

Audit the suppressions this task adds or touches (the lines in your `git diff`) using the commands
and required format defined in `rules/coding.md` Suppression governance. Unjustified suppressions
elsewhere in the repository are out of scope (`AGENTS.md` Global Rule 5): list them in the final
report, do not fix them. Fix the root cause rather than suppress, unless
doing so would require a breaking public-API change or touch a file outside the current
task's scope (`AGENTS.md` Global Rule 5) — in either of those two cases, suppress with the
Mandatory Audit Log Template instead.

After adding a new suppression comment, run `tools/check_suppression_justification.py`
(see `rules/coding.md` Suppression governance) against the changed file to confirm the
justification format itself is accepted — MUST NOT assume the format is correct because it
matches the template by eye.

---

## Step 5: Semantic Refactor Safety

If a rename or structural change must preserve comments and docstrings, use the LibCST
transform recipe and post-transform verification commands in
`skills/python-refactoring/workflow.md` Step 6 (Transformation).

---

## Step 6: Type Flow Analysis

#### mypy — primary

```bash
uv run mypy --no-namespace-packages scripts/
uv run mypy --no-namespace-packages scripts/<file>.py
uv run mypy --no-namespace-packages scripts/ --show-error-codes   # always include error codes
```

`mypy --strict` is not the CI configuration. Use it only to inspect a file's wider type hygiene;
errors that appear only under `--strict` are recorded as Findings and not fixed in this task
(`SKILL.md` CI Parity rule). If `mypy`'s configuration looks stale (for example the `exclude` entry
`scripts/agent\.py` names a file that does not exist), record it as a Finding; do not edit the
configuration unless the failure being fixed requires it.

Always pass `--no-namespace-packages` (the CI and pre-commit invocation; see `rules/toolchain.md`
section 2). Without it, mypy can abort with `Source file found twice` and judges
`# type: ignore` differently, so its result does not predict CI.

A 0-error result is evidence of a clean type-check only after confirming the target file
exists and mypy visited it (e.g. its path appears in a `--verbose` run, or the file is
confirmed non-empty) — per `rules/ai-execution.md` Repository Tool Usage #8.

For each mypy error:

1. Trace the type to its origin — MUST NOT add `# type: ignore` at the call site
2. Add the correct annotation at the definition site
3. Propagate the type through all affected functions

Common patterns:

```python
# incorrect — annotation on parameter with default
def f(x: int = None) -> None: ...         # error: not None-compatible

# correct
def f(x: int | None = None) -> None: ...
```

```python
# incorrect — missing return type
def parse(line):
    return line.strip()

# correct
def parse(line: str) -> str:
    return line.strip()
```

#### pyright — cross-validation

Check availability first (per `skills/DESIGN.md` Tool availability guard):

```bash
uv run pyright --version || echo "pyright unavailable — skip this sub-step, mypy's result stands alone"
```

(`command -v pyright` would wrongly report it missing: it runs only under `uv run`.) If available:

```bash
uv run pyright scripts/
uv run pyright scripts/<file>.py
```

CI runs mypy, not pyright, so pyright is a cross-check on the files this task changed (`uv run
pyright <changed file>`), not a repository gate. If mypy and pyright disagree on a line this task
changed: resolve to the stricter interpretation and annotate why. A pyright finding elsewhere
(or one on an unchanged line) is recorded as a Finding, not fixed (`SKILL.md` CI Parity rule).

#### pyre — strict protocol and TypedDict inference (optional)

`pyre-check` is a declared dependency, but the repository has no `.pyre_configuration`, so
`pyre check` does not run out of the box and CI does not use it. MUST NOT run or configure pyre
unless the user asks for it; if asked, creating the configuration is a separate, explicit change.
Typical need: a module that defines `Protocol` subclasses or `TypedDict`
(`rg "Protocol|TypedDict" scripts/<file>.py`).

For standard application code: mypy + pyright are sufficient.

If a type fix changed a function signature or an import, or added an annotation import
(e.g. `from typing import ...`), re-run Step 2's `ruff check` on the changed file before
Step 7 — a type-driven edit can introduce an unused import or formatting violation.

---

## Step 7: Static Security Validation

See `rules/toolchain.md` section 5 for bandit commands.

Priority findings — MUST resolve before merge: see `rules/coding.md` Bandit priority findings.
CI gates on medium severity and above (`-ll`); a low-severity finding does not fail CI, so it is
not fixed in this task unless the task is that finding: list it in the final report instead.

**Completed when**: `bandit` has been run and every priority finding (per
`rules/coding.md` Bandit priority findings) is resolved or suppressed with the
required justification (per `rules/coding.md` Suppression governance).

---

## Step 8: Diff Scope Enforcement

The point of this step is that the diff contains only the target fixes:

```bash
git diff <path>      # every hunk traces to a reported lint/type/security finding
```

A hunk with no corresponding finding is reverted by hand (no stash/reset).

Diff-scoped coverage (`rules/toolchain.md` §7) applies only when a fix changed runtime behavior
(for example a type fix that altered a branch or a conversion). A formatting, import, annotation,
or suppression change has no new behavior to cover: record `diff-cover: not applicable` and do not
add tests. When it applies, generate the report first, then check:

```bash
uv run coverage run -m pytest tests/ -m "not integration and not production_paths_allowed"
uv run coverage xml
uv run diff-cover coverage.xml --compare-branch=master --fail-under=90
```

(Threshold per `rules/toolchain.md` §7; run the tests only after the production-isolation check in
`python-test-and-fix` Core rules. CI measures without the marker filter, so a pass here also passes in CI, while a miss here may pass in CI; report it as measured with the filter.) If changed lines are uncovered: identify them, add targeted
tests for those lines via `python-test-and-fix`, re-run `diff-cover`. MUST NOT add tests for
unrelated lines to inflate coverage.

**Completed when**: every hunk of the diff traces to a finding, and either `diff-cover` reports
the changed-lines coverage at or above the threshold using only tests scoped to the actual
change, or the step is recorded as not applicable (no behavior change).

---

## Step 9: CI Consistency Validation

Run the CI `lint` job's check-only commands (Step 1's table), then the pre-commit gate on the
files you changed: `uv run pre-commit run --files <changed files>`. Do not run
`pre-commit run --all-files` (the form in `rules/toolchain.md` section 8 and in CI): it rewrites
files across the repository and stashes other sessions' unstaged changes, which breaks Strict
Diff Isolation. The full `--all-files` run is CI's job.

**CI-only gates** (the CI `lint` job runs these beyond ruff/mypy/bandit/lint-imports; run the one
that failed, or all when unsure):

| Gate | Command | Typical fix |
|---|---|---|
| SQLite 4DB separation | `uv run python tools/check_db_separation.py` | remove the cross-DB access, `ATTACH`, or schema-qualified name it names |
| Generated reference docs drift | `uv run python tools/generate_reference_table.py --check` | run the generator with the `--type` it names and include the regenerated block |
| Module docstring format | `uv run python tools/check_docstrings.py` | fix the docstring header it names (read-only checker) |
| Module size | `uv run python tools/check_module_size.py` | split the module (never raise the baseline to pass) |
| Pre-commit | `uv run pre-commit run --files <changed files>` (CI uses `--all-files`) | fix what the failing hook id reports; do not use `--no-verify` |

An unrelated failure (output names none of your changed files, and the gate did not pass earlier in
this run) is recorded in the final report, not fixed here.

`tox.ini` defines the envs `lint`, `typecheck`, and `tests` (one Python version, with
`skip_missing_interpreters`); it is an alternative runner, not a multi-version matrix:

```bash
uv run tox -e lint && uv run tox -e typecheck && uv run tox -e tests
```

An exit-0 result is proof of a passing environment only after confirming each `tox -e
<env>` ran its configured commands (check the printed summary line for the environment
name and a non-zero test/check count) — per `rules/ai-execution.md`
Repository Tool Usage #8.

---

## Step 10: Minimal Change Principle

Enforces `SKILL.md` Strict Diff Isolation. In addition:

- MUST NOT rename symbols while fixing a type error — a rename is a separate change set

Review your own diff:

```bash
git diff scripts/<file>.py
rg "noqa|type: ignore|nosec" scripts/<file>.py     # plain `|`: ripgrep treats `\|` as a literal pipe
```

If the diff contains changes that are not part of the fix: edit those lines back by hand. MUST NOT
`git stash` or reset in the working tree — other sessions' unstaged edits live there and would be
swept in. This skill never stages or commits; when the user asks, use `git-commit-and-sync`
(it stages explicit paths and one logical change per commit).

---

## Step 11: Repository Knowledge Compression

After resolving issues, handle project knowledge files if anything changed:

- **`.importlinter`**: an updated contract is part of the fix when boundary rules change (Step 3); keep it in the change set
- **`pyproject.toml`**: a new `[tool.ruff.lint.per-file-ignores]` entry needs a justification comment next to it; add it only when the failure being fixed requires it
- **`.pre-commit-config.yaml`**: update hook versions only if the task is the upgrade
- **Documentation** (`CLAUDE.md`, `docs/`, `routing.md`, skills): do not edit unprompted (`AGENTS.md` Global Rule 5); describe the needed update in the final report. `CLAUDE.md` has no module table, so there is nothing of that kind to keep in sync

---

## Completion checklist

**This task is complete when, and only when**: `rules/toolchain.md` "Completion checklist
(common to all tasks)" is satisfied in full, the item below also holds, and no Step above
ended in an unresolved `Blocked` state.

- all suppressions have inline justification, and `uv run python tools/check_suppression_justification.py` accepts the changed files
- `pre-commit` ran on the changed files (Step 9), and the final response lists every finding recorded instead of fixed

---

## Prohibited behavior

See `SKILL.md` Strict Diff Isolation (Step 10 above enforces it) and `rules/coding.md` for
project-wide prohibitions (suppression governance, commit hygiene).
