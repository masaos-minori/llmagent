# rules/toolchain.md — Shared Validation Sequence

## Standard validation sequence

Run in this order after each implementation step.

### 1. Format and lint (ruff)

```bash
uv run ruff format scripts/
uv run ruff check scripts/ --fix
uv run ruff check scripts/       # confirm clean
```

### 2. Type check

```bash
uv run mypy scripts/             # primary
uv run pyright scripts/          # alternate (cross-validate)
```

Fix type errors at the source — do not add `type: ignore` without justification.

### 3. Architecture check (import-linter)

```bash
PYTHONPATH=scripts uv run lint-imports
```

### 4. Constraint verification (ast-grep)

```bash
ast-grep --pattern 'except: $$$' --lang python scripts/
```

### 5. Security scan (bandit)

```bash
uv run bandit -r scripts/ -c pyproject.toml
```

Address high/medium severity findings before proceeding.

### 6. Tests (pytest)

```bash
uv run pytest tests/test_<affected_module>.py -v    # targeted
uv run pytest -v                                     # full suite
uv run pytest tests/test_mdq_rag_boundary.py -v     # boundary enforcement (MDQ/RAG cross-DB and agent-layer direct access)
```

### 7. Diff-scoped coverage (diff-cover)

```bash
uv run coverage run -m pytest tests/
uv run coverage xml
uv run diff-cover coverage.xml --compare-branch=main --fail-under=90
```

### 8. Pre-commit (final gate)

```bash
uv run pre-commit run --all-files
```

### 9. Diff review

```bash
git diff                  # review every changed line before staging
git add scripts/<file>.py # stage specific files
git diff --staged         # confirm what will be committed
```

## Completion checklist (common to all tasks)

- `uv run ruff check scripts/` passes with no errors
- `uv run mypy scripts/` passes (no new regressions vs pre-existing errors)
- `uv run bandit -r scripts/ -c pyproject.toml` passes (no high/medium unaddressed)
- `PYTHONPATH=scripts uv run lint-imports` passes (no architecture boundary violations)
- `uv run pytest` passes with no new failures
- `uv run pytest tests/test_mdq_rag_boundary.py` passes (MDQ/RAG boundary clean)
- `uv run diff-cover coverage.xml --compare-branch=main` ≥ 90% on changed lines
- `uv run pre-commit run --all-files` passes
- diff reviewed and staged selectively with `git add <file>`
- `deploy/deploy.sh` updated if a file under `scripts/` was added or removed
- `config/agent.toml mcp_servers` updated if a new MCP server was added

## Environment setup

```bash
uv sync --dev --system-certs   # create .venv/ and install all deps (first time)
```

## Additional static analysis

```bash
uv run radon cc scripts/ -s -n C                   # cyclomatic complexity — grade C or worse
uv run vulture scripts/ --min-confidence 80        # dead code detection
uv run semgrep --config=p/python scripts/          # semantic pattern enforcement
uv run pip-audit                                   # dependency vulnerability scan
```

## Syntax check

```bash
uv run python -m compileall -q scripts/
```

## MCP documentation consistency

```bash
# Run all checks (startup, failopen, routing, active, toolcount)
uv run check-mcp-docs

# Skip specific checks
uv run check-mcp-docs --skip active --skip toolcount
```

The `check-mcp-docs` entry point is registered in `pyproject.toml`. It verifies:
- Valid startup modes (persistent/ondemand/subprocess)
- No fail-open wording for workflow_allowlist
- Routing authority language consistency
- Active MCP issue cross-references (MCP-01 through MCP-08)
- Tool count consistency against canonical frozensets
