# Implementation: memory visibility — full validation

## Goal

Run full validation sequence after all memory visibility changes are implemented.

## Scope

- Full validation sequence

## Implementation

### Procedure

1. Format and lint:
   ```bash
   uv run ruff format scripts/
   uv run ruff check scripts/ --fix
   uv run ruff check scripts/
   ```
2. Type check:
   ```bash
   uv run mypy scripts/
   ```
3. Architecture check:
   ```bash
   PYTHONPATH=scripts uv run lint-imports
   ```
4. Security scan:
   ```bash
   uv run bandit -r scripts/ -c pyproject.toml
   ```
5. Tests:
   ```bash
   uv run pytest tests/test_memory_status.py tests/test_cmd_memory.py -v
   ```
6. Pre-commit:
   ```bash
   uv run pre-commit run --all-files
   ```

## Validation plan

| Check | Tool / Command | Target |
|---|---|---|
| All checks | Full validation sequence | Pass |
