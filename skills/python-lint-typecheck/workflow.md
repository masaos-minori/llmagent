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

Classify the failure type: lint / type error / import boundary / security finding / suppression violation.
Do not fix any issue until you know which tool found it and why.

---

## Step 2: Repository Convention Enforcement

#### ruff — format and lint

```bash
ruff format scripts/                  # reformat (line length, quote style)
ruff check scripts/ --fix             # auto-fix safe violations (imports, unused vars)
ruff check scripts/                   # remaining issues need manual fix
ruff check scripts/<file>.py --select E,W,F,I,UP   # narrow to one file
```

After auto-fix, review the diff. Only accept changes that are correct — do not trust auto-fix blindly on complex expressions.

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
4. If intentional: update the contract definition in `.importlinter`

Never suppress a `lint-imports` violation without updating the contract definition.

Cross-reference with ast-grep to find all call sites before removing an import:

```bash
rg "from agent.repl import" scripts/
ast-grep --pattern 'import $MOD' --lang python scripts/agent/commands/registry.py
```

---

## Step 4: Suppression Governance

Audit all existing suppressions using the commands and required format defined in
`rules/coding.md` Suppression governance. Fix the root cause rather than suppress when feasible.

---

## Step 5: Semantic Refactor Safety

If a rename or structural change must preserve comments and docstrings, use the LibCST
transform recipe and post-transform verification commands in
`skills/python-refactoring/workflow.md` Phase 3 (Semantic Transformation).

---

## Step 6: Type Flow Analysis

#### mypy — primary

```bash
mypy scripts/
mypy scripts/<file>.py --strict
mypy scripts/ --show-error-codes   # always include error codes
```

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

---

## Step 7: Static Security Validation

See `rules/toolchain.md` section 5 for bandit commands.

Priority findings — must resolve before merge: see `rules/coding.md` Bandit priority findings.

---

## Step 8: Diff Scope Enforcement

See `rules/toolchain.md` section 7.

If coverage on changed lines is below 90%:

1. Identify which changed lines are uncovered
2. Add targeted tests for those lines
3. Re-run `diff-cover` to confirm

Do not add tests for unrelated lines to inflate coverage — scope tests to the change.

---

## Step 9: CI Consistency Validation

Run the full pre-commit gate to match CI behavior:

```bash
pre-commit run --all-files
```

Or run individual checks directly:

```bash
ruff format scripts/
ruff check scripts/ --fix && ruff check scripts/
PYTHONPATH=scripts mypy scripts/ tests/
bandit -r scripts/ -c pyproject.toml
PYTHONPATH=scripts pytest tests/ -q
```

If using tox (requires tox.ini to be configured — not in the default dev workflow):

```bash
tox -e lint && tox -e typecheck && tox -e tests
```

---

## Step 10: Minimal Change Principle

- do not reformat files unrelated to the task
- do not fix unrelated lint issues in the same commit
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

- `ruff check scripts/` — 0 errors
- `PYTHONPATH=scripts mypy scripts/ tests/` — no new errors (pre-existing may remain)
- `PYTHONPATH=scripts lint-imports` — 0 violations
- `bandit -r scripts/ -c pyproject.toml` — no HIGH findings unaddressed
- `diff-cover coverage.xml --compare-branch=master --fail-under=90` — passes
- `pre-commit run --all-files` — passes
- all suppressions have inline justification
- diff contains only task-relevant changes

---

## Prohibited behavior

- do not reformat unrelated files to reduce the diff noise
- do not fix multiple unrelated issues in the same commit

See also `rules/coding.md` for project-wide prohibitions (suppression governance, commit hygiene).
