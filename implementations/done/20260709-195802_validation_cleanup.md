# Implementation: validation and cleanup

## Goal

Run full validation sequence after implementing all production hardening changes. Update `deploy/deploy.sh` if new files added.

## Scope

- Full validation sequence (ruff, mypy, lint-imports, bandit, pytest, diff-cover, pre-commit)
- `deploy/deploy.sh` update if needed

## Assumptions

1. All Phase 1-4 implementation is complete and committed.
2. The project uses `tox` with environments: `lint`, `typecheck`, `security`, `tests`.

## Implementation

### Procedure

1. Run format and lint:
   ```bash
   uv run ruff format scripts/
   uv run ruff check scripts/ --fix
   uv run ruff check scripts/
   ```

2. Run type check:
   ```bash
   uv run mypy scripts/
   ```

3. Run architecture check:
   ```bash
   PYTHONPATH=scripts uv run lint-imports
   ```

4. Run constraint verification:
   ```bash
   ast-grep --pattern 'except: $$$' --lang python scripts/
   ```

5. Run security scan:
   ```bash
   uv run bandit -r scripts/ -c pyproject.toml
   ```

6. Run tests:
   ```bash
   uv run pytest tests/test_production_config_validator.py -v
   uv run pytest tests/test_repl_health.py -v
   ```

7. Run diff-cover:
   ```bash
   uv run coverage run -m pytest tests/
   uv run coverage xml
   uv run diff-cover coverage.xml --compare-branch=main --fail-under=90
   ```

8. Run pre-commit:
   ```bash
   uv run pre-commit run --all-files
   ```

9. Update `deploy/deploy.sh` if any file under `scripts/` was added or removed.

### Details

- No new files expected (all changes are modifications to existing files).
- `tests/test_production_config_validator.py` already exists; extend, don't recreate.

## Validation plan

| Check | Tool / Command | Target |
|---|---|---|
| All checks | Full validation sequence | Pass |
| Coverage | `diff-cover` | >= 90% |
