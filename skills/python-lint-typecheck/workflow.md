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
| `pre-commit` | — | Aggregated hook runner; final gate |

## Step failure handling

Apply `rules/ai-execution.md` Step-Level Failure Triage (Base) to every Step below. On a
task-caused failure, stop and report `Blocked: {step} — {error}` once Attempt Limit (3
attempts) is reached. Apply `rules/ai-execution.md` Tool Usage's idempotent-command
rule: do not re-run a Step's validation command against a file whose content has not
changed since that command last ran in this cycle.

---

## Step 1: Identify Failure Source

**Fast path** — see `SKILL.md` Routing (Fast Path Assessment) for the failure-type → step mapping.

**Full diagnosis** — if the cause is unknown, run all tools first:

```bash
ruff check scripts/
mypy scripts/
lint-imports
bandit -r scripts/ -c pyproject.toml
```

Per `rules/ai-execution.md` Repository Tool Usage #8: a clean (0-finding) result from any
of the above is evidence only after confirming `scripts/` exists and is non-empty — not
proof by itself, since a mistyped path or an empty target produces the same output.

Classify the failure type: lint / type error / import boundary / security finding / suppression violation.
Do not fix any issue until you know which tool found it and why.

---

## Step 2: Repository Convention Enforcement

#### ruff — format and lint

See `rules/toolchain.md` section 1 for the standard format/lint sequence. To narrow to one file:

```bash
ruff check scripts/<file>.py --select E,W,F,I,UP
```

After auto-fix, review the diff. For each changed hunk, confirm the fixed line evaluates
to the same result as the original for every input the surrounding code handles — accept
it only then. A hunk touching a lambda, a chained comprehension, or an expression with
more than one boolean operator needs this check most; a simple import-sort or
whitespace-only hunk needs no such re-derivation. If a hunk fails this check, revert only
that hunk (`git diff` shows it in isolation) and fix the line by hand instead — do not
accept a semantically-changed auto-fix and do not re-run `ruff check --fix` hoping for a
different result on the same input.

#### ast-grep — structural pattern enforcement

See `rules/coding.md` Constraint checks for the bare-except / print() / json.load checks.
Additional pattern specific to this skill:

```bash
# no top-level assignment patterns that indicate global state
ast-grep --pattern '$VAR = []' --lang python scripts/
```

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

---

## Step 4: Suppression Governance

Audit all existing suppressions using the commands and required format defined in
`rules/coding.md` Suppression governance. Fix the root cause rather than suppress, unless
doing so would require a breaking public-API change or touch a file outside the current
task's scope (`AGENTS.md` Global Rule 5) — in either of those two cases, suppress with the
Mandatory Audit Log Template instead.

After adding a new suppression comment, run `tools/check_suppression_justification.py`
(see `rules/coding.md` Suppression governance) against the changed file to confirm the
justification format itself is accepted — do not assume the format is correct because it
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
mypy scripts/
mypy scripts/<file>.py --strict
mypy scripts/ --show-error-codes   # always include error codes
```

A 0-error result is evidence of a clean type-check only after confirming the target file
exists and mypy actually visited it (e.g. its path appears in a run with `--verbose`, or
the file is confirmed non-empty) — per `rules/ai-execution.md` Repository Tool Usage #8.

For each mypy error:

1. Trace the type to its origin — do not add `# type: ignore` at the call site
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
command -v pyright || echo "pyright not installed — skip this sub-step, mypy's result stands alone"
```

If available:

```bash
pyright scripts/
pyright scripts/<file>.py
```

If mypy and pyright disagree: resolve to the stricter interpretation and annotate why.

#### pyre — strict protocol and TypedDict inference (optional)

Use pyre only when the module defines `Protocol` subclasses or `TypedDict`.

```bash
# Check if pyre is needed:
rg "Protocol|TypedDict" scripts/<file>.py
# If no results: skip pyre

pyre check         # one-shot
pyre               # incremental server
pyre stop
```

For standard application code: mypy + pyright are sufficient. Do not run pyre by default.

If a type fix here changed a function signature, an import, or introduced a new
annotation import (e.g. `from typing import ...`), re-run Step 2's `ruff check` on the
changed file before proceeding to Step 7 — a type-driven edit can introduce an unused
import or formatting violation Step 2 would otherwise miss.

---

## Step 7: Static Security Validation

See `rules/toolchain.md` section 5 for bandit commands.

Priority findings — must resolve before merge: see `rules/coding.md` Bandit priority findings.

---

## Step 8: Diff Scope Enforcement

Per `rules/toolchain.md` §7 (Diff-scoped coverage).

If coverage on changed lines is below the threshold defined there:

1. Identify which changed lines are uncovered
2. Add targeted tests for those lines
3. Re-run `diff-cover` to confirm

Do not add tests for unrelated lines to inflate coverage — scope tests to the change.

---

## Step 9: CI Consistency Validation

Run the standard validation sequence (`rules/toolchain.md`) in full, ending with the pre-commit
gate (`rules/toolchain.md` section 8) to match CI behavior.

If using tox (requires tox.ini to be configured — not in the default dev workflow):

```bash
tox -e lint && tox -e typecheck && tox -e tests
```

An exit-0 result is proof of a passing environment only after confirming each `tox -e
<env>` actually ran its configured commands (check the printed summary line for the
environment name and a non-zero test/check count) — per `rules/ai-execution.md`
Repository Tool Usage #8.

---

## Step 10: Minimal Change Principle

Enforces `SKILL.md` Strict Diff Isolation. In addition:

- do not rename symbols while fixing a type error — do them in separate commits

Review the diff before staging:

```bash
git diff scripts/<file>.py
rg "noqa\|type: ignore\|nosec" scripts/<file>.py
```

If the diff contains unrelated changes: stash them or reset those lines before committing.

---

## Step 11: Repository Knowledge Compression

After resolving issues, update project knowledge files if anything changed:

- **`CLAUDE.md` module table**: update if a module's role changed
- **`.importlinter`**: commit updated contracts when boundary rules change
- **`pyproject.toml`**: document any new `[tool.ruff.lint.per-file-ignores]` entries with justification
- **`.pre-commit-config.yaml`**: update hook versions if upgraded

---

## Completion checklist

**This task is complete when, and only when**: `rules/toolchain.md` "Completion checklist
(common to all tasks)" is satisfied in full, the item below also holds, and no Step above
ended in an unresolved `Blocked` state.

Satisfy `rules/toolchain.md` "Completion checklist (common to all tasks)" in full. In addition:

- all suppressions have inline justification

---

## Prohibited behavior

See `SKILL.md` Strict Diff Isolation (Step 10 above enforces it) and `rules/coding.md` for
project-wide prohibitions (suppression governance, commit hygiene).
