# Implementation: installer_templates.py — Replace run() with run_http()

## Goal

Change `{cls}().run()` to `{cls}().run_http()` in the generated server script template.

## Scope

- `scripts/mcp/installer_templates.py`: one string replacement.

## Implementation

### Target file

`scripts/mcp/installer_templates.py`

### Procedure

Replace:
```python
            {cls}().run()
```
With:
```python
            {cls}().run_http()
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| No `.run()` | `grep "\.run()" scripts/mcp/installer_templates.py` | 0 matches |
| Lint | `uv run ruff check scripts/mcp/installer_templates.py` | 0 errors |
| Tests | `uv run pytest tests/ -q` | all pass |
