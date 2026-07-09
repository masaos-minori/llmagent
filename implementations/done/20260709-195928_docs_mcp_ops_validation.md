# Implementation: docs — MCP ops cross-doc consistency validation

## Goal

Verify no stale or contradictory content exists across MCP docs after migration checklist, GitHub deny controls, and watchdog updates.

## Scope

- All MCP and agent docs

## Implementation

### Procedure

1. Check cross-doc terminology consistency:
   ```bash
   rg "fail_open\|auth_token\|watchdog" docs/ | sort
   ```
2. Verify terms used consistently (same meaning across docs).
3. Run format check:
   ```bash
   uv run ruff check docs/ --fix
   ```

### Details

- No file creation needed; verification only.

## Validation plan

| Check | Tool / Command | Target |
|---|---|---|
| Consistency | `rg "fail_open\|auth_token\|watchdog" docs/` | Consistent usage |
| Format | `uv run ruff check docs/` | 0 errors |
