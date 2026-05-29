# rules/toolchain.md — Shared Validation Sequence

## Standard validation sequence

Run in this order after each implementation step.

### 1. Format and lint (ruff)

```bash
ruff format scripts/
ruff check scripts/ --fix
ruff check scripts/       # confirm clean
```

### 2. Type check

```bash
mypy scripts/             # primary
pyright scripts/          # alternate (cross-validate)
```

Fix type errors at the source — do not add `type: ignore` without justification.

### 3. Architecture check (import-linter)

```bash
PYTHONPATH=scripts lint-imports
```

### 4. Constraint verification (ast-grep)

```bash
ast-grep --pattern 'except: $$$' --lang python scripts/
```

### 5. Security scan (bandit)

```bash
bandit -r scripts/ -c pyproject.toml
```

Address high/medium severity findings before proceeding.

### 6. Tests (pytest)

```bash
pytest tests/test_<affected_module>.py -v    # targeted
pytest -v                                     # full suite
```

### 7. Diff-scoped coverage (diff-cover)

```bash
coverage run -m pytest tests/
coverage xml
diff-cover coverage.xml --compare-branch=main --fail-under=90
```

### 8. Pre-commit (final gate)

```bash
pre-commit run --all-files
```

### 9. Diff review

```bash
git diff                  # review every changed line before staging
git add scripts/<file>.py # stage specific files
git diff --staged         # confirm what will be committed
```

## Completion checklist (common to all tasks)

- `ruff check scripts/` passes with no errors
- `mypy scripts/` passes (no new regressions vs pre-existing errors)
- `bandit -r scripts/ -c pyproject.toml` passes (no high/medium unaddressed)
- `lint-imports` passes (no architecture boundary violations)
- `pytest` passes with no new failures
- `diff-cover coverage.xml --compare-branch=main` ≥ 90% on changed lines
- `pre-commit run --all-files` passes
- diff reviewed and staged selectively with `git add <file>`
- `deploy/deploy.sh` updated if a file under `scripts/` was added or removed
- `config/agent.toml mcp_servers` updated if a new MCP server was added

## Environment setup

```bash
uv sync --dev --system-certs   # create .venv/ and install all deps (first time)
source .venv/bin/activate       # activate dev venv
```

## Additional static analysis

```bash
radon cc scripts/ -s -n C                   # cyclomatic complexity — grade C or worse
vulture scripts/ --min-confidence 80        # dead code detection
semgrep --config=p/python scripts/          # semantic pattern enforcement
pip-audit                                   # dependency vulnerability scan
```

## Syntax check (no venv required)

```bash
python3 -m compileall -q scripts/
```
