# Implementation: Rename `scripts/shared/tool_routing.py` → `scripts/shared/tool_routing_validation.py`

## Goal

Rename `tool_routing.py` to `tool_routing_validation.py` to reflect its actual responsibility
(drift validation against config and live responses, not runtime routing). Update the module
docstring. Both require-28 and require-29 share this rename step.

## Scope

- In-Scope: `git mv scripts/shared/tool_routing.py scripts/shared/tool_routing_validation.py`;
  update module docstring on line 2 of the renamed file.
- Out-of-Scope: No changes to function bodies or signatures. Import site updates are covered
  by separate implementation docs.

## Assumptions

1. `scripts/shared/tool_routing.py` exists (confirmed by require-28 analysis).
2. `deploy/deploy.sh` uses `rsync -av --delete scripts/`, so the old file is removed from
   deployments automatically after the rename.
3. No file imports `shared.tool_routing` directly; callers used `shared.tool_registry`
   (confirmed by grep: zero direct imports of `shared.tool_routing`).
4. The rename is performed via `git mv` to preserve git history.

## Implementation

### Target file

`scripts/shared/tool_routing_validation.py` (renamed from `tool_routing.py`)

### Procedure

1. Run `git mv scripts/shared/tool_routing.py scripts/shared/tool_routing_validation.py`.
2. Update line 2 of `tool_routing_validation.py`: change the docstring from
   `"""shared/tool_routing.py — ...` to
   `"""shared/tool_routing_validation.py — MCP tool routing drift validation against config and live responses."""`
3. Run `uv run ruff check scripts/shared/tool_routing_validation.py` — expect 0 errors.
4. Run `uv run mypy scripts/shared/tool_routing_validation.py` — expect 0 errors.
5. Verify old path is gone: `ls scripts/shared/tool_routing.py` → "No such file".

### Method

```bash
git mv scripts/shared/tool_routing.py scripts/shared/tool_routing_validation.py
```

Then update line 2 of the docstring in `tool_routing_validation.py`:
```python
"""shared/tool_routing_validation.py — MCP tool routing drift validation against config and live responses."""
```

### Details

- No function bodies change — pure rename + docstring update.
- If `tool_routing_validation.py` imports `ToolRegistry` from `tool_registry.py`, it already uses
  a `TYPE_CHECKING` guard; no circular import issue.

## Validation plan

```bash
# Old path gone
ls scripts/shared/tool_routing.py
# Expected: No such file or directory

# New path exists
ls scripts/shared/tool_routing_validation.py
# Expected: file found

# No stale module path references
grep -rn "shared\.tool_routing[^_]" scripts/ tests/
# Expected: 0 results

# Lint
uv run ruff check scripts/shared/tool_routing_validation.py
# Expected: 0 errors

# Type check
uv run mypy scripts/shared/tool_routing_validation.py
# Expected: 0 errors

# Architecture
PYTHONPATH=scripts uv run lint-imports
# Expected: 0 violations
```
