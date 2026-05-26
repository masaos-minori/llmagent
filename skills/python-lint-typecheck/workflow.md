# Lint Typecheck — Detailed Workflow

## Step 1: Identify Failure Source

**Fast path** — if the failing tool is already identified from the error message, skip to that step:
- `ruff` error → Step 2
- `mypy`/`pyright` error → Step 6
- `lint-imports` violation → Step 3
- `bandit` finding → Step 7
- Suppression without justification → Step 4

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

```bash
# no bare except
ast-grep --pattern 'except: $$$' --lang python scripts/

# no print() in library modules
ast-grep --pattern 'print($$$)' --lang python scripts/

# no json.load() outside config_loader.py
ast-grep --pattern 'json.load($$$)' --lang python scripts/ | grep -v config_loader.py

# no top-level assignment patterns that indicate global state
ast-grep --pattern '$VAR = []' --lang python scripts/
```

---

## Step 3: Architecture Integrity

```bash
lint-imports
cat .importlinter
```

If `lint-imports` reports a violation:

1. Read the failing contract in `.importlinter`
2. Determine if the import is intentional or accidental
3. If accidental: remove the import and refactor
4. If intentional: update the contract definition in `.importlinter`

Never suppress a `lint-imports` violation without updating the contract definition.

Cross-reference with ast-grep to find all call sites before removing an import:

```bash
rg "from agent_repl import" scripts/
ast-grep --pattern 'import $MOD' --lang python scripts/agent_commands.py
```

---

## Step 4: Suppression Governance

Audit all existing suppressions:

```bash
rg '# noqa' scripts/ | grep -v '# noqa:'        # noqa without rule code
rg '# type: ignore' scripts/ | grep -v '\['      # ignore without error code
rg '# nosec' scripts/ | grep -v ' -- '           # nosec without comment
```

Every suppression must have:
- `# noqa: <CODE>` — the specific ruff/flake8 rule code
- `# type: ignore[<error-code>]` — the specific mypy error code
- `# nosec <B-code> -- <reason>` — the bandit finding and why it is safe

Suppressions without explanation are prohibited. Fix the root cause rather than suppress when feasible.

---

## Step 5: Semantic Refactor Safety

Use LibCST when a rename or structural change must preserve comments and docstrings.

```python
import libcst as cst

class RenameFunctionArg(cst.CSTTransformer):
    def leave_Param(
        self, original_node: cst.Param, updated_node: cst.Param
    ) -> cst.Param:
        if (
            isinstance(updated_node.name, cst.Name)
            and updated_node.name.value == "old_param"
        ):
            return updated_node.with_changes(name=cst.Name("new_param"))
        return updated_node

source = open("scripts/agent_repl.py").read()
tree = cst.parse_module(source)
new_tree = tree.visit(RenameFunctionArg())
open("scripts/agent_repl.py", "w").write(new_tree.code)
```

After any LibCST transform:

```bash
ruff format scripts/
ruff check scripts/ --fix
python3 -m compileall -q scripts/   # syntax check
```

Verify no old symbol names remain:

```bash
rg "old_param" scripts/
ast-grep --pattern 'old_param' --lang python scripts/
```

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

```bash
bandit -r scripts/ -c pyproject.toml
bandit -r scripts/ -l -ii            # high severity only
bandit scripts/<file>.py
```

Priority findings — must resolve before merge:

| Code | Issue | Fix |
|---|---|---|
| B105/B106 | Hardcoded password/token | Move to env/conf.d |
| B301/B302 | Pickle deserialization | Replace with JSON or Pydantic |
| B501/B502 | TLS verification disabled | Never in production |
| B608 | SQL injection in f-string query | Parameterized queries |
| B404 | subprocess import | Acceptable; document why |
| B603 | subprocess without shell=True | Preferred; document if shell=True needed |

If a finding is a false positive:

```python
result = subprocess.run(cmd)  # nosec B603 — cmd is a validated static list, no user input
```

---

## Step 8: Diff Scope Enforcement

```bash
coverage run -m pytest tests/
coverage xml
diff-cover coverage.xml --compare-branch=main
diff-cover coverage.xml --compare-branch=main --fail-under=90
```

If coverage on changed lines is below 90%:

1. Identify which changed lines are uncovered
2. Add targeted tests for those lines
3. Re-run `diff-cover` to confirm

Do not add tests for unrelated lines to inflate coverage — scope tests to the change.

---

## Step 9: CI Consistency Validation

```bash
tox -e lint        # ruff in isolated env
tox -e typecheck   # mypy in isolated env
tox -e security    # bandit in isolated env
tox -e tests       # pytest in isolated env
tox                # all four in sequence
```

If tox passes locally but fails in CI: check that `pyproject.toml` tox env definitions match the CI configuration.
If tox fails locally but passes manually: recreate the env and check `tox.ini` deps.

```bash
tox --recreate -e lint
```

---

## Step 10: Minimal Change Principle

- stage files individually — never `git add -A` or `git add .`
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
- `mypy scripts/` — no new errors (pre-existing may remain)
- `lint-imports` — 0 violations
- `bandit -r scripts/ -c pyproject.toml` — no HIGH findings unaddressed
- `diff-cover coverage.xml --compare-branch=main --fail-under=90` — passes
- `pre-commit run --all-files` — passes
- all suppressions have inline justification
- diff contains only task-relevant changes

---

## Prohibited behavior

- do not add `# noqa`, `# type: ignore`, or `# nosec` without an inline explanation
- do not add global ignores to `pyproject.toml` without justification
- do not suppress `lint-imports` violations without updating the contract definition
- do not reformat unrelated files to reduce the diff noise
- do not fix multiple unrelated issues in the same commit
